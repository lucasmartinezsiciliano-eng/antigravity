"use client";
import { use, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { ChevronLeft, X, Sparkles, Camera } from "lucide-react";
import { api } from "@/lib/api";
import { GeneratingScreen } from "@/components/ui/generating-screen";
import { CutCard } from "@/components/ui/cut-card";
import { GlowButton } from "@/components/ui/glow-button";

type Stage = "intro" | "pick" | "preview" | "generating" | "done" | "error";

export default function VisualsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const inputRef = useRef<HTMLInputElement>(null);
  const [stage, setStage] = useState<Stage>("intro");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>("");
  const [visuals, setVisuals] = useState<any[]>([]);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<any | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  // Mutex: prevent double-tap from firing two generateVisuals calls (each costs Fal.ai credit)
  const generatingRef = useRef(false);

  useEffect(() => {
    api.getVisuals(id).then((res) => {
      if (res.visuals_status === "ready" && res.visuals?.length > 0) {
        setVisuals(res.visuals);
        setStage("done");
      } else if (res.visuals_status === "processing") {
        // Already generating (e.g. from /result auto-trigger) — join the poll, don't re-submit
        setStage("generating");
        startPolling();
      }
    }).catch(() => {
      // If we can't reach the API, let the user proceed — the generate call will fail loudly
    });
    return () => {
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
    };
  }, [id]); // eslint-disable-line react-hooks/exhaustive-deps

  function onInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    // Validate file type — allow empty MIME (iOS HEIC arrives with no type), reject clearly wrong types
    const ext = f.name.split(".").pop()?.toLowerCase() ?? "";
    const knownBadExts = ["pdf", "doc", "docx", "xls", "zip", "mp4", "mov", "avi"];
    if (f.type && !f.type.startsWith("image/") && knownBadExts.includes(ext)) {
      setError("El archivo no es una imagen válida.");
      setStage("error");
      return;
    }
    if (f.size === 0) {
      setError("La foto está vacía. Elige otra.");
      setStage("error");
      return;
    }
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setStage("preview");
  }

  async function handleGenerate() {
    if (!file) return;
    // Mutex: block concurrent calls — onClick fires once but rapid taps can queue multiple
    if (generatingRef.current) return;
    generatingRef.current = true;
    setStage("generating");
    setError("");
    try {
      await api.generateVisuals(id, file);
      startPolling();
    } catch (e: any) {
      setError(e.message || "Error al iniciar la prueba virtual.");
      setStage("error");
      generatingRef.current = false;
    }
  }

  function startPolling() {
    // Always clear an existing interval first — prevents orphaned polls on rapid re-generate
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
    const pollStart = Date.now();
    pollRef.current = setInterval(async () => {
      // Pause while tab is hidden — saves battery + avoids spurious errors
      if (document.hidden) return;

      if (Date.now() - pollStart > 300_000) {
        clearInterval(pollRef.current!); pollRef.current = null;
        generatingRef.current = false;
        setError("La generación está tardando demasiado. Inténtalo de nuevo.");
        setStage("error");
        return;
      }
      try {
        const res = await api.getVisuals(id);
        if (res.visuals_status === "ready" && res.visuals?.length > 0) {
          clearInterval(pollRef.current!); pollRef.current = null;
          generatingRef.current = false;
          setVisuals(res.visuals);
          setStage("done");
        } else if (res.visuals_status === "failed") {
          clearInterval(pollRef.current!); pollRef.current = null;
          generatingRef.current = false;
          setError("La generación de imágenes falló. Inténtalo de nuevo.");
          setStage("error");
        }
      } catch { /* keep retrying silently */ }
    }, 3000);
  }

  /* ── Generating ── */
  if (stage === "generating") {
    return <GeneratingScreen />;
  }

  /* ── Done — animated stacked cards (frontal + lateral) ── */
  if (stage === "done" && visuals.length > 0) {
    return (
      <div style={{ background: "var(--bg)", minHeight: "100dvh" }}>
        <div style={{ maxWidth: 480, margin: "0 auto", padding: "24px 20px 60px" }}>

          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}
          >
            <Link href={`/result/${id}`} className="back-btn" aria-label="Volver">
              <ChevronLeft size={20} strokeWidth={2} />
            </Link>
            <h1 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>Tu prueba virtual</h1>
          </motion.div>

          {/* Lightbox */}
          <AnimatePresence>
            {selected && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                style={{
                  position: "fixed", inset: 0, background: "rgba(0,0,0,0.96)", zIndex: 100,
                  display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
                  padding: 20,
                }}
              >
                <button
                  type="button"
                  onClick={() => setSelected(null)}
                  aria-label="Cerrar"
                  style={{
                    position: "absolute", top: 20, right: 20,
                    width: 40, height: 40, borderRadius: "50%",
                    background: "rgba(255,255,255,0.08)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    color: "white",
                  }}
                >
                  <X size={18} strokeWidth={2} />
                </button>
                <motion.img
                  initial={{ scale: 0.92, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.94, opacity: 0 }}
                  transition={{ type: "spring", stiffness: 300, damping: 28 }}
                  src={selected.url}
                  alt={selected.label}
                  style={{ maxWidth: "100%", maxHeight: "80vh", objectFit: "contain", borderRadius: 16 }}
                />
                {selected.cutName && (
                  <motion.p
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    style={{ color: "rgba(255,255,255,0.5)", marginTop: 16, fontSize: 13, letterSpacing: "0.04em" }}
                  >
                    {selected.cutName} — {selected.label}
                  </motion.p>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Animated cut cards */}
          {visuals.map((cut: any) => {
            const cutName = cut.nombre_en || `Corte ${(cut.cut_index ?? 0) + 1}`;
            const frontalAngle = (cut.angles ?? []).find((a: any) => a.angle_id === "frontal");
            const lateralAngle = (cut.angles ?? []).find((a: any) => a.angle_id === "lateral");
            return (
              <CutCard
                key={cut.cut_index ?? cutName}
                cutName={cutName}
                cutIndex={cut.cut_index ?? 0}
                frontal={frontalAngle?.url ? { url: frontalAngle.url, label: "Frontal" } : undefined}
                lateral={lateralAngle?.url ? { url: lateralAngle.url, label: "Lateral" } : undefined}
                onPhotoTap={(url, label, name) => setSelected({ url, label, cutName: name })}
              />
            );
          })}

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            <button
              type="button"
              className="btn-secondary"
              onClick={() => {
                if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
                generatingRef.current = false;
                setStage("pick");
                setVisuals([]);
              }}
            >
              Generar con otra foto
            </button>
          </motion.div>
        </div>
      </div>
    );
  }

  /* ── Intro / Pick / Preview / Error ── */
  return (
    <div className="screen" style={{ gap: 0 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
        <Link href={`/result/${id}`} className="back-btn" aria-label="Volver">
          <ChevronLeft size={20} strokeWidth={2} />
        </Link>
      </div>

      {stage === "intro" && (
        <>
          <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 20 }}>
            <div style={{
              width: 72, height: 72, borderRadius: 20,
              background: "var(--gold-subtle)",
              border: "1px solid var(--gold-border)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <Sparkles size={30} color="var(--gold)" strokeWidth={1.75} />
            </div>
            <div style={{ textAlign: "center" }}>
              <h1 style={{ fontSize: 24, fontWeight: 700, margin: "0 0 8px", letterSpacing: -0.5 }}>Prueba virtual</h1>
              <p style={{ color: "var(--text-muted)", fontSize: 15, lineHeight: 1.65, margin: 0, maxWidth: 300 }}>
                Mira cómo quedarías con cada uno de tus 3 cortes recomendados antes de ir a la barbería.
              </p>
            </div>
            <div className="card" style={{ width: "100%", padding: "16px 18px" }}>
              {[
                "IA aplica el corte a tu foto real",
                "Frontal + lateral por cada corte (6 imágenes)",
                "Foto procesada y eliminada al instante",
              ].map((t, i) => (
                <div key={i} style={{
                  display: "flex", gap: 10, alignItems: "center",
                  padding: "8px 0",
                  borderBottom: i < 2 ? "1px solid var(--border)" : "none",
                }}>
                  <svg width="14" height="12" viewBox="0 0 10 8" fill="none">
                    <path d="M1 4L3.5 6.5L9 1" stroke="var(--gold)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <span style={{ fontSize: 14, color: "var(--text-muted)" }}>{t}</span>
                </div>
              ))}
            </div>
          </div>
          <button type="button" className="btn-primary" onClick={() => setStage("pick")}>
            Hacer mi prueba virtual →
          </button>
        </>
      )}

      {stage === "pick" && (
        <>
          <div style={{ textAlign: "center", marginBottom: 20 }}>
            <h2 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 6px" }}>Hazte una foto</h2>
            <p style={{ color: "var(--text-muted)", fontSize: 14, margin: 0 }}>Cara al frente, buena luz, fondo neutro</p>
          </div>
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            style={{
              flex: 1, border: "1.5px dashed var(--border)", borderRadius: 20,
              display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
              gap: 14, cursor: "pointer", background: "var(--surface)", marginBottom: 20,
            }}
          >
            <div style={{
              width: 56, height: 56, borderRadius: 16,
              background: "var(--gold-subtle)", border: "1px solid var(--gold-border)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <Camera size={26} color="var(--gold)" strokeWidth={1.75} />
            </div>
            <div style={{ textAlign: "center" }}>
              <p style={{ color: "var(--text-muted)", fontSize: 15, margin: "0 0 4px", fontWeight: 600 }}>Toca para abrir cámara</p>
              <p className="caption" style={{ margin: 0 }}>o elige de galería</p>
            </div>
          </button>
          <button type="button" className="btn-primary" onClick={() => inputRef.current?.click()}>
            Abrir cámara →
          </button>
        </>
      )}

      {stage === "preview" && preview && (
        <>
          <div style={{ textAlign: "center", marginBottom: 16 }}>
            <h2 style={{ fontSize: 20, fontWeight: 700, margin: "0 0 4px" }}>¿Esta foto sirve?</h2>
            <p style={{ color: "var(--text-muted)", fontSize: 14, margin: 0 }}>Cara visible, buena iluminación</p>
          </div>
          <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 20 }}>
            <img
              src={preview}
              alt="preview"
              style={{ width: "100%", maxHeight: 380, objectFit: "cover", borderRadius: 18, border: "1px solid var(--border)" }}
            />
          </div>
          {error && <p style={{ color: "var(--danger)", fontSize: 14, textAlign: "center", marginBottom: 10 }}>{error}</p>}
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <button type="button" className="btn-primary" onClick={handleGenerate}>
              Generar mi prueba virtual →
            </button>
            <button type="button" className="btn-secondary" onClick={() => inputRef.current?.click()}>
              Cambiar foto
            </button>
          </div>
        </>
      )}

      {stage === "error" && (
        <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16, textAlign: "center" }}>
          <span style={{ fontSize: 48 }}>😕</span>
          <p style={{ color: "var(--danger)", fontSize: 15 }}>{error}</p>
          <button
            type="button"
            className="btn-secondary"
            style={{ maxWidth: 260, width: "100%" }}
            onClick={() => { setStage("pick"); setError(""); }}
          >
            Intentar de nuevo
          </button>
        </div>
      )}

      <input ref={inputRef} type="file" accept="image/*" capture="user" style={{ display: "none" }} onChange={onInputChange} />
    </div>
  );
}
