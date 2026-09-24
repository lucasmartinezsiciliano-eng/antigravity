/**
 * El esquema normalizado.
 *
 * Esta es la parte que de verdad importa del proyecto: un mismo coche se
 * describe de once maneras distintas segun el portal que lo publique. Aqui se
 * define UNA, y cada adaptador traduce a ella. Si el vocabulario esta bien
 * elegido, escribir un adaptador nuevo son veinte lineas.
 *
 * Reglas del esquema:
 *  - Unidades del SI y euros. La conversion la hace el adaptador, no el cliente.
 *  - Todo campo que no se conoce es `undefined`, nunca 0 ni "".
 *  - Un campo presente es un dato observado, no una suposicion. Lo que se
 *    deduce va en `derived` y dice de donde sale.
 */

export const SCHEMA_VERSION = "1.0";

// --- Vocabulario controlado ------------------------------------------------

export const FUELS = [
  "gasolina", "diesel", "hibrido", "phev", "electrico", "glp", "gnc", "hidrogeno", "otro",
] as const;
export type Fuel = (typeof FUELS)[number];

export const GEARBOXES = ["manual", "automatico"] as const;
export type Gearbox = (typeof GEARBOXES)[number];

export const SELLERS = ["particular", "profesional"] as const;
export type SellerType = (typeof SELLERS)[number];

export const BODIES = [
  "utilitario", "compacto", "berlina", "familiar", "suv", "monovolumen",
  "coupe", "descapotable", "pickup", "furgoneta",
] as const;
export type Body = (typeof BODIES)[number];

/** ISO 3166-1 alpha-2 de los mercados cubiertos. */
export const COUNTRIES = [
  "DE", "FR", "IT", "NL", "BE", "AT", "PT", "PL", "LU", "ES", "CZ", "SE", "DK",
] as const;
export type Country = (typeof COUNTRIES)[number];

// --- Consulta --------------------------------------------------------------

export interface Query {
  make?: string;
  model?: string;
  /** Texto libre, para portales que no tienen taxonomia de marca/modelo. */
  q?: string;
  yearFrom?: number;
  yearTo?: number;
  priceFrom?: number;
  priceTo?: number;
  kmFrom?: number;
  kmTo?: number;
  /** Potencia en CV (no kW: la conversion es del adaptador). */
  powerFrom?: number;
  powerTo?: number;
  co2To?: number;
  fuel?: Fuel[];
  gearbox?: Gearbox[];
  body?: Body[];
  seller?: SellerType;
  countries?: Country[];
  /** Cuantos resultados como mucho POR proveedor. */
  limit?: number;
  sort?: "precio" | "km" | "antiguedad" | "relevancia";
}

// --- Resultado -------------------------------------------------------------

export interface Listing {
  /** `{provider}:{idEnElPortal}`. Estable entre consultas. */
  id: string;
  provider: string;
  providerName: string;
  url: string;
  title: string;

  make?: string;
  model?: string;
  variant?: string;

  /** Siempre en euros. Si el portal publica en otra moneda, el adaptador convierte. */
  price?: number;
  priceCurrencyOriginal?: string;
  priceOriginal?: number;
  vatDeductible?: boolean;

  year?: number;
  /** Primera matriculacion en ISO yyyy-mm, si el portal la da con mes. */
  firstRegistration?: string;
  km?: number;
  /** CV. */
  power?: number;
  powerKw?: number;
  /** g/km. El adaptador debe decir en `co2Cycle` si es NEDC o WLTP. */
  co2?: number;
  co2Cycle?: "nedc" | "wltp" | "desconocido";
  fuel?: Fuel;
  gearbox?: Gearbox;
  body?: Body;
  doors?: number;
  seats?: number;
  color?: string;

  country?: Country;
  city?: string;
  postalCode?: string;

  seller?: SellerType;
  sellerName?: string;

  images?: string[];
  vin?: string;

  /** Cuando lo vio el proveedor. ISO. */
  seenAt: string;

  /** Lo que NO viene del portal: calculado o inferido, y de donde sale. */
  derived?: Record<string, { value: unknown; source: string; confidence: "alta" | "media" | "baja" }>;

  /** Campos del portal que no encajan en el esquema. Sin normalizar. */
  raw?: Record<string, unknown>;
}

// --- Respuesta -------------------------------------------------------------

export type ProviderStatus =
  | "ok"
  | "vacio"
  | "solo-enlace"
  | "sin-credenciales"
  | "bloqueado-robots"
  | "limite-alcanzado"
  | "timeout"
  | "error";

export interface ProviderResult {
  provider: string;
  name: string;
  status: ProviderStatus;
  /** Cuantos devolvio ANTES de deduplicar. */
  count: number;
  ms: number;
  /** Busqueda equivalente en la web del portal, para abrir en el navegador. */
  searchUrl?: string;
  message?: string;
}

export interface SearchResponse {
  schemaVersion: string;
  query: Query;
  listings: Listing[];
  providers: ProviderResult[];
  /** Cuantos se fusionaron por ser el mismo coche en varios portales. */
  deduped: number;
  ms: number;
  warnings: string[];
}

// --- Validacion ------------------------------------------------------------

const num = (v: unknown, min: number, max: number): number | undefined => {
  const n = typeof v === "string" ? Number(v) : v;
  if (typeof n !== "number" || !Number.isFinite(n)) return undefined;
  const r = Math.round(n);
  return r >= min && r <= max ? r : undefined;
};

const str = (v: unknown, max = 80): string | undefined => {
  if (typeof v !== "string") return undefined;
  const s = v.trim().slice(0, max);
  return s || undefined;
};

function enumList<T extends string>(v: unknown, allowed: readonly T[]): T[] | undefined {
  const arr = Array.isArray(v) ? v : typeof v === "string" ? v.split(",") : [];
  const out = arr.map((x) => String(x).trim()).filter((x): x is T => (allowed as readonly string[]).includes(x));
  return out.length ? [...new Set(out)] : undefined;
}

/**
 * Convierte lo que llegue en una Query valida.
 * Nunca lanza: lo que no se entiende se ignora y se avisa.
 */
export function parseQuery(input: unknown): { query: Query; warnings: string[] } {
  const raw = (input ?? {}) as Record<string, unknown>;
  const warnings: string[] = [];
  const anoMax = new Date().getFullYear() + 2;

  const query: Query = {
    make: str(raw.make, 40),
    model: str(raw.model, 40),
    q: str(raw.q, 120),
    yearFrom: num(raw.yearFrom, 1900, anoMax),
    yearTo: num(raw.yearTo, 1900, anoMax),
    priceFrom: num(raw.priceFrom, 0, 10_000_000),
    priceTo: num(raw.priceTo, 0, 10_000_000),
    kmFrom: num(raw.kmFrom, 0, 2_000_000),
    kmTo: num(raw.kmTo, 0, 2_000_000),
    powerFrom: num(raw.powerFrom, 0, 2000),
    powerTo: num(raw.powerTo, 0, 2000),
    co2To: num(raw.co2To, 0, 600),
    fuel: enumList(raw.fuel, FUELS),
    gearbox: enumList(raw.gearbox, GEARBOXES),
    body: enumList(raw.body, BODIES),
    seller: enumList(raw.seller, SELLERS)?.[0],
    countries: enumList(raw.countries, COUNTRIES),
    limit: num(raw.limit, 1, 200) ?? 50,
    sort: (["precio", "km", "antiguedad", "relevancia"] as const).includes(raw.sort as never)
      ? (raw.sort as Query["sort"])
      : "precio",
  };

  // Rangos del reves: los damos la vuelta en vez de devolver cero resultados.
  for (const [a, b] of [
    ["yearFrom", "yearTo"], ["priceFrom", "priceTo"], ["kmFrom", "kmTo"], ["powerFrom", "powerTo"],
  ] as const) {
    const lo = query[a];
    const hi = query[b];
    if (lo !== undefined && hi !== undefined && lo > hi) {
      (query[a] as number) = hi;
      (query[b] as number) = lo;
      warnings.push(`${a} era mayor que ${b}: se han intercambiado.`);
    }
  }

  if (!query.make && !query.model && !query.q) {
    warnings.push("Busqueda sin marca, modelo ni texto: algunos portales devolveran su catalogo entero.");
  }

  return { query, warnings };
}

/** Un listing puede publicarse sin precio (subastas, "a consultar"). */
export function isUsable(l: Partial<Listing>): l is Listing {
  return Boolean(l.id && l.provider && l.url && l.title && l.seenAt);
}
