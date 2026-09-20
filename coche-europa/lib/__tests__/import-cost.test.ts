/**
 * La calculadora fiscal es la pieza que mas facil se rompe sin que se note:
 * un signo mal puesto son cientos de euros de diferencia en el presupuesto de
 * alguien. Estos tests fijan los limites de la norma.
 *
 * Se ejecutan sin dependencias:  npm test
 */

import { test } from "node:test";
import assert from "node:assert/strict";
import { baseMinorada, calcularCostes, costeAproximado, tramoIedmt } from "../import-cost.ts";
import type { CostInputs } from "../types.ts";

const coche: CostInputs = {
  price: 14500,
  country: "DE",
  region: "peninsula",
  co2: 128,
  seller: "particular",
  firstRegistration: "2019-06-01",
  km: 95000,
  itpRate: 5,
  includeItp: true,
  transport: "camion",
  hasCoc: false,
  modificado: false,
  useGestoria: true,
  vinReport: true,
};

test("los limites de CO2 entran en el tramo de abajo (art. 70.1: 'no superiores a')", () => {
  assert.equal(tramoIedmt(119, "peninsula").rate, 0);
  assert.equal(tramoIedmt(120, "peninsula").rate, 0, "120 g/km esta exento");
  assert.equal(tramoIedmt(121, "peninsula").rate, 4.75);
  assert.equal(tramoIedmt(160, "peninsula").rate, 4.75, "160 g/km sigue en el 4,75%");
  assert.equal(tramoIedmt(161, "peninsula").rate, 9.75);
  assert.equal(tramoIedmt(200, "peninsula").rate, 9.75, "200 g/km sigue en el 9,75%");
  assert.equal(tramoIedmt(201, "peninsula").rate, 14.75);
});

test("sin CO2 acreditado se aplica el tramo maximo", () => {
  assert.equal(tramoIedmt(undefined, "peninsula").rate, 14.75);
});

test("Canarias tiene sus propios tipos y Ceuta y Melilla estan exentas", () => {
  assert.equal(tramoIedmt(150, "canarias").rate, 3.75);
  assert.equal(tramoIedmt(300, "ceuta-melilla").rate, 0);
});

test("minoracion del art. 69.b): la base se divide por (1 + IVA + tipo)", () => {
  assert.equal(Math.round(baseMinorada(20000, 9.75)), Math.round(20000 / 1.3075));
  assert.equal(Math.round(baseMinorada(20000, 0)), Math.round(20000 / 1.21));
});

test("un usado ya matriculado fuera tributa sobre la base minorada", () => {
  const r = calcularCostes(coche);
  const iedmt = r.lines.find((l) => l.key === "iedmt")!.amount;
  assert.equal(iedmt, Math.round((14500 / 1.2575) * 0.0475));
  assert.ok(r.minoracion > 0);
});

test("el total es exactamente la suma de las lineas que se ven", () => {
  const r = calcularCostes(coche);
  assert.equal(r.total, r.lines.reduce((s, l) => s + l.amount, 0));
});

test("6.000 km exactos es medio de transporte nuevo (art. 13.2: 'no mas de')", () => {
  const r = calcularCostes({ ...coche, km: 6000, firstRegistration: "2024-01-01" });
  assert.equal(r.esMedioTransporteNuevo, true);
  assert.equal(calcularCostes({ ...coche, km: 6001 }).esMedioTransporteNuevo, false);
});

test("el IVA se calcula sobre el precio pagado, no sobre el valor fiscal", () => {
  const r = calcularCostes({ ...coche, km: 6000, valorFiscal: 25000 });
  assert.equal(r.lines.find((l) => l.key === "iva")!.amount, Math.round(14500 * 0.21));
});

test("los 6 meses se cuentan hasta la entrega, no hasta hoy", () => {
  const r = calcularCostes({
    ...coche,
    km: 40000,
    firstRegistration: "2024-01-01",
    fechaCompra: "2024-04-01",
  });
  assert.equal(r.esMedioTransporteNuevo, true, "3 meses entre matriculacion y compra");
});

test("el ITP grava el valor de mercado sin minorar", () => {
  const r = calcularCostes(coche);
  assert.equal(r.lines.find((l) => l.key === "itp")!.amount, Math.round(14500 * 0.05));
});

test("un coche con reformas arrastra la homologacion individual", () => {
  const con = calcularCostes({ ...coche, modificado: true });
  const sin = calcularCostes(coche);
  assert.equal(con.total - sin.total, 2750);
  assert.ok(con.avisos.some((a) => a.includes("reformas")));
});

test("el recargo autonomico se suma al tipo estatal", () => {
  const r = calcularCostes({ ...coche, co2: 210, recargoAutonomico: 1.25 });
  assert.equal(r.iedmtRate, 16);
});

test("avisa cuando el coche esta a punto de saltar de tramo", () => {
  const r = calcularCostes({ ...coche, co2: 157 });
  assert.ok(r.avisos.some((a) => a.includes("del siguiente tramo")));
});

test("el orden del buscador no lo sesgan gastos opcionales", () => {
  // Dos coches identicos salvo el precio mantienen el orden relativo, y un
  // coche limpio de CO2 adelanta a uno sucio del mismo precio.
  assert.ok(costeAproximado(10000, "DE", 128) < costeAproximado(12000, "DE", 128));
  assert.ok(costeAproximado(15000, "DE", 115) < costeAproximado(15000, "DE", 210));
});
