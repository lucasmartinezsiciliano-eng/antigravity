/** Tipos compartidos entre buscador, calculadora de costes y revision guiada. */

export type CountryCode =
  | "DE" | "FR" | "IT" | "NL" | "BE" | "AT" | "PT" | "PL" | "LU" | "ES";

export type Fuel =
  | "gasolina" | "diesel" | "hibrido" | "phev" | "electrico" | "glp" | "gnc";

export type Gearbox = "manual" | "automatico";
export type SellerType = "particular" | "profesional";

/** Region fiscal: los tipos del impuesto de matriculacion cambian por territorio. */
export type FiscalRegion = "peninsula" | "canarias" | "ceuta-melilla";

export interface SearchFilters {
  make: string;
  model: string;
  yearFrom?: number;
  yearTo?: number;
  priceFrom?: number;
  priceTo?: number;
  kmTo?: number;
  powerFrom?: number;
  fuel?: Fuel;
  gearbox?: Gearbox;
  seller?: SellerType;
  countries: CountryCode[];
  /** Orden de la lista unificada. */
  sort: "coste-total" | "precio" | "km" | "antiguedad";
}

export interface Listing {
  id: string;
  /** id del portal de origen (ver lib/portals.ts) */
  source: string;
  sourceName: string;
  title: string;
  make?: string;
  model?: string;
  price: number;
  year?: number;
  km?: number;
  fuel?: Fuel;
  gearbox?: Gearbox;
  power?: number;
  /** g/km WLTP. Sin esto el impuesto de matriculacion no se puede calcular. */
  co2?: number;
  country: CountryCode;
  city?: string;
  seller?: SellerType;
  url: string;
  image?: string;
  /** true = ficha de ejemplo, no es un coche real a la venta */
  demo?: boolean;
  /** Coste puerta a puerta en Espana, calculado en el servidor. */
  landedCost?: number;
}

/** Como ha respondido cada portal a una busqueda. */
export type PortalMode = "live" | "link" | "demo" | "error";

export interface PortalResult {
  portal: string;
  name: string;
  countries: CountryCode[];
  /** Busqueda con los filtros ya aplicados, para abrir en el navegador. */
  searchUrl: string;
  mode: PortalMode;
  listings: Listing[];
  note?: string;
  ms?: number;
}

export interface SearchResponse {
  filters: SearchFilters;
  listings: Listing[];
  portals: PortalResult[];
  stats: { live: number; link: number; demo: number; error: number; total: number };
}

// ---------------------------------------------------------------------------
// Costes de importacion
// ---------------------------------------------------------------------------

export type TransportMode = "camion" | "conducirlo" | "ya-en-espana";

export interface CostInputs {
  price: number;
  country: CountryCode;
  region: FiscalRegion;
  co2?: number;
  fuel?: Fuel;
  /** Fecha de la primera matriculacion (ISO yyyy-mm-dd) */
  firstRegistration?: string;
  km?: number;
  seller: SellerType;
  /** Valor segun tablas de Hacienda. Si no se indica, se usa el precio pagado. */
  valorFiscal?: number;
  /** Tipo de ITP de tu comunidad autonoma (%). */
  itpRate: number;
  /** Incluir ITP: discutido en compras UE entre particulares. Ver README. */
  includeItp: boolean;
  transport: TransportMode;
  hasCoc: boolean;
  useGestoria: boolean;
  vinReport: boolean;
  /** Precio del mismo coche en el mercado espanol, para comparar. */
  precioEspana?: number;
}

export interface CostLine {
  key: string;
  label: string;
  amount: number;
  note?: string;
  /** true = lo puedes quitar o hacer tu mismo */
  optional?: boolean;
}

export interface CostBreakdown {
  lines: CostLine[];
  impuestos: number;
  gastos: number;
  total: number;
  /** total - price */
  sobrecoste: number;
  ahorro?: number;
  iedmtRate: number;
  esMedioTransporteNuevo: boolean;
  avisos: string[];
}

// ---------------------------------------------------------------------------
// Revision guiada
// ---------------------------------------------------------------------------

export type Answer = "ok" | "ko" | "na" | null;

export interface CheckItem {
  id: string;
  label: string;
  detail?: string;
  /** Un KO aqui es motivo para levantarse y marcharse. */
  critical?: boolean;
  weight: number;
  /** Coste estimado de arreglarlo, en euros. Alimenta la negociacion. */
  repairCost?: number;
  onlyFuel?: Fuel[];
  onlyGearbox?: Gearbox[];
  onlyCountry?: CountryCode[];
  /** Solo si el coche supera estos km / anos */
  minKm?: number;
  minAge?: number;
}

export interface CheckPhase {
  id: string;
  title: string;
  subtitle: string;
  /** Donde se hace: en casa, en el sitio, en la carretera... */
  place: string;
  items: CheckItem[];
}

export interface Dossier {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
  listing?: Partial<Listing>;
  cost?: CostInputs;
  answers: Record<string, Answer>;
  notes: Record<string, string>;
}

export interface Verdict {
  score: number;
  answered: number;
  totalItems: number;
  redFlags: CheckItem[];
  defects: CheckItem[];
  /** Defectos que son cuestion de precio, no de irse. */
  negociables: CheckItem[];
  descuento: number;
  level: "ok" | "negociar" | "riesgo" | "huir" | "incompleto";
  title: string;
  message: string;
}
