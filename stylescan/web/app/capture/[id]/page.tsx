"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { ChevronLeft, Check } from "lucide-react";
import { api } from "@/lib/api";
import { storage } from "@/lib/storage";

const SHOTS = [
  { label: "Frontal",          hint: "Mira directamente a la cámara" },
  { label: "Perfil izquierdo", hint: "Gira la cabeza hacia tu izquierda" },
  { label: "Perfil derecho",   hint: "Gira la cabeza hacia tu derecha" },
];

type Stage = "camera" | "preview" | "uploading" | "processing" | "error";

export default function CapturePage() {
  const params  = useParams();
  const id      = params.id as string;

  const videoRef     = useRef<HTMLVideoElement>(null);
  const canvasRef    = useRef<HTMLCanvasElement>(null);
  const streamRef    = useRef<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef      = useRef<ReturnType<typeof setInterval> | null>(null);
  const shotIdxRef   = useRef(0);
  const photosRef    = useRef<File[]>([]);

  const [stage,        setStage]        = useState<Stage>("camera");
  const [cameraReady,  setCameraReady]  = useState(false);
  const [shotIndex,    setShotIndex]    = useState(0);
  const [previewUrl,   setPreviewUrl]   = useState<string>("");
  const [previewBlob,  setPreviewBlob]  = useState<Blob | null>(null);
  const [flashActive,  setFlashActive]  = useState(false);
  const [error,        setError]        = useState("");

  /* ── camera helpers ── */
  const stopStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setCameraReady(false);
  }, []);

  useEffect(() => () => {
    stopStream();
    if (pollRef.current) clearInterval(pollRef.current);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
  }, [stopStream]);  // eslint-disable-line

  useEffect(() => { startCamera(); }, []);  // eslint-disable-line

  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 960 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await new Promise<void>((res) => { videoRef.current!.onloadedmetadata = () => res(); });
        await videoRef.current.play();
      }
      setCameraReady(true);
    } catch {
      setCameraReady(false);
    }
  }

  /* ── save photo to sessionStorage for auto-visuals ── */
  function savePhotoToSession(blob: Blob, key: string) {
    const small = document.createElement("canvas");
    const src   = document.createElement("canvas");
    const img   = document.createElement("img");
    const url   = URL.createObjectURL(blob);
    img.onload = () => {
      const scale = Math.min(1, 640 / img.width);
      src.width  = img.width;
      src.height = img.height;
      src.getContext("2d")?.drawImage(img, 0, 0);
      small.width  = Math.round(img.width  * scale);
      small.height = Math.round(img.height * scale);
      small.getContext("2d")?.drawImage(src, 0, 0, small.width, small.height);
      small.toBlob((b) => {
        if (!b) return;
        const reader = new FileReader();
        reader.onloadend = () => {
          try { sessionStorage.setItem(key, reader.result as string); } catch {}
        };
        reader.readAsDataURL(b);
      }, "image/jpeg", 0.65);
      URL.revokeObjectURL(url);
    };
    img.src = url;
  }

  /* ── capture: show flash + preview ── */
  function captureFrame() {
    const video  = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    if (video.readyState < 2) return;

    // Flash effect
    setFlashActive(true);
    setTimeout(() => setFlashActive(false), 250);

    canvas.width  = video.videoWidth  || 1280;
    canvas.height = video.videoHeight || 960;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      if (!blob) return;
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setPreviewBlob(blob);
      setPreviewUrl(URL.createObjectURL(blob));
      setStage("preview");
    }, "image/jpeg", 0.92);
  }

  /* ── confirm preview → accept photo ── */
  function confirmPhoto() {
    if (!previewBlob) return;
    const idx = shotIdxRef.current;
    if (idx === 0) savePhotoToSession(previewBlob, `visai_frontal_${id}`);
    if (idx === 1) savePhotoToSession(previewBlob, `visai_profile_${id}`);
    const file = new File([previewBlob], `photo_${idx + 1}.jpg`, { type: "image/jpeg" });
    photosRef.current = [...photosRef.current, file];
    const next = idx + 1;
    shotIdxRef.current = next;
    setShotIndex(next);
    setPreviewBlob(null);
    if (previewUrl) { URL.revokeObjectURL(previewUrl); setPreviewUrl(""); }
    if (next >= SHOTS.length) {
      stopStream();
      setStage("uploading");
      handleUpload(photosRef.current);
    } else {
      setStage("camera");
    }
  }

  /* ── retake: go back to camera ── */
  function retakePhoto() {
    setPreviewBlob(null);
    if (previewUrl) { URL.revokeObjectURL(previewUrl); setPreviewUrl(""); }
    setStage("camera");
  }

  /* ── fallback: file chosen from picker ── */
  function onFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = "";
    // Show preview for file input too
    const blob = file.slice(0, file.size, file.type);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewBlob(blob);
    setPreviewUrl(URL.createObjectURL(blob));
    setStage("preview");
  }

  /* ── repetir (undo last accepted photo) ── */
  function handleRepeat() {
    const idx     = shotIdxRef.current;
    const prevIdx = Math.max(0, idx - 1);
    photosRef.current   = photosRef.current.slice(0, prevIdx);
    shotIdxRef.current  = prevIdx;
    setShotIndex(prevIdx);
  }

  /* ── upload ── */
  async function handleUpload(files: File[]) {
    storage.saveAnalysisId(id);
    setError("");
    try {
      await api.uploadPhotos(id, files);
      setStage("processing");
      pollRef.current = setInterval(async () => {
        try {
          const status = await api.getAnalysisStatus(id);
          if (status.code === 200 && status.result?.face_shape) {
            clearInterval(pollRef.current!);
            pollRef.current = null;
            window.location.href = `/result/${id}`;
          }
        } catch (e: any) {
          clearInterval(pollRef.current!);
          pollRef.current = null;
          setError(e.message || "Error al obtener el resultado.");
          setStage("error");
        }
      }, 3000);
    } catch (e: any) {
      setError(e.message || "Error al subir las fotos. Inténtalo de nuevo.");
      setStage("error");
    }
  }

  function handleRetry() {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
    photosRef.current  = [];
    shotIdxRef.current = 0;
    setShotIndex(0);
    setError("");
    setStage("camera");
    startCamera();
  }

  /* ── loading screens ── */
  if (stage === "uploading" || stage === "processing") {
    return (
      <div className="screen" style={{ alignItems: "center", justifyContent: "center", gap: 24, textAlign: "center" }}>
        <div style={{ width: 72, height: 72, borderRadius: 20, background: "var(--accent-subtle)", border: "1px solid rgba(232,232,232,0.1)", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <span style={{ fontSize: 32 }}>{stage === "uploading" ? "📤" : "🧠"}</span>
        </div>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, margin: "0 0 8px" }}>
            {stage === "uploading" ? "Subiendo fotos…" : "Analizando tu rostro"}
          </h2>
          {stage === "processing" && (
            <p style={{ color: "var(--text-muted)", fontSize: 15, maxWidth: 260, lineHeight: 1.6, margin: "0 auto" }}>
              Detectando 468 puntos y generando tus recomendaciones…
            </p>
          )}
        </div>
        {stage === "processing" && (
          <>
            <div style={{ display: "flex", gap: 6 }}>
              {[0, 1, 2].map((i) => <div key={i} className="dot-pulse" style={{ animationDelay: `${i * 0.4}s` }} />)}
            </div>
            <p className="caption">Suele tardar 40–60 segundos</p>
          </>
        )}
      </div>
    );
  }

  if (stage === "error") {
    return (
      <div className="screen" style={{ alignItems: "center", justifyContent: "center", gap: 16, textAlign: "center" }}>
        <span style={{ fontSize: 48 }}>😕</span>
        <p style={{ color: "var(--danger)", fontSize: 15 }}>{error}</p>
        <button type="button" className="btn-secondary" onClick={handleRetry} style={{ maxWidth: 280, width: "100%" }}>
          Intentar de nuevo
        </button>
      </div>
    );
  }

  /* ── preview screen ── */
  if (stage === "preview") {
    const idx = shotIdxRef.current;
    const shot = SHOTS[Math.min(idx, SHOTS.length - 1)];
    return (
      <div style={{ position: "fixed", inset: 0, background: "#000", display: "flex", flexDirection: "column" }}>
        {/* Preview image — mirrored like viewfinder */}
        {previewUrl && (
          <img
            src={previewUrl}
            alt="preview"
            style={{
              position: "absolute", inset: 0,
              width: "100%", height: "100%",
              objectFit: "cover",
              transform: "scaleX(-1)",
            }}
          />
        )}

        {/* Dark top overlay */}
        <div style={{
          position: "absolute", top: 0, left: 0, right: 0,
          background: "linear-gradient(to bottom, rgba(0,0,0,0.7) 0%, transparent 100%)",
          padding: "calc(env(safe-area-inset-top) + 16px) 24px 40px",
          textAlign: "center",
        }}>
          <p style={{ color: "rgba(201,168,76,0.9)", fontSize: 13, fontWeight: 700, letterSpacing: 1.5, margin: 0 }}>
            ¿ESTÁ BIEN?
          </p>
          <h2 style={{ color: "#fff", fontSize: 24, fontWeight: 800, margin: "6px 0 0", letterSpacing: -0.3 }}>
            {shot.label}
          </h2>
        </div>

        {/* Dark bottom overlay with buttons */}
        <div style={{
          position: "absolute", bottom: 0, left: 0, right: 0,
          background: "linear-gradient(to top, rgba(0,0,0,0.85) 0%, transparent 100%)",
          padding: "40px 40px calc(env(safe-area-inset-bottom) + 32px)",
          display: "flex", alignItems: "center", justifyContent: "space-between",
        }}>
          {/* Retake */}
          <button
            type="button"
            onClick={retakePhoto}
            style={{
              display: "flex", flexDirection: "column", alignItems: "center", gap: 6,
              color: "white",
            }}
          >
            <div style={{
              width: 60, height: 60, borderRadius: "50%",
              background: "rgba(255,255,255,0.15)",
              border: "2px solid rgba(255,255,255,0.4)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <ChevronLeft size={28} strokeWidth={2.5} />
            </div>
            <span style={{ fontSize: 12, fontWeight: 600, opacity: 0.8 }}>Repetir</span>
          </button>

          {/* OK */}
          <button
            type="button"
            onClick={confirmPhoto}
            style={{
              display: "flex", flexDirection: "column", alignItems: "center", gap: 6,
              color: "white",
            }}
          >
            <div style={{
              width: 80, height: 80, borderRadius: "50%",
              background: "rgba(201,168,76,0.9)",
              border: "4px solid rgba(201,168,76,1)",
              boxShadow: "0 0 0 4px rgba(201,168,76,0.25)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <Check size={36} strokeWidth={3} color="#080808" />
            </div>
            <span style={{ fontSize: 13, fontWeight: 700 }}>Usar foto</span>
          </button>

          {/* Spacer */}
          <div style={{ width: 60 }} />
        </div>
      </div>
    );
  }

  /* ── camera stage ── */
  const currentShot = SHOTS[Math.min(shotIndex, SHOTS.length - 1)];
  const isLastShot  = shotIndex === SHOTS.length - 1;
  const isDone      = shotIndex >= SHOTS.length;

  return (
    <div style={{ position: "fixed", inset: 0, background: "#000", display: "flex", flexDirection: "column" }}>

      {/* Flash overlay */}
      {flashActive && (
        <div style={{
          position: "absolute", inset: 0, zIndex: 99,
          background: "white",
          opacity: 0.85,
          pointerEvents: "none",
          animation: "none",
        }} />
      )}

      {/* Live video */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        style={{
          position: "absolute", inset: 0,
          width: "100%", height: "100%",
          objectFit: "cover",
          transform: "scaleX(-1)",
          display: cameraReady ? "block" : "none",
        }}
      />

      {/* No-camera fallback background */}
      {!cameraReady && (
        <div style={{
          position: "absolute", inset: 0,
          background: "radial-gradient(ellipse at center, #1a1a1a 0%, #080808 100%)",
        }} />
      )}

      {/* Dark oval mask overlay */}
      <svg
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
        viewBox="0 0 390 844"
        preserveAspectRatio="xMidYMid slice"
      >
        <defs>
          <mask id="oval-mask">
            <rect width="390" height="844" fill="white" />
            <ellipse cx="195" cy="370" rx="148" ry="195" fill="black" />
          </mask>
        </defs>
        <rect width="390" height="844" fill="rgba(0,0,0,0.6)" mask="url(#oval-mask)" />
        <ellipse cx="195" cy="370" rx="148" ry="195"
          fill="none"
          stroke="rgba(201,168,76,0.9)"
          strokeWidth="2.5"
          strokeDasharray="14 7"
        />
      </svg>

      {/* Emoji guide (no camera) */}
      {!cameraReady && (
        <div style={{
          position: "absolute",
          top: "50%", left: "50%",
          transform: "translate(-50%, -60%)",
          textAlign: "center",
          pointerEvents: "none",
        }}>
          <div style={{ fontSize: 64 }}>🧑</div>
          <div style={{ fontSize: 11, color: "rgba(201,168,76,0.9)", fontWeight: 700, letterSpacing: 1, marginTop: 6 }}>
            CENTRA TU CARA
          </div>
        </div>
      )}

      {/* ── Top UI ── */}
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0,
        padding: "calc(env(safe-area-inset-top) + 16px) 24px 0",
        textAlign: "center",
      }}>
        <div style={{ display: "flex", justifyContent: "center", gap: 6, marginBottom: 10 }}>
          {SHOTS.map((_, i) => (
            <div key={i} style={{
              width: shotIndex > i ? 8 : 10,
              height: shotIndex > i ? 8 : 10,
              borderRadius: "50%",
              background: shotIndex > i
                ? "rgba(201,168,76,0.5)"
                : i === shotIndex
                  ? "rgba(201,168,76,0.95)"
                  : "rgba(255,255,255,0.25)",
              transition: "all 0.2s",
            }} />
          ))}
        </div>

        <div style={{ color: "rgba(201,168,76,0.9)", fontSize: 17, fontWeight: 700, marginBottom: 6 }}>
          {Math.min(shotIndex + 1, SHOTS.length)} / {SHOTS.length}
        </div>

        <h2 style={{ color: "#ffffff", fontSize: 28, fontWeight: 800, margin: "0 0 6px", letterSpacing: -0.3 }}>
          {currentShot.label}
        </h2>

        <p style={{ color: "rgba(201,168,76,0.85)", fontSize: 15, margin: 0, fontWeight: 500 }}>
          {currentShot.hint}
        </p>
      </div>

      {/* ── Bottom controls ── */}
      <div style={{
        position: "absolute", bottom: 0, left: 0, right: 0,
        padding: "20px 32px calc(env(safe-area-inset-bottom) + 28px)",
        display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>

        {/* Repetir */}
        <button
          type="button"
          onClick={handleRepeat}
          disabled={shotIndex === 0 && photosRef.current.length === 0}
          style={{
            display: "flex", flexDirection: "column", alignItems: "center", gap: 4,
            color: "white", opacity: (shotIndex === 0 && photosRef.current.length === 0) ? 0.3 : 1,
            minWidth: 60,
          }}
        >
          <ChevronLeft size={26} strokeWidth={2.5} />
          <span style={{ fontSize: 12, fontWeight: 600 }}>Repetir</span>
        </button>

        {/* Shutter */}
        <button
          type="button"
          onClick={cameraReady ? captureFrame : () => fileInputRef.current?.click()}
          disabled={isDone}
          aria-label="Capturar foto"
          style={{
            width: 80, height: 80, borderRadius: "50%",
            background: "rgba(0,0,0,0.5)",
            border: "5px solid rgba(201,168,76,0.85)",
            boxShadow: "0 0 0 3px rgba(201,168,76,0.25)",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}
        >
          <div style={{
            width: 56, height: 56, borderRadius: "50%",
            background: isLastShot ? "rgba(201,168,76,0.8)" : "rgba(201,168,76,0.4)",
            transition: "background 0.2s",
          }} />
        </button>

        {/* Counter */}
        <div style={{ textAlign: "center", minWidth: 60 }}>
          {!isDone && (
            <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 12 }}>
              {Math.min(shotIndex + 1, SHOTS.length)}/{SHOTS.length}
            </div>
          )}
        </div>
      </div>

      <canvas ref={canvasRef} style={{ display: "none" }} />
      <input ref={fileInputRef} type="file" accept="image/*" capture="user" style={{ display: "none" }} onChange={onFileInput} />
    </div>
  );
}
