"use client";
import { useState } from "react";
import { ChevronLeft } from "lucide-react";
import { storage } from "@/lib/storage";

const STEPS = [
  {
    key: "hair_texture",
    question: "¿Cómo es tu cabello?",
    multi: false,
    options: [
      { value: "straight", label: "Liso", sub: "Sin onda natural" },
      { value: "wavy", label: "Ondulado", sub: "Onda suave" },
      { value: "curly", label: "Rizado", sub: "Rizos definidos" },
      { value: "coily", label: "Muy rizado", sub: "Afro / crespo" },
    ],
  },
  {
    key: "hair_density",
    question: "¿Cuánto cabello tienes?",
    multi: false,
    options: [
      { value: "thin", label: "Fino / escaso", sub: "Se ven zonas del cuero cabelludo" },
      { value: "medium", label: "Normal", sub: "Ni poco ni mucho" },
      { value: "thick", label: "Grueso / abundante", sub: "Mucho volumen natural" },
    ],
  },
  {
    key: "lifestyle",
    question: "¿Cuál es tu entorno habitual?",
    multi: false,
    options: [
      { value: "professional", label: "Profesional", sub: "Oficina, reuniones, formal" },
      { value: "creative", label: "Creativo", sub: "Agencia, arte, sector casual" },
      { value: "active", label: "Deportivo", sub: "Obra, deporte, aire libre" },
      { value: "student", label: "Estudiante", sub: "Campus, vida universitaria" },
      { value: "mixed", label: "Mixto", sub: "Variado, sin código fijo" },
    ],
  },
  {
    key: "style_goal",
    question: "¿Qué buscas con el corte?",
    multi: false,
    options: [
      { value: "professional_look", label: "Más profesional", sub: "Cuidado, serio, imagen sólida" },
      { value: "trendy_look", label: "Más actual", sub: "Tendencias, con personalidad" },
      { value: "effortless_look", label: "Natural y fácil", sub: "Bien sin esforzarse" },
      { value: "confidence_boost", label: "Ganar confianza", sub: "Un cambio real, reinventarse" },
    ],
  },
  {
    key: "preferred_length",
    question: "¿Qué largo prefieres?",
    multi: false,
    options: [
      { value: "very_short", label: "Muy corto", sub: "1–3 cm" },
      { value: "short", label: "Corto", sub: "3–8 cm" },
      { value: "medium", label: "Medio", sub: "12–18 cm" },
      { value: "long", label: "Largo", sub: "Más de 20 cm" },
    ],
  },
  {
    key: "maintenance_willingness",
    question: "¿Cuánto tiempo le dedicas cada mañana?",
    multi: false,
    options: [
      { value: "low", label: "Mínimo", sub: "Ducha y listo, sin producto" },
      { value: "medium", label: "Moderado", sub: "5 min, algo de producto" },
      { value: "high", label: "Me gusta arreglarme", sub: "10+ min, secador, producto" },
    ],
  },
  {
    key: "style_preference",
    question: "¿Con qué estilo te identificas?",
    multi: false,
    options: [
      { value: "classic", label: "Clásico", sub: "Atemporal, sobrio" },
      { value: "modern", label: "Moderno", sub: "Urbano, actual" },
      { value: "trendy", label: "Atrevido", sub: "A la última, llamativo" },
    ],
  },
  {
    key: "beard",
    question: "¿Cómo llevas la barba?",
    multi: false,
    options: [
      { value: "none", label: "Sin barba", sub: "Afeitado" },
      { value: "stubble", label: "Barba de días", sub: "Óptimo según estudios de atractivo" },
      { value: "short", label: "Barba corta", sub: "Menos de 2 cm" },
      { value: "full", label: "Barba completa", sub: "Más de 2 cm" },
      { value: "goatee", label: "Perilla", sub: "Solo en mentón" },
      { value: "mustache", label: "Bigote", sub: "Solo sobre el labio" },
    ],
  },
  {
    key: "problematic_areas",
    question: "¿Tienes alguna zona problemática?",
    multi: true,
    hasOther: true,
    options: [
      { value: "entradas", label: "Entradas", sub: "Retroceso en la línea capilar" },
      { value: "papada", label: "Papada", sub: "Zona bajo el mentón" },
      { value: "orejas_prominentes", label: "Orejas prominentes", sub: "Sobresalen del perfil" },
      { value: "asimetria", label: "Asimetría facial", sub: "Un lado diferente al otro" },
      { value: "frente_alta", label: "Frente alta", sub: "Mucha frente visible" },
      { value: "poco_volumen", label: "Poco volumen", sub: "Cabello fino o aplastado" },
      { value: "mucho_volumen", label: "Demasiado volumen", sub: "Se esponja, se abre" },
      { value: "cicatrices", label: "Cicatrices / manchas", sub: "En cuero cabelludo o rostro" },
      { value: "ninguna", label: "Ninguna", sub: "Todo en orden" },
      { value: "otros", label: "Otros", sub: "Cuéntanos más abajo" },
    ],
  },
];

export default function QuizPage() {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [otherText, setOtherText] = useState("");

  const current = STEPS[step] as typeof STEPS[0] & { hasOther?: boolean };
  const selected = answers[current.key];
  const showOtherInput = current.hasOther && ((selected as string[]) || []).includes("otros");
  const canNext = current.multi
    ? ((selected as string[]) || []).length > 0
    : !!selected;

  function goBack() {
    if (step === 0) { window.location.href = "/"; return; }
    setStep(step - 1);
  }

  function select(value: string) {
    if (current.multi) {
      const prev = (answers[current.key] as string[]) || [];
      if (value === "ninguna") {
        setAnswers({ ...answers, [current.key]: ["ninguna"] });
        return;
      }
      const without = prev.filter((v) => v !== "ninguna");
      const next = without.includes(value)
        ? without.filter((v) => v !== value)
        : [...without, value];
      setAnswers({ ...answers, [current.key]: next });
    } else {
      setAnswers({ ...answers, [current.key]: value });
    }
  }

  function isSelected(value: string) {
    if (current.multi) return ((answers[current.key] as string[]) || []).includes(value);
    return answers[current.key] === value;
  }

  function handleNext() {
    const finalAnswers = { ...answers };
    if (otherText.trim()) finalAnswers.additional_notes = otherText.trim();
    if (step < STEPS.length - 1) {
      setStep(step + 1);
      return;
    }
    storage.saveQuiz(finalAnswers);
    window.location.href = "/checkout";
  }

  return (
    <div className="screen" style={{ gap: 0 }}>

      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 28 }}>
        <button type="button" className="back-btn" onClick={goBack} aria-label="Volver">
          <ChevronLeft size={20} strokeWidth={2} />
        </button>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 11, color: "var(--text-dim)", marginBottom: 7, fontWeight: 600, letterSpacing: 0.5 }}>
            {step + 1} / {STEPS.length}
          </div>
          <div style={{ height: 3, background: "var(--border)", borderRadius: 99, overflow: "hidden" }}>
            <div style={{
              height: "100%",
              background: "var(--accent)",
              borderRadius: 99,
              width: `${((step + 1) / STEPS.length) * 100}%`,
              transition: "width 0.35s cubic-bezier(0.4, 0, 0.2, 1)",
            }} />
          </div>
        </div>
      </div>

      {/* Step content */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
        <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20, marginTop: 0, lineHeight: 1.3 }}>
          {current.question}
        </h2>

        <div style={{ display: "flex", flexDirection: "column", gap: 8, flex: 1, overflowY: "auto", minHeight: 0, WebkitOverflowScrolling: "touch" } as React.CSSProperties}>
          {current.options.map((opt) => {
            const sel = isSelected(opt.value);
            return (
              <button
                type="button"
                key={opt.value}
                onClick={() => select(opt.value)}
                style={{
                  display: "flex", alignItems: "center", gap: 14,
                  padding: "14px 16px", borderRadius: 14, textAlign: "left",
                  border: `1.5px solid ${sel ? "var(--accent)" : "var(--border)"}`,
                  background: sel ? "var(--accent-subtle)" : "var(--surface)",
                  transition: "border-color 0.15s, background 0.15s",
                  flexShrink: 0,
                }}
              >
                <div style={{
                  width: 20, height: 20,
                  borderRadius: current.multi ? 5 : "50%",
                  border: `1.5px solid ${sel ? "var(--accent)" : "var(--border)"}`,
                  background: sel ? "var(--accent)" : "transparent",
                  flexShrink: 0,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  transition: "border-color 0.15s, background 0.15s",
                }}>
                  {sel && (
                    <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                      <path d="M1 4L3.5 6.5L9 1" stroke="#0C0C0C" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 15 }}>{opt.label}</div>
                  <div style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 2 }}>{opt.sub}</div>
                </div>
              </button>
            );
          })}

          {showOtherInput && (
            <textarea
              value={otherText}
              onChange={(e) => setOtherText(e.target.value)}
              placeholder="Cuéntanos tu caso con tus palabras…"
              rows={3}
              style={{
                width: "100%", padding: "14px 16px",
                background: "var(--surface2)", border: "1px solid var(--accent)",
                borderRadius: 12, fontSize: 14, resize: "none", outline: "none",
                color: "var(--text)", lineHeight: 1.5,
              }}
            />
          )}
        </div>
      </div>

      <div style={{ paddingTop: 16 }}>
        <button type="button" className="btn-primary" onClick={handleNext} disabled={!canNext}>
          {step < STEPS.length - 1 ? "Siguiente" : "Continuar"}
        </button>
      </div>
    </div>
  );
}
