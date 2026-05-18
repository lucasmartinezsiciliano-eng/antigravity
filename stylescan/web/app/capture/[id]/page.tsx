"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { ChevronLeft, Check } from "lucide-react";
import { api } from "@/lib/api";
import { storage } from "@/lib/storage";

const SHOTS = [
  {
    label: "Frontal",
    sublabel: "Mírame de frente",
    hint: "Cara centrada en el óvalo · Barbilla recta · Luz en tu cara, no detrás",
  },
  {
    label: "Perfil izquierdo",
    sublabel: "Gira 90° a tu derecha",
    hint: "Solo debe verse media cara: un ojo, una oreja, la nariz de lado",
  },
  {
    label: "Perfil derecho",
    sublabel: "Ahora 90° al otro lado",
    hint: "Hombro derecho a la cámara · Media cara visible · Igual que antes pero al revés",
  },
];

const INTRO_TIPS = [
  { icon: "💡", text: "Luz de frente, nunca a tu espalda. Si la luz viene de atrás, el análisis falla." },
  { icon: "🧢", text: "Quítate gorra, gafas y capucha. El pelo y la línea de la cara deben verse limpios." },
  { icon: "📐", text: "Perfiles a 90 grados exactos. Gira el cuerpo entero, no solo los ojos." },
  { icon: "🤝", text: "Si puedes, pide a alguien que te haga los perfiles. Es la diferencia entre un buen y mal resultado." },
  { icon: "🔄", text: "Si dudas, repítela. Mejor 10 segundos extra que un resultado que no sirve." },
];

type Stage = "intro" | "camera" | "preview" | "uploading" | "processing" | "error";

export default function CapturePage() {
  const params = useParams();
  const id     = params.id as string;

  const videoRef      = useRef<HTMLVideoElement>(null);
  const canvasRef     = useRef<HTMLCanvasElement>(null);
  const streamRef     = useRef<MediaStream | null>(null);
  const fileInputRef  = useRef<HTMLInputElement>(null);
  const pollRef       = useRef<ReturnType<typeof setInterval> | null>(null);
  const flashTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const shotIdxRef    = useRef(0);
  const photosRef     = useRef<File[]>([]);
  /* Ref for reliable previewUrl cleanup — avoids stale closure on unmount */
  const previewUrlRef = useRef<string>("");

  const [stage,            setStage]            = useState<Stage>("intro");
  const [cameraReady,      setCameraReady]      = useState(false);
  const [shotIndex,        setShotIndex]        = useState(0);
  const [previewUrl,       setPreviewUrl]       = useState<string>("");
  const [previewBlob,      setPreviewBlob]      = useState<Blob | null>(null);
  const [flashActive,      setFlashActive]      = useState(false);
  const [capturing,        setCapturing]        = useState(false);
  const [error,            setError]            = useState("");
  const [showProfileAlert, setShowProfileAlert] = useState(false);

  /* ── helpers ── */
  const stopStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setCameraReady(false);
  }, []);

  /* Always revoke through the ref so unmount cleanup is never stale */
  function setPreviewUrlSafe(url: string) {
    if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
    previewUrlRef.current = url;
    setPreviewUrl(url);
  }

  /* ── mount / unmount — cámara se inicia cuando el usuario sale del intro ── */
  useEffect(() => {
    return () => {
      stopStream();
      if (pollRef.current)       clearInterval(pollRef.current);
      if (flashTimerRef.current) clearTimeout(flashTimerRef.current);
      if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
    };
  }, []); // eslint-disable-line

  /* ── Bug 9: re-associate stream when returning to camera stage ──
     Video is fully re-mounted after leaving preview, so srcObject must be re-set */
  useEffect(() => {
    if (stage === "camera" && streamRef.current && videoRef.current) {
      videoRef.current.srcObject = streamRef.current;
      videoRef.current.play().catch(() => {});
      setCameraReady(true);
    }
  }, [stage]);

  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 960 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        /* Bug 13: assign onloadedmetadata BEFORE srcObject; guard readyState */
        await new Promise<void>((res) => {
          if (!videoRef.current) return res();
          videoRef.current.onloadedmetadata = () => res();
          videoRef.current.srcObject = stream;
          if (videoRef.current.readyState >= 1) res();
        });
        await videoRef.current.play();
      }
      setCameraReady(true);
    } catch (e: any) {
      if (e?.name === "NotAllowedError") {
        setError("Debes permitir el acceso a la cámara. Recarga la página y acepta el permiso cuando el navegador lo pida.");
      } else if (e?.name === "NotFoundError") {
        setError("No se detectó ninguna cámara. Usa otro dispositivo o un navegador compatible.");
      } else {
        setError("Error al iniciar la cámara. Intenta recargar la página.");
      }
      setCameraReady(false);
    }
  }

  /* ── save thumbnail to sessionStorage for auto-visuals ── */
  function savePhotoToSession(blob: Blob, key: string) {
    const small = document.createElement("canvas");
    const src   = document.createElement("canvas");
    const img   = document.createElement("img");
    const url   = URL.createObjectURL(blob);
    img.onload = () => {
      const scale = Math.min(1, 640 / img.width);
      src.width  = img.width;  src.height = img.height;
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

  /* ── capture: flash + go to preview ── */
  function captureFrame() {
    if (capturing) return; // Bug 16: block double-click
    const video  = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2) return;

    setCapturing(true);

    /* Flash — Bug 3/4: keyframe animation + timer stored in ref */
    setFlashActive(true);
    if (flashTimerRef.current) clearTimeout(flashTimerRef.current);
    flashTimerRef.current = setTimeout(() => setFlashActive(false), 300);

    canvas.width  = video.videoWidth  || 1280;
    canvas.height = video.videoHeight || 960;
    const ctx = canvas.getContext("2d");
    if (!ctx) { setCapturing(false); return; }
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      if (!blob) { setCapturing(false); return; }
      setPreviewUrlSafe(URL.createObjectURL(blob));
      setPreviewBlob(blob);
      setStage("preview");
      setCapturing(false);
    }, "image/jpeg", 0.92);
  }

  /* ── accept previewed photo ── */
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
    setPreviewUrlSafe("");
    if (next >= SHOTS.length) {
      stopStream();
      setStage("uploading");
      handleUpload(photosRef.current);
    } else {
      // Muestra aviso de perfil 90° antes del primer perfil (solo una vez)
      if (next === 1) {
        setShowProfileAlert(true);
      } else {
        setStage("camera");
      }
    }
  }

  /* ── retake current shot ── */
  function retakePhoto() {
    setPreviewBlob(null);
    setPreviewUrlSafe("");
    setStage("camera"); // triggers re-association effect (Bug 9)
  }

  /* ── fallback: file from gallery ── */
  function onFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = "";
    /* Bug 2: use file directly, not file.slice() which creates a nameless Blob */
    setPreviewUrlSafe(URL.createObjectURL(file));
    setPreviewBlob(file);
    setStage("preview");
  }

  /* ── undo last confirmed photo (camera stage only) ── */
  function handleRepeat() {
    const prev = Math.max(0, shotIdxRef.current - 1);
    photosRef.current  = photosRef.current.slice(0, prev);
    shotIdxRef.current = prev;
    setShotIndex(prev);
  }

  /* ── upload ── */
  async function handleUpload(files: File[]) {
    storage.saveAnalysisId(id);
    setError("");
    try {
      await api.uploadPhotos(id, files);
      setStage("processing");
      /* Bug 11: clear any existing interval before starting a new one */
      if (pollRef.current) clearInterval(pollRef.current);
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
    stopStream(); // Bug 10: stop any lingering stream before starting a new one
    photosRef.current  = [];
    shotIdxRef.current = 0;
    setShotIndex(0);
    setError("");
    setStage("camera");
    startCamera();
  }

  /* ── intro ── */
  if (stage === "intro") {
    return (
      <div className="screen" style={{ background: "var(--bg)", padding: "0 24px 40px", overflowY: "auto" }}>
        <div style={{ paddingTop: 56, paddingBottom: 32, maxWidth: 420, margin: "0 auto" }}>

          <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 2, color: "var(--accent)", marginBottom: 12 }}>
            ANTES DE EMPEZAR
          </div>
          <h1 style={{ fontSize: 26, fontWeight: 800, margin: "0 0 6px", letterSpacing: -0.6, lineHeight: 1.15 }}>
            Cómo hacerte las 3 fotos
          </h1>
          <p style={{ fontSize: 14, color: "var(--text-muted)", margin: "0 0 32px", lineHeight: 1.6 }}>
            El análisis es tan bueno como tus fotos. Dedícale 30 segundos.
          </p>

          <div style={{ display: "flex", flexDirection: "column", gap: 16, marginBottom: 36 }}>
            {INTRO_TIPS.map((tip, i) => (
              <div key={i} style={{ display: "flex", gap: 16, alignItems: "flex-start" }}>
                <div style={{
                  width: 40, height: 40, borderRadius: 12, flexShrink: 0,
                  background: "var(--surface2)", border: "1px solid var(--border)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 20,
                }}>
                  {tip.icon}
                </div>
                <p style={{ fontSize: 14, lineHeight: 1.6, margin: 0, paddingTop: 10 }}>
                  {tip.text}
                </p>
              </div>
            ))}
          </div>

          {/* Aviso especial perfiles */}
          <div style={{
            background: "rgba(201,168,76,0.06)", border: "1px solid rgba(201,168,76,0.25)",
            borderRadius: 14, padding: "16px 18px", marginBottom: 32,
          }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: "var(--accent)", letterSpacing: 1, marginBottom: 8 }}>
              📐 LOS PERFILES SON LO MÁS IMPORTANTE
            </div>
            <p style={{ fontSize: 13, lineHeight: 1.65, margin: 0, color: "var(--text-muted)" }}>
              Tienen que ser a <strong style={{ color: "var(--text)" }}>exactamente 90 grados</strong> — no "un poco girado". Gira el cuerpo entero. Solo debe verse <strong style={{ color: "var(--text)" }}>media cara</strong>: un ojo, una oreja y la nariz de perfil. Si tienes a alguien cerca, pídele que te la haga.
            </p>
          </div>

          <button
            type="button"
            className="btn-primary"
            style={{ fontSize: 16, padding: "16px" }}
            onClick={() => {
              setStage("camera");
              startCamera();
            }}
          >
            Entendido, vamos →
          </button>
        </div>
      </div>
    );
  }

  /* ── modal alerta perfil 90° ── */
  if (showProfileAlert) {
    return (
      <div style={{
        position: "fixed", inset: 0, background: "rgba(8,8,8,0.96)",
        display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
        padding: "32px 28px", zIndex: 200,
      }}>
        <div style={{ maxWidth: 380, width: "100%" }}>
          <div style={{ fontSize: 48, textAlign: "center", marginBottom: 20 }}>📐</div>
          <h2 style={{ fontSize: 22, fontWeight: 800, margin: "0 0 8px", textAlign: "center", letterSpacing: -0.5 }}>
            Esta foto es la que más falla
          </h2>
          <p style={{ fontSize: 14, color: "var(--text-muted)", textAlign: "center", margin: "0 0 28px", lineHeight: 1.6 }}>
            El perfil tiene que ser a <strong style={{ color: "var(--text)" }}>90 grados literales</strong>, no "un poco de lado".
          </p>

          <div style={{ background: "var(--surface2)", borderRadius: 14, padding: "18px", marginBottom: 28 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: "var(--accent)", letterSpacing: 1, marginBottom: 12 }}>
              TIENE QUE VERSE:
            </div>
            {["Una sola oreja", "Un solo ojo", "La nariz de perfil completo, marcando silueta"].map((item, i) => (
              <div key={i} style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: i < 2 ? 10 : 0 }}>
                <div style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--accent)", flexShrink: 0 }} />
                <span style={{ fontSize: 14 }}>{item}</span>
              </div>
            ))}
          </div>

          <div style={{
            background: "rgba(201,168,76,0.06)", border: "1px solid rgba(201,168,76,0.2)",
            borderRadius: 12, padding: "14px 16px", marginBottom: 28,
          }}>
            <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0, lineHeight: 1.6 }}>
              <strong style={{ color: "var(--text)" }}>Truco:</strong> gira los pies, no la cabeza. Si solo mueves los ojos hacia la cámara, la foto no sirve. Si tienes a alguien cerca, pídele que te la haga.
            </p>
          </div>

          <button
            type="button"
            className="btn-primary"
            style={{ fontSize: 15, padding: "15px" }}
            onClick={() => {
              setShowProfileAlert(false);
              setStage("camera");
            }}
          >
            Listo, hacer el perfil →
          </button>
        </div>
      </div>
    );
  }

  /* ── uploading / processing ── */
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

  /* ── error ── */
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

  /* ── preview ── */
  if (stage === "preview") {
    /* Bug 8: use shotIndex state (not ref) for render */
    const shot = SHOTS[Math.min(shotIndex, SHOTS.length - 1)];
    return (
      <div style={{ position: "fixed", inset: 0, background: "#000", display: "flex", flexDirection: "column" }}>
        {previewUrl && (
          <img
            src={previewUrl}
            alt="preview"
            style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", transform: "scaleX(-1)" }}
          />
        )}

        <div style={{
          position: "absolute", top: 0, left: 0, right: 0,
          background: "linear-gradient(to bottom, rgba(0,0,0,0.7) 0%, transparent 100%)",
          padding: "calc(env(safe-area-inset-top) + 16px) 24px 40px",
          textAlign: "center",
        }}>
          <p style={{ color: "rgba(201,168,76,0.9)", fontSize: 13, fontWeight: 700, letterSpacing: 1.5, margin: 0 }}>
            ¿ESTÁ BIEN?
          </p>
          <h2 style={{ color: "#fff", fontSize: 24, fontWeight: 800, margin: "6px 0 2px", letterSpacing: -0.3 }}>
            {shot.sublabel}
          </h2>
          <p style={{ color: "rgba(255,255,255,0.5)", fontSize: 12, margin: 0 }}>{shot.label}</p>
        </div>

        <div style={{
          position: "absolute", bottom: 0, left: 0, right: 0,
          background: "linear-gradient(to top, rgba(0,0,0,0.85) 0%, transparent 100%)",
          padding: "40px 40px calc(env(safe-area-inset-bottom) + 32px)",
          display: "flex", alignItems: "center", justifyContent: "space-between",
        }}>
          <button type="button" onClick={retakePhoto}
            style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6, color: "white" }}>
            <div style={{
              width: 60, height: 60, borderRadius: "50%",
              background: "rgba(255,255,255,0.15)", border: "2px solid rgba(255,255,255,0.4)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <ChevronLeft size={28} strokeWidth={2.5} />
            </div>
            <span style={{ fontSize: 12, fontWeight: 600, opacity: 0.8 }}>Repetir</span>
          </button>

          <button type="button" onClick={confirmPhoto}
            style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6, color: "white" }}>
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

          <div style={{ width: 60 }} />
        </div>
      </div>
    );
  }

  /* ── camera ── */
  const currentShot     = SHOTS[Math.min(shotIndex, SHOTS.length - 1)];
  const isLastShot      = shotIndex === SHOTS.length - 1;
  const isDone          = shotIndex >= SHOTS.length;
  const shutterDisabled = isDone || capturing;

  return (
    <div style={{ position: "fixed", inset: 0, background: "#000", display: "flex", flexDirection: "column" }}>

      {/* Bug 3: keyframe inline so no globals.css dependency */}
      <style>{`@keyframes flashFade{0%{opacity:.9}100%{opacity:0}}`}</style>

      {/* Bug 3/4: flash overlay with real animation */}
      {flashActive && (
        <div style={{
          position: "absolute", inset: 0, zIndex: 99,
          background: "white", pointerEvents: "none",
          animation: "flashFade 300ms ease-out forwards",
        }} />
      )}

      {/* Bug 14: opacity instead of display:none — keeps video alive in iOS Safari */}
      <video
        ref={videoRef}
        autoPlay playsInline muted
        style={{
          position: "absolute", inset: 0,
          width: "100%", height: "100%",
          objectFit: "cover",
          transform: "scaleX(-1)",
          opacity: cameraReady ? 1 : 0,
          transition: "opacity 0.3s",
        }}
      />

      {!cameraReady && (
        <div style={{ position: "absolute", inset: 0, background: "radial-gradient(ellipse at center, #1a1a1a 0%, #080808 100%)" }} />
      )}

      <svg style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
        viewBox="0 0 390 844" preserveAspectRatio="xMidYMid slice">
        <defs>
          <mask id="oval-mask">
            <rect width="390" height="844" fill="white" />
            <ellipse cx="195" cy="370" rx="148" ry="195" fill="black" />
          </mask>
        </defs>
        <rect width="390" height="844" fill="rgba(0,0,0,0.6)" mask="url(#oval-mask)" />
        <ellipse cx="195" cy="370" rx="148" ry="195"
          fill="none" stroke="rgba(201,168,76,0.9)" strokeWidth="2.5" strokeDasharray="14 7" />
      </svg>

      {!cameraReady && (
        <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%, -60%)", textAlign: "center", pointerEvents: "none" }}>
          <div style={{ fontSize: 64 }}>🧑</div>
          <div style={{ fontSize: 11, color: "rgba(201,168,76,0.9)", fontWeight: 700, letterSpacing: 1, marginTop: 6 }}>
            CENTRA TU CARA
          </div>
        </div>
      )}

      {/* Top UI */}
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, padding: "calc(env(safe-area-inset-top) + 16px) 24px 0", textAlign: "center" }}>
        <div style={{ display: "flex", justifyContent: "center", gap: 6, marginBottom: 10 }}>
          {SHOTS.map((_, i) => (
            <div key={i} style={{
              width: shotIndex > i ? 8 : 10, height: shotIndex > i ? 8 : 10,
              borderRadius: "50%",
              background: shotIndex > i ? "rgba(201,168,76,0.5)" : i === shotIndex ? "rgba(201,168,76,0.95)" : "rgba(255,255,255,0.25)",
              transition: "all 0.2s",
            }} />
          ))}
        </div>
        <div style={{ color: "rgba(201,168,76,0.9)", fontSize: 17, fontWeight: 700, marginBottom: 6 }}>
          {Math.min(shotIndex + 1, SHOTS.length)} / {SHOTS.length}
        </div>
        <h2 style={{ color: "#ffffff", fontSize: 28, fontWeight: 800, margin: "0 0 2px", letterSpacing: -0.3 }}>
          {currentShot.sublabel}
        </h2>
        <p style={{ color: "rgba(255,255,255,0.5)", fontSize: 12, margin: "0 0 4px", fontWeight: 500 }}>
          {currentShot.label}
        </p>
        <p style={{ color: "rgba(201,168,76,0.85)", fontSize: 13, margin: 0, fontWeight: 500, lineHeight: 1.5, maxWidth: 280, marginLeft: "auto", marginRight: "auto" }}>
          {currentShot.hint}
        </p>
      </div>

      {/* Bottom controls */}
      <div style={{
        position: "absolute", bottom: 0, left: 0, right: 0,
        padding: "20px 32px calc(env(safe-area-inset-bottom) + 28px)",
        display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <button type="button" onClick={handleRepeat}
          disabled={shotIndex === 0 && photosRef.current.length === 0}
          style={{
            display: "flex", flexDirection: "column", alignItems: "center", gap: 4,
            color: "white", minWidth: 60,
            opacity: (shotIndex === 0 && photosRef.current.length === 0) ? 0.3 : 1,
          }}>
          <ChevronLeft size={26} strokeWidth={2.5} />
          <span style={{ fontSize: 12, fontWeight: 600 }}>Repetir</span>
        </button>

        <button
          type="button"
          onClick={cameraReady ? captureFrame : () => fileInputRef.current?.click()}
          disabled={shutterDisabled}
          aria-label="Capturar foto"
          style={{
            width: 80, height: 80, borderRadius: "50%",
            background: "rgba(0,0,0,0.5)",
            border: "5px solid rgba(201,168,76,0.85)",
            boxShadow: "0 0 0 3px rgba(201,168,76,0.25)",
            display: "flex", alignItems: "center", justifyContent: "center",
            opacity: shutterDisabled ? 0.5 : 1,
            transition: "opacity 0.15s",
          }}>
          <div style={{
            width: 56, height: 56, borderRadius: "50%",
            background: isLastShot ? "rgba(201,168,76,0.8)" : "rgba(201,168,76,0.4)",
            transition: "background 0.2s",
          }} />
        </button>

        <div style={{ textAlign: "center", minWidth: 60 }}>
          {!isDone && (
            <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 12 }}>
              {Math.min(shotIndex + 1, SHOTS.length)}/{SHOTS.length}
            </div>
          )}
        </div>
      </div>

      <canvas ref={canvasRef} style={{ display: "none" }} />
      <input ref={fileInputRef} type="file" accept="image/*" capture="user" aria-label="Seleccionar foto" style={{ display: "none" }} onChange={onFileInput} />
    </div>
  );
}
