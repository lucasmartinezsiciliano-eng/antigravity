/**
 * El servidor HTTP. Sin framework: node:http basta y no arrastra dependencias.
 *
 * Rutas:
 *   GET  /health              estado y proveedores activos
 *   GET  /providers           catalogo completo con su regimen legal
 *   GET  /search?make=BMW...  busqueda (tambien POST con JSON)
 *   POST /bridge              mismo contrato que espera coche-europa
 */

import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { search } from "./engine.ts";
import { Fetcher } from "./http/fetcher.ts";
import { ALL, enabled, forQuery } from "./registry.ts";
import { parseQuery, SCHEMA_VERSION, type Listing } from "./schema.ts";

export interface ServerConfig {
  port: number;
  userAgent: string;
  ignoreRobots: boolean;
  providerTimeoutMs: number;
  corsOrigin: string;
  bridgeToken?: string;
  verbose: boolean;
}

export function configFromEnv(env = process.env): ServerConfig {
  return {
    port: Number(env.PORT ?? 8080),
    // Identificarse de verdad es parte del trato. Pon aqui un contacto real.
    userAgent:
      env.USER_AGENT ??
      "coche-api/0.1 (metabusqueda bajo demanda; +https://github.com/antigravity/coche-api)",
    ignoreRobots: env.IGNORE_ROBOTS === "true",
    providerTimeoutMs: Number(env.PROVIDER_TIMEOUT_MS ?? 12_000),
    corsOrigin: env.CORS_ORIGIN ?? "*",
    bridgeToken: env.BRIDGE_TOKEN,
    verbose: env.VERBOSE === "true",
  };
}

export function createApp(cfg: ServerConfig) {
  const log = cfg.verbose ? (m: string) => console.log(`  ${m}`) : () => {};
  const fetcher = new Fetcher({
    userAgent: cfg.userAgent,
    ignoreRobots: cfg.ignoreRobots,
    log,
  });

  if (cfg.ignoreRobots) {
    console.warn("AVISO: IGNORE_ROBOTS=true. Se ignorara robots.txt. Es tu decision y tu responsabilidad.");
  }

  async function buscar(input: unknown) {
    const { query, warnings } = parseQuery(input);
    const providers = forQuery(query);
    return search(providers, query, warnings, {
      fetcher,
      providerTimeoutMs: cfg.providerTimeoutMs,
      log,
    });
  }

  return async function handle(req: IncomingMessage, res: ServerResponse) {
    const url = new URL(req.url ?? "/", `http://${req.headers.host ?? "localhost"}`);
    const send = (code: number, body: unknown) => {
      const json = JSON.stringify(body, null, 2);
      res.writeHead(code, {
        "content-type": "application/json; charset=utf-8",
        "access-control-allow-origin": cfg.corsOrigin,
        "access-control-allow-headers": "content-type, authorization",
        "access-control-allow-methods": "GET, POST, OPTIONS",
        "cache-control": "no-store",
      });
      res.end(json);
    };

    if (req.method === "OPTIONS") return send(204, null);

    try {
      if (url.pathname === "/health") {
        const activos = enabled();
        return send(200, {
          ok: true,
          schemaVersion: SCHEMA_VERSION,
          providersEnabled: activos.length,
          providersTotal: ALL.length,
          robots: cfg.ignoreRobots ? "ignorado" : "respetado",
        });
      }

      if (url.pathname === "/providers") {
        const activos = new Set(enabled().map((p) => p.meta.id));
        return send(200, {
          schemaVersion: SCHEMA_VERSION,
          providers: ALL.map((p) => ({
            ...p.meta,
            enabled: activos.has(p.meta.id),
            canSearch: Boolean(p.search),
          })),
        });
      }

      if (url.pathname === "/search") {
        const input =
          req.method === "POST" ? await leerJson(req) : Object.fromEntries(url.searchParams);
        return send(200, await buscar(input));
      }

      // Contrato de coche-europa: { filters, portals } -> { listings }
      if (url.pathname === "/bridge" && req.method === "POST") {
        if (cfg.bridgeToken) {
          const auth = req.headers.authorization ?? "";
          if (auth !== `Bearer ${cfg.bridgeToken}`) return send(401, { error: "token invalido" });
        }
        const body = (await leerJson(req)) as { filters?: unknown };
        const r = await buscar(traducirFiltros(body.filters));
        return send(200, {
          listings: r.listings.map(aBridge),
          providers: r.providers,
        });
      }

      if (url.pathname === "/") {
        return send(200, {
          name: "coche-api",
          schemaVersion: SCHEMA_VERSION,
          descripcion: "Metabusqueda de coches usados en Europa. Bajo demanda, sin indice propio.",
          rutas: ["/health", "/providers", "/search?make=BMW&model=Serie+3&priceTo=20000", "POST /bridge"],
        });
      }

      return send(404, { error: "no existe" });
    } catch (e) {
      console.error(e);
      return send(500, { error: e instanceof Error ? e.message : "error interno" });
    }
  };
}

async function leerJson(req: IncomingMessage): Promise<unknown> {
  const trozos: Buffer[] = [];
  let bytes = 0;
  for await (const t of req) {
    bytes += (t as Buffer).length;
    if (bytes > 256 * 1024) throw new Error("cuerpo demasiado grande");
    trozos.push(t as Buffer);
  }
  if (!trozos.length) return {};
  try {
    return JSON.parse(Buffer.concat(trozos).toString("utf8"));
  } catch {
    return {};
  }
}

/** coche-europa usa `SearchFilters`; aqui la consulta se llama `Query`. */
function traducirFiltros(f: unknown): unknown {
  const raw = (f ?? {}) as Record<string, unknown>;
  return {
    ...raw,
    fuel: raw.fuel ? [raw.fuel] : undefined,
    gearbox: raw.gearbox ? [raw.gearbox] : undefined,
  };
}

/** Del esquema de aqui al que espera coche-europa. */
function aBridge(l: Listing) {
  return {
    id: l.id,
    sourceName: l.providerName,
    title: l.title,
    price: l.price ?? 0,
    year: l.year,
    km: l.km,
    co2: l.co2,
    power: l.power,
    fuel: l.fuel,
    gearbox: l.gearbox,
    country: l.country,
    city: l.city,
    seller: l.seller,
    url: l.url,
    image: l.images?.[0],
  };
}

export function start(cfg = configFromEnv()) {
  const server = createServer(createApp(cfg));
  server.listen(cfg.port, () => {
    const activos = enabled();
    console.log(`coche-api escuchando en http://localhost:${cfg.port}`);
    console.log(`  ${activos.length} de ${ALL.length} proveedores activos:`);
    for (const p of activos) console.log(`    ${p.meta.id.padEnd(22)} ${p.meta.compliance}`);
    const apagados = ALL.filter((p) => !activos.includes(p));
    if (apagados.length) {
      console.log(`  apagados: ${apagados.map((p) => p.meta.id).join(", ")}`);
      console.log(`  (se encienden con PROVIDERS_ENABLED=id1,id2)`);
    }
  });
  return server;
}
