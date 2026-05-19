"use client";

import { useCallback, useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
const ANGLES = ["frontal", "perfil_izquierdo", "perfil_derecho"] as const;
type Angle = (typeof ANGLES)[number];

interface ReferenceEntry {
  id: string;
  haircut_name: string;
  angle: string;
  notes: string;
  filename: string;
  image_url: string;
  face_detected: boolean;
  metrics: Record<string, unknown>;
  added_at: string;
}

interface ListResponse {
  total: number;
  references: ReferenceEntry[];
}

export default function AdminPage() {
  const [adminKey, setAdminKey] = useState<string>("");
  const [pendingKey, setPendingKey] = useState<string>("");
  const [authChecked, setAuthChecked] = useState(false);

  const [references, setReferences] = useState<ReferenceEntry[]>([]);
  const [listLoading, setListLoading] = useState(false);
  const [listError, setListError] = useState<string>("");

  const [file, setFile] = useState<File | null>(null);
  const [haircutName, setHaircutName] = useState("");
  const [angle, setAngle] = useState<Angle>("frontal");
  const [notes, setNotes] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");

  // Load key from sessionStorage on mount
  useEffect(() => {
    const stored = sessionStorage.getItem("adminKey");
    if (stored) setAdminKey(stored);
    setAuthChecked(true);
  }, []);

  const fetchReferences = useCallback(async () => {
    if (!adminKey) return;
    setListLoading(true);
    setListError("");
    try {
      const res = await fetch(`${API_BASE}/admin/referencias/`, {
        headers: { "x-admin-key": adminKey },
      });
      if (res.status === 403) {
        // Bad key — clear it and force re-auth
        sessionStorage.removeItem("adminKey");
        setAdminKey("");
        setListError("Clave inválida.");
        return;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: ListResponse = await res.json();
      setReferences(data.references || []);
    } catch (e) {
      setListError(e instanceof Error ? e.message : "Error cargando referencias.");
    } finally {
      setListLoading(false);
    }
  }, [adminKey]);

  useEffect(() => {
    if (adminKey) fetchReferences();
  }, [adminKey, fetchReferences]);

  function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    const k = pendingKey.trim();
    if (!k) return;
    sessionStorage.setItem("adminKey", k);
    setAdminKey(k);
    setPendingKey("");
  }

  function handleLogout() {
    sessionStorage.removeItem("adminKey");
    setAdminKey("");
    setReferences([]);
  }

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !haircutName.trim()) return;
    setUploading(true);
    setUploadError("");
    try {
      const fd = new FormData();
      fd.append("photo", file);
      fd.append("haircut_name", haircutName.trim());
      fd.append("angle", angle);
      if (notes.trim()) fd.append("notes", notes.trim());

      const res = await fetch(`${API_BASE}/admin/referencias/upload`, {
        method: "POST",
        headers: { "x-admin-key": adminKey },
        body: fd,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || `HTTP ${res.status}`);
      }
      // Reset form
      setFile(null);
      setHaircutName("");
      setNotes("");
      setAngle("frontal");
      (document.getElementById("admin-file-input") as HTMLInputElement | null)?.value &&
        ((document.getElementById("admin-file-input") as HTMLInputElement).value = "");
      await fetchReferences();
    } catch (e) {
      setUploadError(e instanceof Error ? e.message : "Error subiendo la foto.");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(ref: ReferenceEntry) {
    if (!confirm(`¿Eliminar "${ref.haircut_name}" (${ref.angle})?`)) return;
    try {
      const res = await fetch(`${API_BASE}/admin/referencias/${ref.id}`, {
        method: "DELETE",
        headers: { "x-admin-key": adminKey },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await fetchReferences();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Error eliminando.");
    }
  }

  // ── Auth gate ────────────────────────────────────────────────────────────
  if (!authChecked) {
    return null;
  }

  if (!adminKey) {
    return (
      <div className="screen" style={{ alignItems: "center", justifyContent: "center" }}>
        <form
          onSubmit={handleLogin}
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--r-md)",
            padding: 24,
            display: "flex",
            flexDirection: "column",
            gap: 14,
            width: "100%",
            maxWidth: 360,
          }}
        >
          <div style={{ fontWeight: 700, fontSize: 16 }}>VISAI · Admin</div>
          <div style={{ color: "var(--text-muted)", fontSize: 13 }}>
            Clave de administrador
          </div>
          <input
            type="password"
            autoFocus
            value={pendingKey}
            onChange={(e) => setPendingKey(e.target.value)}
            placeholder="x-admin-key"
            style={{
              background: "var(--bg)",
              border: "1px solid var(--border)",
              color: "var(--text)",
              padding: "10px 12px",
              borderRadius: "var(--r-sm)",
              fontSize: 14,
              outline: "none",
            }}
          />
          <button
            type="submit"
            style={{
              background: "var(--accent)",
              color: "#080808",
              border: "none",
              padding: "10px 12px",
              borderRadius: "var(--r-full)",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            Entrar
          </button>
        </form>
      </div>
    );
  }

  // ── Authed view ─────────────────────────────────────────────────────────
  return (
    <div className="screen" style={{ gap: 24, paddingTop: 24, paddingBottom: 48 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontWeight: 800, fontSize: 20 }}>Referencias curadas</div>
          <div style={{ color: "var(--text-muted)", fontSize: 13 }}>
            {references.length} {references.length === 1 ? "referencia" : "referencias"}
          </div>
        </div>
        <button
          onClick={handleLogout}
          style={{
            background: "transparent",
            color: "var(--text-muted)",
            border: "1px solid var(--border)",
            padding: "6px 12px",
            borderRadius: "var(--r-full)",
            fontSize: 12,
            cursor: "pointer",
          }}
        >
          Cerrar sesión
        </button>
      </div>

      {/* ── Upload form ── */}
      <form
        onSubmit={handleUpload}
        style={{
          background: "var(--surface)",
          border: "1px solid var(--border)",
          borderRadius: "var(--r-md)",
          padding: 18,
          display: "flex",
          flexDirection: "column",
          gap: 12,
        }}
      >
        <div style={{ fontWeight: 700, fontSize: 14 }}>Subir nueva referencia</div>

        <input
          id="admin-file-input"
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          required
          style={{ color: "var(--text-muted)", fontSize: 13 }}
        />

        <input
          type="text"
          required
          placeholder="Nombre del corte (ej. Skin Fade)"
          value={haircutName}
          onChange={(e) => setHaircutName(e.target.value)}
          style={{
            background: "var(--bg)",
            border: "1px solid var(--border)",
            color: "var(--text)",
            padding: "10px 12px",
            borderRadius: "var(--r-sm)",
            fontSize: 14,
            outline: "none",
          }}
        />

        <select
          value={angle}
          onChange={(e) => setAngle(e.target.value as Angle)}
          style={{
            background: "var(--bg)",
            border: "1px solid var(--border)",
            color: "var(--text)",
            padding: "10px 12px",
            borderRadius: "var(--r-sm)",
            fontSize: 14,
            outline: "none",
          }}
        >
          {ANGLES.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>

        <textarea
          placeholder="Notas (opcional)"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={2}
          style={{
            background: "var(--bg)",
            border: "1px solid var(--border)",
            color: "var(--text)",
            padding: "10px 12px",
            borderRadius: "var(--r-sm)",
            fontSize: 14,
            outline: "none",
            fontFamily: "inherit",
            resize: "vertical",
          }}
        />

        {uploadError && (
          <div style={{ color: "var(--danger)", fontSize: 13 }}>{uploadError}</div>
        )}

        <button
          type="submit"
          disabled={uploading || !file || !haircutName.trim()}
          style={{
            background: "var(--accent)",
            color: "#080808",
            border: "none",
            padding: "10px 12px",
            borderRadius: "var(--r-full)",
            fontWeight: 700,
            cursor: uploading ? "not-allowed" : "pointer",
            opacity: uploading || !file || !haircutName.trim() ? 0.5 : 1,
          }}
        >
          {uploading ? "Subiendo…" : "Subir referencia"}
        </button>
      </form>

      {/* ── Grid of refs ── */}
      {listError && (
        <div style={{ color: "var(--danger)", fontSize: 13 }}>{listError}</div>
      )}
      {listLoading && references.length === 0 ? (
        <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Cargando…</div>
      ) : references.length === 0 ? (
        <div style={{ color: "var(--text-muted)", fontSize: 13 }}>
          No hay referencias todavía. Sube la primera arriba.
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
            gap: 12,
          }}
        >
          {references.map((ref) => {
            const src = `${API_BASE}/admin/referencias/imagen/${ref.filename}?key=${encodeURIComponent(adminKey)}`;
            return (
              <div
                key={ref.id}
                style={{
                  background: "var(--surface)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--r-md)",
                  overflow: "hidden",
                  display: "flex",
                  flexDirection: "column",
                }}
              >
                <div style={{ aspectRatio: "1 / 1", background: "var(--bg)" }}>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={src}
                    alt={ref.haircut_name}
                    style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }}
                  />
                </div>
                <div style={{ padding: 10, display: "flex", flexDirection: "column", gap: 6 }}>
                  <div style={{ fontWeight: 700, fontSize: 13, lineHeight: 1.2 }}>
                    {ref.haircut_name}
                  </div>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    <span
                      style={{
                        fontSize: 10,
                        padding: "2px 8px",
                        borderRadius: "var(--r-full)",
                        background: "var(--accent-subtle)",
                        border: "1px solid var(--border)",
                        color: "var(--text-muted)",
                      }}
                    >
                      {ref.angle}
                    </span>
                    <span
                      style={{
                        fontSize: 10,
                        padding: "2px 8px",
                        borderRadius: "var(--r-full)",
                        background: ref.face_detected ? "rgba(61,184,130,0.1)" : "rgba(217,79,79,0.1)",
                        border: `1px solid ${ref.face_detected ? "rgba(61,184,130,0.3)" : "rgba(217,79,79,0.3)"}`,
                        color: ref.face_detected ? "var(--success)" : "var(--danger)",
                      }}
                    >
                      {ref.face_detected ? "cara ✓" : "sin cara"}
                    </span>
                  </div>
                  {ref.notes && (
                    <div style={{ fontSize: 11, color: "var(--text-muted)", lineHeight: 1.3 }}>
                      {ref.notes}
                    </div>
                  )}
                  <button
                    onClick={() => handleDelete(ref)}
                    style={{
                      marginTop: 4,
                      background: "transparent",
                      color: "var(--danger)",
                      border: "1px solid var(--border)",
                      padding: "6px 10px",
                      borderRadius: "var(--r-sm)",
                      fontSize: 11,
                      cursor: "pointer",
                    }}
                  >
                    Eliminar
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
