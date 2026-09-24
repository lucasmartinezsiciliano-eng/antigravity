import { test } from "node:test";
import assert from "node:assert/strict";
import { modelFor, queryText, toFuel, toGearbox, toNumber, toPower, toYear, toFirstRegistration, toCountry } from "../src/normalize.ts";

test("los numeros de los portales vienen en formatos incompatibles", () => {
  assert.equal(toNumber("24.500 €"), 24500);        // aleman/espanol
  assert.equal(toNumber("€ 12,999"), 12999);        // ingles
  assert.equal(toNumber("1.234,56"), 1234.56);      // europeo con decimales
  assert.equal(toNumber("1,234.56"), 1234.56);      // ingles con decimales
  assert.equal(toNumber("145 000 km"), 145000);     // frances con espacio
  assert.equal(toNumber("A consultar"), undefined);
  assert.equal(toNumber(""), undefined);
});

test("el mismo combustible en seis idiomas es el mismo combustible", () => {
  for (const s of ["Diesel", "Gasoil", "Gazole", "Nafta"]) assert.equal(toFuel(s), "diesel");
  for (const s of ["Benzin", "Essence", "Gasolina", "Benzina", "Petrol"]) assert.equal(toFuel(s), "gasolina");
  for (const s of ["Elektro", "Électrique", "Elettrica", "BEV"]) assert.equal(toFuel(s), "electrico");
});

test("hibrido enchufable no es lo mismo que hibrido, y el orden importa", () => {
  assert.equal(toFuel("Hybrid (Benzin/Elektro) Plug-in"), "phev");
  assert.equal(toFuel("Hybride rechargeable"), "phev");
  assert.equal(toFuel("Hybrid"), "hibrido");
});

test("las cajas de cambio tambien", () => {
  for (const s of ["Automatik", "DSG", "S tronic", "PDK", "EAT8", "CVT"]) assert.equal(toGearbox(s), "automatico");
  for (const s of ["Schaltgetriebe", "Boite mecanique", "Manual"]) assert.equal(toGearbox(s), "manual");
});

test("kW y CV se convierten en los dos sentidos", () => {
  assert.equal(toPower("140 kW").cv, 190);
  assert.equal(toPower("190 PS").cv, 190);
  assert.equal(toPower("190 CV").kw, 140);
  assert.deepEqual(toPower("sin datos"), {});
});

test("las fechas de matriculacion vienen de mil maneras", () => {
  assert.equal(toYear("03/2019"), 2019);
  assert.equal(toYear("EZ 06.2018"), 2018);
  assert.equal(toFirstRegistration("03/2019"), "2019-03");
  assert.equal(toFirstRegistration("2019"), "2019");
  assert.equal(toYear("1890"), undefined, "fuera de rango");
});

test("los paises llegan como nombre o como codigo", () => {
  assert.equal(toCountry("Deutschland"), "DE");
  assert.equal(toCountry("Belgique"), "BE");
  assert.equal(toCountry("España"), "ES");
  assert.equal(toCountry("Marte"), undefined);
});

test("un Serie 3 en Alemania es un 3er, y sin eso la busqueda vuelve vacia", () => {
  assert.equal(modelFor("Serie 3", "de"), "3er");
  assert.equal(modelFor("Clase C", "de"), "C-Klasse");
  assert.equal(modelFor("Clase C", "fr"), "Classe C");
  assert.equal(modelFor("Golf", "de"), "Golf", "lo que no cambia se deja igual");
  assert.equal(queryText({ make: "BMW", model: "Serie 3" }, "de"), "BMW 3er");
  assert.equal(queryText({ q: "cualquier cosa" }, "de"), "cualquier cosa", "el texto libre manda");
});
