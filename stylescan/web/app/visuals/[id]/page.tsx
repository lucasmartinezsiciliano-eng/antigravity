"use client";
import { use, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ChevronLeft, X, Sparkles, Camera } from "lucide-react";
import { api } from "@/lib/api";

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

  useEffect(() => {
    api.getVisuals(id).then((res) => {
      if (res.visuals_status === "completed" && res.visuals?.length > 0) {
        setVisuals(res.visuals);
        setStage("done");
      }
    }).catch(() => {});
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [id]);

  function onInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setStage("preview");
  }

  async function handleGenerate() {
    if (!file) return;
    setStage("generating");
    setError("");
    try {
      await api.generateVisuals(id, file);
      startPolling();
    } catch (e: any) {
      setError(e.message || "Error al iniciar la prueba virtual.");
      setStage("error");
    }
  }

  function startPolling() {
    pollRef.current = setInterval(async () => {
      try {
        const res = await api.getVisuals(id);
        if (res.visuals_status === "completed" && res.visuals?.length > 0) {
          clearInterval(pollRef.current!);
          setVisuals(res.visuals);
          setStage("done");
        } else if (res.visuals_status === "failed") {
          clearInterval(pollRef.current!);
          setError("La generación de imágenes falló. Inténtalo de nuevo.");
          setStage("error");
        }
      } catch {}
    }, 3000);
  }

  /* ── Generating ── */
  if (stage === "generating") {
    return (
      <div className="screen" style={{ alignItems: "center", justifyContent: "center", gap: 24, textAlign: "center" }}>
        <div style={{
          width: 72, height: 72, borderRadius: 20,
          background: "var(--accent-subtle)",
          border: "1px solid rgba(201,168,76,0.2)",
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          <Sparkles size={30} color="var(--accent)" strokeWidth={1.75} />
        </div>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, margin: "0 0 8px" }}>Generando tu prueba virtual</h2>
          <p style={{ color: "var(--text-muted)", fontSize: 15, maxWidth: 280, lineHeight: 1.6, margin: "0 auto" }}>
            Aplicando tus 3 cortes recomendados. Esto puede tardar 1–2 minutos…
          </p>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          {[0, 1, 2].map((i) => (
            <div key={i} className="dot-pulse" style={{ animationDelay: `${i * 0.4}s` }} />
          ))}
        </div>
      </div>
    );
  }

  /* ── Done — grid of visuals ── */
  if (stage === "done" && visuals.length > 0) {
    const cutGroups: Record<string, any[]> = {};
    for (const v of visuals) {
      const key = v.cut_name || v.cut_index || "Corte";
      if (!cutGroups[key]) cutGroups[key] = [];
      cutGroups[key].push(v);
    }

    return (
      <div style={{ background: "var(--bg)", minHeight: "100dvh" }}>
        <div style={{ maxWidth: 480, margin: "0 auto", padding: "24px 20px 60px" }}>

          {/* Header */}
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
            <Link href={`/result/${id}`} className="back-btn" aria-label="Volver">
              <ChevronLeft size={20} strokeWidth={2} />
            </Link>
            <h1 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>Tu prueba virtual</h1>
          </div>

          {/* Lightbox */}
          {selected && (
            <div style={{
              position: "fixed", inset: 0, background: "rgba(0,0,0,0.95)", zIndex: 100,
              display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
              padding: 20,
            }}>
              <button
                type="button"
                onClick={() => setSelected(null)}
                onPointerDown={(e) => { e.preventDefault(); setSelected(null); }}
                aria-label="Cerrar"
                style={{
                  position: "absolute", top: 20, right: 20,
                  width: 36, height: 36, borderRadius: "50%",
                  background: "rgba(255,255,255,0.1)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  color: "white",
                }}
              >
                <X size={18} strokeWidth={2} />
              </button>
              <img
                src={selected.url || selected.image_url}
                alt={selected.cut_name}
                style={{ maxWidth: "100%", maxHeight: "80vh", objectFit: "contain", borderRadius: 14 }}
              />
              {selected.cut_name && (
                <p style={{ color: "rgba(255,255,255,0.7)", marginTop: 14, fontSize: 14 }}>{selected.cut_name}</p>
              )}
            </div>
          )}

          {/* Cut groups */}
          {Object.entries(cutGroups).map(([cutName, items]) => (
            <div key={cutName} style={{ marginBottom: 28 }}>
              <div className="label-accent" style={{ marginBottom: 10 }}>{cutName}</div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 6 }}>
                {items.map((v: any, i: number) => (
                  <button
                    type="button"
                    key={i}
                    onClick={() => setSelected(v)}
                    onPointerDown={(e) => { e.preventDefault(); setSelected(v); }}
                    aria-label={`${cutName} ángulo ${i + 1}`}
                    style={{ aspectRatio: "3/4", borderRadius: 10, overflow: "hidden", border: "1px solid var(--border)" }}
                  >
                    <img
                      src={v.url || v.image_url}
                      alt={`${cutName} ángulo ${i + 1}`}
                      style={{ width: "100%", height: "100%", objectFit: "cover" }}
                    />
                  </button>
                ))}
              </div>
            </div>
          ))}

          <button type="button" className="btn-secondary" onClick={() => { setStage("pick"); setVisuals([]); }} onPointerDown={(e) => { e.preventDefault(); setStage("pick"); setVisuals([]); }}>
            Generar con otra foto
          </button>
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
              background: "var(--accent-subtle)",
              border: "1px solid rgba(201,168,76,0.2)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <Sparkles size={30} color="var(--accent)" strokeWidth={1.75} />
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
                "3 ángulos por cada corte (9 imágenes)",
                "Foto procesada y eliminada al instante",
              ].map((t, i) => (
                <div key={i} style={{
                  display: "flex", gap: 10, alignItems: "center",
                  padding: "8px 0",
                  borderBottom: i < 2 ? "1px solid var(--border)" : "none",
                }}>
                  <svg width="14" height="12" viewBox="0 0 10 8" fill="none">
                    <path d="M1 4L3.5 6.5L9 1" stroke="var(--accent)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <span style={{ fontSize: 14, color: "var(--text-muted)" }}>{t}</span>
                </div>
              ))}
            </div>
          </div>
          <button type="button" className="btn-primary" onClick={() => setStage("pick")} onPointerDown={(e) => { e.preventDefault(); setStage("pick"); }}>
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
            onPointerDown={(e) => { e.preventDefault(); inputRef.current?.click(); }}
            style={{
              flex: 1, border: "1.5px dashed var(--border)", borderRadius: 20,
              display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
              gap: 14, cursor: "pointer", background: "var(--surface)", marginBottom: 20,
            }}
          >
            <div style={{
              width: 56, height: 56, borderRadius: 16,
              background: "var(--accent-subtle)", border: "1px solid rgba(201,168,76,0.2)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <Camera size={26} color="var(--accent)" strokeWidth={1.75} />
            </div>
            <div style={{ textAlign: "center" }}>
              <p style={{ color: "var(--text-muted)", fontSize: 15, margin: "0 0 4px", fontWeight: 600 }}>Toca para abrir cámara</p>
              <p className="caption" style={{ margin: 0 }}>o elige de galería</p>
            </div>
          </button>
          <button type="button" className="btn-primary" onClick={() => inputRef.current?.click()} onPointerDown={(e) => { e.preventDefault(); inputRef.current?.click(); }}>
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
            <button type="button" className="btn-primary" onClick={handleGenerate} onPointerDown={(e) => { e.preventDefault(); handleGenerate(); }}>
              Generar mi prueba virtual →
            </button>
            <button type="button" className="btn-secondary" onClick={() => inputRef.current?.click()} onPointerDown={(e) => { e.preventDefault(); inputRef.current?.click(); }}>
              Cambiar foto
            </button>
          </div>
        </>
      )}

      {stage === "error" && (
        <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 16, textAlign: "center" }}>
          <span style={{ fontSize: 48 }}>😕</span>
          <p style={{ color: "var(--danger)", fontSize: 15 }}>{error}</p>
          <button type="button" className="btn-secondary" style={{ maxWidth: 260, width: "100%" }}
            onClick={() => { setStage("pick"); setError(""); }}
            onPointerDown={(e) => { e.preventDefault(); setStage("pick"); setError(""); }}>
            Intentar de nuevo
          </button>
        </div>
      )}

      <input ref={inputRef} type="file" accept="image/*" capture="user" style={{ display: "none" }} onChange={onInputChange} />
    </div>
  );
}
