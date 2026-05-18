"use client";

import { useState, useRef } from "react";
import { Upload, AlertCircle, CheckCircle2, X, Camera } from "lucide-react";

export type HaircutType =
  | "fade"
  | "skin_fade"
  | "zero_fade"
  | "low_fade"
  | "mid_fade"
  | "high_fade"
  | "drop_fade"
  | "taper"
  | "french_crop"
  | "quiff"
  | "pompadour"
  | "slick_back"
  | "undercut"
  | "modern_mullet"
  | "mohawk"
  | "caesar"
  | "buzz_cut"
  | "crew_cut";

export type PhotoAngle = "frontal" | "lateral";

interface ReferencePhotoUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  barber_id: string;
  onSuccess?: (photo: any) => void;
}

const HAIRCUT_TYPES: { value: HaircutType; label: string }[] = [
  { value: "fade", label: "Fade" },
  { value: "skin_fade", label: "Skin Fade" },
  { value: "zero_fade", label: "Zero Fade" },
  { value: "low_fade", label: "Low Fade" },
  { value: "mid_fade", label: "Mid Fade" },
  { value: "high_fade", label: "High Fade" },
  { value: "drop_fade", label: "Drop Fade" },
  { value: "taper", label: "Taper" },
  { value: "french_crop", label: "French Crop" },
  { value: "quiff", label: "Quiff" },
  { value: "pompadour", label: "Pompadour" },
  { value: "slick_back", label: "Slick Back" },
  { value: "undercut", label: "Undercut" },
  { value: "modern_mullet", label: "Modern Mullet" },
  { value: "mohawk", label: "Mohawk" },
  { value: "caesar", label: "Caesar" },
  { value: "buzz_cut", label: "Buzz Cut" },
  { value: "crew_cut", label: "Crew Cut" },
];

const PHOTO_ANGLES: { value: PhotoAngle; label: string; description: string }[] = [
  { value: "frontal", label: "Frontal", description: "Cara de frente (0°)" },
  { value: "lateral", label: "Lateral", description: "Perfil (90°)" },
];

type UploadStatus = "idle" | "selecting" | "uploading" | "success" | "error";

export default function ReferencePhotoUploadModal({
  isOpen,
  onClose,
  barber_id,
  onSuccess,
}: ReferencePhotoUploadModalProps) {
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [error, setError] = useState("");
  const [haircut, setHaircut] = useState<HaircutType>("fade");
  const [angle, setAngle] = useState<PhotoAngle>("frontal");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [qualityScore, setQualityScore] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    // Validate file
    if (!selectedFile.type.startsWith("image/")) {
      setError("Por favor, selecciona una imagen (JPG, PNG, etc.)");
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setError("Foto demasiado grande (máx 10MB)");
      return;
    }

    // Preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target?.result as string);
      setFile(selectedFile);
      setStatus("selecting");
      setError("");
    };
    reader.readAsDataURL(selectedFile);
  };

  const handleUpload = async () => {
    if (!file || !haircut || !angle) {
      setError("Por favor, completa todos los campos");
      return;
    }

    setStatus("uploading");
    setError("");

    try {
      const { api } = await import("@/lib/api");
      const data = await api.uploadReferencePhoto(barber_id, file, haircut, angle);

      setQualityScore(data.quality_score);
      setStatus("success");

      if (onSuccess) {
        onSuccess(data);
      }

      // Reset after 2 seconds
      setTimeout(() => {
        resetForm();
        onClose();
      }, 2000);
    } catch (err: any) {
      setStatus("error");
      setError(err.message || "Error al subir la foto");
    }
  };

  const resetForm = () => {
    setStatus("idle");
    setFile(null);
    setPreview(null);
    setQualityScore(null);
    setError("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
      <div className="bg-gray-900 border border-gray-800 rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-800 sticky top-0 bg-gray-900">
          <h2 className="text-white font-bold text-lg flex items-center gap-2">
            <Camera className="h-5 w-5" />
            Subir Foto de Referencia
          </h2>
          <button
            onClick={() => {
              resetForm();
              onClose();
            }}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Step 1: Select Haircut Type */}
          <div>
            <label className="block text-white font-semibold mb-3">1. Tipo de Corte</label>
            <select
              value={haircut}
              onChange={(e) => setHaircut(e.target.value as HaircutType)}
              disabled={status === "uploading"}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:border-gold focus:outline-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed appearance-none cursor-pointer"
            >
              {HAIRCUT_TYPES.map((h) => (
                <option key={h.value} value={h.value}>
                  {h.label}
                </option>
              ))}
            </select>
            <p className="text-gray-400 text-xs mt-2">
              Selecciona el tipo de corte para esta foto
            </p>
          </div>

          {/* Step 2: Select Angle */}
          <div>
            <label className="block text-white font-semibold mb-3">2. Ángulo de Foto</label>
            <div className="space-y-2">
              {PHOTO_ANGLES.map((a) => (
                <label
                  key={a.value}
                  className={`flex items-center p-3 rounded border cursor-pointer transition-colors ${
                    angle === a.value
                      ? "border-gold bg-gold/10"
                      : "border-gray-700 hover:border-gray-600"
                  } ${status === "uploading" ? "opacity-50 cursor-not-allowed" : ""}`}
                >
                  <input
                    type="radio"
                    name="angle"
                    value={a.value}
                    checked={angle === a.value}
                    onChange={(e) => setAngle(e.target.value as PhotoAngle)}
                    disabled={status === "uploading"}
                    className="mr-3 cursor-pointer"
                  />
                  <div>
                    <p className="text-white font-medium">{a.label}</p>
                    <p className="text-gray-400 text-xs">{a.description}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Step 3: Upload Photo */}
          <div>
            <label className="block text-white font-semibold mb-3">3. Foto</label>

            {!preview ? (
              <div
                onClick={() => !status || status === "idle" ? fileInputRef.current?.click() : null}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  status === "uploading"
                    ? "border-gray-700 bg-gray-800/30 opacity-50 cursor-not-allowed"
                    : "border-gray-700 hover:border-gold hover:bg-gold/5"
                }`}
              >
                <Upload className="h-8 w-8 text-gray-500 mx-auto mb-2" />
                <p className="text-white font-medium mb-1">Selecciona una foto</p>
                <p className="text-gray-400 text-xs">
                  O arrastra tu foto aquí
                  <br />
                  (JPG, PNG • Max 10MB)
                </p>
              </div>
            ) : (
              <div className="relative">
                <img
                  src={preview}
                  alt="Preview"
                  className="w-full rounded-lg max-h-72 object-cover"
                />
                <button
                  onClick={() => {
                    setPreview(null);
                    setFile(null);
                    if (fileInputRef.current) {
                      fileInputRef.current.value = "";
                    }
                  }}
                  disabled={status === "uploading"}
                  className="absolute top-2 right-2 bg-black/50 hover:bg-black text-white p-1 rounded transition-colors disabled:opacity-50"
                >
                  <X className="h-4 w-4" />
                </button>

                {qualityScore !== null && (
                  <div className="mt-2 bg-blue-900/30 border border-blue-700/50 rounded p-3">
                    <p className="text-blue-200 text-xs font-medium">
                      Calidad: {(qualityScore * 100).toFixed(0)}%
                    </p>
                  </div>
                )}
              </div>
            )}

            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              disabled={status === "uploading"}
              className="hidden"
            />

            <p className="text-gray-400 text-xs mt-2">
              La foto se analizará con MediaPipe para extraer parámetros del corte
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-900/30 border border-red-700/50 rounded p-3 flex gap-2">
              <AlertCircle className="h-4 w-4 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-red-200 text-xs">{error}</p>
            </div>
          )}

          {/* Status Messages */}
          {status === "uploading" && (
            <div className="bg-blue-900/30 border border-blue-700/50 rounded p-3 flex gap-2">
              <div className="animate-spin">
                <div className="h-4 w-4 border-2 border-blue-400 border-t-transparent rounded-full" />
              </div>
              <p className="text-blue-200 text-xs">Subiendo foto...</p>
            </div>
          )}

          {status === "success" && (
            <div className="bg-green-900/30 border border-green-700/50 rounded p-3 flex gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-green-200 text-xs font-medium">¡Foto subida correctamente!</p>
                <p className="text-green-200/70 text-xs">
                  Será validada en las próximas 24 horas
                </p>
              </div>
            </div>
          )}

          {/* Buttons */}
          <div className="flex gap-3 pt-4 border-t border-gray-800">
            <button
              onClick={() => {
                resetForm();
                onClose();
              }}
              disabled={status === "uploading"}
              className="flex-1 bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancelar
            </button>
            <button
              onClick={handleUpload}
              disabled={!preview || status === "uploading" || status === "success"}
              className="flex-1 bg-gold hover:bg-gold/90 text-black px-4 py-2 rounded font-bold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {status === "uploading" ? "Subiendo..." : "Subir Foto"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
