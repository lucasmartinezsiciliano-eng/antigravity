/**
 * Cuanto cuesta DE VERDAD traer un coche de Europa a Espana.
 *
 * Todos los importes son orientativos salvo los tipos impositivos, que salen
 * de la norma. Revisa DATOS_ACTUALIZADOS antes de fiarte de un numero.
 *
 * Fuentes:
 *  - Impuesto de matriculacion (IEDMT): Ley 38/1992, art. 70. Tramos de CO2
 *    vigentes: 0 / 4,75 / 9,75 / 14,75 % en peninsula y Baleares.
 *  - Base imponible de vehiculos usados: valor de mercado segun las tablas de
 *    precios medios de venta que publica Hacienda cada ano (no el precio pagado).
 *  - Tasa DGT de matriculacion definitiva: ~99,77 EUR para turismos.
 */

import type { CostBreakdown, CostInputs, CostLine, CountryCode, FiscalRegion } from "./types";

export const DATOS_ACTUALIZADOS = "2026-09";

// --- Impuesto de matriculacion (IEDMT) -------------------------------------

interface Tramo {
  hasta: number;
  rate: number;
  label: string;
}

const TRAMOS: Record<FiscalRegion, Tramo[]> = {
  peninsula: [
    { hasta: 120, rate: 0, label: "menos de 120 g/km" },
    { hasta: 160, rate: 4.75, label: "120 a 159 g/km" },
    { hasta: 200, rate: 9.75, label: "160 a 199 g/km" },
    { hasta: Infinity, rate: 14.75, label: "200 g/km o mas" },
  ],
  canarias: [
    { hasta: 120, rate: 0, label: "menos de 120 g/km" },
    { hasta: 160, rate: 3.75, label: "120 a 159 g/km" },
    { hasta: 200, rate: 8.75, label: "160 a 199 g/km" },
    { hasta: Infinity, rate: 13.75, label: "200 g/km o mas" },
  ],
  "ceuta-melilla": [{ hasta: Infinity, rate: 0, label: "exento" }],
};

export function tramoIedmt(co2: number | undefined, region: FiscalRegion): Tramo {
  const tabla = TRAMOS[region];
  if (co2 === undefined || Number.isNaN(co2)) {
    // Sin dato de CO2 asumimos el peor caso: es lo que hace Hacienda si no
    // puedes acreditarlo con el COC o la ficha tecnica.
    return tabla[tabla.length - 1];
  }
  return tabla.find((t) => co2 < t.hasta) ?? tabla[tabla.length - 1];
}

// --- Valor fiscal ----------------------------------------------------------

/**
 * Porcentaje del precio de venta del modelo NUEVO que Hacienda considera valor
 * del coche segun sus anos de uso (anexo de la orden anual de precios medios).
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

/** Valor fiscal estimado a partir del precio del modelo nuevo. */
export function valorFiscalEstimado(precioNuevo: number, firstRegistration?: string): number {
  const anos = antiguedadEnAnos(firstRegistration) ?? 0;
  return Math.round((precioNuevo * coeficienteAntiguedad(Math.ceil(anos || 1))) / 100);
}

export function antiguedadEnAnos(firstRegistration?: string): number | undefined {
  if (!firstRegistration) return undefined;
  const d = new Date(firstRegistration);
  if (Number.isNaN(d.getTime())) return undefined;
  return (Date.now() - d.getTime()) / (365.25 * 24 * 3600 * 1000);
}

// --- Transporte ------------------------------------------------------------

/** Camion porta-coches hasta el centro/este peninsular. Orientativo. */
const CAMION: Record<CountryCode, number> = {
  DE: 850, FR: 600, IT: 750, NL: 880, BE: 820, AT: 980, PT: 350, PL: 1150, LU: 800, ES: 0,
};

/** Km aproximados de vuelta conduciendo hasta el este peninsular. */
const DISTANCIA: Record<CountryCode, number> = {
  DE: 1800, FR: 1050, IT: 1500, NL: 1850, BE: 1650, AT: 2000, PT: 700, PL: 2600, LU: 1550, ES: 0,
};

/** Placas temporales + seguro de traslado para volver conduciendo. */
const PLACAS: Record<CountryCode, number> = {
  DE: 160, FR: 110, IT: 130, NL: 120, BE: 120, AT: 140, PT: 90, PL: 130, LU: 120, ES: 0,
};

const COSTE_COMBUSTIBLE_KM = 0.12; // ~7 l/100 km a 1,70 EUR/l
const COSTE_PEAJES_KM = 0.07;
const VUELO_IDA = 130;

// --- Gastos fijos ----------------------------------------------------------

export const GASTOS = {
  tasaDgt: 99.77,
  itv: 170,
  fichaTecnica: 250,
  coc: 150,
  gestoria: 300,
  informeVin: 25,
};

// --- Calculo ---------------------------------------------------------------

function esMedioTransporteNuevo(i: CostInputs): boolean {
  // Art. 13 Ley 37/1992: menos de 6 meses o menos de 6.000 km => se paga IVA
  // espanol aunque lo compres a un particular.
  const anos = antiguedadEnAnos(i.firstRegistration);
  const nuevoPorFecha = anos !== undefined && anos < 0.5;
  const nuevoPorKm = i.km !== undefined && i.km < 6000;
  return nuevoPorFecha || nuevoPorKm;
}

export function calcularCostes(i: CostInputs): CostBreakdown {
  const lines: CostLine[] = [];
  const avisos: string[] = [];

  const base = i.valorFiscal && i.valorFiscal > 0 ? i.valorFiscal : i.price;
  if (!i.valorFiscal) {
    avisos.push(
      "Estamos usando el precio de compra como base imponible. Hacienda usa sus propias tablas de valor: si el coche vale mas en tabla que lo que pagaste, pagaras mas impuesto.",
    );
  }

  lines.push({ key: "precio", label: "Precio del coche", amount: i.price });

  // --- Impuestos ---
  const tramo = tramoIedmt(i.co2, i.region);
  const iedmt = (base * tramo.rate) / 100;
  lines.push({
    key: "iedmt",
    label: `Impuesto de matriculacion (${tramo.rate}%)`,
    amount: iedmt,
    note:
      i.co2 === undefined
        ? "Sin dato de CO2 aplicamos el tramo maximo. Pide el COC o la ficha tecnica: puede ahorrarte miles de euros."
        : `${i.co2} g/km WLTP, tramo de ${tramo.label}`,
  });
  if (i.co2 === undefined) {
    avisos.push("Falta el CO2. Es el dato que mas mueve el precio final: pidelo antes de cerrar nada.");
  }

  const nuevo = esMedioTransporteNuevo(i);
  if (nuevo) {
    const iva = base * 0.21;
    lines.push({
      key: "iva",
      label: "IVA espanol (21%)",
      amount: iva,
      note: "El coche tiene menos de 6 meses o menos de 6.000 km: para Hacienda es nuevo y el IVA se paga aqui.",
    });
    avisos.push(
      "Cuidado: menos de 6 meses o menos de 6.000 km = medio de transporte nuevo. Pagas el 21% de IVA en Espana aunque ya se pagara alli (modelo 309).",
    );
  }

  if (i.includeItp && i.seller === "particular") {
    lines.push({
      key: "itp",
      label: `ITP (${i.itpRate}%)`,
      amount: (base * i.itpRate) / 100,
      note: "Compra a particular. Discutido en compras dentro de la UE: confirmalo con tu gestoria.",
      optional: true,
    });
    avisos.push(
      "El ITP en importaciones UE entre particulares no esta claro: hay comunidades que lo reclaman y gestorias que sostienen que no procede. Lo incluimos para que el presupuesto no se quede corto.",
    );
  }

  const impuestos = lines
    .filter((l) => ["iedmt", "iva", "itp"].includes(l.key))
    .reduce((s, l) => s + l.amount, 0);

  // --- Gastos ---
  if (i.transport === "camion") {
    lines.push({
      key: "transporte",
      label: "Transporte en camion",
      amount: CAMION[i.country],
      note: "Puerta a puerta, seguro incluido. Pide 3 presupuestos: varia mucho.",
    });
  } else if (i.transport === "conducirlo") {
    const km = DISTANCIA[i.country];
    const viaje = VUELO_IDA + km * (COSTE_COMBUSTIBLE_KM + COSTE_PEAJES_KM) + (km > 1200 ? 150 : 60);
    lines.push({
      key: "transporte",
      label: "Ir a buscarlo",
      amount: Math.round(viaje),
      note: `Vuelo + ~${km} km de vuelta entre combustible, peajes y dieta.`,
    });
    lines.push({
      key: "placas",
      label: "Placas temporales + seguro de traslado",
      amount: PLACAS[i.country],
      note: "Sin esto no puedes circular legalmente de vuelta.",
    });
  }

  if (!i.hasCoc) {
    lines.push({
      key: "coc",
      label: "Certificado de conformidad (COC)",
      amount: GASTOS.coc,
      note: "Se pide al fabricante. Si el coche lo trae, te lo ahorras.",
      optional: true,
    });
    lines.push({
      key: "ficha",
      label: "Ficha tecnica reducida / homologacion",
      amount: GASTOS.fichaTecnica,
      note: "Necesaria cuando no hay COC. Tarda entre 1 y 3 semanas.",
    });
    avisos.push("Sin COC el tramite se alarga y se encarece. Preguntalo SIEMPRE antes de comprar.");
  }

  lines.push({ key: "itv", label: "ITV de importacion", amount: GASTOS.itv });
  lines.push({
    key: "tasaDgt",
    label: "Tasa DGT de matriculacion",
    amount: GASTOS.tasaDgt,
    note: "Tasa oficial por el permiso de circulacion.",
  });

  if (i.useGestoria) {
    lines.push({
      key: "gestoria",
      label: "Gestoria",
      amount: GASTOS.gestoria,
      note: "Opcional: puedes hacer los tramites tu, pero son 4 ventanillas.",
      optional: true,
    });
  }
  if (i.vinReport) {
    lines.push({
      key: "vin",
      label: "Informe de historial por VIN",
      amount: GASTOS.informeVin,
      note: "25 EUR que te pueden ahorrar 8.000. Hazlo antes de viajar.",
      optional: true,
    });
  }

  const gastos = lines
    .filter((l) => !["precio", "iedmt", "iva", "itp"].includes(l.key))
    .reduce((s, l) => s + l.amount, 0);

  const total = i.price + impuestos + gastos;

  return {
    lines,
    impuestos: Math.round(impuestos),
    gastos: Math.round(gastos),
    total: Math.round(total),
    sobrecoste: Math.round(total - i.price),
    ahorro: i.precioEspana ? Math.round(i.precioEspana - total) : undefined,
    iedmtRate: tramo.rate,
    esMedioTransporteNuevo: nuevo,
    avisos,
  };
}

/** Version rapida para ordenar la lista de resultados del buscador. */
export function costeAproximado(
  price: number,
  country: CountryCode,
  co2?: number,
  year?: number,
): number {
  const tramo = tramoIedmt(co2, "peninsula");
  const impuesto = (price * tramo.rate) / 100;
  const fijos = GASTOS.tasaDgt + GASTOS.itv + GASTOS.fichaTecnica + GASTOS.gestoria;
  const transporte = CAMION[country] ?? 700;
  void year;
  return Math.round(price + impuesto + fijos + transporte);
}

export const CCAA_ITP: { id: string; name: string; rate: number }[] = [
  { id: "andalucia", name: "Andalucia", rate: 4 },
  { id: "aragon", name: "Aragon", rate: 4 },
  { id: "asturias", name: "Asturias", rate: 4 },
  { id: "baleares", name: "Baleares", rate: 4 },
  { id: "canarias", name: "Canarias", rate: 5.5 },
  { id: "cantabria", name: "Cantabria", rate: 8 },
  { id: "castilla-la-mancha", name: "Castilla-La Mancha", rate: 6 },
  { id: "castilla-y-leon", name: "Castilla y Leon", rate: 5 },
  { id: "cataluna", name: "Cataluna", rate: 5 },
  { id: "extremadura", name: "Extremadura", rate: 6 },
  { id: "galicia", name: "Galicia", rate: 3 },
  { id: "madrid", name: "Madrid", rate: 4 },
  { id: "murcia", name: "Murcia", rate: 4 },
  { id: "navarra", name: "Navarra", rate: 4 },
  { id: "pais-vasco", name: "Pais Vasco", rate: 4 },
  { id: "la-rioja", name: "La Rioja", rate: 4 },
  { id: "valencia", name: "Comunidad Valenciana", rate: 6 },
];
