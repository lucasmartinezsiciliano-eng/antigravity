/**
 * Descriptores de portales.
 *
 * AVISO IMPORTANTE, Y VA EN SERIO: estos descriptores estan escritos sobre la
 * estructura habitual de cada portal, pero NO se han podido comprobar contra
 * las paginas reales (el entorno donde se escribieron tiene esos dominios
 * bloqueados). Antes de fiarte de ninguno, ejecutalo desde tu red:
 *
 *     npm run probe -- autoscout24-html --make BMW --model "Serie 3"
 *
 * El comando dice que estrategia entro, cuantos anuncios salieron y ensena el
 * primero, para que veas si los campos estan bien mapeados.
 *
 * Todos van APAGADOS por defecto. Encenderlos es una decision de quien
 * despliega, no del codigo: ver README, seccion "Postura legal".
 */

import { queryText, slug } from "../../normalize.ts";
import type { Country, Query } from "../../schema.ts";
import { fromDescriptor, type Descriptor } from "./engine.ts";
import type { Provider } from "../types.ts";

const AS24_COUNTRY: Partial<Record<Country, string>> = {
  AT: "A", BE: "B", DE: "D", ES: "E", FR: "F", IT: "I", LU: "L", NL: "NL",
};

function qs(params: Record<string, string | number | undefined>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== "") sp.set(k, String(v));
  return sp.toString() ? `?${sp}` : "";
}

const autoscout24: Descriptor = {
  meta: {
    id: "autoscout24-html",
    name: "AutoScout24 (lectura)",
    countries: ["DE", "FR", "IT", "NL", "BE", "AT", "LU", "ES"],
    host: "www.autoscout24.es",
    rateLimitPerMin: 6,
    notes: "El mayor inventario de Europa y el unico multipais. Descriptor SIN VERIFICAR.",
  },
  url: (q: Query) => {
    const path = q.make ? `/lst/${slug(q.make)}${q.model ? `/${slug(q.model)}` : ""}` : "/lst";
    const cy = (q.countries ?? []).map((c) => AS24_COUNTRY[c]).filter(Boolean).join(",");
    return (
      `https://www.autoscout24.es${path}` +
      qs({
        atype: "C",
        cy: cy || undefined,
        fregfrom: q.yearFrom,
        fregto: q.yearTo,
        pricefrom: q.priceFrom,
        priceto: q.priceTo,
        kmto: q.kmTo,
        sort: "price",
        desc: 0,
      })
    );
  },
  strategies: [
    // 1. AutoScout24 publica schema.org para Google. Es lo mas estable.
    { kind: "json-ld", types: ["Car", "Vehicle", "Product", "Offer"] },
    // 2. Es una app Next.js: el listado entero suele estar en __NEXT_DATA__.
    { kind: "embedded-json", varName: "__NEXT_DATA__", path: "props.pageProps.listings" },
    // 3. Ultimo recurso. Los atributos data-* aguantan mas que las clases,
    //    que llevan hash y cambian en cada despliegue.
    {
      kind: "selectors",
      item: "article[data-guid], article[data-testid='list-item']",
      fields: {
        url: { sel: "a[href*='/ofertas/'], a[href*='/angebote/'], a[href*='/offres/']", attr: "href" },
        title: { sel: "h2" },
        price: { sel: "[data-testid='regular-price'], p[class*='Price']" },
        km: { sel: "[data-testid='VehicleDetails-mileage_road']" },
        year: { sel: "[data-testid='VehicleDetails-calendar']" },
        gearbox: { sel: "[data-testid='VehicleDetails-transmission']" },
        fuel: { sel: "[data-testid='VehicleDetails-gas_pump']" },
        power: { sel: "[data-testid='VehicleDetails-speedometer']" },
        image: { sel: "img", attr: "src" },
        seller: { sel: "[class*='SellerInfo']" },
      },
    },
  ],
};

const mobileDe: Descriptor = {
  meta: {
    id: "mobile-de-html",
    name: "mobile.de (lectura)",
    countries: ["DE"],
    host: "suchen.mobile.de",
    rateLimitPerMin: 6,
    notes:
      "La referencia alemana. Tiene ademas una Search API oficial de partner (services.mobile.de/docs/search-api.html) que se pide a atencion al cliente: si te la dan, usa esa y desactiva este adaptador.",
  },
  url: (q: Query) =>
    "https://suchen.mobile.de/fahrzeuge/search.html" +
    qs({
      isSearchRequest: "true",
      vc: "Car",
      q: queryText(q, "de") || undefined,
      minPrice: q.priceFrom,
      maxPrice: q.priceTo,
      maxMileage: q.kmTo,
      minFirstRegistrationDate: q.yearFrom ? `${q.yearFrom}-01-01` : undefined,
      sb: "p",
      od: "up",
    }),
  strategies: [
    { kind: "json-ld", types: ["Car", "Vehicle", "Product"] },
    { kind: "embedded-json", varName: "__INITIAL_STATE__", path: "search.srp.data.searchResults.items" },
    {
      kind: "selectors",
      item: "[data-testid='result-list-item'], .cBox-body--resultitem",
      fields: {
        url: { sel: "a", attr: "href" },
        title: { sel: "[data-testid='listing-title'], .h3" },
        price: { sel: "[data-testid='price-label'], .h3.u-block" },
        km: { sel: "[data-testid='mileage']", re: "([\\d.,]+)" },
        year: { sel: "[data-testid='first-registration']" },
        image: { sel: "img", attr: "src" },
      },
    },
  ],
};

const descriptores: Descriptor[] = [autoscout24, mobileDe];

export const htmlProviders: Provider[] = descriptores.map(fromDescriptor);
export { descriptores };
