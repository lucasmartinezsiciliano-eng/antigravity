"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { LogIn, KeyRound, AlertCircle, Eye, EyeOff } from "lucide-react";
import { api } from "@/lib/api";
import { setBarberSession } from "@/lib/barber-auth";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") || "/barber/dashboard";

  const [mode, setMode] = useState<"login" | "set-password">("login");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPw, setShowPw] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.barberLogin(code.trim(), password);
      setBarberSession(res.token, res.barber_id, res.promo_code);
      router.push(next);
    } catch (err: any) {
      setError(err.message || "Error al iniciar sesión.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSetPassword(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (password.length < 6) {
      setError("La contraseña debe tener al menos 6 caracteres.");
      return;
    }
    setLoading(true);
    try {
      const res = await api.barberSetPassword(email.trim(), code.trim(), password);
      setBarberSession(res.token, res.barber_id, code.trim().toUpperCase());
      router.push(next);
    } catch (err: any) {
      setError(err.message || "Error al crear contraseña.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        background: "var(--bg)",
        minHeight: "100dvh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "var(--screen-pad)",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 400,
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--r-md)",
          padding: 32,
        }}
      >
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <h1
            style={{
              fontFamily: "var(--font-logo), serif",
              fontSize: 40,
              fontWeight: 400,
              letterSpacing: "-0.01em",
              color: "var(--text)",
              lineHeight: 1,
              margin: 0,
            }}
          >
            VISAI
          </h1>
          <p style={{
            fontSize: 10,
            color: "var(--text-dim)",
            marginTop: 10,
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            fontWeight: 600,
          }}>
            Portal Barberos
          </p>
        </div>

        {/* Tabs */}
        <div
          style={{
            display: "flex",
            gap: 0,
            marginBottom: 24,
            borderRadius: "var(--r-sm)",
            overflow: "hidden",
            border: "1px solid var(--border)",
          }}
        >
          {(["login", "set-password"] as const).map((m) => (
            <button
              key={m}
              onClick={() => {
                setMode(m);
                setError("");
              }}
              style={{
                flex: 1,
                padding: "10px 0",
                fontSize: 13,
                fontWeight: 600,
                background: mode === m ? "var(--surface2)" : "transparent",
                color: mode === m ? "var(--text)" : "var(--text-dim)",
                border: "none",
                cursor: "pointer",
                transition: "background-color 180ms var(--ease-out), color 180ms var(--ease-out)",
              }}
            >
              {m === "login" ? "Iniciar sesión" : "Crear contraseña"}
            </button>
          ))}
        </div>

        {error && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "10px 12px",
              background: "rgba(217,79,79,0.1)",
              border: "1px solid rgba(217,79,79,0.2)",
              borderRadius: "var(--r-sm)",
              marginBottom: 16,
              fontSize: 13,
              color: "var(--danger)",
            }}
          >
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        {mode === "login" ? (
          <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <label style={labelStyle}>
              <span style={labelTextStyle}>Código promocional</span>
              <div style={inputWrapStyle}>
                <KeyRound size={16} style={{ color: "var(--text-dim)" }} />
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value.toUpperCase())}
                  placeholder="TUCODIGO"
                  required
                  autoComplete="username"
                  style={inputStyle}
                />
              </div>
            </label>
            <label style={labelStyle}>
              <span style={labelTextStyle}>Contraseña</span>
              <div style={inputWrapStyle}>
                <input
                  type={showPw ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••"
                  required
                  autoComplete="current-password"
                  style={inputStyle}
                />
                <button
                  type="button"
                  onPointerDown={() => setShowPw(true)}
                  onPointerUp={() => setShowPw(false)}
                  onPointerLeave={() => setShowPw(false)}
                  style={eyeBtnStyle}
                  tabIndex={-1}
                >
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </label>
            <button type="submit" disabled={loading} style={btnStyle}>
              {loading ? "Entrando..." : (
                <>
                  <LogIn size={16} />
                  Entrar
                </>
              )}
            </button>
          </form>
        ) : (
          <form onSubmit={handleSetPassword} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <p style={{ fontSize: 12, color: "var(--text-muted)", margin: 0 }}>
              Si ya eres barbero VISAI pero aún no tienes contraseña, créala aquí.
            </p>
            <label style={labelStyle}>
              <span style={labelTextStyle}>Email de registro</span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="tu@email.com"
                required
                autoComplete="email"
                style={{ ...inputStyle, padding: "11px 14px" }}
              />
            </label>
            <label style={labelStyle}>
              <span style={labelTextStyle}>Código promocional</span>
              <div style={inputWrapStyle}>
                <KeyRound size={16} style={{ color: "var(--text-dim)" }} />
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value.toUpperCase())}
                  placeholder="TUCODIGO"
                  required
                  style={inputStyle}
                />
              </div>
            </label>
            <label style={labelStyle}>
              <span style={labelTextStyle}>Nueva contraseña</span>
              <div style={inputWrapStyle}>
                <input
                  type={showPw ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Mínimo 6 caracteres"
                  required
                  minLength={6}
                  autoComplete="new-password"
                  style={inputStyle}
                />
                <button
                  type="button"
                  onPointerDown={() => setShowPw(true)}
                  onPointerUp={() => setShowPw(false)}
                  onPointerLeave={() => setShowPw(false)}
                  style={eyeBtnStyle}
                  tabIndex={-1}
                >
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </label>
            <button type="submit" disabled={loading} style={btnStyle}>
              {loading ? "Creando..." : "Crear contraseña y entrar"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

const labelStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 6,
};

const labelTextStyle: React.CSSProperties = {
  fontSize: 12,
  fontWeight: 600,
  color: "var(--text-muted)",
  textTransform: "uppercase",
  letterSpacing: "0.04em",
};

const inputWrapStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 10,
  background: "var(--surface2)",
  border: "1px solid var(--border)",
  borderRadius: "var(--r-sm)",
  padding: "0 14px",
};

const inputStyle: React.CSSProperties = {
  flex: 1,
  padding: "11px 0",
  fontSize: 15,
  color: "var(--text)",
  background: "transparent",
  border: "none",
  outline: "none",
  fontFamily: "inherit",
};

const eyeBtnStyle: React.CSSProperties = {
  background: "none",
  border: "none",
  cursor: "pointer",
  color: "var(--text-dim)",
  padding: 4,
  display: "flex",
  alignItems: "center",
  flexShrink: 0,
};

const btnStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  gap: 8,
  padding: "13px 0",
  fontSize: 14,
  fontWeight: 700,
  color: "#050505",
  background: "var(--text)",
  border: "none",
  borderRadius: "var(--r-sm)",
  cursor: "pointer",
  marginTop: 4,
  letterSpacing: "-0.01em",
};

export default function BarberLoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
