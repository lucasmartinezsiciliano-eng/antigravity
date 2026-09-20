/**
 * El contrato de un proveedor.
 *
 * Cada proveedor declara de donde saca los datos y bajo que regimen. Eso no es
 * documentacion: el motor lo usa para decidir que se ejecuta y que no. Un
 * proveedor `html` no corre a menos que quien despliega lo encienda a mano.
 */

import type { Country, Listing, ProviderResult, Query } from "../schema.ts";

/**
 * De donde vienen los datos. Ordenado de mas a menos defendible:
 *
 *  - `official-api`: API publica del portal, con credenciales propias. Sin duda.
 *  - `open-data`:    datos abiertos de un organismo publico (RDW, AEMA). Sin duda.
 *  - `feed`:         feed que el vendedor publica para ser distribuido.
 *  - `deeplink`:     no se descarga nada, solo se construye la URL de busqueda.
 *                    Es lo que hace un navegador. Sin duda.
 *  - `html`:         lectura del HTML publico bajo demanda del usuario.
 *                    La jurisprudencia europea ampara la metabusqueda bajo
 *                    demanda (BGH I ZR 159/10; TJUE C-762/19), pero las
 *                    condiciones de uso del portal son un contrato aparte que
 *                    ninguna sentencia anula. Por eso va apagado por defecto.
 */
export type Compliance = "official-api" | "open-data" | "feed" | "deeplink" | "html";

export interface ProviderMeta {
  id: string;
  name: string;
  countries: Country[];
  compliance: Compliance;
  /** Solo los que no dependen de decisiones de quien despliega. */
  enabledByDefault: boolean;
  /** Variables de entorno sin las cuales no puede funcionar. */
  requiresEnv?: string[];
  /** Dominio para robots.txt y para el limitador de ritmo. */
  host?: string;
  /** Peticiones por minuto que se considera educado hacerle. */
  rateLimitPerMin?: number;
  docs?: string;
  notes?: string;
}

export interface ProviderContext {
  /** Fetch educado: respeta robots.txt, limita el ritmo y cachea. */
  fetch: (url: string, init?: RequestInit) => Promise<Response>;
  signal: AbortSignal;
  env: Record<string, string | undefined>;
  log: (msg: string) => void;
}

export interface Provider {
  meta: ProviderMeta;
  /** La busqueda equivalente en la web, para abrir en el navegador. */
  searchUrl(q: Query): string | undefined;
  /**
   * Devuelve anuncios. Si no puede, LANZA o devuelve `status`.
   * Nunca debe tardar mas que el `signal` que recibe.
   */
  search?(q: Query, ctx: ProviderContext): Promise<Listing[] | ProviderPartial>;
}

export interface ProviderPartial {
  listings: Listing[];
  status?: ProviderResult["status"];
  message?: string;
}

export function isPartial(v: Listing[] | ProviderPartial): v is ProviderPartial {
  return !Array.isArray(v);
}

/** Error que un proveedor lanza cuando sabe por que ha fallado. */
export class ProviderError extends Error {
  readonly status: ProviderResult["status"];

  constructor(message: string, status: ProviderResult["status"] = "error") {
    super(message);
    this.name = "ProviderError";
    this.status = status;
  }
}
