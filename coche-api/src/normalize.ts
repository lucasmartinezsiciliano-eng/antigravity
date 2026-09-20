/**
 * Traducir lo que dice cada portal al vocabulario del esquema.
 *
 * Esto es el 80% del trabajo real de una metabusqueda: "Schaltgetriebe",
 * "boite manuelle", "cambio manuale" y "manual" son la misma cosa, y hasta que
 * no lo son de verdad no se pueden comparar dos anuncios.
 */

import type { Body, Country, Fuel, Gearbox, SellerType } from "./schema.ts";

const sinAcentos = (s: string) =>
  s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").trim();

/** Busca la primera clave cuyo patron aparezca en el texto. */
function mapear<T extends string>(texto: string, tabla: [RegExp, T][]): T | undefined {
  const t = sinAcentos(texto);
  for (const [re, v] of tabla) if (re.test(t)) return v;
  return undefined;
}

// El orden importa: lo mas especifico primero. "hibrido enchufable" antes que
// "hibrido", y "electrico" despues de ambos.
const FUEL_MAP: [RegExp, Fuel][] = [
  [/plug.?in|enchufab|hybride rechargeable|ibrida plug|phev/, "phev"],
  [/hybrid|hibrid|ibrid/, "hibrido"],
  [/elektr|electri|electrique|elettric|\bev\b|bev/, "electrico"],
  [/diesel|gasoil|gazole|diesel|nafta/, "diesel"],
  [/benzin|gasolin|essence|benzina|petrol|super/, "gasolina"],
  [/\blpg\b|autogas|glp|gpl/, "glp"],
  [/\bcng\b|erdgas|gnc|metano|gnv/, "gnc"],
  [/wasserstoff|hidrogen|hydrogen|idrogeno/, "hidrogeno"],
];

const GEARBOX_MAP: [RegExp, Gearbox][] = [
  [/automat|dsg|tiptronic|s.?tronic|pdk|cvt|edc|dct|eat\d/, "automatico"],
  [/manuell|manual|schaltgetriebe|boite mecanique|meccanico|handgeschakeld/, "manual"],
];

const BODY_MAP: [RegExp, Body][] = [
  [/cabrio|convertible|descapotab|roadster|spider/, "descapotable"],
  [/coupe|coupé/, "coupe"],
  [/kombi|estate|familiar|break|station|touring|avant|sw\b/, "familiar"],
  [/suv|gelandewagen|todoterreno|4x4|crossover/, "suv"],
  [/\bvan\b|transporter|furgon|fourgon|bestelwagen/, "furgoneta"],
  [/pick.?up/, "pickup"],
  [/monovolum|minivan|mpv|monospace|kleinbus/, "monovolumen"],
  [/limousine|berlin|sedan|saloon|salon/, "berlina"],
  [/kleinwagen|utilitario|citadine|city/, "utilitario"],
  [/kompakt|compact|compacto/, "compacto"],
];

const SELLER_MAP: [RegExp, SellerType][] = [
  [/privat|particulier|particular|privato|prive|fsbo|priv\b/, "particular"],
  [/handler|dealer|profession|concesion|rivendit|garage|gewerb|bedrijf/, "profesional"],
];

export const toFuel = (s?: string) => (s ? mapear(s, FUEL_MAP) : undefined);
export const toGearbox = (s?: string) => (s ? mapear(s, GEARBOX_MAP) : undefined);
export const toBody = (s?: string) => (s ? mapear(s, BODY_MAP) : undefined);
export const toSeller = (s?: string) => (s ? mapear(s, SELLER_MAP) : undefined);

/**
 * Un numero de un texto de portal.
 * "24.500 €" -> 24500 | "1 234,5 km" -> 1234.5 | "€ 12,999" -> 12999
 */
export function toNumber(v: unknown): number | undefined {
  if (typeof v === "number") return Number.isFinite(v) ? v : undefined;
  if (typeof v !== "string") return undefined;

  const limpio = v.replace(/[^\d.,-]/g, "");
  if (!limpio) return undefined;

  const ultimaComa = limpio.lastIndexOf(",");
  const ultimoPunto = limpio.lastIndexOf(".");
  let normalizado: string;

  if (ultimaComa > ultimoPunto) {
    const decimales = limpio.length - ultimaComa - 1;
    // "12,999" es ambiguo: 12.999 en Europa, 12999 en ingles. En este dominio
    // tres decimales no significan nada (ni un precio ni unos km se dan con
    // milesimas), asi que con tres digitos detras y sin punto lo tratamos como
    // separador de miles. Se pierde el caso raro de "0,999"; merece la pena.
    normalizado =
      decimales === 3 && ultimoPunto < 0
        ? limpio.replace(/,/g, "")
        : limpio.replace(/\./g, "").replace(",", ".");
  } else if (ultimoPunto > ultimaComa) {
    // Puede ser 1,234.56 (ingles) o 1.234 (europeo sin decimales).
    const decimales = limpio.length - ultimoPunto - 1;
    normalizado = decimales === 3 && !limpio.includes(",")
      ? limpio.replace(/\./g, "")
      : limpio.replace(/,/g, "");
  } else {
    normalizado = limpio;
  }

  const n = Number(normalizado);
  return Number.isFinite(n) ? n : undefined;
}

export const kwACv = (kw: number) => Math.round(kw * 1.35962);
export const cvAKw = (cv: number) => Math.round(cv / 1.35962);

/** Potencia de un texto, venga en kW o en CV/PS/ch. */
export function toPower(s?: string): { cv?: number; kw?: number } {
  if (!s) return {};
  const kw = /(\d[\d.,]*)\s*kw/i.exec(s);
  const cv = /(\d[\d.,]*)\s*(cv|ps|hp|ch|pk)/i.exec(s);
  const nkw = kw ? toNumber(kw[1]) : undefined;
  const ncv = cv ? toNumber(cv[1]) : undefined;
  if (ncv) return { cv: Math.round(ncv), kw: cvAKw(ncv) };
  if (nkw) return { cv: kwACv(nkw), kw: Math.round(nkw) };
  return {};
}

/** Ano de matriculacion de formatos tipo "03/2019", "2019", "2019-03". */
export function toYear(s?: string): number | undefined {
  if (!s) return undefined;
  const m = /(19|20)\d{2}/.exec(s);
  const n = m ? Number(m[0]) : undefined;
  const max = new Date().getFullYear() + 2;
  return n && n >= 1900 && n <= max ? n : undefined;
}

export function toFirstRegistration(s?: string): string | undefined {
  if (!s) return undefined;
  const mes = /(\d{1,2})\s*[/.-]\s*((?:19|20)\d{2})/.exec(s);
  if (mes) {
    const m = Number(mes[1]);
    if (m >= 1 && m <= 12) return `${mes[2]}-${String(m).padStart(2, "0")}`;
  }
  const ano = toYear(s);
  return ano ? String(ano) : undefined;
}

const PAISES: Record<string, Country> = {
  de: "DE", deutschland: "DE", germany: "DE", alemania: "DE",
  fr: "FR", france: "FR", francia: "FR",
  it: "IT", italia: "IT", italy: "IT",
  nl: "NL", netherlands: "NL", nederland: "NL", holanda: "NL",
  be: "BE", belgium: "BE", belgique: "BE", belgica: "BE",
  at: "AT", austria: "AT", osterreich: "AT",
  pt: "PT", portugal: "PT",
  pl: "PL", poland: "PL", polska: "PL", polonia: "PL",
  lu: "LU", luxembourg: "LU", luxemburgo: "LU",
  es: "ES", spain: "ES", espana: "ES",
};

export function toCountry(s?: string): Country | undefined {
  if (!s) return undefined;
  return PAISES[sinAcentos(s).replace(/[^a-z]/g, "")];
}

/**
 * El mismo coche no se llama igual en cada mercado. Sin esto, buscar
 * "Serie 3" en un portal aleman no devuelve nada: alli es un "3er".
 */
const ALIAS: Record<string, Partial<Record<"de" | "fr" | "it" | "nl" | "pl" | "pt" | "es", string>>> = {
  "serie 1": { de: "1er" }, "serie 2": { de: "2er" }, "serie 3": { de: "3er" },
  "serie 4": { de: "4er" }, "serie 5": { de: "5er" }, "serie 6": { de: "6er" },
  "serie 7": { de: "7er" }, "serie 8": { de: "8er" },
  "clase a": { de: "A-Klasse", fr: "Classe A", it: "Classe A" },
  "clase b": { de: "B-Klasse", fr: "Classe B", it: "Classe B" },
  "clase c": { de: "C-Klasse", fr: "Classe C", it: "Classe C" },
  "clase e": { de: "E-Klasse", fr: "Classe E", it: "Classe E" },
  "clase s": { de: "S-Klasse", fr: "Classe S", it: "Classe S" },
  "clase v": { de: "V-Klasse", fr: "Classe V", it: "Classe V" },
  escarabajo: { de: "Beetle", fr: "Beetle", it: "Beetle" },
  "ibiza": {}, "leon": {}, "golf": {},
};

export type Lang = "de" | "fr" | "it" | "nl" | "pl" | "pt" | "es";

/** El modelo tal y como lo escriben en ese mercado. */
export function modelFor(model: string | undefined, lang: Lang): string {
  if (!model) return "";
  return ALIAS[sinAcentos(model)]?.[lang] ?? model;
}

export function queryText(
  q: { make?: string; model?: string; q?: string },
  lang: Lang = "es",
): string {
  if (q.q) return q.q;
  return [q.make, modelFor(q.model, lang)].filter(Boolean).join(" ").trim();
}

export function slug(s: string): string {
  return sinAcentos(s).replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}
