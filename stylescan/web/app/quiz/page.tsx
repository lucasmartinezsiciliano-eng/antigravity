"use client";
import { useState } from "react";
import { ChevronLeft } from "lucide-react";
import { storage } from "@/lib/storage";

// ── Pre-payment steps (7) — expert visagismo consultation order ──────────────
// Emotional hook first (goal), then structural (texture, beard),
// then corrective (focus_areas, density), then lifestyle (time, identity).
// Post-payment questions (hair_history, lifestyle_context, age, scalp)
// will be collected on a future /refine/[id] screen to keep pre-pay short.
const STEPS = [
  {
    key: "main_goal",
    question: "¿Qué quieres conseguir con tu próximo corte?",
    multi: false,
    options: [
      { value: "look_younger",      label: "Verme más joven",               sub: "Quiero rejuvenecer mi imagen" },
      { value: "look_professional",  label: "Proyectar más seriedad",        sub: "Para el trabajo, entrevistas o reuniones" },
      { value: "attract_more",       label: "Gustar más",                    sub: "Sentirme más seguro y atractivo" },
      { value: "modern_update",      label: "Actualizarme",                  sub: "Mi estilo lleva tiempo sin cambiar" },
      { value: "fix_problem",        label: "Corregir algo que no me gusta", sub: "Tengo algo que siempre me ha molestado" },
      { value: "find_identity",      label: "Encontrar mi propio estilo",    sub: "Un look que me represente de verdad" },
    ],
  },
  {
    key: "hair_texture",
    question: "¿Cómo es tu pelo de forma natural, sin productos?",
    multi: false,
    options: [
      { value: "straight", label: "Liso",             sub: "Cae recto, sin onda natural" },
      { value: "wavy",     label: "Ondulado",          sub: "Onda suave o marcada" },
      { value: "curly",    label: "Rizado",            sub: "Rizos definidos" },
      { value: "coily",    label: "Muy rizado / Afro", sub: "Rizo muy cerrado, crespo" },
      { value: "unsure",   label: "No estoy seguro",   sub: "Depende del día o difícil de definir" },
    ],
  },
  {
    key: "beard_status",
    question: "¿Cómo llevas la barba actualmente?",
    multi: false,
    options: [
      { value: "clean_shaven", label: "Sin barba, afeitado",  sub: "Me afeito a diario o casi" },
      { value: "stubble",      label: "Barba de 3 días",      sub: "Siempre con algo de crecimiento corto" },
      { value: "short_beard",  label: "Barba corta",          sub: "Recortada, entre 0,5 y 2 cm" },
      { value: "medium_beard", label: "Barba mediana",        sub: "Perfilada, entre 2 y 5 cm" },
      { value: "full_beard",   label: "Barba larga",          sub: "Más de 5 cm, parte de mi identidad" },
      { value: "considering",  label: "Pensando en cambiarla", sub: "Quiero probar algo diferente" },
    ],
  },
  {
    key: "focus_areas",
    question: "¿Qué te gustaría que tuviéramos especialmente en cuenta?",
    multi: true,
    options: [
      { value: "receding_hairline", label: "Entradas",               sub: "Retroceso en la línea capilar" },
      { value: "crown_thinning",    label: "Coronilla",              sub: "Zona superior con menos volumen" },
      { value: "overall_thinning",  label: "Pelo fino en general",   sub: "Falta densidad en toda la cabeza" },
      { value: "asymmetry",         label: "Asimetría facial",       sub: "Un lado diferente al otro" },
      { value: "cowlick",           label: "Remolinos / pelo rebelde", sub: "Zonas que no siguen la dirección" },
      { value: "wide_forehead",     label: "Frente alta o ancha",    sub: "Mucha frente visible" },
      { value: "round_face",        label: "Cara redonda",           sub: "Quiero dar más longitud visual" },
      { value: "long_face",         label: "Cara larga",             sub: "Quiero dar más anchura visual" },
      { value: "none",              label: "Nada en concreto",       sub: "Todo en orden, el mejor corte posible" },
    ],
  },
  {
    key: "hair_density",
    question: "Cuando te miras al espejo, tu pelo se ve…",
    multi: false,
    options: [
      { value: "thick_dense",        label: "Denso y abundante",    sub: "Mucho pelo, a veces demasiado volumen" },
      { value: "medium",             label: "Normal",               sub: "Ni mucho ni poco" },
      { value: "fine_visible_scalp", label: "Fino, se ve el cuero", sub: "Poca densidad, se transparenta" },
      { value: "uneven",             label: "Irregular",            sub: "Más denso en unas zonas que en otras" },
    ],
  },
  {
    key: "styling_time",
    question: "¿Cuánto tiempo dedicas a peinarte por la mañana?",
    multi: false,
    options: [
      { value: "under_2min", label: "Menos de 2 minutos", sub: "Me paso el agua o directamente nada" },
      { value: "2_5min",     label: "2 a 5 minutos",      sub: "Un poco de producto y listo" },
      { value: "5_10min",    label: "5 a 10 minutos",     sub: "Me importa verme bien cada mañana" },
      { value: "over_10min", label: "Más de 10 minutos",  sub: "Me tomo mi tiempo para el look perfecto" },
    ],
  },
  {
    key: "style_identity",
    question: "¿Qué energía quieres que transmita tu próximo corte?",
    multi: false,
    options: [
      { value: "classic_elegant",    label: "Clásico y elegante",     sub: "Atemporal, cuidado, que nunca falla" },
      { value: "modern_trendy",      label: "Moderno y a la moda",    sub: "Al día con las tendencias, con personalidad" },
      { value: "bold_statement",     label: "Atrevido y diferente",   sub: "Que llame la atención, que sea único" },
      { value: "natural_effortless", label: "Natural y sin esfuerzo", sub: "Que quede bien sin mucho styling" },
      { value: "executive_powerful", label: "Ejecutivo y poderoso",   sub: "Autoridad, imagen de líder" },
      { value: "urban_casual",       label: "Urbano y casual",        sub: "Relajado pero con estilo propio" },
    ],
  },
];

// Non-linear progress — goal-gradient effect (acceleration near the end)
const PROGRESS_PCTS   = [14, 29, 43, 57, 70, 85, 100];
const PROGRESS_LABELS = [
  "Analizando tu objetivo",
  "Perfil capilar detectado",
  "Integrando tu barba",
  "Identificando áreas clave",
  "Calculando densidad y tipo",
  "Ajustando al lifestyle",
  "Último paso — define tu energía",
];

// Micro-commitment ticker — shown for 900 ms between steps
const TICKER_MESSAGES = [
  "Objetivo registrado. Cruzando con 47 referencias de estilo →",
  "Tipo capilar identificado. Filtrando cortes compatibles.",
  "Barba analizada. Ajustando proporción facial y estilo.",
  "Áreas clave anotadas. Calculando técnicas de corrección.",
  "Densidad registrada. Refinando opciones de volumen.",
  "Rutina anotada. Priorizando cortes de bajo mantenimiento.",
];

export default function QuizPage() {
  const [step, setStep]       = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [tickerMsg, setTickerMsg]   = useState("");
  const [showTicker, setShowTicker] = useState(false);

  const current  = STEPS[step];
  const selected = answers[current.key];
  const canNext  = current.multi
    ? ((selected as string[]) || []).length > 0
    : !!selected;

  function goBack() {
    if (step === 0) { window.location.href = "/"; return; }
    storage.saveQuiz(answers);
    setStep(step - 1);
  }

  function select(value: string) {
    if (current.multi) {
      const prev = (answers[current.key] as string[]) || [];
      // "none" is exclusive
      if (value === "none") {
        setAnswers({ ...answers, [current.key]: ["none"] });
        return;
      }
      const without = prev.filter((v) => v !== "none");
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
    storage.saveQuiz(answers);

    if (step < STEPS.length - 1) {
      setTickerMsg(TICKER_MESSAGES[step]);
      setShowTicker(true);
      setTimeout(() => {
        setShowTicker(false);
        setStep(step + 1);
      }, 900);
      return;
    }

    // Last step — proceed to checkout
    window.location.href = "/checkout";
  }

  return (
    <div className="screen" style={{ gap: 0 }}>

      {/* Header — progress */}
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 28 }}>
        <button type="button" className="back-btn" onClick={goBack} aria-label="Volver">
          <ChevronLeft size={20} strokeWidth={2} />
        </button>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 11, color: "var(--gold)", marginBottom: 7, fontWeight: 700, letterSpacing: 0.5 }}>
            {PROGRESS_LABELS[step]}
          </div>
          <div style={{ height: 3, background: "var(--border)", borderRadius: 99, overflow: "hidden" }}>
            <div style={{
              height: "100%",
              background: "var(--gold)",
              borderRadius: 99,
              width: `${PROGRESS_PCTS[step]}%`,
              transition: "width 0.45s cubic-bezier(0.4, 0, 0.2, 1)",
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
                  border: `1.5px solid ${sel ? "var(--gold)" : "var(--border)"}`,
                  background: sel ? "var(--gold-subtle)" : "var(--surface)",
                  transition: "border-color 0.15s, background 0.15s",
                  flexShrink: 0,
                }}
              >
                <div style={{
                  width: 20, height: 20,
                  borderRadius: current.multi ? 5 : "50%",
                  border: `1.5px solid ${sel ? "var(--gold)" : "var(--border)"}`,
                  background: sel ? "var(--gold)" : "transparent",
                  flexShrink: 0,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  transition: "border-color 0.15s, background 0.15s",
                }}>
                  {sel && (
                    <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                      <path d="M1 4L3.5 6.5L9 1" stroke="var(--bg)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
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

          {/* Micro-commitment ticker */}
          {showTicker && (
            <div style={{
              padding: "12px 16px", borderRadius: 10, marginTop: 4,
              background: "var(--gold-subtle)", border: "1px solid var(--gold-border)",
              display: "flex", alignItems: "center", gap: 10,
            }}>
              <div className="dot-pulse" style={{ width: 6, height: 6, flexShrink: 0 }} />
              <span style={{ fontSize: 12, color: "var(--gold)", fontWeight: 600 }}>
                {tickerMsg}
              </span>
            </div>
          )}
        </div>
      </div>

      <div style={{ paddingTop: 16 }}>
        <button
          type="button"
          className="btn-primary"
          onClick={handleNext}
          disabled={!canNext || showTicker}
        >
          {step < STEPS.length - 1 ? "Siguiente" : "Ver mi análisis →"}
        </button>
      </div>
    </div>
  );
}
