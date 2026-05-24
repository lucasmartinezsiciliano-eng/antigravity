"use client";

import { Suspense, useState, useRef, useEffect, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Camera, CheckCircle2, Upload, ChevronRight, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";

// Same enum as backend HaircutType
const HAIRCUT_TYPES = [
  // Fades
  { value: "skin_fade", label: "Skin Fade" },
  { value: "low_fade", label: "Low Fade" },
  { value: "mid_fade", label: "Mid Fade" },
  { value: "high_fade", label: "High Fade" },
  { value: "drop_fade", label: "Drop Fade" },
  { value: "burst_fade", label: "Burst Fade" },
  { value: "blowout_fade", label: "Blowout Fade" },
  // Tapers & crops
  { value: "taper", label: "Taper" },
  { value: "french_crop", label: "French Crop" },
  { value: "textured_crop", label: "Textured Crop" },
  { value: "edgar_cut", label: "Edgar Cut" },
  { value: "caesar", label: "Caesar" },
  { value: "buzz_cut", label: "Buzz Cut" },
  { value: "crew_cut", label: "Crew Cut" },
  // Styled tops
  { value: "quiff", label: "Quiff" },
  { value: "pompadour", label: "Pompadour" },
  { value: "slick_back", label: "Slick Back" },
  { value: "undercut", label: "Undercut" },
  { value: "curtains", label: "Curtains" },
  { value: "wolf_cut", label: "Wolf Cut" },
  { value: "modern_mullet", label: "Modern Mullet" },
  { value: "mohawk", label: "Mohawk" },
  { value: "afro_taper", label: "Afro Taper" },
  { value: "bro_flow", label: "Bro Flow" },
] as const;

type PhotoAngle = "frontal" | "lateral";

const ANGLE_CONFIG: Record<PhotoAngle, { label: string; hint: string }> = {
  frontal: { label: "Frontal", hint: "De frente, corte completo" },
  lateral: { label: "Lateral", hint: "Perfil 90°, graduación" },
};

interface UploadedPhoto {
  id: string;
  haircut_type: string;
  photo_angle: string;
  cloudinary_url: string;
}

// Minimum to activate code: 1 type with BOTH frontal + lateral photos
const MIN_COMPLETE_TYPES = 1;

function FotosReferenciaPage() {
  const params = useSearchParams();
  const router = useRouter();
  const barberId = params.get("id") || "";

  const [uploaded, setUploaded] = useState<UploadedPhoto[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState<string | null>(null); // "skin_fade_back" etc.
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const pendingUpload = useRef<{ type: string; angle: PhotoAngle } | null>(null);

  // Load existing photos
  const loadPhotos = useCallback(async () => {
    if (!barberId) return;
    try {
      const photos = await api.getBarberReferencePhotos(barberId);
      setUploaded(photos as UploadedPhoto[]);
    } catch {
      // Barber may have no photos yet
    } finally {
      setLoading(false);
    }
  }, [barberId]);

  useEffect(() => { loadPhotos(); }, [loadPhotos]);

  // A type is complete when it has BOTH frontal + lateral — both are mandatory.
  function getCompleteTypes(): string[] {
    return HAIRCUT_TYPES
      .map(({ value }) => value)
      .filter((type) =>
        uploaded.some((p) => p.haircut_type === type && p.photo_angle === "frontal") &&
        uploaded.some((p) => p.haircut_type === type && p.photo_angle === "lateral")
      );
  }

  const completeTypes = getCompleteTypes();
  const canContinue = completeTypes.length >= MIN_COMPLETE_TYPES;

  function hasPhoto(type: string, angle: PhotoAngle): boolean {
    return uploaded.some((p) => p.haircut_type === type && p.photo_angle === angle);
  }

  function triggerUpload(type: string, angle: PhotoAngle) {
    pendingUpload.current = { type, angle };
    fileRef.current?.click();
  }

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !pendingUpload.current) return;

    const { type, angle } = pendingUpload.current;
    const key = `${type}_${angle}`;
    setUploading(key);
    setError("");

    try {
      const data = await api.uploadReferencePhoto(barberId, file, type, angle);
      setUploaded((prev) => [
        ...prev,
        {
          id: data.id,
          haircut_type: type,
          photo_angle: angle,
          cloudinary_url: data.cloudinary_url,
        },
      ]);
    } catch (err: any) {
      setError(err.message || "Error al subir la foto");
    } finally {
      setUploading(null);
      pendingUpload.current = null;
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  if (!barberId) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <p className="text-gray-400">ID de barbero no encontrado</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black">
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        onChange={handleFile}
        className="hidden"
      />

      {/* Header */}
      <div className="sticky top-0 bg-black/95 backdrop-blur border-b border-gray-800 z-10 px-4 py-4">
        <div className="max-w-lg mx-auto">
          <div className="flex items-center gap-3 mb-3">
            <Camera className="h-6 w-6 text-[#C9A84C]" />
            <h1 className="text-white text-xl font-bold">Fotos de referencia</h1>
          </div>
          <p className="text-gray-400 text-sm leading-relaxed">
            Sube fotos reales de tus cortes: <span className="text-[#C9A84C] font-semibold">frontal</span> (de frente, corte completo) y <span className="text-[#C9A84C] font-semibold">lateral</span> (perfil 90°, graduación).
            La IA usa estas fotos como referencia — nunca las verá el cliente.
          </p>

          {/* Progress */}
          <div className="mt-3 flex items-center justify-between">
            <span className="text-xs text-gray-500">
              {completeTypes.length} tipo{completeTypes.length !== 1 ? "s" : ""} completo{completeTypes.length !== 1 ? "s" : ""}
              {" "}(frontal + lateral, min. {MIN_COMPLETE_TYPES})
            </span>
            <span className={`text-xs font-bold ${canContinue ? "text-green-400" : "text-[#C9A84C]"}`}>
              {canContinue ? "Puedes continuar" : "Sube frontal + lateral de 1 corte"}
            </span>
          </div>
          <div className="mt-2 h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${Math.min(100, (completeTypes.length / Math.max(MIN_COMPLETE_TYPES, 3)) * 100)}%`,
                background: canContinue ? "#22c55e" : "#C9A84C",
              }}
            />
          </div>
        </div>
      </div>

      {/* Important notice */}
      <div className="max-w-lg mx-auto px-4 pt-4">
        <div className="bg-[#C9A84C]/10 border border-[#C9A84C]/30 rounded-lg p-3 mb-4">
          <p className="text-[#C9A84C] text-xs font-semibold mb-1">
            📸 Fotos reales de tus cortes
          </p>
          <p className="text-gray-400 text-xs leading-relaxed">
            Frontal: cliente mirando a cámara, se ve la forma del corte completo.
            Lateral: perfil 90°, se ve la graduación y la longitud.
            Tus fotos son privadas — el cliente solo ve su propia imagen con el corte generado.
          </p>
        </div>
      </div>

      {/* Haircut type grid */}
      <div className="max-w-lg mx-auto px-4 pb-32">
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin h-6 w-6 border-2 border-[#C9A84C] border-t-transparent rounded-full mx-auto" />
            <p className="text-gray-500 text-sm mt-3">Cargando fotos...</p>
          </div>
        ) : (
          <div className="space-y-3">
            {HAIRCUT_TYPES.map(({ value, label }) => {
              const hasFrontal = hasPhoto(value, "frontal");
              const hasLateral = hasPhoto(value, "lateral");
              const isComplete = hasFrontal && hasLateral; // both mandatory

              return (
                <div
                  key={value}
                  className={`border rounded-xl p-4 transition-colors ${
                    isComplete
                      ? "border-green-700/50 bg-green-900/10"
                      : hasFrontal || hasLateral
                        ? "border-[#C9A84C]/40 bg-[#C9A84C]/5"
                        : "border-gray-800 bg-gray-900/50"
                  }`}
                >
                  {/* Cut name + status */}
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-white font-semibold text-sm">{label}</span>
                    {isComplete && (
                      <span className="flex items-center gap-1 text-green-400 text-xs font-semibold">
                        <CheckCircle2 className="h-3.5 w-3.5" /> Activo
                      </span>
                    )}
                  </div>

                  {/* Photo slots — frontal (mandatory) + lateral (recommended) */}
                  <div className="grid grid-cols-2 gap-3">
                    {(["frontal", "lateral"] as PhotoAngle[]).map((angle) => {
                      const has = hasPhoto(value, angle);
                      const isUploading = uploading === `${value}_${angle}`;
                      const photo = uploaded.find(
                        (p) => p.haircut_type === value && p.photo_angle === angle
                      );
                      const cfg = ANGLE_CONFIG[angle];
                      const isMandatory = true; // frontal and lateral both mandatory

                      return (
                        <button
                          key={angle}
                          type="button"
                          onClick={() => !has && !isUploading && triggerUpload(value, angle)}
                          disabled={has || isUploading}
                          className={`relative rounded-lg border-2 border-dashed h-24 flex flex-col items-center justify-center gap-1 transition-all ${
                            has
                              ? "border-solid border-green-700/50 bg-green-900/20 cursor-default"
                              : isUploading
                                ? "border-[#C9A84C]/50 bg-[#C9A84C]/5 cursor-wait"
                                : "border-gray-700 hover:border-[#C9A84C] hover:bg-[#C9A84C]/5 cursor-pointer"
                          }`}
                        >
                          {has && photo?.cloudinary_url ? (
                            <>
                              <img
                                src={photo.cloudinary_url}
                                alt={`${label} ${angle}`}
                                className="absolute inset-0 w-full h-full object-cover rounded-lg opacity-40"
                              />
                              <CheckCircle2 className="h-5 w-5 text-green-400 relative z-10" />
                              <span className="text-green-300 text-xs font-medium relative z-10">
                                {cfg.label}
                              </span>
                            </>
                          ) : isUploading ? (
                            <>
                              <div className="animate-spin h-5 w-5 border-2 border-[#C9A84C] border-t-transparent rounded-full" />
                              <span className="text-[#C9A84C] text-xs">Subiendo...</span>
                            </>
                          ) : (
                            <>
                              <Upload className="h-5 w-5 text-gray-500" />
                              <span className="text-gray-400 text-xs">{cfg.label}</span>
                              <span className="text-gray-600 text-[10px]">{cfg.hint}</span>
                              {isMandatory && (
                                <span className="text-[#C9A84C] text-[9px] font-bold uppercase tracking-wide">obligatoria</span>
                              )}
                            </>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="fixed bottom-20 left-4 right-4 max-w-lg mx-auto z-20">
          <div className="bg-red-900/90 border border-red-700 rounded-lg p-3 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-red-400 flex-shrink-0" />
            <p className="text-red-200 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Bottom CTA */}
      <div className="fixed bottom-0 left-0 right-0 bg-black/95 backdrop-blur border-t border-gray-800 p-4 z-10">
        <div className="max-w-lg mx-auto flex gap-3">
          <button
            type="button"
            onClick={() => router.push(`/barber/dashboard?id=${barberId}`)}
            className="flex-1 bg-gray-800 text-gray-300 px-4 py-3 rounded-xl font-medium text-sm"
          >
            {canContinue ? "Ir al panel" : "Omitir por ahora"}
          </button>
          {canContinue && (
            <button
              type="button"
              onClick={() => router.push(`/barber/dashboard?id=${barberId}`)}
              className="flex-1 bg-[#C9A84C] text-black px-4 py-3 rounded-xl font-bold text-sm flex items-center justify-center gap-2"
            >
              Continuar al panel
              <ChevronRight className="h-4 w-4" />
            </button>
          )}
        </div>
        {!canContinue && (
          <p className="text-center text-gray-500 text-xs mt-2 max-w-lg mx-auto">
            Tu código no estará activo hasta que subas frontal + lateral de al menos 1 corte
          </p>
        )}
      </div>
    </div>
  );
}

export default function FotosReferenciaPageWrapper() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="animate-spin h-6 w-6 border-2 border-[#C9A84C] border-t-transparent rounded-full" />
      </div>
    }>
      <FotosReferenciaPage />
    </Suspense>
  );
}
