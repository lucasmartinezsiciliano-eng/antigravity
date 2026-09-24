import { NextResponse } from "next/server";
import { runSearch, DEFAULT_FILTERS } from "@/lib/search";
import type { CountryCode, SearchFilters } from "@/lib/types";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const PAISES: CountryCode[] = ["DE", "FR", "IT", "NL", "BE", "AT", "PT", "PL", "LU", "ES"];

/** Nunca confiamos en lo que llega del formulario. */
function parse(input: unknown): SearchFilters {
  const raw = (input ?? {}) as Record<string, unknown>;
  const num = (v: unknown, max = 10_000_000) => {
    const n = Number(v);
    return Number.isFinite(n) && n > 0 ? Math.min(Math.round(n), max) : undefined;
  };
  const str = (v: unknown, max = 40) => (typeof v === "string" ? v.trim().slice(0, max) : "");

  const countries = Array.isArray(raw.countries)
    ? (raw.countries.filter((c) => PAISES.includes(c as CountryCode)) as CountryCode[])
    : [];

  const sorts = ["coste-total", "precio", "km", "antiguedad"];
  const sort = sorts.includes(String(raw.sort))
    ? (raw.sort as SearchFilters["sort"])
    : DEFAULT_FILTERS.sort;

  return {
    make: str(raw.make),
    model: str(raw.model),
    yearFrom: num(raw.yearFrom, 2100),
    yearTo: num(raw.yearTo, 2100),
    priceFrom: num(raw.priceFrom),
    priceTo: num(raw.priceTo),
    kmTo: num(raw.kmTo, 2_000_000),
    powerFrom: num(raw.powerFrom, 2000),
    fuel: raw.fuel ? (raw.fuel as SearchFilters["fuel"]) : undefined,
    gearbox: raw.gearbox ? (raw.gearbox as SearchFilters["gearbox"]) : undefined,
    seller: raw.seller ? (raw.seller as SearchFilters["seller"]) : undefined,
    countries: countries.length ? countries : DEFAULT_FILTERS.countries,
    sort,
  };
}

export async function POST(req: Request) {
  let body: unknown = {};
  try {
    body = await req.json();
  } catch {
    /* body vacio: buscamos con los filtros por defecto */
  }
  const data = await runSearch(parse(body));
  return NextResponse.json(data);
}
