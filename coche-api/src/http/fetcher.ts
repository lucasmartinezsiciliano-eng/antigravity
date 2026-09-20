/**
 * Fetch educado.
 *
 * Todo lo que sale a internet pasa por aqui, y aqui se cumplen cuatro cosas:
 * identificarse de verdad, respetar robots.txt, no pasarse de ritmo y no pedir
 * dos veces lo mismo. No es cortesia: es lo que separa una metabusqueda de un
 * scraper que acaba baneado en una semana.
 */

import { parseRobots, permitido, type Robots } from "./robots.ts";

export interface FetcherOptions {
  userAgent: string;
  /** Saltarse robots.txt. Solo lo activa quien despliega, y queda en el log. */
  ignoreRobots?: boolean;
  timeoutMs?: number;
  cacheTtlMs?: number;
  log?: (msg: string) => void;
}

export class RobotsBlocked extends Error {
  constructor(url: string) {
    super(`robots.txt no permite ${url}`);
    this.name = "RobotsBlocked";
  }
}

interface Entrada {
  body: string;
  status: number;
  headers: Record<string, string>;
  expira: number;
}

export class Fetcher {
  private robots = new Map<string, Promise<Robots | null>>();
  private ultima = new Map<string, number>();
  private cola = new Map<string, Promise<unknown>>();
  private cache = new Map<string, Entrada>();

  private readonly opts: FetcherOptions;

  constructor(opts: FetcherOptions) {
    this.opts = opts;
  }

  private log(msg: string) {
    this.opts.log?.(msg);
  }

  /** robots.txt de un host, cacheado mientras viva el proceso. */
  private async robotsDe(origin: string): Promise<Robots | null> {
    let p = this.robots.get(origin);
    if (!p) {
      p = (async () => {
        try {
          const res = await fetch(`${origin}/robots.txt`, {
            headers: { "user-agent": this.opts.userAgent },
            signal: AbortSignal.timeout(8000),
          });
          // Sin robots.txt (404) se entiende que todo esta permitido.
          if (res.status === 404) return { rules: [] };
          if (!res.ok) return null;
          return parseRobots(await res.text(), this.opts.userAgent);
        } catch {
          return null; // Si no se puede leer, no inventamos permiso.
        }
      })();
      this.robots.set(origin, p);
    }
    return p;
  }

  /**
   * Espera lo que haga falta para no pasarse del ritmo de ese host.
   * Serializa por host: dos peticiones al mismo sitio no salen a la vez.
   */
  private async ritmo(host: string, porMinuto: number, crawlDelay?: number) {
    const minimo = Math.max(crawlDelay ? crawlDelay * 1000 : 0, 60_000 / Math.max(1, porMinuto));
    const anterior = this.cola.get(host) ?? Promise.resolve();
    const turno = anterior.then(async () => {
      const ultima = this.ultima.get(host) ?? 0;
      const esperar = ultima + minimo - Date.now();
      if (esperar > 0) await new Promise((r) => setTimeout(r, esperar));
      this.ultima.set(host, Date.now());
    });
    this.cola.set(
      host,
      turno.catch(() => {}),
    );
    await turno;
  }

  async get(
    url: string,
    init: RequestInit & { rateLimitPerMin?: number } = {},
  ): Promise<{ body: string; status: number; headers: Record<string, string> }> {
    const u = new URL(url);
    const ahora = Date.now();

    const enCache = this.cache.get(url);
    if (enCache && enCache.expira > ahora) {
      this.log(`cache ${url}`);
      return enCache;
    }

    let crawlDelay: number | undefined;
    if (!this.opts.ignoreRobots) {
      const robots = await this.robotsDe(u.origin);
      if (robots === null) {
        throw new RobotsBlocked(`${u.origin}/robots.txt ilegible: no asumimos permiso`);
      }
      if (!permitido(robots, url)) throw new RobotsBlocked(url);
      crawlDelay = robots.crawlDelay;
    } else {
      this.log(`AVISO: robots.txt ignorado por configuracion en ${u.host}`);
    }

    await this.ritmo(u.host, init.rateLimitPerMin ?? 20, crawlDelay);

    const res = await fetch(url, {
      ...init,
      headers: {
        "user-agent": this.opts.userAgent,
        "accept-language": "es-ES,es;q=0.9,en;q=0.8",
        ...(init.headers ?? {}),
      },
      signal: init.signal ?? AbortSignal.timeout(this.opts.timeoutMs ?? 15_000),
      redirect: "follow",
    });

    const body = await res.text();
    const headers: Record<string, string> = {};
    res.headers.forEach((v, k) => (headers[k] = v));
    const salida = { body, status: res.status, headers };

    if (res.ok) {
      this.cache.set(url, { ...salida, expira: ahora + (this.opts.cacheTtlMs ?? 60_000) });
      // La cache es de alivio, no un indice: se poda sola.
      if (this.cache.size > 500) {
        for (const [k, v] of this.cache) if (v.expira <= ahora) this.cache.delete(k);
      }
    }
    return salida;
  }

  /** Igual que `get` pero devolviendo un Response, para los adaptadores de API. */
  async fetch(url: string, init: RequestInit = {}): Promise<Response> {
    const r = await this.get(url, init);
    return new Response(r.body, { status: r.status, headers: r.headers });
  }
}
