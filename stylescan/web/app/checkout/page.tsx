"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { ChevronLeft, Lock, Trash2, Zap, Check, ShieldCheck, Mail, MessageCircle, RotateCcw } from "lucide-react";
import { storage } from "@/lib/storage";
import { api } from "@/lib/api";

const TRUST = [
  { Icon: Lock,   label: "Pago seguro",       color: "var(--gold)" },
  { Icon: Trash2, label: "Foto eliminada",     color: "var(--gold)" },
  { Icon: Zap,    label: "Resultado en 1 min", color: "var(--gold)" },
];

const INCLUDES = [
  { emoji: "📐", title: "Análisis facial completo", sub: "468 puntos · forma · proporciones · asimetría" },
  { emoji: "💈", title: "3 cortes personalizados", sub: "Instrucciones exactas para pedir en la barbería" },
  { emoji: "🪄", title: "Prueba virtual", sub: "Ve cómo quedas antes de cortarte" },
];

// RGPD consent items — required before payment
const CONSENT_ITEMS = [
  { key: "biometric", label: "Acepto el análisis de datos biométricos faciales para determinar mi forma de cráneo y proporciones." },
  { key: "special",   label: "Entiendo que los datos biométricos son datos de categoría especial (RGPD Art. 9) y consiento expresamente su tratamiento." },
  { key: "retention", label: "Acepto que las métricas faciales (no las fotos) se conserven durante 90 días para entregar mi informe." },
  { key: "age",       label: "Confirmo que tengo 18 años o más." },
];
const MARKETING_KEY = "marketing_emails";

// RFC 5322-lite — covers >99% of real Spanish emails without false negatives
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
// Acepta: 6XXXXXXXX, 7XXXXXXXX, +34 6XX XXX XXX, 0034..., con espacios/guiones
const PHONE_RE = /^(?:\+?34[\s-]?)?[67]\d{2}[\s-]?\d{3}[\s-]?\d{3}$/;


function ConsentCheckbox({ label, checked, onToggle, muted }: { label: string; checked: boolean; onToggle: () => void; muted?: boolean }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      style={{
        display: "flex", alignItems: "flex-start", gap: 12,
        padding: "12px 14px", borderRadius: 12, textAlign: "left", width: "100%",
        border: `1.5px solid ${checked ? "var(--gold)" : "var(--border)"}`,
        background: checked ? "var(--gold-subtle)" : "var(--surface)",
        transition: "border-color 0.15s, background 0.15s",
      }}
    >
      <div style={{
        width: 18, height: 18, borderRadius: 5, flexShrink: 0, marginTop: 2,
        border: `1.5px solid ${checked ? "var(--gold)" : "var(--border)"}`,
        background: checked ? "var(--gold)" : "transparent",
        display: "flex", alignItems: "center", justifyContent: "center",
        transition: "border-color 0.15s, background 0.15s",
      }}>
        {checked && (
          <svg width="9" height="7" viewBox="0 0 10 8" fill="none">
            <path d="M1 4L3.5 6.5L9 1" stroke="#080808" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        )}
      </div>
      <span style={{ fontSize: 13, lineHeight: 1.5, color: muted ? "var(--text-muted)" : "var(--text)" }}>{label}</span>
    </button>
  );
}

export default function CheckoutPage() {
  const [barberCode, setBarberCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [consent, setConsent] = useState<Record<string, boolean>>({});
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [emailTouched, setEmailTouched] = useState(false);
  const [phoneTouched, setPhoneTouched] = useState(false);

  const hasCode = barberCode.trim().length > 0;
  const emailValid = EMAIL_RE.test(email.trim());
  const phoneValid = phone.trim() === "" || PHONE_RE.test(phone.trim());
  const allRequired = CONSENT_ITEMS.every((item) => consent[item.key]) && emailValid && phoneValid;

  useEffect(() => {
    const code = storage.getBarberCode();
    if (code) setBarberCode(code);
    const savedEmail = storage.getEmail();
    if (savedEmail) setEmail(savedEmail);
    const savedPhone = storage.getPhone();
    if (savedPhone) setPhone(savedPhone);
    const quiz = storage.getQuiz();
    if (!quiz || Object.keys(quiz).length === 0) { window.location.href = "/quiz"; }
  }, []);

  function toggleConsent(key: string) {
    setConsent((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  function handlePay() {
    if (!allRequired) return;
    const code = barberCode.trim().toUpperCase() || undefined;
    if (code) storage.saveBarberCode(code);
    storage.saveConsentState(consent);
    storage.saveEmail(email.trim().toLowerCase());
    const cleanedPhone = phone.trim();
    if (cleanedPhone) storage.savePhone(cleanedPhone);
    window.location.href = "/add-ons";
  }

  return (
    <div className="screen" style={{ justifyContent: "space-between", paddingTop: 32, paddingBottom: 40 }}>

      <div>
        {/* Back */}
        <Link href="/quiz" className="back-btn" aria-label="Volver" style={{ marginBottom: 28 }}>
          <ChevronLeft size={20} strokeWidth={2} />
        </Link>

        {/* Price hero */}
        <div style={{ textAlign: "center", marginBottom: 28, position: "relative" }}>

          <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 10, letterSpacing: 0.8, fontWeight: 600 }}>
            VISAGISMO PROFESIONAL CON IA
          </div>

          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "center", gap: 2, lineHeight: 1 }}>
            <span style={{ fontSize: 22, fontWeight: 700, color: "var(--gold)", marginTop: 10 }}>€</span>
            <span style={{ fontSize: 72, fontWeight: 900, letterSpacing: -3 }}>
              {hasCode ? "10" : "12"}
            </span>
            <span style={{ fontSize: 32, fontWeight: 700, marginTop: 14 }}>,99</span>
          </div>

          {hasCode ? (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 8, marginTop: 6 }}>
              <span style={{ color: "var(--text-dim)", fontSize: 14, textDecoration: "line-through" }}>12,99 €</span>
              <span style={{
                color: "var(--success)", fontSize: 12, fontWeight: 700,
                background: "rgba(61,184,130,0.1)", padding: "3px 8px", borderRadius: 99,
              }}>
                −2 € código barbería
              </span>
            </div>
          ) : (
            <p style={{ color: "var(--text-muted)", fontSize: 14, marginTop: 4 }}>Pago único · Sin suscripción</p>
          )}
        </div>

        {/* Anchoring — loss frame (2x más persuasivo que el gain frame) */}
        <div style={{ textAlign: "center", marginBottom: 16, padding: "0 4px" }}>
          <p style={{ fontSize: 12, color: "var(--text-dim)", margin: 0, lineHeight: 1.7 }}>
            Un corte a ciegas en España cuesta <strong style={{ color: "var(--text)" }}>€16–20</strong> y 4 semanas esperando que crezca.<br />
            <span style={{ color: "var(--text-muted)", fontWeight: 600 }}>
              VISAI: €12,99 · una vez · siempre aciertas.
            </span>
          </p>
        </div>

        {/* What's included */}
        <div className="card" style={{ marginBottom: 16, padding: "16px 18px" }}>
          <div className="label" style={{ marginBottom: 14 }}>Lo que obtienes</div>
          {INCLUDES.map(({ emoji, title, sub }, i) => (
            <div key={title} style={{
              display: "flex", gap: 12, alignItems: "flex-start",
              padding: "10px 0",
              borderBottom: i < INCLUDES.length - 1 ? "1px solid var(--border)" : "none",
            }}>
              <span style={{ fontSize: 18, flexShrink: 0, marginTop: 1 }}>{emoji}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: 14 }}>{title}</div>
                <div style={{ color: "var(--text-muted)", fontSize: 12, marginTop: 2 }}>{sub}</div>
              </div>
              <Check size={16} color="var(--success)" strokeWidth={2.5} style={{ flexShrink: 0, marginTop: 3 }} />
            </div>
          ))}
        </div>

        {/* Contact — delivery channel + recovery */}
        <div className="card" style={{ marginBottom: 16, padding: "16px 18px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
            <RotateCcw size={13} color="var(--gold)" strokeWidth={2.25} />
            <span className="label" style={{ color: "var(--text)" }}>¿Dónde te enviamos los resultados?</span>
          </div>
          <p style={{ fontSize: 12, color: "var(--text-muted)", margin: "0 0 14px", lineHeight: 1.55 }}>
            Te enviamos tu análisis y un <strong style={{ color: "var(--text)" }}>enlace para recuperarlo</strong> cuando quieras —
            aunque cambies de móvil o cierres la app.
          </p>

          {/* Email — required */}
          <label htmlFor="email" style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, color: "var(--text-muted)", marginBottom: 6, fontWeight: 500 }}>
            <Mail size={13} strokeWidth={2} />
            Email <span style={{ color: "var(--gold)" }}>*</span>
          </label>
          <input
            id="email"
            type="email"
            inputMode="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onBlur={() => setEmailTouched(true)}
            placeholder="tu@email.com"
            style={{
              width: "100%", padding: "12px 14px",
              background: "var(--surface)", outline: "none",
              border: `1.5px solid ${emailTouched && !emailValid ? "var(--danger)" : emailValid ? "var(--gold)" : "var(--border)"}`,
              borderRadius: 12, fontSize: 15,
              transition: "border-color 0.2s",
            }}
          />
          {emailTouched && !emailValid && (
            <p style={{ color: "var(--danger)", fontSize: 12, marginTop: 4 }}>
              Introduce un email válido — es donde recibirás tu análisis.
            </p>
          )}

          {/* Phone — optional */}
          <label htmlFor="phone" style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, color: "var(--text-muted)", margin: "14px 0 6px", fontWeight: 500 }}>
            <MessageCircle size={13} strokeWidth={2} color="#25D366" />
            Móvil <span style={{ color: "var(--text-dim)", fontWeight: 400 }}>(opcional · WhatsApp)</span>
          </label>
          <input
            id="phone"
            type="tel"
            inputMode="tel"
            autoComplete="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            onBlur={() => setPhoneTouched(true)}
            placeholder="+34 6XX XXX XXX"
            style={{
              width: "100%", padding: "12px 14px",
              background: "var(--surface)", outline: "none",
              border: `1.5px solid ${phoneTouched && !phoneValid ? "var(--danger)" : phone && phoneValid ? "var(--gold)" : "var(--border)"}`,
              borderRadius: 12, fontSize: 15,
              transition: "border-color 0.2s",
            }}
          />
          {phoneTouched && !phoneValid ? (
            <p style={{ color: "var(--danger)", fontSize: 12, marginTop: 4 }}>
              Formato no válido. Ejemplo: +34 612 345 678
            </p>
          ) : (
            <p style={{ fontSize: 11, color: "var(--text-dim)", marginTop: 6, lineHeight: 1.5 }}>
              Solo lo usamos para avisarte por WhatsApp cuando tu análisis esté listo. No spam, no marketing.
            </p>
          )}
        </div>

        {/* RGPD Consent — required before paying */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 10 }}>
            <ShieldCheck size={13} color="var(--text-muted)" strokeWidth={2} />
            <span className="label">Privacidad y consentimiento</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {CONSENT_ITEMS.map((item) => (
              <ConsentCheckbox
                key={item.key}
                label={item.label}
                checked={!!consent[item.key]}
                onToggle={() => toggleConsent(item.key)}
              />
            ))}
            <div style={{ borderTop: "1px solid var(--border)", paddingTop: 6, marginTop: 2 }}>
              <p className="label" style={{ marginBottom: 6, color: "var(--text-dim)", fontSize: 10 }}>OPCIONAL</p>
              <ConsentCheckbox
                label="Acepto recibir comunicaciones comerciales de VISAI por email (novedades, tendencias y ofertas). Puedes darte de baja en cualquier momento."
                checked={!!consent[MARKETING_KEY]}
                onToggle={() => toggleConsent(MARKETING_KEY)}
                muted
              />
            </div>
          </div>
        </div>

        {/* Trust badges */}
        <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
          {TRUST.map(({ Icon, label, color }) => (
            <div key={label} style={{
              flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 6,
              padding: "12px 6px",
              background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "var(--r-md)",
            }}>
              <Icon size={16} color={color} strokeWidth={1.75} />
              <span style={{ fontSize: 10, color: "var(--text-muted)", textAlign: "center", lineHeight: 1.3, fontWeight: 500 }}>
                {label}
              </span>
            </div>
          ))}
        </div>

        {/* Social proof */}
        <div style={{
          background: "var(--surface)", border: "1px solid var(--border)",
          borderRadius: "var(--r-md)", padding: "14px 16px", marginBottom: 16,
          textAlign: "center",
        }}>
          <p style={{ fontSize: 13, color: "var(--text-muted)", margin: 0 }}>
            <span style={{ fontWeight: 900, color: "var(--text)", fontSize: 15 }}>+2.847</span>
            {" "}análisis · Valoración media{" "}
            <span style={{ fontWeight: 700, color: "var(--gold)" }}>4,8★</span>
            {" "}· Barberos en toda España
          </p>
        </div>

        {/* Discount code */}
        <div>
          <label style={{ display: "block", fontSize: 13, color: "var(--text-muted)", marginBottom: 8, fontWeight: 500 }}>
            Código descuento
          </label>
          <input
            value={barberCode}
            onChange={(e) => setBarberCode(e.target.value.toUpperCase())}
            placeholder="VISAI-..."
            style={{
              width: "100%", padding: "14px 16px",
              background: "var(--surface)", outline: "none",
              border: `1.5px solid ${hasCode ? "var(--gold)" : "var(--border)"}`,
              borderRadius: 12, fontSize: 15, letterSpacing: 1,
              transition: "border-color 0.2s",
            }}
          />
          {hasCode && (
            <p style={{ color: "var(--success)", fontSize: 13, marginTop: 6, fontWeight: 600 }}>
              ✓ Código aplicado — precio 10,99 €
            </p>
          )}
        </div>
      </div>

      {/* Bottom CTA */}
      <div style={{ marginTop: 24 }}>
        {!allRequired && (
          <p style={{ color: "var(--text-muted)", fontSize: 13, textAlign: "center", marginBottom: 8 }}>
            {!emailValid
              ? "Introduce tu email para continuar"
              : !phoneValid
                ? "Revisa el formato del móvil"
                : "Acepta los consentimientos para continuar"}
          </p>
        )}
        {error && (
          <p style={{ color: "var(--danger)", fontSize: 14, textAlign: "center", marginBottom: 12 }}>{error}</p>
        )}
        <button type="button" className="btn-primary" onClick={handlePay} disabled={!allRequired}>
          Obtener mi análisis →
        </button>

        {/* Payment method badges */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 6, marginTop: 14 }}>
          <span className="pay-badge pay-badge--visa">VISA</span>
          <span className="pay-badge pay-badge--mc" aria-label="Mastercard">
            <svg width="30" height="18" viewBox="0 0 30 18" aria-hidden="true">
              <circle cx="9"  cy="9" r="9" fill="#EB001B" />
              <circle cx="21" cy="9" r="9" fill="#F79E1B" />
              <path d="M15 2.5a9 9 0 0 1 0 13A9 9 0 0 1 15 2.5z" fill="#FF5F00" />
            </svg>
          </span>
          <span className="pay-badge pay-badge--apple">Apple Pay</span>
          <span className="pay-badge pay-badge--google" aria-label="Google Pay">
            <span className="g-blue">G</span>
            <span className="g-red">o</span>
            <span className="g-yellow">o</span>
            <span className="g-blue">g</span>
            <span className="g-green">l</span>
            <span className="g-red">e</span>
            &nbsp;Pay
          </span>
        </div>

        <p className="caption" style={{ textAlign: "center", marginTop: 8 }}>
          Pago seguro · SSL 256-bit · Si algo falla, te devolvemos el dinero
        </p>
      </div>
    </div>
  );
}
