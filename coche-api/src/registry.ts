/**
 * Que proveedores se ejecutan y cuales no.
 *
 * La regla es una sola: un proveedor corre si esta encendido por defecto
 * (enlace profundo, API oficial, datos abiertos) o si quien despliega lo ha
 * encendido a mano con PROVIDERS_ENABLED. Los de lectura de HTML nunca se
 * encienden solos.
 */

import { deeplinkProviders } from "./providers/deeplink.ts";
import { ebay } from "./providers/ebay.ts";
import { htmlProviders } from "./providers/html/descriptors.ts";
import type { Provider } from "./providers/types.ts";
import type { Country, Query } from "./schema.ts";

export const ALL: Provider[] = [...deeplinkProviders, ebay, ...htmlProviders];

export function byId(id: string): Provider | undefined {
  return ALL.find((p) => p.meta.id === id);
}

function listaDe(env: Record<string, string | undefined>, clave: string): string[] {
  return (env[clave] ?? "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

/** Los que estan activos con esta configuracion. */
export function enabled(env: Record<string, string | undefined> = process.env): Provider[] {
  const encendidos = new Set(listaDe(env, "PROVIDERS_ENABLED"));
  const apagados = new Set(listaDe(env, "PROVIDERS_DISABLED"));

  return ALL.filter((p) => {
    if (apagados.has(p.meta.id)) return false;
    if (encendidos.has(p.meta.id)) return true;
    if (encendidos.has("all")) return true;
    return p.meta.enabledByDefault;
  });
}

/** Los que tocan alguno de los paises pedidos. Los espanoles entran siempre:
 *  sirven para saber si de verdad compensa importar. */
export function forQuery(q: Query, env?: Record<string, string | undefined>): Provider[] {
  const paises = q.countries;
  if (!paises?.length) return enabled(env);

  return enabled(env).filter(
    (p) => p.meta.countries.some((c) => paises.includes(c)) || p.meta.countries.includes("ES" as Country),
  );
}
