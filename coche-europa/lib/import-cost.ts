/**
 * Cuanto cuesta DE VERDAD traer un coche de Europa a Espana.
 *
 * Los tipos impositivos salen de la norma. Los gastos son horquillas de
 * mercado: se muestran como rango porque un presupuesto de importacion con
 * precision de dos decimales miente mas que uno con margen honesto.
 *
 * Fuentes principales:
 *  - Ley 38/1992 (Impuestos Especiales), arts. 69 y 70: base imponible y tramos
 *    de CO2 del impuesto de matriculacion.
 *  - Orden HAC/1501/2025 (BOE-A-2025-26357, en vigor 1/1/2026): precios medios
 *    de venta y coeficientes de antiguedad.
 *  - Ley 37/1992 (IVA), art. 13.2: medios de transporte nuevos.
 *  - RDLeg 1/1993 (TRLITPAJD), art. 6.1.A): sujecion del ITP.
 *
 * Investigacion completa y deuda de verificacion pendiente:
 *  obsidian/Coches/Importación — Fiscalidad y Trámites.md
 */

import type { CostBreakdown, CostInputs, CostLine, CountryCode, FiscalRegion } from "./types";

export const DATOS_ACTUALIZADOS = "2026-09 · Orden HAC/1501/2025, vigente hasta 31/12/2026";

/** Tipo general del IVA. Entra en la minoracion del art. 69.b). */
const TIPO_IVA = 0.21;

// --- Impuesto de matriculacion (IEDMT) -------------------------------------

interface Tramo {
  /** Limite superior INCLUIDO: la ley dice "no superiores a". */
  hasta: number;
  rate: number;
  label: string;
}

const TRAMOS: Record<FiscalRegion, Tramo[]> = {
  peninsula: [
    { hasta: 120, rate: 0, label: "hasta 120 g/km" },
    { hasta: 160, rate: 4.75, label: "mas de 120 y hasta 160 g/km" },
    { hasta: 200, rate: 9.75, label: "mas de 160 y hasta 200 g/km" },
    { hasta: Infinity, rate: 14.75, label: "mas de 200 g/km" },
  ],
  canarias: [
    { hasta: 120, rate: 0, label: "hasta 120 g/km" },
    { hasta: 160, rate: 3.75, label: "mas de 120 y hasta 160 g/km" },
    { hasta: 200, rate: 8.75, label: "mas de 160 y hasta 200 g/km" },
    { hasta: Infinity, rate: 13.75, label: "mas de 200 g/km" },
  ],
  "ceuta-melilla": [{ hasta: Infinity, rate: 0, label: "exento" }],
};

export function tramoIedmt(co2: number | undefined, region: FiscalRegion): Tramo {
  const tabla = TRAMOS[region];
  if (co2 === undefined || Number.isNaN(co2)) {
    // Sin CO2 acreditado se aplica el tramo maximo: es lo que hace Hacienda si
    // no puedes demostrarlo con el COC o la ficha tecnica.
    return tabla[tabla.length - 1];
  }
  // "Emisiones no superiores a X": el limite entra en el tramo de abajo.
  return tabla.find((t) => co2 <= t.hasta) ?? tabla[tabla.length - 1];
}

/**
 * Minoracion del art. 69.b) Ley 38/1992.
 *
 * En un vehiculo usado que ya estuvo matriculado en el extranjero, la base no
 * es el valor de mercado a secas: se le quita la parte que corresponde a los
 * impuestos que ya lleva incorporados. Sin esto se sobrestima el impuesto en
 * torno a un 20-25%.
 */
export function baseMinorada(valorMercado: number, tipoIedmt: number): number {
  return valorMercado / (1 + TIPO_IVA + tipoIedmt / 100);
}

// --- Valor fiscal ----------------------------------------------------------

/**
 * Porcentaje del precio medio de venta que Hacienda considera valor del coche
 * segun sus anos de uso (Anexo IV de la Orden HAC/1501/2025).
 */
const DEPRECIACION: [number, number][] = [
  [1, 100], [2, 84], [3, 67], [4, 56], [5, 47], [6, 39],
  [7, 34], [8, 28], [9, 24], [10, 19], [11, 17], [12, 13],
];

export function coeficienteAntiguedad(anos: number): number {
  for (const [limite, pct] of DEPRECIACION) {
    if (anos <= limite) return pct;
  }
  return 10;
}

/**
 * Valor fiscal estimado.
 *
 * OJO: el punto de partida legal es el precio medio del Anexo I de la orden,
 * que no es el PVP del concesionario. Esto es una aproximacion.
 */
export function valorFiscalEstimado(precioMedioNuevo: number, firstRegistration?: string): number {
  const anos = antiguedadEnAnos(firstRegistration) ?? 0;
  return Math.round((precioMedioNuevo * coeficienteAntiguedad(Math.ceil(anos || 1))) / 100);
}

export function antiguedadEnAnos(firstRegistration?: string, hasta?: string): number | undefined {
  if (!firstRegistration) return undefined;
  const d = new Date(firstRegistration);
  if (Number.isNaN(d.getTime())) return undefined;
  const ref = hasta ? new Date(hasta) : new Date();
  const fin = Number.isNaN(ref.getTime()) ? Date.now() : ref.getTime();
  return (fin - d.getTime()) / (365.25 * 24 * 3600 * 1000);
}

// --- Transporte ------------------------------------------------------------

/** Camion porta-coches hasta el centro/este peninsular. Horquillas de mercado. */
const CAMION: Record<CountryCode, [number, number]> = {
  DE: [850, 1250], FR: [600, 900], IT: [750, 1100], NL: [880, 1300], BE: [820, 1200],
  AT: [980, 1400], PT: [350, 600], PL: [1150, 1600], LU: [800, 1150], ES: [0, 0],
};

/** Km aproximados de vuelta conduciendo hasta el este peninsular. */
const DISTANCIA: Record<CountryCode, number> = {
  DE: 1800, FR: 1050, IT: 1500, NL: 1850, BE: 1650, AT: 2000, PT: 700, PL: 2600, LU: 1550, ES: 0,
};

/** Placas de exportacion + seguro de traslado. */
const PLACAS: Record<CountryCode, [number, number]> = {
  DE: [160, 320], FR: [110, 230], IT: [130, 260], NL: [120, 240], BE: [120, 240],
  AT: [140, 280], PT: [90, 190], PL: [130, 260], LU: [120, 240], ES: [0, 0],
};

const COSTE_COMBUSTIBLE_KM = 0.12; // ~7 l/100 km a 1,70 EUR/l
const COSTE_PEAJES_KM = 0.07;
const VUELO_IDA = 130;

// --- Gastos fijos ----------------------------------------------------------

export const GASTOS: Record<string, [number, number]> = {
  tasaDgt: [99.77, 99.77],
  itv: [50, 170],
  fichaReducida: [39, 90],
  homologacionIndividual: [400, 900],
  homologacionReformas: [2500, 3000],
  coc: [109, 250],
  gestoria: [250, 500],
  informeVin: [16, 35],
  ivtm: [30, 200],
};

const medio = ([a, b]: [number, number]) => (a + b) / 2;

// --- Calculo ---------------------------------------------------------------

function esMedioTransporteNuevo(i: CostInputs): boolean {
  // Art. 13.2 Ley 37/1992: basta con que se de CUALQUIERA de las dos.
  // Los 6 meses se cuentan hasta la entrega, no hasta hoy.
  const anos = antiguedadEnAnos(i.firstRegistration, i.fechaCompra);
  const nuevoPorFecha = anos !== undefined && anos < 0.5;
  const nuevoPorKm = i.km !== undefined && i.km <= 6000;
  return nuevoPorFecha || nuevoPorKm;
}

export function calcularCostes(i: CostInputs): CostBreakdown {
  const lines: CostLine[] = [];
  const avisos: string[] = [];

  const push = (l: Omit<CostLine, "amount"> & { amount: number }) =>
    lines.push({ ...l, amount: Math.round(l.amount) });

  const valorMercado = i.valorFiscal && i.valorFiscal > 0 ? i.valorFiscal : i.price;
  if (!i.valorFiscal) {
    avisos.push(
      "Estamos usando el precio de compra como valor de mercado. Hacienda usa sus propias tablas: si el coche vale mas en tabla que lo que pagaste, pagaras mas impuesto.",
    );
  }
  if (!i.firstRegistration) {
    avisos.push(
      "Sin la fecha de primera matriculacion no podemos saber la antiguedad, y eso mueve tanto el valor fiscal como el criterio de vehiculo nuevo. Pidesela al vendedor.",
    );
  }

  push({ key: "precio", label: "Precio del coche", amount: i.price });

  // --- Impuesto de matriculacion ---
  const tramo = tramoIedmt(i.co2, i.region);
  const tipoIedmt = tramo.rate + (i.recargoAutonomico ?? 0);
  const nuevo = esMedioTransporteNuevo(i);

  // Art. 69.b): solo para usados ya matriculados fuera.
  const baseIedmt = nuevo ? valorMercado : baseMinorada(valorMercado, tipoIedmt);
  const minoracion = valorMercado - baseIedmt;
  const iedmt = (baseIedmt * tipoIedmt) / 100;

  push({
    key: "iedmt",
    label: `Impuesto de matriculacion (${tipoIedmt}%)`,
    amount: iedmt,
    note:
      i.co2 === undefined
        ? "Sin dato de CO2 aplicamos el tramo maximo. Pide el COC o el campo V.7 del permiso: puede ahorrarte miles de euros."
        : `${i.co2} g/km, tramo de ${tramo.label}` +
          (minoracion > 0
            ? `. Base minorada a ${Math.round(baseIedmt).toLocaleString("es-ES")} EUR por el art. 69.b), al ser un usado ya matriculado fuera.`
            : ""),
  });

  if (i.co2 === undefined) {
    avisos.push(
      "Falta el CO2. Es el dato que mas mueve el precio final: mira el campo V.7 del permiso de circulacion del coche, que existe en toda la UE.",
    );
  } else if (i.co2 <= 200) {
    // Avisa de lo cerca que esta del siguiente escalon.
    const siguiente = TRAMOS[i.region].find((t) => t.hasta > (i.co2 ?? 0));
    const margen = siguiente && siguiente.hasta !== Infinity ? siguiente.hasta - i.co2 : undefined;
    if (margen !== undefined && margen <= 10) {
      avisos.push(
        `Estas a ${margen} g/km del siguiente tramo. Una version o un equipamiento distinto del mismo modelo puede cruzarlo y subirte el impuesto miles de euros: confirma el CO2 de ESTE coche, no el del modelo.`,
      );
    }
  }

  if (i.region === "peninsula" && !i.recargoAutonomico) {
    avisos.push(
      "Algunas comunidades pueden subir el tipo del impuesto de matriculacion hasta un 15% sobre el estatal. Confirmalo con la tuya antes de dar el numero por bueno.",
    );
  }

  // --- IVA ---
  if (nuevo) {
    // La base de una adquisicion intracomunitaria es la contraprestacion.
    push({
      key: "iva",
      label: "IVA espanol (21%)",
      amount: i.price * TIPO_IVA,
      note: "Menos de 6 meses o no mas de 6.000 km: para Hacienda es nuevo y el IVA se paga aqui, sobre el precio pagado.",
    });
    avisos.push(
      "Este coche es medio de transporte nuevo. EXIGE al vendedor una factura SIN IVA: la entrega intracomunitaria debe ir exenta en origen y el 21% lo liquidas tu aqui con el modelo 309. Si te cobra el IVA alli, pagaras dos veces.",
    );
  }

  // --- ITP ---
  if (i.includeItp && i.seller === "particular") {
    // La base del ITP es el valor de mercado SIN la minoracion del 69.b).
    push({
      key: "itp",
      label: `ITP (${i.itpRate}%) — riesgo fiscal latente`,
      amount: (valorMercado * i.itpRate) / 100,
      note: "Legalmente sujeto, pero la DGT no pide el modelo 620 para matricular una importacion. Casi nadie lo paga; la deuda existe y prescribe a los 4 anos.",
      optional: true,
    });
    avisos.push(
      "El ITP de una compra a particular en la UE esta sujeto (art. 6.1.A del TRLITPAJD) pero no engranado con ningun tramite: nadie te lo va a pedir en la ventanilla. Lo dejamos dentro para que veas el riesgo completo. Si decides no pagarlo, que sea una decision tuya y no un descuido.",
    );
  }

  const impuestos = lines
    .filter((l) => ["iedmt", "iva", "itp"].includes(l.key))
    .reduce((s, l) => s + l.amount, 0);

  // --- Gastos ---
  if (i.transport === "camion") {
    const r = CAMION[i.country];
    push({
      key: "transporte",
      label: "Transporte en camion",
      amount: medio(r),
      range: r,
      note: "Puerta a puerta con seguro. Pide 3 presupuestos: varia mucho.",
    });
  } else if (i.transport === "conducirlo") {
    const km = DISTANCIA[i.country];
    const viaje = VUELO_IDA + km * (COSTE_COMBUSTIBLE_KM + COSTE_PEAJES_KM) + (km > 1200 ? 150 : 60);
    push({
      key: "transporte",
      label: "Ir a buscarlo",
      amount: viaje,
      range: [Math.round(viaje * 0.8), Math.round(viaje * 1.35)],
      note: `Vuelo + ~${km} km de vuelta entre combustible, peajes y dieta.`,
    });
    const pl = PLACAS[i.country];
    push({
      key: "placas",
      label: "Placas de exportacion + seguro de traslado",
      amount: medio(pl),
      range: pl,
      note:
        i.country === "DE"
          ? "Necesitas Ausfuhrkennzeichen (roja, valida fuera de Alemania), NO Kurzzeitkennzeichen (amarilla, solo 5 dias y sin validez internacional)."
          : "Sin esto no puedes circular legalmente de vuelta.",
    });
  }

  // --- Homologacion ---
  if (i.modificado) {
    const r = GASTOS.homologacionReformas;
    push({
      key: "reformas",
      label: "Homologacion de reformas",
      amount: medio(r),
      range: r,
      note: "Espana no convalida las reformas anotadas en el TUV aleman ni equivalentes.",
    });
    avisos.push(
      "El coche lleva reformas. Llantas, suspension, escape o cambios de potencia obligan a homologacion individual en Espana, y se descubre con el coche ya aqui. Es el gasto sorpresa mas caro de toda la importacion.",
    );
  }

  if (i.hasCoc) {
    const r = GASTOS.fichaReducida;
    push({
      key: "ficha",
      label: "Ficha tecnica reducida",
      amount: medio(r),
      range: r,
      note: "Hace falta aunque tengas COC, pero con el es tramite de horas.",
    });
  } else {
    const c = GASTOS.coc;
    push({
      key: "coc",
      label: "Certificado de conformidad (COC)",
      amount: medio(c),
      range: c,
      note: "Se pide al fabricante, de 1 a 20 dias. Intenta siempre conseguirlo.",
      optional: true,
    });
    const h = GASTOS.homologacionIndividual;
    push({
      key: "homologacion",
      label: "Homologacion individual (sin COC)",
      amount: medio(h),
      range: h,
      note: "Necesaria si no hay COC ni homologacion europea equivalente.",
    });
    avisos.push("Sin COC el tramite se alarga y se encarece. Preguntalo SIEMPRE antes de comprar.");
  }

  const itv = GASTOS.itv;
  push({ key: "itv", label: "ITV de importacion", amount: medio(itv), range: itv });

  push({
    key: "tasaDgt",
    label: "Tasa DGT de matriculacion",
    amount: GASTOS.tasaDgt[0],
    note: "Tasa 1.1, importe oficial.",
  });

  const ivtm = GASTOS.ivtm;
  push({
    key: "ivtm",
    label: "Impuesto de circulacion (IVTM)",
    amount: medio(ivtm),
    range: ivtm,
    note: "Lo cobra tu ayuntamiento segun los caballos fiscales. La DGT exige el justificante para matricular.",
  });

  if (i.useGestoria) {
    const g = GASTOS.gestoria;
    push({
      key: "gestoria",
      label: "Gestoria",
      amount: medio(g),
      range: g,
      note: "Opcional: puedes hacerlo tu, pero son cuatro ventanillas.",
      optional: true,
    });
  }
  if (i.vinReport) {
    const v = GASTOS.informeVin;
    push({
      key: "vin",
      label: "Informe de historial por VIN",
      amount: medio(v),
      range: v,
      note: "Util en NL, FR, PL y BE. En Alemania los informes salen casi ciegos: alli vale mas pedir los 3 ultimos HU.",
      optional: true,
    });
  }

  const gastos = lines
    .filter((l) => !["precio", "iedmt", "iva", "itp"].includes(l.key))
    .reduce((s, l) => s + l.amount, 0);

  // El total es la suma de lo que se ve en pantalla, no un calculo aparte.
  const total = lines.reduce((s, l) => s + l.amount, 0);

  return {
    lines,
    impuestos,
    gastos,
    total,
    sobrecoste: total - i.price,
    ahorro: i.precioEspana ? Math.round(i.precioEspana - total) : undefined,
    iedmtRate: tipoIedmt,
    baseIedmt: Math.round(baseIedmt),
    minoracion: Math.round(minoracion),
    esMedioTransporteNuevo: nuevo,
    avisos,
  };
}

/**
 * Version rapida para ORDENAR la lista del buscador.
 *
 * Solo mete lo inevitable: impuesto y transporte. No suma gestoria ni
 * homologacion porque dependen de decisiones del usuario y sesgarian el orden
 * de unos coches frente a otros.
 */
export function costeAproximado(
  price: number,
  country: CountryCode,
  co2?: number,
  region: FiscalRegion = "peninsula",
): number {
  const tramo = tramoIedmt(co2, region);
  const impuesto = (baseMinorada(price, tramo.rate) * tramo.rate) / 100;
  const inevitables = GASTOS.tasaDgt[0] + medio(GASTOS.itv) + medio(GASTOS.fichaReducida);
  const transporte = medio(CAMION[country] ?? [700, 1000]);
  return Math.round(price + impuesto + inevitables + transporte);
}

/**
 * Tipos de ITP por comunidad.
 *
 * ADVERTENCIA: ninguno de estos tipos esta verificado contra la normativa
 * autonomica vigente. Ademas varias comunidades aplican cuotas fijas en euros
 * para vehiculos antiguos o de baja cilindrada, que esta tabla no representa.
 * Navarra y Pais Vasco son forales y liquidan en su propia hacienda.
 */
export const CCAA_ITP: { id: string; name: string; rate: number; foral?: boolean }[] = [
  { id: "andalucia", name: "Andalucia", rate: 4 },
  { id: "aragon", name: "Aragon", rate: 4 },
  { id: "asturias", name: "Asturias", rate: 4 },
  { id: "baleares", name: "Baleares", rate: 4 },
  { id: "canarias", name: "Canarias", rate: 5.5 },
  { id: "cantabria", name: "Cantabria", rate: 8 },
  { id: "castilla-la-mancha", name: "Castilla-La Mancha", rate: 6 },
  { id: "castilla-y-leon", name: "Castilla y Leon", rate: 5 },
  { id: "cataluna", name: "Cataluna", rate: 5 },
  { id: "ceuta", name: "Ceuta", rate: 4 },
  { id: "extremadura", name: "Extremadura", rate: 6 },
  { id: "galicia", name: "Galicia", rate: 3 },
  { id: "madrid", name: "Madrid", rate: 4 },
  { id: "melilla", name: "Melilla", rate: 4 },
  { id: "murcia", name: "Murcia", rate: 4 },
  { id: "navarra", name: "Navarra (foral)", rate: 4, foral: true },
  { id: "pais-vasco", name: "Pais Vasco (foral)", rate: 4, foral: true },
  { id: "la-rioja", name: "La Rioja", rate: 4 },
  { id: "valencia", name: "Comunidad Valenciana", rate: 6 },
];
