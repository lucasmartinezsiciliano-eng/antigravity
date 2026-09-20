/**
 * Proveedores de solo enlace.
 *
 * No descargan nada: traducen la consulta a la URL de busqueda del portal.
 * Es exactamente lo que hace un navegador cuando rellenas su formulario, asi
 * que no hay nada que discutir ni por condiciones de uso ni por robots.txt.
 *
 * Funcionan SIEMPRE, sin credenciales y sin riesgo. Son el suelo del
 * proyecto: pase lo que pase con el resto de adaptadores, esto sigue de pie.
 *
 * Si un portal cambia sus parametros, se arregla en este fichero y en ninguno
 * mas.
 */

import { modelFor, queryText, slug, type Lang } from "../normalize.ts";
import type { Country, Fuel, Gearbox, Query } from "../schema.ts";
import type { Provider, ProviderMeta } from "./types.ts";

function qs(params: Record<string, string | number | undefined | null>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

const uno = <T>(v: T[] | undefined): T | undefined => (v?.length === 1 ? v[0] : undefined);

// --- AutoScout24 -----------------------------------------------------------
// El unico que busca en varios paises a la vez con un solo parametro.

const AS24_COUNTRY: Partial<Record<Country, string>> = {
  AT: "A", BE: "B", DE: "D", ES: "E", FR: "F", IT: "I", LU: "L", NL: "NL",
};
const AS24_FUEL: Partial<Record<Fuel, string>> = {
  gasolina: "B", diesel: "D", electrico: "E", glp: "2", gnc: "3", hibrido: "2C", phev: "3C",
};

function autoscout24(tld: string, countries: Country[]): Provider {
  const meta: ProviderMeta = {
    id: `autoscout24-${tld.replace(/\./g, "")}`,
    name: "AutoScout24",
    countries,
    compliance: "deeplink",
    enabledByDefault: true,
    host: `www.autoscout24.${tld}`,
    notes: "~2,5M de anuncios. El unico que cubre varios paises en una sola busqueda.",
  };
  return {
    meta,
    searchUrl(q) {
      const path = q.make ? `/lst/${slug(q.make)}${q.model ? `/${slug(q.model)}` : ""}` : "/lst";
      const cy = (q.countries ?? []).map((c) => AS24_COUNTRY[c]).filter(Boolean).join(",");
      const fuel = uno(q.fuel);
      const gear = uno(q.gearbox);
      return (
        `https://www.autoscout24.${tld}${path}` +
        qs({
          atype: "C",
          cy: cy || undefined,
          fregfrom: q.yearFrom,
          fregto: q.yearTo,
          pricefrom: q.priceFrom,
          priceto: q.priceTo,
          kmfrom: q.kmFrom,
          kmto: q.kmTo,
          powerfrom: q.powerFrom,
          powertype: q.powerFrom ? "hp" : undefined,
          fuel: fuel ? AS24_FUEL[fuel] : undefined,
          gear: gear === "manual" ? "M" : gear === "automatico" ? "A" : undefined,
          custtype: q.seller === "particular" ? "P" : q.seller === "profesional" ? "D" : undefined,
          ustate: "N,U",
          damaged_listing: "exclude",
          sort: "price",
          desc: 0,
        })
      );
    },
  };
}

// --- Resto de portales -----------------------------------------------------

interface Simple {
  id: string;
  name: string;
  countries: Country[];
  lang: Lang;
  notes: string;
  url: (q: Query, texto: string) => string;
}

const MOBILE_FUEL: Partial<Record<Fuel, string>> = {
  gasolina: "PETROL", diesel: "DIESEL", electrico: "ELECTRICITY",
  hibrido: "HYBRID", phev: "HYBRID_PLUGIN", glp: "LPG", gnc: "CNG",
};
const LBC_FUEL: Partial<Record<Fuel, string>> = {
  gasolina: "1", diesel: "2", glp: "3", electrico: "4", hibrido: "5", phev: "5",
};

const SIMPLES: Simple[] = [
  {
    id: "mobile-de",
    name: "mobile.de",
    countries: ["DE"],
    lang: "de",
    notes: "~1,3M de anuncios. La referencia en Alemania.",
    url: (q, texto) =>
      "https://suchen.mobile.de/fahrzeuge/search.html" +
      qs({
        isSearchRequest: "true",
        vc: "Car",
        dam: "false",
        q: texto || undefined,
        minPrice: q.priceFrom,
        maxPrice: q.priceTo,
        maxMileage: q.kmTo,
        minMileage: q.kmFrom,
        minFirstRegistrationDate: q.yearFrom ? `${q.yearFrom}-01-01` : undefined,
        maxFirstRegistrationDate: q.yearTo ? `${q.yearTo}-12-31` : undefined,
        minPowerAsArray: q.powerFrom ? `${q.powerFrom}:PS` : undefined,
        fuels: uno(q.fuel) ? MOBILE_FUEL[uno(q.fuel)!] : undefined,
        transmissions:
          uno(q.gearbox) === "manual" ? "MANUAL_GEAR"
          : uno(q.gearbox) === "automatico" ? "AUTOMATIC_GEAR" : undefined,
        sellerType: q.seller === "particular" ? "FSBO" : q.seller === "profesional" ? "DEALER" : undefined,
        damageUnrepaired: "NO_DAMAGE_UNREPAIRED",
        sb: "p",
        od: "up",
      }),
  },
  {
    id: "kleinanzeigen",
    name: "Kleinanzeigen.de",
    countries: ["DE"],
    lang: "de",
    notes: "Particulares alemanes. Mas barato y mas riesgo que mobile.de.",
    url: (q, texto) => {
      const precio = q.priceFrom || q.priceTo ? `preis:${q.priceFrom ?? ""}:${q.priceTo ?? ""}/` : "";
      const vendedor = q.seller === "particular" ? "anbieter:privat/" : "";
      const t = slug(texto);
      return `https://www.kleinanzeigen.de/s-autos/${vendedor}${precio}${t ? t + "/" : ""}k0c216`;
    },
  },
  {
    id: "leboncoin",
    name: "Leboncoin",
    countries: ["FR"],
    lang: "fr",
    notes: "El Wallapop frances: particulares y buenos precios.",
    url: (q, texto) =>
      "https://www.leboncoin.fr/recherche" +
      qs({
        category: 2,
        text: texto || undefined,
        price: q.priceFrom || q.priceTo ? `${q.priceFrom ?? "min"}-${q.priceTo ?? "max"}` : undefined,
        regdate: q.yearFrom || q.yearTo ? `${q.yearFrom ?? "min"}-${q.yearTo ?? "max"}` : undefined,
        mileage: q.kmTo ? `${q.kmFrom ?? "min"}-${q.kmTo}` : undefined,
        fuel: uno(q.fuel) ? LBC_FUEL[uno(q.fuel)!] : undefined,
        gearbox: uno(q.gearbox) === "manual" ? "1" : uno(q.gearbox) === "automatico" ? "2" : undefined,
        owner_type: q.seller === "particular" ? "private" : q.seller === "profesional" ? "pro" : undefined,
        sort: "price",
        order: "asc",
      }),
  },
  {
    id: "lacentrale",
    name: "La Centrale",
    countries: ["FR"],
    lang: "fr",
    notes: "Profesionales franceses, fichas con historial.",
    url: (q) =>
      "https://www.lacentrale.fr/listing" +
      qs({
        makesModelsCommercialNames: q.make
          ? `${q.make.toUpperCase()}${q.model ? `:${modelFor(q.model, "fr").toUpperCase()}` : ""}`
          : undefined,
        priceMin: q.priceFrom,
        priceMax: q.priceTo,
        yearMin: q.yearFrom,
        yearMax: q.yearTo,
        mileageMax: q.kmTo,
        energies:
          uno(q.fuel) === "diesel" ? "dies"
          : uno(q.fuel) === "gasolina" ? "ess"
          : uno(q.fuel) === "electrico" ? "elec" : undefined,
        gearbox:
          uno(q.gearbox) === "automatico" ? "AUTO"
          : uno(q.gearbox) === "manual" ? "MANUAL" : undefined,
        sortBy: "priceAsc",
      }),
  },
  {
    id: "subito",
    name: "Subito.it",
    countries: ["IT"],
    lang: "it",
    notes: "Particulares italianos. Ojo al oxido en el norte.",
    url: (q, texto) =>
      "https://www.subito.it/annunci-italia/vendita/auto/" +
      qs({ q: texto || undefined, ps: q.priceFrom, pe: q.priceTo, rs: q.yearFrom, re: q.yearTo, ke: q.kmTo, order: "price" }),
  },
  {
    id: "marktplaats",
    name: "Marktplaats",
    countries: ["NL"],
    lang: "nl",
    notes: "Holanda: coches cuidados y el mejor registro publico de Europa (RDW).",
    url: (q, texto) =>
      (texto ? `https://www.marktplaats.nl/q/${encodeURIComponent(texto)}/` : "https://www.marktplaats.nl/l/auto-s/") +
      qs({
        categoryId: 91,
        priceFrom: q.priceFrom ? q.priceFrom * 100 : undefined,
        priceTo: q.priceTo ? q.priceTo * 100 : undefined,
        sortBy: "PRICE",
        sortOrder: "INCREASING",
      }),
  },
  {
    id: "2dehands",
    name: "2dehands.be",
    countries: ["BE"],
    lang: "nl",
    notes: "Belgica. Car-Pass obligatorio por ley en toda venta.",
    url: (q, texto) =>
      (texto ? `https://www.2dehands.be/q/${encodeURIComponent(texto)}/` : "https://www.2dehands.be/l/auto-s/") +
      qs({
        priceFrom: q.priceFrom ? q.priceFrom * 100 : undefined,
        priceTo: q.priceTo ? q.priceTo * 100 : undefined,
        sortBy: "PRICE",
        sortOrder: "INCREASING",
      }),
  },
  {
    id: "otomoto",
    name: "Otomoto",
    countries: ["PL"],
    lang: "pl",
    notes: "Polonia: los mas baratos, pero 62% con siniestro registrado.",
    url: (q) => {
      const path = q.make ? `/osobowe/${slug(q.make)}${q.model ? `/${slug(q.model)}` : ""}` : "/osobowe";
      return (
        `https://www.otomoto.pl${path}` +
        qs({
          "search[filter_float_price:from]": q.priceFrom,
          "search[filter_float_price:to]": q.priceTo,
          "search[filter_float_year:from]": q.yearFrom,
          "search[filter_float_year:to]": q.yearTo,
          "search[filter_float_mileage:to]": q.kmTo,
          "search[order]": "filter_float_price:asc",
        })
      );
    },
  },
  {
    id: "standvirtual",
    name: "Standvirtual",
    countries: ["PT"],
    lang: "pt",
    notes: "Portugal: cerca y sin barrera de idioma en los tramites.",
    url: (q) => {
      const path = q.make ? `/carros/${slug(q.make)}${q.model ? `/${slug(q.model)}` : ""}` : "/carros";
      return (
        `https://www.standvirtual.com${path}` +
        qs({
          "search[filter_float_price:from]": q.priceFrom,
          "search[filter_float_price:to]": q.priceTo,
          "search[filter_float_first_registration_year:from]": q.yearFrom,
          "search[filter_float_mileage:to]": q.kmTo,
          "search[order]": "filter_float_price:asc",
        })
      );
    },
  },
  {
    id: "coches-net",
    name: "Coches.net",
    countries: ["ES"],
    lang: "es",
    notes: "Referencia de precio en Espana: para saber si de verdad compensa importar.",
    url: (q, texto) =>
      "https://www.coches.net/segunda-mano/" +
      qs({ fi: texto || undefined, pf: q.priceFrom, pt: q.priceTo, ymf: q.yearFrom, ymt: q.yearTo, kmt: q.kmTo, orden: "precio-asc" }),
  },
  {
    id: "milanuncios",
    name: "Milanuncios",
    countries: ["ES"],
    lang: "es",
    notes: "Referencia de precio de particular en Espana.",
    url: (q, texto) =>
      "https://www.milanuncios.com/coches-de-segunda-mano/" +
      qs({ s: texto || undefined, desde: q.priceFrom, hasta: q.priceTo, orden: "baratos" }),
  },
];

function simple(s: Simple): Provider {
  return {
    meta: {
      id: s.id,
      name: s.name,
      countries: s.countries,
      compliance: "deeplink",
      enabledByDefault: true,
      notes: s.notes,
    },
    searchUrl: (q) => s.url(q, queryText(q, s.lang)),
  };
}

export const deeplinkProviders: Provider[] = [
  autoscout24("es", ["DE", "FR", "IT", "NL", "BE", "AT", "LU", "ES"]),
  ...SIMPLES.map(simple),
];
