"use client";
import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ChevronLeft, ChevronDown, ChevronUp, Scissors, CalendarDays, Home, Star, Camera } from "lucide-react";
import { api, AnalysisResult } from "@/lib/api";

type UpsellType = "colorimetry" | "products" | "pack";
type VisualsStatus = "idle" | "uploading" | "processing" | "ready" | "failed";

const MAINTENANCE_COLOR: Record<string, string> = {
  bajo: "#3DB882",
  medio: "#C9A84C",
  alto: "#D94F4F",
};

const FACE_SHAPE_LABEL: Record<string, string> = {
  oval: "Óvalo",
  round: "Redonda",
  square: "Cuadrada",
  oblong: "Alargada",
  heart: "Corazón",
  diamond: "Diamante",
};

const ANGLE_LABELS = ["Frontal", "3/4 ←", "3/4 →"];

export default function ResultPage() {
  const params = useParams();
  const id = params.id as string;

  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedCut, setExpandedCut] = useState<number | null>(0);
  const [upsellLoading, setUpsellLoading] = useState<UpsellType | null>(null);

  // Visuals — virtual try-on per cut
  const [visuals, setVisuals] = useState<any[]>([]);
  const [visualsStatus, setVisualsStatus] = useState<VisualsStatus>("idle");
  const [cutAngle, setCutAngle] = useState([0, 0, 0]);
  const visualsFileRef = useRef<HTMLInputElement>(null);
  const visualsPollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function startVisualsPoll() {
    if (visualsPollRef.current) clearInterval(visualsPollRef.current);
    visualsPollRef.current = setInterval(async () => {
      try {
        const data = await api.getVisuals(id);
        if (data.visuals_status === "ready") {
          clearInterval(visualsPollRef.current!);
          setVisuals(data.visuals);
          setVisualsStatus("ready");
        } else if (data.visuals_status === "failed") {
          clearInterval(visualsPollRef.current!);
          setVisualsStatus("failed");
        }
      } catch {}
    }, 3000);
  }

  useEffect(() => {
    let mounted = true;

    api.getResult(id)
      .then((r) => { if (mounted) setResult(r); })
      .catch((e) => { if (mounted) setError(e.message || "No se pudo cargar el resultado."); })
      .finally(() => { if (mounted) setLoading(false); });

    // Check visuals status, then auto-trigger from sessionStorage if needed
    api.getVisuals(id).then((data) => {
      if (!mounted) return;
      if (data.visuals_status === "ready" && data.visuals.length) {
        setVisuals(data.visuals);
        setVisualsStatus("ready");
        return;
      }
      if (data.visuals_status === "processing") {
        setVisualsStatus("processing");
        startVisualsPoll();
        return;
      }
      // Not started — auto-trigger from frontal photo saved during capture
      const saved = sessionStorage.getItem(`visai_frontal_${id}`);
      if (!saved) return;
      sessionStorage.removeItem(`visai_frontal_${id}`);
      setVisualsStatus("uploading");
      fetch(saved)
        .then((r) => r.blob())
        .then((blob) => {
          if (!mounted) return null;
          const file = new File([blob], "frontal.jpg", { type: "image/jpeg" });
          return api.generateVisuals(id, file);
        })
        .then(() => {
          if (!mounted) return;
          setVisualsStatus("processing");
          startVisualsPoll();
        })
        .catch(() => { if (mounted) setVisualsStatus("idle"); });
    }).catch(() => {});

    return () => {
      mounted = false;
      if (visualsPollRef.current) clearInterval(visualsPollRef.current);
    };
  }, [id]); // eslint-disable-line

  async function handleVisualsFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = "";
    setVisualsStatus("uploading");
    try {
      await api.generateVisuals(id, file);
      setVisualsStatus("processing");
      startVisualsPoll();
    } catch {
      setVisualsStatus("failed");
    }
  }

  async function handleUpsell(type: UpsellType) {
    setUpsellLoading(type);
    try {
      const res = await api.upsell(id, type);
      if (res.checkout_url.startsWith("https://checkout.stripe.com")) {
        window.location.href = res.checkout_url;
      } else {
        const updated = await api.getResult(id);
        setResult(updated);
      }
    } catch (e: any) {
      alert(e.message || "Error al procesar la compra.");
    } finally {
      setUpsellLoading(null);
    }
  }

  if (loading) {
    return (
      <div className="screen" style={{ alignItems: "center", justifyContent: "center", gap: 20 }}>
        <div style={{ display: "flex", gap: 6 }}>
          {[0, 1, 2].map((i) => (
            <div key={i} className="dot-pulse" style={{ animationDelay: `${i * 0.4}s` }} />
          ))}
        </div>
        <p style={{ color: "var(--text-muted)", fontSize: 14 }}>Cargando tu análisis…</p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="screen" style={{ alignItems: "center", justifyContent: "center", gap: 16, textAlign: "center" }}>
        <span style={{ fontSize: 48 }}>😕</span>
        <p style={{ color: "var(--danger)", fontSize: 15 }}>{error || "Resultado no disponible"}</p>
        <Link href="/" className="btn-secondary" style={{ maxWidth: 280, width: "100%", textDecoration: "none" }}>
          Volver al inicio
        </Link>
      </div>
    );
  }

  const report = result.report || {};
  const cuts: any[] = report.cortes_recomendados || [];
  const avoid: string[] = report.cortes_a_evitar || [];
  const shapeLabel = FACE_SHAPE_LABEL[result.face_shape] || result.face_shape;

  return (
    <div style={{ background: "var(--bg)", minHeight: "100dvh", paddingBottom: 60 }}>
      <div style={{ maxWidth: 480, margin: "0 auto", padding: "0 20px" }}>

        {/* Header */}
        <div style={{ paddingTop: 24, paddingBottom: 8, display: "flex", alignItems: "center", gap: 12 }}>
          <Link href="/" className="back-btn" aria-label="Inicio">
            <ChevronLeft size={20} strokeWidth={2} />
          </Link>
          <span style={{ fontSize: 14, fontWeight: 600, color: "var(--text-muted)" }}>Tu análisis</span>
        </div>

        {/* Face shape hero */}
        <div style={{ paddingTop: 16, paddingBottom: 24 }}>
          <div className="card" style={{ textAlign: "center", padding: "28px 20px" }}>
            <div style={{
              display: "inline-flex", alignItems: "center", justifyContent: "center",
              width: 64, height: 64, borderRadius: 18,
              background: "var(--accent-subtle)", border: "1px solid rgba(201,168,76,0.2)",
              marginBottom: 14,
            }}>
              <Scissors size={28} color="var(--accent)" strokeWidth={1.75} />
            </div>
            <div className="label" style={{ marginBottom: 6 }}>Forma de cara detectada</div>
            <h1 style={{ fontSize: 30, fontWeight: 800, margin: "0 0 4px", letterSpacing: -0.5 }}>
              Cara {shapeLabel}
            </h1>
            <p className="caption" style={{ marginBottom: report.resumen_facial ? 16 : 0 }}>
              {Math.round((result.confidence || 0) * 100)}% de confianza
            </p>
            {report.resumen_facial && (
              <p style={{ fontSize: 14, lineHeight: 1.7, color: "var(--text-muted)", margin: 0, textAlign: "left" }}>
                {report.resumen_facial}
              </p>
            )}
          </div>
        </div>

        {/* Ventaja facial */}
        {report.ventaja_facial && (
          <div style={{ marginBottom: 12 }}>
            <div className="card-accent" style={{ padding: "16px 18px" }}>
              <div className="label-accent" style={{ marginBottom: 8 }}>Tu punto fuerte</div>
              <p style={{ fontSize: 14, lineHeight: 1.65, margin: 0 }}>{report.ventaja_facial}</p>
            </div>
          </div>
        )}

        {/* Cortes */}
        <h2 style={{ fontSize: 17, fontWeight: 700, margin: "24px 0 12px", letterSpacing: -0.3 }}>
          Tus 3 cortes ideales
        </h2>

        {/* Visuals prompt / status */}
        {visualsStatus === "idle" && (
          <div className="card" style={{
            marginBottom: 12, padding: "14px 18px",
            display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12,
          }}>
            <div>
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 2 }}>🪄 Prueba virtual</div>
              <div style={{ color: "var(--text-muted)", fontSize: 12, lineHeight: 1.4 }}>
                Sube una selfie y verás cómo te queda cada corte
              </div>
            </div>
            <button
              type="button"
              onClick={() => visualsFileRef.current?.click()}
              style={{
                display: "flex", alignItems: "center", gap: 6,
                padding: "10px 14px", borderRadius: 99, flexShrink: 0,
                background: "var(--accent)", color: "#080808",
                fontSize: 13, fontWeight: 700,
              }}
            >
              <Camera size={14} strokeWidth={2.5} />
              Foto
            </button>
          </div>
        )}

        {(visualsStatus === "uploading" || visualsStatus === "processing") && (
          <div className="card" style={{ marginBottom: 12, padding: "14px 18px", display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{ display: "flex", gap: 4 }}>
              {[0, 1, 2].map((i) => (
                <div key={i} className="dot-pulse" style={{ width: 6, height: 6, animationDelay: `${i * 0.4}s` }} />
              ))}
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 14 }}>
                {visualsStatus === "uploading" ? "Subiendo foto…" : "Generando prueba virtual…"}
              </div>
              {visualsStatus === "processing" && (
                <div style={{ color: "var(--text-muted)", fontSize: 12 }}>Suele tardar 30–60 segundos</div>
              )}
            </div>
          </div>
        )}

        {visualsStatus === "failed" && (
          <div className="card" style={{ marginBottom: 12, padding: "14px 18px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
            <span style={{ color: "var(--danger)", fontSize: 13 }}>No se pudo generar la prueba visual.</span>
            <button type="button" onClick={() => setVisualsStatus("idle")} style={{ fontSize: 12, color: "var(--text-muted)", textDecoration: "underline" }}>
              Reintentar
            </button>
          </div>
        )}

        <input
          ref={visualsFileRef}
          type="file"
          accept="image/*"
          capture="user"
          style={{ display: "none" }}
          onChange={handleVisualsFile}
        />

        {/* Cut cards */}
        {cuts.map((cut: any, i: number) => {
          const open = expandedCut === i;
          const maintColor = MAINTENANCE_COLOR[cut.nivel_mantenimiento] || "#888";
          const cutVisual = visuals[i];
          const angles: any[] = cutVisual?.angles || [];
          const selectedAngle = cutAngle[i] ?? 0;
          const imgUrl = angles[selectedAngle]?.url;

          return (
            <div key={i} className="card" style={{ marginBottom: 10, padding: 0, overflow: "hidden" }}>

              {/* Virtual try-on image + angle switcher */}
              {visualsStatus === "ready" && angles.length > 0 && (
                <div>
                  {imgUrl && (
                    <img
                      src={imgUrl}
                      alt={`${cut.nombre} — ${ANGLE_LABELS[selectedAngle]}`}
                      style={{ width: "100%", height: 220, objectFit: "cover", objectPosition: "center top", display: "block" }}
                    />
                  )}
                  <div style={{ display: "flex", gap: 4, padding: "8px 12px", background: "var(--surface2)", borderBottom: "1px solid var(--border)" }}>
                    {ANGLE_LABELS.map((lbl, ai) => (
                      <button
                        key={ai}
                        type="button"
                        onClick={() => setCutAngle((prev) => { const next = [...prev]; next[i] = ai; return next; })}
                        style={{
                          fontSize: 11, fontWeight: 600, padding: "4px 10px", borderRadius: 99,
                          background: cutAngle[i] === ai ? "var(--accent)" : "var(--surface)",
                          color: cutAngle[i] === ai ? "#080808" : "var(--text-muted)",
                          border: `1px solid ${cutAngle[i] === ai ? "var(--accent)" : "var(--border)"}`,
                          transition: "all 0.15s",
                        }}
                      >
                        {lbl}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Accordion header */}
              <button
                type="button"
                onClick={() => setExpandedCut(open ? null : i)}
                style={{ width: "100%", textAlign: "left", padding: "16px 18px" }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", gap: 6, marginBottom: 6, flexWrap: "wrap" }}>
                      <span style={{
                        fontSize: 11, fontWeight: 700, padding: "3px 8px", borderRadius: 99,
                        background: "var(--surface2)", color: "var(--text-muted)", letterSpacing: 0.3,
                      }}>
                        {cut.nivel_estilo}
                      </span>
                      <span style={{
                        fontSize: 11, fontWeight: 700, padding: "3px 8px", borderRadius: 99,
                        background: `${maintColor}18`, color: maintColor, letterSpacing: 0.3,
                      }}>
                        mantenimiento {cut.nivel_mantenimiento}
                      </span>
                    </div>
                    <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 2 }}>{cut.nombre}</div>
                    <div style={{ color: "var(--text-muted)", fontSize: 13 }}>{cut.nombre_tecnico}</div>
                  </div>
                  <div style={{ color: "var(--text-dim)", flexShrink: 0, marginTop: 2 }}>
                    {open ? <ChevronUp size={18} strokeWidth={2} /> : <ChevronDown size={18} strokeWidth={2} />}
                  </div>
                </div>
              </button>

              {/* Expanded content */}
              {open && (
                <div style={{ padding: "0 18px 18px", borderTop: "1px solid var(--border)", paddingTop: 16 }}>
                  <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                    {cut.descripcion_favorece && (
                      <div>
                        <div className="label-accent" style={{ marginBottom: 6 }}>Por qué te favorece</div>
                        <p style={{ fontSize: 14, lineHeight: 1.65, margin: 0 }}>{cut.descripcion_favorece}</p>
                      </div>
                    )}
                    {cut.como_pedirlo_al_barbero && (
                      <div style={{
                        background: "var(--surface2)", border: "1px solid var(--border)",
                        borderRadius: 12, padding: "14px 16px",
                      }}>
                        <div className="label-accent" style={{ marginBottom: 8 }}>Cómo pedirlo en la barbería</div>
                        <p style={{ fontSize: 14, lineHeight: 1.65, margin: 0 }}>{cut.como_pedirlo_al_barbero}</p>
                      </div>
                    )}
                    {cut.mantenimiento_casa && (
                      <div>
                        <div className="label" style={{ marginBottom: 6 }}>
                          <Home size={11} style={{ display: "inline", marginRight: 4 }} />
                          En casa
                        </div>
                        <p style={{ fontSize: 14, lineHeight: 1.6, margin: 0, color: "var(--text-muted)" }}>
                          {cut.mantenimiento_casa}
                        </p>
                      </div>
                    )}
                    {cut.frecuencia_barberia && (
                      <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
                        <CalendarDays size={15} color="var(--text-muted)" strokeWidth={1.75} style={{ flexShrink: 0, marginTop: 2 }} />
                        <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0, lineHeight: 1.5 }}>
                          {cut.frecuencia_barberia}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {/* Consejos específicos */}
        {report.consejos_especificos && (
          <div style={{ margin: "24px 0 12px" }}>
            <h2 style={{ fontSize: 17, fontWeight: 700, margin: "0 0 12px", letterSpacing: -0.3 }}>Consejos para ti</h2>
            <div className="card">
              <p style={{ fontSize: 14, lineHeight: 1.75, margin: 0, whiteSpace: "pre-line", color: "var(--text-muted)" }}>
                {report.consejos_especificos}
              </p>
            </div>
          </div>
        )}

        {/* Cortes a evitar */}
        {avoid.length > 0 && (
          <div style={{ margin: "24px 0 12px" }}>
            <h2 style={{ fontSize: 17, fontWeight: 700, margin: "0 0 12px", letterSpacing: -0.3 }}>Cortes a evitar</h2>
            <div className="card">
              {avoid.map((a: string, i: number) => (
                <div key={i} style={{
                  display: "flex", gap: 10, alignItems: "flex-start",
                  paddingBottom: i < avoid.length - 1 ? 12 : 0,
                  marginBottom: i < avoid.length - 1 ? 12 : 0,
                  borderBottom: i < avoid.length - 1 ? "1px solid var(--border)" : "none",
                }}>
                  <span style={{ color: "var(--danger)", fontSize: 13, flexShrink: 0, fontWeight: 700, marginTop: 2 }}>✕</span>
                  <p style={{ fontSize: 14, lineHeight: 1.6, margin: 0, color: "var(--text-muted)" }}>{a}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Upsells */}
        <div style={{ margin: "32px 0 24px" }}>
          <h2 style={{ fontSize: 17, fontWeight: 700, margin: "0 0 4px", letterSpacing: -0.3 }}>Añade más a tu análisis</h2>
          <p style={{ color: "var(--text-muted)", fontSize: 13, margin: "0 0 16px" }}>Un solo pago · Sin suscripción</p>

          {!result.includes_colorimetry && !result.includes_products_guide && (
            <div className="card-accent" style={{ marginBottom: 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                    <Star size={14} color="var(--accent)" strokeWidth={2} fill="var(--accent)" />
                    <span style={{ fontWeight: 700, fontSize: 15 }}>Pack completo</span>
                  </div>
                  <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Colorimetría + Guía de productos</div>
                </div>
                <div style={{ fontWeight: 800, fontSize: 17, color: "var(--accent)", flexShrink: 0, marginLeft: 12 }}>3,49 €</div>
              </div>
              <button
                type="button"
                className="btn-primary"
                onClick={() => handleUpsell("pack")}
                disabled={upsellLoading !== null}
                style={{ fontSize: 14, padding: "14px" }}
              >
                {upsellLoading === "pack" ? "Procesando…" : "Pack completo — ahorra 22% →"}
              </button>
            </div>
          )}

          {!result.includes_colorimetry && (
            <div className="card" style={{ marginBottom: 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 3 }}>🎨 Colorimetría personal</div>
                  <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Paleta de ropa, tonos, monturas de gafas</div>
                </div>
                <div style={{ fontWeight: 700, fontSize: 15, color: "var(--accent)", flexShrink: 0, marginLeft: 12 }}>2,49 €</div>
              </div>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => handleUpsell("colorimetry")}
                disabled={upsellLoading !== null}
                style={{ fontSize: 14, padding: "12px" }}
              >
                {upsellLoading === "colorimetry" ? "Procesando…" : "Añadir colorimetría →"}
              </button>
            </div>
          )}

          {result.includes_colorimetry && result.colorimetry_report && (
            <div className="card-accent" style={{ marginBottom: 10 }}>
              <div className="label-accent" style={{ marginBottom: 10 }}>🎨 Tu colorimetría</div>
              {result.colorimetry_report.paleta_colores_ropa && (
                <div style={{ marginBottom: 10 }}>
                  <div className="label" style={{ marginBottom: 8 }}>Paleta recomendada</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {(result.colorimetry_report.paleta_colores_ropa as string[]).map((c: string, i: number) => (
                      <span key={i} style={{
                        padding: "4px 10px", borderRadius: 99,
                        background: "var(--surface2)", fontSize: 13,
                        border: "1px solid var(--border)",
                      }}>{c}</span>
                    ))}
                  </div>
                </div>
              )}
              {result.colorimetry_report.razon_paleta && (
                <p style={{ fontSize: 14, lineHeight: 1.6, margin: 0, color: "var(--text-muted)" }}>
                  {result.colorimetry_report.razon_paleta}
                </p>
              )}
            </div>
          )}

          {!result.includes_products_guide && (
            <div className="card" style={{ marginBottom: 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 3 }}>🧴 Guía de productos</div>
                  <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Productos exactos, rutina diaria, técnica</div>
                </div>
                <div style={{ fontWeight: 700, fontSize: 15, color: "var(--accent)", flexShrink: 0, marginLeft: 12 }}>1,99 €</div>
              </div>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => handleUpsell("products")}
                disabled={upsellLoading !== null}
                style={{ fontSize: 14, padding: "12px" }}
              >
                {upsellLoading === "products" ? "Procesando…" : "Añadir guía de productos →"}
              </button>
            </div>
          )}

          {result.includes_products_guide && result.products_guide && (
            <div className="card-accent" style={{ marginBottom: 10 }}>
              <div className="label-accent" style={{ marginBottom: 10 }}>🧴 Tu guía de productos</div>
              {result.products_guide.tipo_cabello_descripcion && (
                <p style={{ fontSize: 14, lineHeight: 1.6, margin: "0 0 10px" }}>
                  {result.products_guide.tipo_cabello_descripcion}
                </p>
              )}
              {result.products_guide.rutina_diaria && (
                <div>
                  <div className="label" style={{ marginBottom: 6 }}>Rutina diaria</div>
                  <p style={{ fontSize: 14, lineHeight: 1.7, margin: 0, whiteSpace: "pre-line", color: "var(--text-muted)" }}>
                    {result.products_guide.rutina_diaria}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        <p className="caption" style={{ textAlign: "center", paddingBottom: 40 }}>
          Resultados válidos 90 días · La foto se eliminó al instante (RGPD)
        </p>
      </div>
    </div>
  );
}
