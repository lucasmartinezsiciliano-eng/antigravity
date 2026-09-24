/**
 * Portales de coches de segunda mano en Europa.
 *
 * Cada portal sabe construir la URL de su buscador con los filtros ya puestos.
 * Si algun portal cambia sus parametros, se arregla AQUI y en ningun sitio mas.
 *
 * Los que tienen `fetcher` ademas pueden devolver fichas para la lista
 * unificada (ver lib/adapters/). Los que no, se abren en una pestana.
 */

import type { CountryCode, Fuel, SearchFilters } from "./types";

export interface Portal {
  id: string;
  name: string;
  /** Paises donde tiene inventario relevante. */
  countries: CountryCode[];
  /** Cuantos anuncios mueve, en texto. Solo informativo. */
  hint: string;
  buildUrl: (f: SearchFilters) => string;
  /** Portales espanoles: sirven para comparar precio, no para importar. */
  reference?: boolean;
}

export const COUNTRIES: Record<CountryCode, { name: string; flag: string }> = {
  DE: { name: "Alemania", flag: "\u{1F1E9}\u{1F1EA}" },
  FR: { name: "Francia", flag: "\u{1F1EB}\u{1F1F7}" },
  IT: { name: "Italia", flag: "\u{1F1EE}\u{1F1F9}" },
  NL: { name: "Paises Bajos", flag: "\u{1F1F3}\u{1F1F1}" },
  BE: { name: "Belgica", flag: "\u{1F1E7}\u{1F1EA}" },
  AT: { name: "Austria", flag: "\u{1F1E6}\u{1F1F9}" },
  PT: { name: "Portugal", flag: "\u{1F1F5}\u{1F1F9}" },
  PL: { name: "Polonia", flag: "\u{1F1F5}\u{1F1F1}" },
  LU: { name: "Luxemburgo", flag: "\u{1F1F1}\u{1F1FA}" },
  ES: { name: "Espana", flag: "\u{1F1EA}\u{1F1F8}" },
};

// --- helpers ---------------------------------------------------------------

const slug = (s: string) =>
  s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");

const q = (f: SearchFilters) => [f.make, f.model].filter(Boolean).join(" ").trim();

/**
 * El mismo coche no se llama igual en cada pais. Sin esto, buscar "Serie 3"
 * en mobile.de no devuelve nada: alli es un "3er".
 */
const ALIAS: Record<string, { de?: string; fr?: string; it?: string }> = {
  "serie 1": { de: "1er" },
  "serie 2": { de: "2er" },
  "serie 3": { de: "3er" },
  "serie 4": { de: "4er" },
  "serie 5": { de: "5er" },
  "serie 6": { de: "6er" },
  "serie 7": { de: "7er" },
  "clase a": { de: "A-Klasse", fr: "Classe A", it: "Classe A" },
  "clase b": { de: "B-Klasse", fr: "Classe B", it: "Classe B" },
  "clase c": { de: "C-Klasse", fr: "Classe C", it: "Classe C" },
  "clase e": { de: "E-Klasse", fr: "Classe E", it: "Classe E" },
  "clase s": { de: "S-Klasse", fr: "Classe S", it: "Classe S" },
  "clase cla": { de: "CLA" },
  "clase gla": { de: "GLA" },
  "escarabajo": { de: "Beetle", fr: "Beetle" },
  "leon": { de: "Leon", fr: "Leon" },
};

/** Nombre del modelo tal y como lo escriben en ese pais. */
function modelFor(model: string, lang: "de" | "fr" | "it"): string {
  if (!model) return "";
  return ALIAS[model.toLowerCase().trim()]?.[lang] ?? model;
}

/** Texto de busqueda ya traducido al mercado de destino. */
function queryFor(f: SearchFilters, lang: "de" | "fr" | "it"): string {
  return [f.make, modelFor(f.model, lang)].filter(Boolean).join(" ").trim();
}


/** Anade parametros al querystring saltandose los vacios. */
function qs(params: Record<string, string | number | undefined | null>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

// --- AutoScout24 -----------------------------------------------------------
// El mas grande de Europa y el unico que ya busca en varios paises a la vez
// (parametro cy). Por eso es el portal por defecto.

const AS24_COUNTRY: Partial<Record<CountryCode, string>> = {
  AT: "A", BE: "B", DE: "D", ES: "E", FR: "F", IT: "I", LU: "L", NL: "NL",
};

const AS24_FUEL: Partial<Record<Fuel, string>> = {
  gasolina: "B",
  diesel: "D",
  electrico: "E",
  glp: "2",
  gnc: "3",
  hibrido: "2C",
  phev: "3C",
};

function autoscout24(tld: string, name: string, countries: CountryCode[]): Portal {
  return {
    id: `autoscout24-${tld.replace(".", "")}`,
    name,
    countries,
    hint: "~2,5M de anuncios, busca en varios paises de una vez",
    buildUrl: (f) => {
      const path = f.make
        ? `/lst/${slug(f.make)}${f.model ? `/${slug(f.model)}` : ""}`
        : "/lst";
      const cy = f.countries
        .map((c) => AS24_COUNTRY[c])
        .filter(Boolean)
        .join(",");
      return (
        `https://www.autoscout24.${tld}${path}` +
        qs({
          atype: "C",
          cy: cy || undefined,
          fregfrom: f.yearFrom,
          fregto: f.yearTo,
          pricefrom: f.priceFrom,
          priceto: f.priceTo,
          kmto: f.kmTo,
          powerfrom: f.powerFrom,
          powertype: f.powerFrom ? "hp" : undefined,
          fuel: f.fuel ? AS24_FUEL[f.fuel] : undefined,
          gear: f.gearbox === "manual" ? "M" : f.gearbox === "automatico" ? "A" : undefined,
          custtype: f.seller === "particular" ? "P" : f.seller === "profesional" ? "D" : undefined,
          ustate: "N,U",
          damaged_listing: "exclude",
          sort: "price",
          desc: 0,
        })
      );
    },
  };
}

// --- mobile.de -------------------------------------------------------------
// Referencia absoluta en Alemania. Filtra por texto libre (q) porque los ids
// internos de marca/modelo cambian y no merece la pena mantenerlos.

const MOBILE_FUEL: Partial<Record<Fuel, string>> = {
  gasolina: "PETROL",
  diesel: "DIESEL",
  electrico: "ELECTRICITY",
  hibrido: "HYBRID",
  phev: "HYBRID_PLUGIN",
  glp: "LPG",
  gnc: "CNG",
};

const mobileDe: Portal = {
  id: "mobile-de",
  name: "mobile.de",
  countries: ["DE"],
  hint: "~1,3M de anuncios, el rey en Alemania",
  buildUrl: (f) =>
    "https://suchen.mobile.de/fahrzeuge/search.html" +
    qs({
      isSearchRequest: "true",
      vc: "Car",
      dam: "false",
      q: queryFor(f, "de") || undefined,
      minPrice: f.priceFrom,
      maxPrice: f.priceTo,
      maxMileage: f.kmTo,
      minFirstRegistrationDate: f.yearFrom ? `${f.yearFrom}-01-01` : undefined,
      maxFirstRegistrationDate: f.yearTo ? `${f.yearTo}-12-31` : undefined,
      minPowerAsArray: f.powerFrom ? `${f.powerFrom}:PS` : undefined,
      fuels: f.fuel ? MOBILE_FUEL[f.fuel] : undefined,
      transmissions:
        f.gearbox === "manual" ? "MANUAL_GEAR" : f.gearbox === "automatico" ? "AUTOMATIC_GEAR" : undefined,
      sellerType: f.seller === "particular" ? "FSBO" : f.seller === "profesional" ? "DEALER" : undefined,
      damageUnrepaired: "NO_DAMAGE_UNREPAIRED",
      sb: "p",
      od: "up",
    }),
};

// --- Kleinanzeigen (antes eBay Kleinanzeigen) ------------------------------
// Donde publican los particulares alemanes. Precios mas bajos, mas riesgo.

const kleinanzeigen: Portal = {
  id: "kleinanzeigen",
  name: "Kleinanzeigen.de",
  countries: ["DE"],
  hint: "Particulares alemanes, precios por debajo de mobile.de",
  buildUrl: (f) => {
    const text = slug(queryFor(f, "de"));
    const price =
      f.priceFrom || f.priceTo ? `preis:${f.priceFrom ?? ""}:${f.priceTo ?? ""}/` : "";
    const seller = f.seller === "particular" ? "anbieter:privat/" : "";
    return `https://www.kleinanzeigen.de/s-autos/${seller}${price}${text ? text + "/" : ""}k0c216`;
  },
};

// --- Leboncoin -------------------------------------------------------------

const LBC_FUEL: Partial<Record<Fuel, string>> = {
  gasolina: "1",
  diesel: "2",
  glp: "3",
  electrico: "4",
  hibrido: "5",
  phev: "5",
};

const leboncoin: Portal = {
  id: "leboncoin",
  name: "Leboncoin",
  countries: ["FR"],
  hint: "El Wallapop frances: particulares y buenos precios",
  buildUrl: (f) =>
    "https://www.leboncoin.fr/recherche" +
    qs({
      category: 2,
      text: queryFor(f, "fr") || undefined,
      price: f.priceFrom || f.priceTo ? `${f.priceFrom ?? "min"}-${f.priceTo ?? "max"}` : undefined,
      regdate: f.yearFrom || f.yearTo ? `${f.yearFrom ?? "min"}-${f.yearTo ?? "max"}` : undefined,
      mileage: f.kmTo ? `min-${f.kmTo}` : undefined,
      fuel: f.fuel ? LBC_FUEL[f.fuel] : undefined,
      gearbox: f.gearbox === "manual" ? "1" : f.gearbox === "automatico" ? "2" : undefined,
      owner_type: f.seller === "particular" ? "private" : f.seller === "profesional" ? "pro" : undefined,
      sort: "price",
      order: "asc",
    }),
};

// --- La Centrale (FR) ------------------------------------------------------

const laCentrale: Portal = {
  id: "lacentrale",
  name: "La Centrale",
  countries: ["FR"],
  hint: "Profesionales franceses, fichas con historial",
  buildUrl: (f) =>
    "https://www.lacentrale.fr/listing" +
    qs({
      // La Centrale separa marca y modelo con ":" sin codificar.
      makesModelsCommercialNames: f.make
        ? `${f.make.toUpperCase()}${f.model ? `:${modelFor(f.model, "fr").toUpperCase()}` : ""}`
        : undefined,
      priceMin: f.priceFrom,
      priceMax: f.priceTo,
      yearMin: f.yearFrom,
      yearMax: f.yearTo,
      mileageMax: f.kmTo,
      energies:
        f.fuel === "diesel" ? "dies" : f.fuel === "gasolina" ? "ess" : f.fuel === "electrico" ? "elec" : undefined,
      gearbox: f.gearbox === "automatico" ? "AUTO" : f.gearbox === "manual" ? "MANUAL" : undefined,
      sortBy: "priceAsc",
    }),
};

// --- Italia ----------------------------------------------------------------

const subito: Portal = {
  id: "subito",
  name: "Subito.it",
  countries: ["IT"],
  hint: "Particulares italianos. Ojo al oxido en el norte",
  buildUrl: (f) =>
    "https://www.subito.it/annunci-italia/vendita/auto/" +
    qs({
      q: queryFor(f, "it") || undefined,
      ps: f.priceFrom,
      pe: f.priceTo,
      rs: f.yearFrom,
      re: f.yearTo,
      ks: undefined,
      ke: f.kmTo,
      order: "price",
    }),
};

// --- Paises Bajos / Belgica -----------------------------------------------

const marktplaats: Portal = {
  id: "marktplaats",
  name: "Marktplaats",
  countries: ["NL"],
  hint: "Holanda: coches muy cuidados, pocos km, sin sal en carretera",
  buildUrl: (f) => {
    const text = q(f);
    const base = text
      ? `https://www.marktplaats.nl/q/${encodeURIComponent(text)}/`
      : "https://www.marktplaats.nl/l/auto-s/";
    return (
      base +
      qs({
        categoryId: 91,
        priceFrom: f.priceFrom ? f.priceFrom * 100 : undefined,
        priceTo: f.priceTo ? f.priceTo * 100 : undefined,
        sortBy: "PRICE",
        sortOrder: "INCREASING",
      })
    );
  },
};

const gocar: Portal = {
  id: "2dehands",
  name: "2dehands.be",
  countries: ["BE"],
  hint: "Belgica: IVA recuperable en algunos profesionales",
  buildUrl: (f) => {
    const text = q(f);
    return (
      (text
        ? `https://www.2dehands.be/q/${encodeURIComponent(text)}/`
        : "https://www.2dehands.be/l/auto-s/") +
      qs({
        priceFrom: f.priceFrom ? f.priceFrom * 100 : undefined,
        priceTo: f.priceTo ? f.priceTo * 100 : undefined,
        sortBy: "PRICE",
        sortOrder: "INCREASING",
      })
    );
  },
};

// --- Polonia / Portugal ----------------------------------------------------

const otomoto: Portal = {
  id: "otomoto",
  name: "Otomoto",
  countries: ["PL"],
  hint: "Polonia: los mas baratos de Europa, pero revisa km y papeles",
  buildUrl: (f) => {
    const path = f.make ? `/osobowe/${slug(f.make)}${f.model ? `/${slug(f.model)}` : ""}` : "/osobowe";
    return (
      `https://www.otomoto.pl${path}` +
      qs({
        "search[filter_float_price:from]": f.priceFrom,
        "search[filter_float_price:to]": f.priceTo,
        "search[filter_float_year:from]": f.yearFrom,
        "search[filter_float_year:to]": f.yearTo,
        "search[filter_float_mileage:to]": f.kmTo,
        "search[order]": "filter_float_price:asc",
      })
    );
  },
};

const standvirtual: Portal = {
  id: "standvirtual",
  name: "Standvirtual",
  countries: ["PT"],
  hint: "Portugal: cerca, mismo idioma de tramites y sin barrera de km",
  buildUrl: (f) => {
    const path = f.make ? `/carros/${slug(f.make)}${f.model ? `/${slug(f.model)}` : ""}` : "/carros";
    return (
      `https://www.standvirtual.com${path}` +
      qs({
        "search[filter_float_price:from]": f.priceFrom,
        "search[filter_float_price:to]": f.priceTo,
        "search[filter_float_first_registration_year:from]": f.yearFrom,
        "search[filter_float_mileage:to]": f.kmTo,
        "search[order]": "filter_float_price:asc",
      })
    );
  },
};

// --- eBay ------------------------------------------------------------------

const ebay: Portal = {
  id: "ebay-de",
  name: "eBay Motors DE",
  countries: ["DE"],
  hint: "Subastas: chollos reales si sabes lo que compras",
  buildUrl: (f) =>
    "https://www.ebay.de/sch/i.html" +
    qs({
      _nkw: queryFor(f, "de") || "auto",
      _sacat: 9800,
      _udlo: f.priceFrom,
      _udhi: f.priceTo,
      _sop: 15,
    }),
};

// --- Referencia de precio en Espana ---------------------------------------

const cochesNet: Portal = {
  id: "coches-net",
  name: "Coches.net",
  countries: ["ES"],
  reference: true,
  hint: "Para comparar: cuanto cuesta el mismo coche aqui",
  buildUrl: (f) =>
    "https://www.coches.net/segunda-mano/" +
    qs({
      fi: q(f) || undefined,
      pf: f.priceFrom,
      pt: f.priceTo,
      ymf: f.yearFrom,
      ymt: f.yearTo,
      kmt: f.kmTo,
      orden: "precio-asc",
    }),
};

const milanuncios: Portal = {
  id: "milanuncios",
  name: "Milanuncios",
  countries: ["ES"],
  reference: true,
  hint: "Para comparar: precio real de particular en Espana",
  buildUrl: (f) =>
    "https://www.milanuncios.com/coches-de-segunda-mano/" +
    qs({
      s: q(f) || undefined,
      desde: f.priceFrom,
      hasta: f.priceTo,
      orden: "baratos",
    }),
};

export const PORTALS: Portal[] = [
  autoscout24("es", "AutoScout24", ["DE", "FR", "IT", "NL", "BE", "AT", "LU", "ES"]),
  mobileDe,
  kleinanzeigen,
  leboncoin,
  laCentrale,
  subito,
  marktplaats,
  gocar,
  otomoto,
  standvirtual,
  ebay,
  cochesNet,
  milanuncios,
];

/** Portales que tocan alguno de los paises elegidos. */
export function portalsFor(countries: CountryCode[]): Portal[] {
  return PORTALS.filter(
    (p) => p.reference || p.countries.some((c) => countries.includes(c)),
  );
}

export function getPortal(id: string): Portal | undefined {
  return PORTALS.find((p) => p.id === id);
}
