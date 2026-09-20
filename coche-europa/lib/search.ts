/**
 * Orquestador del buscador multiportal.
 *
 * Lanza a la vez todas las fuentes en vivo que haya configuradas, construye el
 * enlace de busqueda de cada portal con los filtros puestos, junta todo en una
 * sola lista, quita duplicados y la ordena por lo que de verdad importa: lo que
 * te va a costar el coche ya matriculado en Espana.
 */

import { fetchBridge, bridgeEnabled } from "./adapters/bridge";
import { fetchEbay, ebayEnabled } from "./adapters/ebay";
import { demoListings } from "./adapters/demo";
import { costeAproximado } from "./import-cost";
import { portalsFor } from "./portals";
import type { Listing, PortalResult, SearchFilters, SearchResponse } from "./types";

export const DEFAULT_FILTERS: SearchFilters = {
  make: "",
  model: "",
  countries: ["DE", "FR"],
  sort: "coste-total",
};

export function hasLiveSources(): boolean {
  return bridgeEnabled() || ebayEnabled();
}

export async function runSearch(filters: SearchFilters): Promise<SearchResponse> {
  const portales = portalsFor(filters.countries);

  // 1. Enlaces profundos: esto funciona siempre, sin claves ni permisos.
  const linkResults: PortalResult[] = portales.map((p) => ({
    portal: p.id,
    name: p.name,
    countries: p.countries,
    searchUrl: p.buildUrl(filters),
    mode: "link",
    listings: [],
    note: p.hint,
  }));

  // 2. Fuentes en vivo, todas en paralelo y cada una con su propio limite.
  const live: PortalResult[] = [];
  const tareas: Promise<PortalResult[] | PortalResult | null>[] = [];
  if (bridgeEnabled()) tareas.push(fetchBridge(filters, portales.map((p) => p.id)));
  if (ebayEnabled()) tareas.push(fetchEbay(filters));

  const settled = await Promise.allSettled(tareas);
  for (const r of settled) {
    if (r.status !== "fulfilled" || !r.value) continue;
    live.push(...(Array.isArray(r.value) ? r.value : [r.value]));
  }

  // 3. Sin nada en vivo, ensenamos ejemplos para que la pantalla no este vacia.
  const demo: PortalResult[] = [];
  if (!live.some((r) => r.listings.length > 0)) {
    const listings = demoListings(filters);
    if (listings.length) {
      demo.push({
        portal: "demo",
        name: "Fichas de ejemplo",
        countries: filters.countries,
        searchUrl: "",
        mode: "demo",
        listings,
        note: "No son coches reales. Configura BRIDGE_URL o las claves de eBay para ver anuncios de verdad.",
      });
    }
  }

  // 4. Una sola lista: deduplicada, con coste estimado y ordenada.
  const vistos = new Set<string>();
  const listings: Listing[] = [];
  for (const r of [...live, ...demo]) {
    for (const l of r.listings) {
      const huella = fingerprint(l);
      if (vistos.has(huella)) continue;
      vistos.add(huella);
      listings.push({
        ...l,
        landedCost: costeAproximado(l.price, l.country, l.co2),
      });
    }
  }

  ordenar(listings, filters.sort);

  const merged = mergeLinks(linkResults, live, demo);

  return {
    filters,
    listings,
    portals: merged,
    stats: {
      live: merged.filter((p) => p.mode === "live").length,
      link: merged.filter((p) => p.mode === "link").length,
      demo: merged.filter((p) => p.mode === "demo").length,
      error: merged.filter((p) => p.mode === "error").length,
      total: merged.length,
    },
  };
}

/** Un mismo coche publicado en dos portales no debe aparecer dos veces. */
function fingerprint(l: Listing): string {
  if (l.url) {
    const limpio = l.url.split("?")[0].toLowerCase();
    return `u:${limpio}`;
  }
  return [
    l.make?.toLowerCase(),
    l.model?.toLowerCase(),
    l.year,
    l.km ? Math.round(l.km / 5000) : "",
    Math.round(l.price / 250),
  ].join("|");
}

function ordenar(listings: Listing[], sort: SearchFilters["sort"]) {
  const cmp: Record<SearchFilters["sort"], (a: Listing, b: Listing) => number> = {
    "coste-total": (a, b) => (a.landedCost ?? a.price) - (b.landedCost ?? b.price),
    precio: (a, b) => a.price - b.price,
    km: (a, b) => (a.km ?? Infinity) - (b.km ?? Infinity),
    antiguedad: (a, b) => (b.year ?? 0) - (a.year ?? 0),
  };
  listings.sort(cmp[sort] ?? cmp["coste-total"]);
}

/** Si un portal ha respondido en vivo, su tarjeta lo refleja. */
function mergeLinks(
  links: PortalResult[],
  live: PortalResult[],
  demo: PortalResult[],
): PortalResult[] {
  const out = links.map((l) => {
    const encontrado = live.find((v) => v.portal === l.portal);
    if (!encontrado) return l;
    return {
      ...l,
      mode: encontrado.mode,
      listings: encontrado.listings,
      ms: encontrado.ms,
      note: encontrado.note ?? l.note,
    };
  });

  const extra = live.filter((v) => !links.some((l) => l.portal === v.portal));
  return [...out, ...extra, ...demo];
}
