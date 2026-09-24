import { test } from "node:test";
import assert from "node:assert/strict";
import { createServer } from "node:http";
import { createApp, type ServerConfig } from "../src/server.ts";

const cfg: ServerConfig = {
  port: 0,
  userAgent: "coche-api/test",
  ignoreRobots: false,
  providerTimeoutMs: 3000,
  corsOrigin: "*",
  verbose: false,
};

async function conServidor<T>(fn: (base: string) => Promise<T>): Promise<T> {
  const server = createServer(createApp(cfg));
  await new Promise<void>((r) => server.listen(0, r));
  const { port } = server.address() as { port: number };
  try {
    return await fn(`http://127.0.0.1:${port}`);
  } finally {
    server.close();
  }
}

test("/health dice si robots.txt se respeta", async () => {
  await conServidor(async (base) => {
    const r = await fetch(`${base}/health`);
    assert.equal(r.status, 200);
    const j = (await r.json()) as Record<string, unknown>;
    assert.equal(j.ok, true);
    assert.equal(j.robots, "respetado");
    assert.ok((j.providersEnabled as number) > 0);
  });
});

test("/providers declara el regimen legal de cada fuente", async () => {
  await conServidor(async (base) => {
    const j = (await (await fetch(`${base}/providers`)).json()) as {
      providers: { id: string; compliance: string; enabled: boolean }[];
    };
    const html = j.providers.filter((p) => p.compliance === "html");
    assert.ok(html.length > 0, "hay adaptadores de html");
    assert.ok(html.every((p) => !p.enabled), "y ninguno viene encendido de fabrica");
  });
});

test("/search solo consulta los portales del pais pedido, mas los espanoles de referencia", async () => {
  await conServidor(async (base) => {
    const r = await fetch(`${base}/search?make=BMW&model=Serie+3&priceTo=20000&countries=DE,FR`);
    const j = (await r.json()) as { providers: { searchUrl?: string; name: string; provider: string }[]; query: Record<string, unknown> };
    assert.equal(j.query.make, "BMW");

    const ids = j.providers.map((p) => p.provider);
    for (const esperado of ["autoscout24-es", "mobile-de", "kleinanzeigen", "leboncoin", "lacentrale"]) {
      assert.ok(ids.includes(esperado), `falta ${esperado}`);
    }
    // Los espanoles entran siempre: sirven para saber si compensa importar.
    assert.ok(ids.includes("coches-net") && ids.includes("milanuncios"));
    // Y los de paises que no se han pedido, no.
    for (const fuera of ["otomoto", "subito", "marktplaats", "standvirtual"]) {
      assert.ok(!ids.includes(fuera), `${fuera} no deberia consultarse`);
    }
    assert.ok(j.providers.every((p) => p.searchUrl), "todos traen su enlace de busqueda");

    const as24 = j.providers.find((p) => p.name === "AutoScout24")!;
    assert.ok(as24.searchUrl!.includes("cy=D%2CF"), "los paises llegan al enlace de AutoScout24");
    const ebay = j.providers.find((p) => p.provider === "ebay")!;
    assert.ok(ebay.searchUrl!.includes("3er"), "el modelo se traduce al mercado aleman");
  });
});

test("una consulta absurda no rompe el servidor", async () => {
  await conServidor(async (base) => {
    const r = await fetch(`${base}/search`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ make: { $ne: null }, priceTo: "DROP TABLE", limit: 1e9 }),
    });
    assert.equal(r.status, 200);
    const j = (await r.json()) as { query: { limit: number } };
    assert.equal(j.query.limit, 50);
  });
});

test("/bridge habla el idioma de coche-europa", async () => {
  await conServidor(async (base) => {
    const r = await fetch(`${base}/bridge`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ filters: { make: "Audi", model: "A4", fuel: "diesel", countries: ["DE"] }, portals: [] }),
    });
    assert.equal(r.status, 200);
    const j = (await r.json()) as { listings: unknown[]; providers: unknown[] };
    assert.ok(Array.isArray(j.listings));
    assert.ok(Array.isArray(j.providers));
  });
});

test("404 con cuerpo JSON, no una pagina de error", async () => {
  await conServidor(async (base) => {
    const r = await fetch(`${base}/no-existe`);
    assert.equal(r.status, 404);
    assert.equal((await r.json() as { error: string }).error, "no existe");
  });
});
