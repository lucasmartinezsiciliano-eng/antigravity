/**
 * La checklist es contenido, pero tiene invariantes que si se rompen dejan la
 * revision inservible sin que nadie se entere: ids duplicados que machacan
 * respuestas, puntos criticos con coste de reparacion (un motivo para irse no
 * se negocia) o un punto de un pais que se cuela en otro.
 */

import { test } from "node:test";
import assert from "node:assert/strict";
import { PHASES, allItems, phasesFor } from "../checklist.ts";

test("ningun id repetido: dos puntos con el mismo id comparten respuesta", () => {
  const ids = PHASES.flatMap((p) => p.items.map((i) => i.id));
  assert.equal(new Set(ids).size, ids.length);
});

test("las fases tienen id unico y ningun campo vacio", () => {
  const ids = PHASES.map((p) => p.id);
  assert.equal(new Set(ids).size, ids.length);
  for (const p of PHASES) {
    assert.ok(p.title && p.subtitle && p.place, `fase ${p.id} incompleta`);
    assert.ok(p.items.length > 0, `fase ${p.id} sin puntos`);
  }
});

test("el arranque en frio va antes que los papeles: solo se puede hacer una vez", () => {
  const orden = PHASES.map((p) => p.id);
  assert.ok(orden.indexOf("frio") < orden.indexOf("documentos"));
  assert.ok(orden.indexOf("antifraude") === 0, "el antifraude es lo primero de todo");
});

test("un punto critico no lleva coste de reparacion: no es cuestion de precio", () => {
  for (const i of PHASES.flatMap((p) => p.items)) {
    if (i.critical) assert.equal(i.repairCost, undefined, `${i.id} es critico y negociable a la vez`);
  }
});

test("todos los pesos estan entre 1 y 3", () => {
  for (const i of PHASES.flatMap((p) => p.items)) {
    assert.ok(i.weight >= 1 && i.weight <= 3, `${i.id} tiene peso ${i.weight}`);
  }
});

test("los puntos de un pais no se cuelan en otro", () => {
  const alemania = allItems({ country: "DE" }).map((i) => i.id);
  const francia = allItems({ country: "FR" }).map((i) => i.id);
  assert.ok(alemania.includes("doc-de-2"), "falta el Teil II en Alemania");
  assert.ok(!francia.includes("doc-de-2"), "el Teil II aparece en Francia");
  assert.ok(francia.includes("fuente-oficial-fr"));
  assert.ok(!alemania.includes("fuente-oficial-fr"));
});

test("cada pais tiene su fuente oficial de historial", () => {
  for (const c of ["DE", "FR", "NL", "BE", "PL", "IT", "AT"] as const) {
    const ids = allItems({ country: c }).map((i) => i.id);
    assert.ok(
      ids.some((id) => id.startsWith("fuente-oficial-")),
      `${c} no tiene fuente oficial`,
    );
  }
});

test("la lista se adapta al motor y al cambio", () => {
  const diesel = allItems({ fuel: "diesel" }).map((i) => i.id);
  const electrico = allItems({ fuel: "electrico" }).map((i) => i.id);
  assert.ok(diesel.includes("dpf-vaciado") && !electrico.includes("dpf-vaciado"));
  assert.ok(electrico.includes("bateria-hv") && !diesel.includes("bateria-hv"));
  assert.ok(allItems({ gearbox: "manual" }).some((i) => i.id === "embrague"));
  assert.ok(!allItems({ gearbox: "automatico" }).some((i) => i.id === "embrague"));
});

test("un coche sin datos sigue dando una revision util", () => {
  const items = allItems({});
  assert.ok(items.length > 50, `solo ${items.length} puntos sin contexto`);
  assert.ok(items.some((i) => i.critical));
});

test("el antifraude entero es critico: ahi no hay nada negociable", () => {
  const fase = phasesFor({ country: "DE" }).find((p) => p.id === "antifraude")!;
  const noCriticos = fase.items.filter((i) => !i.critical).map((i) => i.id);
  assert.ok(noCriticos.length <= 1, `demasiados puntos blandos: ${noCriticos.join(", ")}`);
});
