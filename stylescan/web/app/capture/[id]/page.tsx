"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { ChevronLeft } from "lucide-react";
import { api } from "@/lib/api";

const SHOTS = [
  { label: "Frontal",          hint: "Mira directamente a la cámara" },
  { label: "Perfil izquierdo", hint: "Gira la cabeza hacia tu izquierda" },
  { label: "Perfil derecho",   hint: "Gira la cabeza hacia tu derecha" },
  { label: "Mentón arriba",    hint: "Levanta el mentón ligeramente" },
  { label: "Mentón abajo",     hint: "Baja el mentón ligeramente hacia el pecho" },
];

type Stage = "camera" | "uploading" | "processing" | "error";

export default function CapturePage() {
  const params  = useParams();
  const id      = params.id as string;

  const videoRef     = useRef<HTMLVideoElement>(null);
  const canvasRef    = useRef<HTMLCanvasElement>(null);
  const streamRef    = useRef<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef      = useRef<ReturnType<typeof setInterval> | null>(null);
  const tickRef      = useRef<ReturnType<typeof setInterval> | null>(null);
  /* refs so callbacks never have stale values */
  const shotIdxRef   = useRef(0);
  const photosRef    = useRef<File[]>([]);

  const [stage,       setStage]       = useState<Stage>("camera");
  const [cameraReady, setCameraReady] = useState(false);
  const [shotIndex,   setShotIndex]   = useState(0);   // drives re-render
  const [countdown,   setCountdown]   = useState(3);
  const [error,       setError]       = useState("");

  /* ── camera helpers ── */
  const stopStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setCameraReady(false);
  }, []);

  function clearTick() {
    if (tickRef.current) { clearInterval(tickRef.current); tickRef.current = null; }
  }

  useEffect(() => () => {
    stopStream();
    clearTick();
    if (pollRef.current) clearInterval(pollRef.current);
  }, [stopStream]);

  /* start camera on mount */
  useEffect(() => { startCamera(); }, []);           // eslint-disable-line

  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 960 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraReady(true);
      startCountdown();
    } catch {
      setCameraReady(false);
    }
  }

  /* ── countdown ── */
  function startCountdown() {
    clearTick();
    setCountdown(3);
    let c = 3;
    tickRef.current = setInterval(() => {
      c--;
      setCountdown(c);
      if (c <= 0) { clearTick(); captureFrame(); }
    }, 1000);
  }

  /* ── save frontal for auto-visuals ── */
  function saveFrontalToSession(blob: Blob) {
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
          try { sessionStorage.setItem(`visai_frontal_${id}`, reader.result as string); } catch {}
        };
        reader.readAsDataURL(b);
      }, "image/jpeg", 0.65);
      URL.revokeObjectURL(url);
    };
    img.src = url;
  }

  /* ── capture ── */
  function captureFrame() {
    clearTick();
    const video  = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    canvas.width  = video.videoWidth  || 1280;
    canvas.height = video.videoHeight || 960;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      if (!blob) return;
      const idx  = shotIdxRef.current;
      if (idx === 0) saveFrontalToSession(blob);
      const file = new File([blob], `photo_${idx + 1}.jpg`, { type: "image/jpeg" });
      photosRef.current = [...photosRef.current, file];
      const next = idx + 1;
      shotIdxRef.current = next;
      setShotIndex(next);
      if (next >= SHOTS.length) {
        stopStream(); clearTick();
        handleUpload(photosRef.current);
      } else {
        startCountdown();
      }
    }, "image/jpeg", 0.92);
  }

  /* fallback: file chosen from picker */
  function onFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = "";
    const idx = shotIdxRef.current;
    if (idx === 0) {
      const reader = new FileReader();
      reader.onloadend = () => {
        try { sessionStorage.setItem(`visai_frontal_${id}`, reader.result as string); } catch {}
      };
      reader.readAsDataURL(file);
    }
    photosRef.current = [...photosRef.current, file];
    const next = idx + 1;
    shotIdxRef.current = next;
    setShotIndex(next);
    if (next >= SHOTS.length) handleUpload(photosRef.current);
  }

  /* ── repetir ── */
  function handleRepeat() {
    clearTick();
    const idx     = shotIdxRef.current;
    const prevIdx = Math.max(0, idx - 1);
    photosRef.current   = photosRef.current.slice(0, prevIdx);
    shotIdxRef.current  = prevIdx;
    setShotIndex(prevIdx);
    if (cameraReady) startCountdown();
  }

  /* ── upload ── */
  async function handleUpload(files: File[]) {
    setStage("uploading");
    setError("");
    try {
      await api.uploadPhotos(id, files);
      setStage("processing");
      pollRef.current = setInterval(async () => {
        try {
          const result = await api.getResult(id);
          if (result.face_shape) {
            clearInterval(pollRef.current!);
            window.location.href = `/result/${id}`;
          }
        } catch (e: any) {
          const msg = e.message ?? "";
          if (!msg.includes("202") && !msg.includes("progreso") && !msg.includes("procesando")) {
            clearInterval(pollRef.current!);
            setError(msg || "Error al obtener el resultado.");
            setStage("error");
          }
        }
      }, 2500);
    } catch (e: any) {
      setError(e.message || "Error al subir las fotos. Inténtalo de nuevo.");
      setStage("error");
    }
  }

  function handleRetry() {
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
            <p className="caption">Suele tardar 15–30 segundos</p>
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

  /* ── camera stage ── */
  const currentShot = SHOTS[Math.min(shotIndex, SHOTS.length - 1)];
  const isLastShot  = shotIndex === SHOTS.length - 1;
  const isDone      = shotIndex >= SHOTS.length;

  return (
    <div style={{ position: "fixed", inset: 0, background: "#000", display: "flex", flexDirection: "column" }}>

      {/* Live video — always rendered so ref attaches */}
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
        {/* Progress dots */}
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

        {/* Shot number */}
        <div style={{ color: "rgba(201,168,76,0.9)", fontSize: 17, fontWeight: 700, marginBottom: 6 }}>
          {Math.min(shotIndex + 1, SHOTS.length)} / {SHOTS.length}
        </div>

        {/* Shot label */}
        <h2 style={{ color: "#ffffff", fontSize: 28, fontWeight: 800, margin: "0 0 6px", letterSpacing: -0.3 }}>
          {currentShot.label}
        </h2>

        {/* Hint */}
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

        {/* Countdown + count */}
        <div style={{ textAlign: "center", minWidth: 60 }}>
          {cameraReady && !isDone && (
            <>
              <div style={{ color: "rgba(201,168,76,0.95)", fontSize: 32, fontWeight: 800, lineHeight: 1 }}>
                {countdown}s
              </div>
              <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 12, marginTop: 2 }}>
                {Math.min(shotIndex + 1, SHOTS.length)}/{SHOTS.length}
              </div>
            </>
          )}
          {!cameraReady && !isDone && (
            <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 12 }}>
              {shotIndex + 1}/{SHOTS.length}
            </div>
          )}
        </div>
      </div>

      <canvas ref={canvasRef} style={{ display: "none" }} />
      <input ref={fileInputRef} type="file" accept="image/*" capture="user" style={{ display: "none" }} onChange={onFileInput} />
    </div>
  );
}
