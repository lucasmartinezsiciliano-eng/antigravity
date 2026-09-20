/**
 * Adaptadores declarativos.
 *
 * Un adaptador de portal no es codigo: es un objeto que dice donde mirar. Eso
 * es lo que decide si un proyecto asi sobrevive. Cuando un portal cambie su
 * maquetacion —y lo hara— arreglarlo es editar tres selectores y mandar un
 * parche de seis lineas, no entender el motor entero.
 *
 * Tres estrategias, en orden de robustez:
 *
 *  1. `json-ld`       — schema.org en <script type="application/ld+json">.
 *                       Es dato estructurado que el portal publica a proposito
 *                       para Google. Cambia poquisimo y viene ya etiquetado.
 *  2. `embedded-json` — el estado que el portal deja en la pagina
 *                       (__NEXT_DATA__, __INITIAL_STATE__). Muy completo y
 *                       bastante estable.
 *  3. `selectors`     — CSS sobre el HTML. Lo ultimo, porque es lo primero
 *                       que se rompe.
 *
 * Se prueban en ese orden y vale la primera que devuelve algo.
 */

import * as cheerio from "cheerio";
import { toBody, toCountry, toFuel, toGearbox, toNumber, toPower, toSeller, toYear } from "../../normalize.ts";
import type { Listing, Query } from "../../schema.ts";
import { ProviderError, type Provider, type ProviderMeta, type ProviderContext } from "../types.ts";

/** De donde sale un campo cuando se usan selectores CSS. */
export interface Campo {
  sel?: string;
  /** Atributo en vez del texto. */
  attr?: string;
  /** Primer grupo de captura del regex sobre el texto. */
  re?: string;
  /** Valor fijo. */
  const?: string;
}

export interface Descriptor {
  meta: Omit<ProviderMeta, "compliance" | "enabledByDefault"> & { enabledByDefault?: boolean };
  /** La URL que se pide. Suele ser la misma que veria una persona. */
  url: (q: Query) => string;
  strategies: Strategy[];
}

export type Strategy =
  | { kind: "json-ld"; types?: string[] }
  | { kind: "embedded-json"; varName: string; path: string }
  | {
      kind: "selectors";
      item: string;
      fields: Partial<Record<CampoNombre, Campo>>;
    };

type CampoNombre =
  | "url" | "title" | "price" | "year" | "km" | "power" | "fuel" | "gearbox"
  | "body" | "city" | "country" | "seller" | "image" | "make" | "model" | "vin" | "co2";

// --- Estrategia 1: JSON-LD -------------------------------------------------

function extraerJsonLd(html: string, tipos: string[]): Record<string, unknown>[] {
  const $ = cheerio.load(html);
  const salida: Record<string, unknown>[] = [];

  $('script[type="application/ld+json"]').each((_, el) => {
    const txt = $(el).contents().text().trim();
    if (!txt) return;
    let data: unknown;
    try {
      data = JSON.parse(txt);
    } catch {
      return; // JSON-LD roto: lo saltamos sin hacer ruido
    }
    recorrer(data, tipos, salida);
  });
  return salida;
}

function recorrer(nodo: unknown, tipos: string[], salida: Record<string, unknown>[], hondo = 0) {
  if (hondo > 8 || !nodo) return;
  if (Array.isArray(nodo)) {
    for (const n of nodo) recorrer(n, tipos, salida, hondo + 1);
    return;
  }
  if (typeof nodo !== "object") return;

  const obj = nodo as Record<string, unknown>;
  const tipo = obj["@type"];
  const tipoStr = Array.isArray(tipo) ? tipo.join(" ") : String(tipo ?? "");
  if (tipos.some((t) => tipoStr.includes(t))) salida.push(obj);

  for (const v of Object.values(obj)) recorrer(v, tipos, salida, hondo + 1);
}

function desdeJsonLd(obj: Record<string, unknown>): Partial<Listing> {
  const g = (k: string) => obj[k];
  const oferta = (g("offers") ?? {}) as Record<string, unknown>;
  const precio = toNumber((oferta.price ?? oferta.lowPrice) as string);
  const motor = (g("vehicleEngine") ?? {}) as Record<string, unknown>;
  const potenciaObj = (motor.enginePower ?? {}) as Record<string, unknown>;
  const km = (g("mileageFromOdometer") ?? {}) as Record<string, unknown>;
  const direccion = ((oferta.availableAtOrFrom ?? g("location") ?? {}) as Record<string, unknown>)
    .address as Record<string, unknown> | undefined;

  const imagen = g("image");
  const imagenes = Array.isArray(imagen)
    ? imagen.map(String)
    : typeof imagen === "string"
      ? [imagen]
      : undefined;

  return {
    url: typeof g("url") === "string" ? (g("url") as string) : undefined,
    title: typeof g("name") === "string" ? (g("name") as string) : undefined,
    make: nombreDe(g("brand") ?? g("manufacturer")),
    model: nombreDe(g("model")),
    price: precio,
    priceCurrencyOriginal: typeof oferta.priceCurrency === "string" ? oferta.priceCurrency : undefined,
    year: toYear(String(g("vehicleModelDate") ?? g("productionDate") ?? g("releaseDate") ?? "")),
    km: toNumber((km.value ?? g("mileageFromOdometer")) as string),
    fuel: toFuel(String(g("fuelType") ?? motor.fuelType ?? "")),
    gearbox: toGearbox(String(g("vehicleTransmission") ?? "")),
    body: toBody(String(g("bodyType") ?? "")),
    doors: toNumber(g("numberOfDoors")),
    seats: toNumber(g("seatingCapacity") ?? g("vehicleSeatingCapacity")),
    color: typeof g("color") === "string" ? (g("color") as string) : undefined,
    vin: typeof g("vehicleIdentificationNumber") === "string"
      ? (g("vehicleIdentificationNumber") as string)
      : undefined,
    power: toNumber(potenciaObj.value) ? toPower(`${potenciaObj.value} ${potenciaObj.unitText ?? "kW"}`).cv : undefined,
    city: typeof direccion?.addressLocality === "string" ? direccion.addressLocality : undefined,
    postalCode: typeof direccion?.postalCode === "string" ? direccion.postalCode : undefined,
    country: toCountry(String(direccion?.addressCountry ?? "")),
    images: imagenes,
  };
}

function nombreDe(v: unknown): string | undefined {
  if (typeof v === "string") return v;
  if (v && typeof v === "object" && typeof (v as Record<string, unknown>).name === "string") {
    return (v as Record<string, string>).name;
  }
  return undefined;
}

// --- Estrategia 2: JSON incrustado ----------------------------------------

function extraerEmbebido(html: string, varName: string, path: string): Record<string, unknown>[] {
  // Busca  varName = {...}  o  <script id="varName">{...}</script>
  const patrones = [
    new RegExp(`${escapar(varName)}\\s*=\\s*(\\{[\\s\\S]*?\\})\\s*[;<]`),
    new RegExp(`id=["']${escapar(varName)}["'][^>]*>\\s*(\\{[\\s\\S]*?\\})\\s*<`),
  ];

  for (const re of patrones) {
    const m = re.exec(html);
    if (!m?.[1]) continue;
    try {
      const raiz = JSON.parse(m[1]) as unknown;
      const nodo = path.split(".").reduce<unknown>((acc, k) => {
        if (acc && typeof acc === "object") return (acc as Record<string, unknown>)[k];
        return undefined;
      }, raiz);
      if (Array.isArray(nodo)) return nodo as Record<string, unknown>[];
    } catch {
      continue;
    }
  }
  return [];
}

const escapar = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

// --- Estrategia 3: selectores CSS -----------------------------------------

function leerCampo($: cheerio.CheerioAPI, raiz: cheerio.Cheerio<never>, campo?: Campo): string | undefined {
  if (!campo) return undefined;
  if (campo.const) return campo.const;

  const nodo = campo.sel ? raiz.find(campo.sel).first() : raiz;
  if (!nodo.length) return undefined;

  let valor = campo.attr ? nodo.attr(campo.attr) : nodo.text();
  if (!valor) return undefined;
  valor = valor.replace(/\s+/g, " ").trim();

  if (campo.re) {
    const m = new RegExp(campo.re).exec(valor);
    valor = m?.[1] ?? m?.[0];
  }
  return valor || undefined;
}

function desdeSelectores(html: string, base: string, s: Extract<Strategy, { kind: "selectors" }>): Partial<Listing>[] {
  const $ = cheerio.load(html);
  const salida: Partial<Listing>[] = [];

  $(s.item).each((_, el) => {
    const raiz = $(el) as unknown as cheerio.Cheerio<never>;
    const f = (k: CampoNombre) => leerCampo($, raiz, s.fields[k]);

    const url = f("url");
    const potencia = toPower(f("power"));
    salida.push({
      url: url ? new URL(url, base).toString() : undefined,
      title: f("title"),
      make: f("make"),
      model: f("model"),
      price: toNumber(f("price")),
      year: toYear(f("year")),
      km: toNumber(f("km")),
      power: potencia.cv,
      powerKw: potencia.kw,
      co2: toNumber(f("co2")),
      fuel: toFuel(f("fuel")),
      gearbox: toGearbox(f("gearbox")),
      body: toBody(f("body")),
      seller: toSeller(f("seller")),
      city: f("city"),
      country: toCountry(f("country") ?? ""),
      vin: f("vin"),
      images: f("image") ? [new URL(f("image")!, base).toString()] : undefined,
    });
  });
  return salida;
}

// --- Montaje ---------------------------------------------------------------

/** Convierte un descriptor en un proveedor de verdad. */
export function fromDescriptor(d: Descriptor): Provider {
  const meta: ProviderMeta = {
    ...d.meta,
    compliance: "html",
    // Apagado salvo que quien despliega lo encienda: son condiciones de uso
    // de un tercero y esa decision no la toma el codigo.
    enabledByDefault: false,
  };

  return {
    meta,
    searchUrl: (q) => d.url(q),

    async search(q, ctx: ProviderContext) {
      const url = d.url(q);
      const res = await ctx.fetch(url, { rateLimitPerMin: meta.rateLimitPerMin ?? 10 } as RequestInit);

      if (res.status === 403 || res.status === 429) {
        throw new ProviderError(
          `el portal respondio ${res.status}: proteccion anti-bot o limite de ritmo`,
          "limite-alcanzado",
        );
      }
      if (!res.ok) throw new ProviderError(`HTTP ${res.status}`);

      const html = await res.text();
      const ahora = new Date().toISOString();

      for (const s of d.strategies) {
        let parciales: Partial<Listing>[] = [];

        if (s.kind === "json-ld") {
          parciales = extraerJsonLd(html, s.types ?? ["Car", "Vehicle", "Product"]).map(desdeJsonLd);
        } else if (s.kind === "embedded-json") {
          parciales = extraerEmbebido(html, s.varName, s.path).map(desdeJsonLd);
        } else {
          parciales = desdeSelectores(html, url, s);
        }

        const listings = parciales
          .filter((p) => p.url && p.title)
          .map((p, n): Listing => ({
            ...p,
            id: `${meta.id}:${idDe(p, n)}`,
            provider: meta.id,
            providerName: meta.name,
            url: p.url!,
            title: p.title!,
            country: p.country ?? meta.countries[0],
            seenAt: ahora,
            derived: {
              strategy: { value: s.kind, source: "html-adapter", confidence: "alta" },
            },
          }));

        if (listings.length) return { listings, message: `estrategia ${s.kind}` };
      }

      return {
        listings: [],
        status: "vacio" as const,
        message:
          "ninguna estrategia encontro anuncios: o la busqueda no tiene resultados, o el portal ha cambiado y hay que revisar el descriptor",
      };
    },
  };
}

/** Un id estable: el del portal si se puede sacar de la URL, si no la posicion. */
function idDe(p: Partial<Listing>, n: number): string {
  const m = /(\d{6,})/.exec(p.url ?? "");
  return m?.[1] ?? String(n);
}

export { extraerJsonLd, desdeJsonLd, extraerEmbebido, desdeSelectores };
