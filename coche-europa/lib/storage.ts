"use client";

/**
 * Los expedientes viven en el navegador: sin cuentas, sin servidor, sin RGPD.
 *
 * Se expone como un store suscribible para que las pantallas se lean con
 * useSyncExternalStore. Asi no hay setState dentro de useEffect, no hay
 * parpadeo de hidratacion y dos pestanas abiertas se mantienen al dia.
 */

import type { Answer, Dossier } from "./types";

const KEY = "coche-europa:dossiers";
const ACTIVE = "coche-europa:active";

const listeners = new Set<() => void>();
let snapshot = "";
let iniciado = false;

function leerCrudo(): string {
  try {
    return `${window.localStorage.getItem(ACTIVE) ?? ""}|${window.localStorage.getItem(KEY) ?? "[]"}`;
  } catch {
    return "|[]";
  }
}

function avisar() {
  snapshot = leerCrudo();
  listeners.forEach((l) => l());
}

/** Para useSyncExternalStore. Devuelve un string: estable entre renders. */
export function subscribe(cb: () => void): () => void {
  if (!iniciado) {
    iniciado = true;
    snapshot = leerCrudo();
    window.addEventListener("storage", avisar);
  }
  listeners.add(cb);
  return () => listeners.delete(cb);
}

export function getSnapshot(): string {
  if (!iniciado) snapshot = leerCrudo();
  return snapshot;
}

/** En el servidor no hay localStorage: se renderiza el estado vacio. */
export function getServerSnapshot(): string {
  return "";
}

/** Del string del snapshot a datos utiles. */
export function parseSnapshot(raw: string): { active: string | null; dossiers: Dossier[] } {
  const corte = raw.indexOf("|");
  if (corte < 0) return { active: null, dossiers: [] };
  const active = raw.slice(0, corte) || null;
  try {
    const dossiers = JSON.parse(raw.slice(corte + 1) || "[]") as Dossier[];
    return {
      active,
      dossiers: dossiers.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt)),
    };
  } catch {
    return { active, dossiers: [] };
  }
}

// --- escritura -------------------------------------------------------------

function read(): Dossier[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as Dossier[]) : [];
  } catch {
    return [];
  }
}

function write(list: Dossier[]) {
  try {
    window.localStorage.setItem(KEY, JSON.stringify(list));
  } catch {
    /* modo incognito o almacenamiento lleno: seguimos sin guardar */
  }
  avisar();
}

export function listDossiers(): Dossier[] {
  return read().sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
}

export function getDossier(id: string): Dossier | undefined {
  return read().find((d) => d.id === id);
}

export function saveDossier(d: Dossier): Dossier {
  const list = read();
  const next = { ...d, updatedAt: new Date().toISOString() };
  const i = list.findIndex((x) => x.id === d.id);
  if (i >= 0) list[i] = next;
  else list.unshift(next);
  write(list);
  return next;
}

export function deleteDossier(id: string) {
  write(read().filter((d) => d.id !== id));
  if (getActiveId() === id) setActiveId(null);
}

export function createDossier(partial: Partial<Dossier> = {}): Dossier {
  const now = new Date().toISOString();
  const d: Dossier = {
    id: `d_${Date.now().toString(36)}${Math.random().toString(36).slice(2, 7)}`,
    name: partial.name || "Coche sin nombre",
    createdAt: now,
    updatedAt: now,
    answers: {},
    notes: {},
    ...partial,
  };
  saveDossier(d);
  setActiveId(d.id);
  return d;
}

export function setAnswer(id: string, itemId: string, answer: Answer): Dossier | undefined {
  const d = getDossier(id);
  if (!d) return;
  return saveDossier({ ...d, answers: { ...d.answers, [itemId]: answer } });
}

export function setNote(id: string, itemId: string, note: string): Dossier | undefined {
  const d = getDossier(id);
  if (!d) return;
  return saveDossier({ ...d, notes: { ...d.notes, [itemId]: note } });
}

export function getActiveId(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(ACTIVE);
  } catch {
    return null;
  }
}

export function setActiveId(id: string | null) {
  try {
    if (id) window.localStorage.setItem(ACTIVE, id);
    else window.localStorage.removeItem(ACTIVE);
  } catch {
    /* noop */
  }
  avisar();
}
