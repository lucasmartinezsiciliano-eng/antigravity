/**
 * eBay Browse API: la unica fuente grande con API oficial, publica y gratuita.
 *
 * Alta en developer.ebay.com -> credenciales de produccion -> EBAY_CLIENT_ID y
 * EBAY_CLIENT_SECRET. Sin ellas el proveedor se reporta como sin-credenciales
 * y la busqueda sigue con el resto.
 */

import { toFuel, toGearbox, toNumber, toPower, toYear, queryText } from "../normalize.ts";
import type { Country, Listing } from "../schema.ts";
import { ProviderError, type Provider } from "./types.ts";

const TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token";
const SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search";

/**
 * Categoria de COCHES por mercado.
 * Ojo: 9800 es "Auto & Motorrad: Fahrzeuge", que incluye motos. La de coches
 * en el mercado aleman es 9801.
 */
const CATEGORIA: Record<string, string> = {
  EBAY_DE: "9801",
  EBAY_FR: "9801",
  EBAY_IT: "9801",
  EBAY_ES: "9801",
  EBAY_GB: "9801",
  EBAY_US: "6001",
};

const MERCADO_PAIS: Record<string, Country> = {
  EBAY_DE: "DE", EBAY_FR: "FR", EBAY_IT: "IT", EBAY_ES: "ES",
};

let cache: { token: string; expira: number } | null = null;

async function token(env: Record<string, string | undefined>): Promise<string> {
  if (cache && cache.expira > Date.now() + 60_000) return cache.token;

  const basic = Buffer.from(`${env.EBAY_CLIENT_ID}:${env.EBAY_CLIENT_SECRET}`).toString("base64");
  const res = await fetch(TOKEN_URL, {
    method: "POST",
    headers: { authorization: `Basic ${basic}`, "content-type": "application/x-www-form-urlencoded" },
    body: "grant_type=client_credentials&scope=https%3A%2F%2Fapi.ebay.com%2Foauth%2Fapi_scope",
    signal: AbortSignal.timeout(10_000),
  });
  if (!res.ok) throw new ProviderError(`token ${res.status}`, "sin-credenciales");

  const data = (await res.json()) as { access_token: string; expires_in: number };
  cache = { token: data.access_token, expira: Date.now() + data.expires_in * 1000 };
  return cache.token;
}

interface ItemSummary {
  itemId: string;
  title: string;
  price?: { value: string; currency: string };
  itemWebUrl: string;
  image?: { imageUrl: string };
  thumbnailImages?: { imageUrl: string }[];
  itemLocation?: { country?: string; city?: string; postalCode?: string };
  seller?: { username?: string };
  itemCreationDate?: string;
  localizedAspects?: { name: string; value: string }[];
}

export const ebay: Provider = {
  meta: {
    id: "ebay",
    name: "eBay Motors",
    countries: ["DE", "FR", "IT", "ES"],
    compliance: "official-api",
    enabledByDefault: true,
    requiresEnv: ["EBAY_CLIENT_ID", "EBAY_CLIENT_SECRET"],
    host: "api.ebay.com",
    rateLimitPerMin: 60,
    docs: "https://developer.ebay.com/api-docs/buy/browse/overview.html",
    notes: "API oficial y gratuita. Inventario de coches modesto pero real, y con subastas.",
  },

  searchUrl(q) {
    const mercado = process.env.EBAY_MARKETPLACE ?? "EBAY_DE";
    const dominio = mercado.replace("EBAY_", "").toLowerCase();
    const sp = new URLSearchParams({ _nkw: queryText(q, "de") || "auto", _sacat: CATEGORIA[mercado] ?? "9801", _sop: "15" });
    if (q.priceFrom) sp.set("_udlo", String(q.priceFrom));
    if (q.priceTo) sp.set("_udhi", String(q.priceTo));
    return `https://www.ebay.${dominio === "gb" ? "co.uk" : dominio}/sch/i.html?${sp}`;
  },

  async search(q, ctx) {
    const mercado = ctx.env.EBAY_MARKETPLACE ?? "EBAY_DE";
    const acceso = await token(ctx.env);

    const filtros: string[] = [];
    if (q.priceFrom || q.priceTo) {
      filtros.push(`price:[${q.priceFrom ?? ""}..${q.priceTo ?? ""}]`, "priceCurrency:EUR");
    }

    const url =
      `${SEARCH_URL}?` +
      new URLSearchParams({
        q: queryText(q, "de") || "auto",
        category_ids: CATEGORIA[mercado] ?? "9801",
        limit: String(Math.min(q.limit ?? 50, 200)),
        sort: q.sort === "precio" ? "price" : "newlyListed",
        ...(filtros.length ? { filter: filtros.join(",") } : {}),
      });

    const res = await ctx.fetch(url, {
      headers: { authorization: `Bearer ${acceso}`, "X-EBAY-C-MARKETPLACE-ID": mercado },
    });
    if (!res.ok) throw new ProviderError(`HTTP ${res.status}`);

    const data = (await res.json()) as { itemSummaries?: ItemSummary[] };
    const ahora = new Date().toISOString();

    return (data.itemSummaries ?? []).map((it): Listing => {
      const aspectos = Object.fromEntries(
        (it.localizedAspects ?? []).map((a) => [a.name.toLowerCase(), a.value]),
      );
      const potencia = toPower(aspectos["leistung"] ?? aspectos["power"]);

      return {
        id: `ebay:${it.itemId}`,
        provider: "ebay",
        providerName: "eBay Motors",
        url: it.itemWebUrl,
        title: it.title,
        price: it.price ? toNumber(it.price.value) : undefined,
        priceCurrencyOriginal: it.price?.currency,
        make: aspectos["marke"] ?? aspectos["brand"],
        model: aspectos["modell"] ?? aspectos["model"],
        year: toYear(aspectos["baujahr"] ?? aspectos["year"] ?? ""),
        km: toNumber(aspectos["kilometerstand"] ?? aspectos["mileage"]),
        fuel: toFuel(aspectos["kraftstoffart"] ?? aspectos["fuel"]),
        gearbox: toGearbox(aspectos["getriebe"] ?? aspectos["transmission"]),
        power: potencia.cv,
        powerKw: potencia.kw,
        vin: aspectos["fahrzeugidentifikationsnummer"] ?? aspectos["vin"],
        country: MERCADO_PAIS[mercado] ?? "DE",
        city: it.itemLocation?.city,
        postalCode: it.itemLocation?.postalCode,
        sellerName: it.seller?.username,
        images: [it.image?.imageUrl, ...(it.thumbnailImages ?? []).map((i) => i.imageUrl)].filter(
          (x): x is string => Boolean(x),
        ),
        seenAt: ahora,
      };
    });
  },
};
