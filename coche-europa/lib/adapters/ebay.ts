/**
 * eBay Browse API: la unica fuente grande con API oficial, publica y gratuita.
 * Necesita darse de alta en developer.ebay.com y poner las claves en .env.
 */

import type { CountryCode, Listing, PortalResult, SearchFilters } from "../types";

const TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token";
const SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search";
const CATEGORIA_COCHES = "9800";

let cachedToken: { value: string; expires: number } | null = null;

export function ebayEnabled(): boolean {
  return Boolean(process.env.EBAY_CLIENT_ID && process.env.EBAY_CLIENT_SECRET);
}

async function getToken(): Promise<string | null> {
  if (cachedToken && cachedToken.expires > Date.now() + 60_000) return cachedToken.value;

  const basic = Buffer.from(
    `${process.env.EBAY_CLIENT_ID}:${process.env.EBAY_CLIENT_SECRET}`,
  ).toString("base64");

  const res = await fetch(TOKEN_URL, {
    method: "POST",
    headers: {
      authorization: `Basic ${basic}`,
      "content-type": "application/x-www-form-urlencoded",
    },
    body: "grant_type=client_credentials&scope=https%3A%2F%2Fapi.ebay.com%2Foauth%2Fapi_scope",
    cache: "no-store",
  });
  if (!res.ok) return null;

  const data = (await res.json()) as { access_token: string; expires_in: number };
  cachedToken = {
    value: data.access_token,
    expires: Date.now() + data.expires_in * 1000,
  };
  return cachedToken.value;
}

export async function fetchEbay(f: SearchFilters): Promise<PortalResult | null> {
  if (!ebayEnabled()) return null;
  const started = Date.now();

  try {
    const token = await getToken();
    if (!token) throw new Error("sin token");

    const filtros: string[] = [];
    if (f.priceFrom || f.priceTo) {
      filtros.push(`price:[${f.priceFrom ?? ""}..${f.priceTo ?? ""}]`, "priceCurrency:EUR");
    }

    const url =
      `${SEARCH_URL}?` +
      new URLSearchParams({
        q: [f.make, f.model].filter(Boolean).join(" ") || "auto",
        category_ids: CATEGORIA_COCHES,
        limit: "50",
        sort: "price",
        ...(filtros.length ? { filter: filtros.join(",") } : {}),
      });

    const res = await fetch(url, {
      headers: {
        authorization: `Bearer ${token}`,
        "X-EBAY-C-MARKETPLACE-ID": process.env.EBAY_MARKETPLACE || "EBAY_DE",
      },
      cache: "no-store",
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = (await res.json()) as {
      itemSummaries?: {
        itemId: string;
        title: string;
        price?: { value: string };
        itemWebUrl: string;
        image?: { imageUrl: string };
        itemLocation?: { country?: string; city?: string };
      }[];
    };

    const listings: Listing[] = (data.itemSummaries ?? []).map((it) => ({
      id: `ebay_${it.itemId}`,
      source: "ebay-de",
      sourceName: "eBay Motors",
      title: it.title,
      price: Number(it.price?.value ?? 0),
      country: (it.itemLocation?.country as CountryCode) ?? "DE",
      city: it.itemLocation?.city,
      url: it.itemWebUrl,
      image: it.image?.imageUrl,
    }));

    return {
      portal: "ebay-de",
      name: "eBay Motors",
      countries: ["DE"],
      searchUrl: "",
      mode: "live",
      listings,
      ms: Date.now() - started,
    };
  } catch (e) {
    return {
      portal: "ebay-de",
      name: "eBay Motors",
      countries: ["DE"],
      searchUrl: "",
      mode: "error",
      listings: [],
      note: e instanceof Error ? e.message : "error",
      ms: Date.now() - started,
    };
  }
}
