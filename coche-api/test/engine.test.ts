import { test } from "node:test";
import assert from "node:assert/strict";
import { fusionar } from "../src/engine.ts";
import type { Listing } from "../src/schema.ts";

const base = (p: Partial<Listing>): Listing => ({
  id: "x:1", provider: "x", providerName: "X", url: "https://x.example/1",
  title: "BMW 320d", seenAt: "2026-09-20T00:00:00Z", ...p,
});

test("el mismo VIN es el mismo coche, este donde este publicado", () => {
  const { listings, deduped } = fusionar([
    base({ id: "a:1", provider: "a", url: "https://a.example/1", vin: "WBA8E51070K123456", price: 25000 }),
    base({ id: "b:9", provider: "b", url: "https://b.example/9", vin: "wba8e51070k123456", price: 24000 }),
  ]);
  assert.equal(deduped, 1);
  assert.equal(listings.length, 1);
  assert.equal(listings[0]!.price, 24000, "se queda el mas barato");
  assert.deepEqual(listings[0]!.derived?.alsoOn?.value, ["a"], "pero se anota donde mas esta");
});

test("sin VIN, el mismo coche se detecta por marca, ano, km y precio parecidos", () => {
  const { deduped } = fusionar([
    base({ id: "a:1", provider: "a", url: "https://a.example/1", make: "BMW", model: "320d", year: 2019, km: 95000, price: 24500 }),
    base({ id: "b:2", provider: "b", url: "https://b.example/2", make: "BMW", model: "320d", year: 2019, km: 95400, price: 24600 }),
  ]);
  assert.equal(deduped, 1);
});

test("dos coches parecidos pero distintos no se fusionan", () => {
  const { listings } = fusionar([
    base({ id: "a:1", provider: "a", url: "https://a.example/1", make: "BMW", model: "320d", year: 2019, km: 95000, price: 24500 }),
    base({ id: "b:2", provider: "b", url: "https://b.example/2", make: "BMW", model: "320d", year: 2019, km: 140000, price: 19500 }),
  ]);
  assert.equal(listings.length, 2);
});

test("al fusionar se completan los huecos con lo que sepa el otro anuncio", () => {
  const { listings } = fusionar([
    base({ id: "a:1", provider: "a", url: "https://a.example/1", vin: "WBA8E51070K123456", price: 24000, co2: 128 }),
    base({ id: "b:2", provider: "b", url: "https://b.example/2", vin: "WBA8E51070K123456", price: 25000, km: 95000, city: "Munich" }),
  ]);
  assert.equal(listings.length, 1);
  assert.equal(listings[0]!.price, 24000);
  assert.equal(listings[0]!.co2, 128);
  assert.equal(listings[0]!.km, 95000, "el dato que solo tenia el otro se conserva");
  assert.equal(listings[0]!.city, "Munich");
});

test("la misma URL con distintos parametros es el mismo anuncio", () => {
  const { deduped } = fusionar([
    base({ id: "a:1", url: "https://a.example/1?utm_source=x" }),
    base({ id: "a:1b", url: "https://a.example/1?ref=otro" }),
  ]);
  assert.equal(deduped, 1);
});
