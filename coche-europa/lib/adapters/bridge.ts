/**
 * Puente hacia tu propio buscador.
 *
 * Los portales grandes no tienen API publica, asi que la app deja un hueco:
 * si defines BRIDGE_URL, cada busqueda se le reenvia y lo que devuelva entra
 * en la lista unificada junto al resto. Ahi es donde encaja un flujo de n8n
 * (ver n8n/coche-europa-bridge.json) o cualquier servicio tuyo.
 *
 * Contrato:
 *   POST {BRIDGE_URL}
 *   Authorization: Bearer {BRIDGE_TOKEN}
 *   body: { filters: SearchFilters, portals: string[] }
 *   200:  { listings: Listing[] }  |  { results: [{ portal, listings }] }
 */

import type { Listing, PortalResult, SearchFilters } from "../types";

const TIMEOUT_MS = 12_000;

export function bridgeEnabled(): boolean {
  return Boolean(process.env.BRIDGE_URL);
}

export async function fetchBridge(
  filters: SearchFilters,
  portals: string[],
): Promise<PortalResult[]> {
  const url = process.env.BRIDGE_URL;
  if (!url) return [];

  const started = Date.now();
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);

  try {
    const res = await fetch(url, {
      method: "POST",
      signal: ctrl.signal,
      headers: {
        "content-type": "application/json",
        ...(process.env.BRIDGE_TOKEN
          ? { authorization: `Bearer ${process.env.BRIDGE_TOKEN}` }
          : {}),
      },
      body: JSON.stringify({ filters, portals }),
      cache: "no-store",
    });

    if (!res.ok) {
      return [errorResult(`El puente respondio ${res.status}`, Date.now() - started)];
    }

    const data = (await res.json()) as {
      listings?: Listing[];
      results?: { portal: string; name?: string; listings: Listing[] }[];
    };

    if (Array.isArray(data.results)) {
      return data.results.map((r) => ({
        portal: r.portal,
        name: r.name ?? r.portal,
        countries: [],
        searchUrl: "",
        mode: "live" as const,
        listings: (r.listings ?? []).map((l) => normalize(l, r.portal)),
        ms: Date.now() - started,
      }));
    }

    return [
      {
        portal: "bridge",
        name: "Puente propio",
        countries: [],
        searchUrl: "",
        mode: "live",
        listings: (data.listings ?? []).map((l) => normalize(l, "bridge")),
        ms: Date.now() - started,
      },
    ];
  } catch (e) {
    const msg = e instanceof Error && e.name === "AbortError" ? "tardo demasiado" : "no respondio";
    return [errorResult(`El puente ${msg}`, Date.now() - started)];
  } finally {
    clearTimeout(timer);
  }
}

function errorResult(note: string, ms: number): PortalResult {
  return {
    portal: "bridge",
    name: "Puente propio",
    countries: [],
    searchUrl: "",
    mode: "error",
    listings: [],
    note,
    ms,
  };
}

/** Nos fiamos poco de lo que llega de fuera: todo pasa por aqui. */
function normalize(l: Partial<Listing>, source: string): Listing {
  return {
    id: String(l.id ?? `${source}_${Math.random().toString(36).slice(2)}`),
    source,
    sourceName: l.sourceName ?? source,
    title: String(l.title ?? "Sin titulo"),
    price: Number(l.price) || 0,
    year: num(l.year),
    km: num(l.km),
    power: num(l.power),
    co2: num(l.co2),
    fuel: l.fuel,
    gearbox: l.gearbox,
    country: l.country ?? "DE",
    city: l.city,
    seller: l.seller,
    url: String(l.url ?? ""),
    image: l.image,
    make: l.make,
    model: l.model,
  };
}

function num(v: unknown): number | undefined {
  const n = Number(v);
  return Number.isFinite(n) && n > 0 ? n : undefined;
}
