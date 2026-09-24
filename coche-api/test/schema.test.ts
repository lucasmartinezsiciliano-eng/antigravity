import { test } from "node:test";
import assert from "node:assert/strict";
import { parseQuery } from "../src/schema.ts";

test("lo que no se entiende se ignora, nunca revienta", () => {
  const { query } = parseQuery({ make: 42, priceTo: "no soy un numero", fuel: "unicornio", sort: "; DROP TABLE" });
  assert.equal(query.make, undefined);
  assert.equal(query.priceTo, undefined);
  assert.equal(query.fuel, undefined);
  assert.equal(query.sort, "precio", "cae al orden por defecto");
});

test("acepta que los filtros lleguen como texto (vienen de un querystring)", () => {
  const { query } = parseQuery({ priceTo: "20000", yearFrom: "2018", fuel: "diesel,hibrido", countries: "DE,FR" });
  assert.equal(query.priceTo, 20000);
  assert.equal(query.yearFrom, 2018);
  assert.deepEqual(query.fuel, ["diesel", "hibrido"]);
  assert.deepEqual(query.countries, ["DE", "FR"]);
});

test("un rango del reves se endereza en vez de devolver cero resultados", () => {
  const { query, warnings } = parseQuery({ priceFrom: 20000, priceTo: 5000 });
  assert.equal(query.priceFrom, 5000);
  assert.equal(query.priceTo, 20000);
  assert.ok(warnings.some((w) => w.includes("intercambiado")));
});

test("avisa de una busqueda sin criterios en vez de traerse catalogos enteros a ciegas", () => {
  const { warnings } = parseQuery({});
  assert.ok(warnings.some((w) => w.includes("catalogo")));
});

test("los limites se acotan: nadie pide 10.000 resultados", () => {
  assert.equal(parseQuery({ limit: 99999 }).query.limit, 50);
  assert.equal(parseQuery({ limit: 25 }).query.limit, 25);
});
