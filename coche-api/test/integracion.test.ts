/**
 * Los adaptadores, ejecutados de verdad.
 *
 * Hasta aqui solo se habian probado las funciones de extraccion con cadenas de
 * texto. Esto pasa el circuito entero: fetcher real, robots.txt real, peticion
 * HTTP real y motor real, contra un portal de mentira que se comporta como los
 * de verdad (incluido devolver 403 cuando le da por ahi).
 */

import { test } from "node:test";
import assert from "node:assert/strict";
import { levantarPortal } from "./portal-falso.ts";
import { Fetcher } from "../src/http/fetcher.ts";
import { fromDescriptor } from "../src/providers/html/engine.ts";
import { ebay, olvidarTokens } from "../src/providers/ebay.ts";
import { search } from "../src/engine.ts";
import { parseQuery } from "../src/schema.ts";
import type { Provider } from "../src/providers/types.ts";

const UA = "coche-api/test (+https://ejemplo/contacto)";
const nuevoFetcher = (ignoreRobots = false) =>
  new Fetcher({ userAgent: UA, ignoreRobots, cacheTtlMs: 60_000 });

function descriptor(base: string, ruta: string): Provider {
  return fromDescriptor({
    meta: { id: "falso", name: "Portal Falso", countries: ["DE"], rateLimitPerMin: 600 },
    url: () => base + ruta,
    strategies: [
      { kind: "json-ld", types: ["Car", "Vehicle"] },
      {
        kind: "selectors",
        item: "article[data-guid]",
        fields: {
          url: { sel: "a", attr: "href" },
          title: { sel: "h2" },
          price: { sel: "[data-testid='regular-price']" },
          km: { sel: "[data-testid='VehicleDetails-mileage_road']" },
          year: { sel: "[data-testid='VehicleDetails-calendar']" },
          fuel: { sel: "[data-testid='VehicleDetails-gas_pump']" },
          gearbox: { sel: "[data-testid='VehicleDetails-transmission']" },
          power: { sel: "[data-testid='VehicleDetails-speedometer']" },
          image: { sel: "img", attr: "src" },
        },
      },
    ],
  });
}

const consulta = (extra = {}) => parseQuery({ make: "BMW", model: "Serie 3", ...extra }).query;

async function correr(p: Provider, base: string, opts: { ignoreRobots?: boolean; timeout?: number; env?: Record<string, string | undefined> } = {}) {
  const r = await search([p], consulta(), [], {
    fetcher: nuevoFetcher(opts.ignoreRobots),
    providerTimeoutMs: opts.timeout ?? 8000,
    env: opts.env ?? {},
  });
  void base;
  return r;
}

// ── adaptador de HTML, circuito completo ────────────────────────────────────

test("un anuncio real pasa de HTML a esquema normalizado", async () => {
  const portal = await levantarPortal();
  try {
    const r = await correr(descriptor(portal.base, "/lst/bmw"), portal.base);

    assert.equal(r.providers[0]!.status, "ok");
    assert.equal(r.listings.length, 2);
    assert.match(r.providers[0]!.message ?? "", /json-ld/);

    const l = r.listings.find((x) => x.title.includes("Touring"))!;
    assert.equal(l.price, 24500, "el precio venia como '24.500' en formato aleman");
    assert.equal(l.km, 95000);
    assert.equal(l.year, 2019);
    assert.equal(l.power, 190, "140 kW convertidos a CV");
    assert.equal(l.fuel, "diesel");
    assert.equal(l.gearbox, "automatico", "'Automatik' traducido");
    assert.equal(l.country, "DE");
    assert.equal(l.city, "Munchen");
    assert.equal(l.vin, "WBA8E51070K123456");
    assert.ok(l.url.startsWith(portal.base), "la URL relativa se resolvio contra la pagina");
    assert.equal(l.provider, "falso");
    assert.ok(l.seenAt);

    // El segundo trae 'Schaltgetriebe', que es la otra rama del diccionario.
    assert.equal(r.listings.find((x) => x.title.includes("Advantage"))!.gearbox, "manual");
  } finally {
    await portal.cierra();
  }
});

test("sin JSON-LD cae a los selectores y lo dice", async () => {
  const portal = await levantarPortal();
  try {
    const r = await correr(descriptor(portal.base, "/solo-html"), portal.base);
    assert.equal(r.providers[0]!.status, "ok");
    assert.match(r.providers[0]!.message ?? "", /selectors/);

    const l = r.listings[0]!;
    assert.equal(l.title, "Audi A4 Avant 2.0 TDI");
    assert.equal(l.price, 21750);
    assert.equal(l.km, 88000);
    assert.equal(l.year, 2020);
    assert.equal(l.power, 190);
  } finally {
    await portal.cierra();
  }
});

test("una pagina sin anuncios no es un error, es 'vacio'", async () => {
  const portal = await levantarPortal();
  try {
    const r = await correr(descriptor(portal.base, "/vacio"), portal.base);
    assert.equal(r.providers[0]!.status, "vacio");
    assert.match(r.providers[0]!.message ?? "", /ha cambiado|no tiene resultados/);
  } finally {
    await portal.cierra();
  }
});

// ── portarse bien ───────────────────────────────────────────────────────────

test("robots.txt manda: una ruta prohibida no se pide siquiera", async () => {
  const portal = await levantarPortal({ robots: "User-agent: *\nDisallow: /privado\n" });
  try {
    const r = await correr(descriptor(portal.base, "/privado/lst"), portal.base);
    assert.equal(r.providers[0]!.status, "bloqueado-robots");
    assert.ok(portal.peticiones.includes("/robots.txt"), "se leyo robots.txt");
    assert.ok(!portal.peticiones.some((p) => p.startsWith("/privado")), "y no se pidio la pagina");
  } finally {
    await portal.cierra();
  }
});

test("un robots.txt que nos nombra a nosotros tambien manda", async () => {
  const portal = await levantarPortal({ robots: "User-agent: *\nDisallow:\n\nUser-agent: coche-api\nDisallow: /\n" });
  try {
    const r = await correr(descriptor(portal.base, "/lst"), portal.base);
    assert.equal(r.providers[0]!.status, "bloqueado-robots");
  } finally {
    await portal.cierra();
  }
});

test("sin robots.txt (404) se entiende que todo esta permitido", async () => {
  const portal = await levantarPortal({ robots: null });
  try {
    const r = await correr(descriptor(portal.base, "/lst"), portal.base);
    assert.equal(r.providers[0]!.status, "ok");
  } finally {
    await portal.cierra();
  }
});

test("IGNORE_ROBOTS se salta la prohibicion (y es decision de quien despliega)", async () => {
  const portal = await levantarPortal({ robots: "User-agent: *\nDisallow: /\n" });
  try {
    const r = await correr(descriptor(portal.base, "/lst"), portal.base, { ignoreRobots: true });
    assert.equal(r.providers[0]!.status, "ok");
  } finally {
    await portal.cierra();
  }
});

test("la cache evita pedir dos veces lo mismo en la misma sesion", async () => {
  const portal = await levantarPortal();
  const fetcher = nuevoFetcher();
  const p = descriptor(portal.base, "/lst");
  try {
    for (let i = 0; i < 3; i++) {
      await search([p], consulta(), [], { fetcher, providerTimeoutMs: 8000, env: {} });
    }
    const lst = portal.peticiones.filter((x) => x.startsWith("/lst"));
    assert.equal(lst.length, 1, `se pidio ${lst.length} veces en vez de una`);
    assert.equal(portal.peticiones.filter((x) => x === "/robots.txt").length, 1);
  } finally {
    await portal.cierra();
  }
});

// ── fallos ──────────────────────────────────────────────────────────────────

test("un 403 anti-bot se reporta como limite alcanzado, no como error generico", async () => {
  const portal = await levantarPortal();
  try {
    const r = await correr(descriptor(portal.base, "/antibot"), portal.base);
    assert.equal(r.providers[0]!.status, "limite-alcanzado");
    assert.match(r.providers[0]!.message ?? "", /anti-bot|403/);
  } finally {
    await portal.cierra();
  }
});

test("un portal lento no bloquea la respuesta", async () => {
  const portal = await levantarPortal({ retraso: 5000 });
  try {
    const t0 = Date.now();
    const r = await correr(descriptor(portal.base, "/lento"), portal.base, { timeout: 600 });
    assert.equal(r.providers[0]!.status, "timeout");
    assert.ok(Date.now() - t0 < 3000, "la busqueda espero al portal lento");
  } finally {
    await portal.cierra();
  }
});

test("un proveedor que revienta no tumba a los demas", async () => {
  const portal = await levantarPortal();
  const roto: Provider = {
    meta: { id: "roto", name: "Roto", countries: ["DE"], compliance: "html", enabledByDefault: false },
    searchUrl: () => "http://roto.invalido/x",
    search: async () => {
      throw new Error("explota");
    },
  };
  try {
    const r = await search([roto, descriptor(portal.base, "/lst")], consulta(), [], {
      fetcher: nuevoFetcher(),
      providerTimeoutMs: 5000,
      env: {},
    });
    assert.equal(r.providers.find((p) => p.provider === "roto")!.status, "error");
    assert.equal(r.providers.find((p) => p.provider === "falso")!.status, "ok");
    assert.equal(r.listings.length, 2, "los anuncios del que funciona siguen llegando");
  } finally {
    await portal.cierra();
  }
});

// ── eBay, con su API de mentira ─────────────────────────────────────────────

test("eBay: OAuth, busqueda y mapeo de aspectos alemanes", async () => {
  olvidarTokens();
  const portal = await levantarPortal({ robots: null });
  const env = {
    EBAY_CLIENT_ID: "cliente-bueno",
    EBAY_CLIENT_SECRET: "secreto-bueno",
    EBAY_MARKETPLACE: "EBAY_DE",
    EBAY_API_BASE: portal.base,
  };
  try {
    const r = await correr(ebay, portal.base, { env });
    assert.equal(r.providers[0]!.status, "ok");

    const l = r.listings[0]!;
    assert.equal(l.provider, "ebay");
    assert.equal(l.price, 23450);
    assert.equal(l.make, "BMW", "leido del aspecto 'Marke'");
    assert.equal(l.km, 112500, "'112.500' en formato aleman");
    assert.equal(l.year, 2018);
    assert.equal(l.fuel, "diesel");
    assert.equal(l.gearbox, "automatico");
    assert.equal(l.power, 190, "140 kW a CV");
    assert.equal(l.city, "Hamburg");
    assert.ok(l.title.includes("EBAY_DE"), "la cabecera de mercado llego al servidor");
    assert.ok(l.images!.length > 0);
  } finally {
    await portal.cierra();
  }
});

test("eBay: la categoria que se pide es la de coches, no la que incluye motos", async () => {
  olvidarTokens();
  const portal = await levantarPortal({ robots: null });
  const peticiones: string[] = [];
  const fetcher = nuevoFetcher();
  const original = fetcher.fetch.bind(fetcher);
  fetcher.fetch = (url, init) => {
    peticiones.push(url);
    return original(url, init);
  };
  try {
    await search([ebay], consulta(), [], {
      fetcher,
      providerTimeoutMs: 8000,
      env: { EBAY_CLIENT_ID: "cliente-bueno", EBAY_CLIENT_SECRET: "secreto-bueno", EBAY_API_BASE: portal.base },
    });
    const busqueda = peticiones.find((u) => u.includes("item_summary"))!;
    assert.match(busqueda, /category_ids=9801/, "9800 incluye motos; coches es 9801");
    // URLSearchParams codifica el espacio como "+", que decodeURIComponent no deshace.
    assert.match(decodeURIComponent(busqueda).replace(/\+/g, " "), /BMW 3er/, "el modelo se tradujo al mercado aleman");
  } finally {
    await portal.cierra();
  }
});

test("eBay: credenciales malas se reportan como tal, no como error de red", async () => {
  olvidarTokens();
  const portal = await levantarPortal({ robots: null });
  try {
    const r = await correr(ebay, portal.base, {
      env: { EBAY_CLIENT_ID: "malo", EBAY_CLIENT_SECRET: "malo", EBAY_API_BASE: portal.base },
    });
    assert.equal(r.providers[0]!.status, "sin-credenciales");
  } finally {
    await portal.cierra();
  }
});

test("eBay sin credenciales ni se intenta, pero deja su enlace", async () => {
  const r = await correr(ebay, "", { env: {} });
  assert.equal(r.providers[0]!.status, "sin-credenciales");
  assert.match(r.providers[0]!.searchUrl ?? "", /ebay\.de/);
});

// ── el conjunto ─────────────────────────────────────────────────────────────

test("dos portales con el mismo coche devuelven un solo anuncio", async () => {
  const a = await levantarPortal();
  const b = await levantarPortal();
  try {
    const pa = descriptor(a.base, "/lst");
    // Ojo: `meta` va capturado en el cierre del proveedor, asi que copiarlo por
    // encima no cambia el id que acaba en los anuncios. Hay que construirlo.
    const pb = descriptor(b.base, "/lst");
    pb.meta.id = "falso2";
    pb.meta.name = "Otro Portal";
    const r = await search([pa, pb], consulta(), [], { fetcher: nuevoFetcher(), providerTimeoutMs: 8000, env: {} });

    assert.equal(r.providers.filter((p) => p.status === "ok").length, 2);
    assert.equal(r.providers.reduce((s, p) => s + p.count, 0), 4, "cuatro anuncios en bruto");
    assert.equal(r.listings.length, 2, "dos coches de verdad");
    assert.ok(r.deduped >= 2);
    assert.ok(r.listings.some((l) => l.derived?.alsoOn), "queda anotado donde mas estaba publicado");
  } finally {
    await a.cierra();
    await b.cierra();
  }
});
