/**
 * El motor de extraccion se puede probar entero sin tocar internet: le damos
 * HTML de mentira con la forma que tiene el de verdad. Lo que NO prueba esto
 * es que los selectores de cada portal sigan siendo validos hoy; para eso esta
 * `npm run probe`.
 */

import { test } from "node:test";
import assert from "node:assert/strict";
import { desdeJsonLd, desdeSelectores, extraerEmbebido, extraerJsonLd } from "../src/providers/html/engine.ts";

const CON_JSONLD = `<!doctype html><html><head>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"ItemList","itemListElement":[
 {"@type":"Car","name":"BMW 320d xDrive","url":"https://portal.example/a/1",
  "brand":{"@type":"Brand","name":"BMW"},"model":"320d",
  "vehicleModelDate":"2019","vehicleTransmission":"Automatik","fuelType":"Diesel",
  "mileageFromOdometer":{"@type":"QuantitativeValue","value":"95000","unitCode":"KMT"},
  "vehicleEngine":{"@type":"EngineSpecification","enginePower":{"value":140,"unitText":"kW"}},
  "vehicleIdentificationNumber":"WBA8E51070K123456",
  "image":["https://cdn.example/1.jpg"],
  "offers":{"@type":"Offer","price":"24.500","priceCurrency":"EUR",
    "availableAtOrFrom":{"address":{"addressLocality":"Munchen","addressCountry":"DE","postalCode":"80331"}}}}
]}
</script></head><body></body></html>`;

test("json-ld: se extrae el coche aunque venga anidado en un ItemList", () => {
  const objetos = extraerJsonLd(CON_JSONLD, ["Car", "Vehicle"]);
  assert.equal(objetos.length, 1);

  const l = desdeJsonLd(objetos[0]!);
  assert.equal(l.title, "BMW 320d xDrive");
  assert.equal(l.make, "BMW", "la marca viene como objeto Brand, no como texto");
  assert.equal(l.price, 24500, "el precio venia como '24.500' en formato aleman");
  assert.equal(l.year, 2019);
  assert.equal(l.km, 95000);
  assert.equal(l.fuel, "diesel");
  assert.equal(l.gearbox, "automatico");
  assert.equal(l.power, 190, "140 kW son 190 CV");
  assert.equal(l.country, "DE");
  assert.equal(l.city, "Munchen");
  assert.equal(l.vin, "WBA8E51070K123456");
  assert.deepEqual(l.images, ["https://cdn.example/1.jpg"]);
});

test("json-ld roto no tumba la pagina entera", () => {
  const html = `<script type="application/ld+json">{esto no es json</script>` + CON_JSONLD;
  assert.equal(extraerJsonLd(html, ["Car"]).length, 1);
});

test("embedded-json: se saca el estado que el portal deja en la pagina", () => {
  const html = `<html><body><script>window.__NEXT_DATA__ = {"props":{"pageProps":{"listings":[
    {"@type":"Car","name":"Audi A4","url":"https://p.example/2","offers":{"price":"18900","priceCurrency":"EUR"}}
  ]}}};</script></body></html>`;
  const items = extraerEmbebido(html, "__NEXT_DATA__", "props.pageProps.listings");
  assert.equal(items.length, 1);
  assert.equal(desdeJsonLd(items[0]!).price, 18900);
});

test("embedded-json: tambien lo lee de un <script id=...>", () => {
  const html = `<script id="__NEXT_DATA__" type="application/json">{"props":{"pageProps":{"listings":[{"name":"X","url":"u"}]}}}</script>`;
  assert.equal(extraerEmbebido(html, "__NEXT_DATA__", "props.pageProps.listings").length, 1);
});

test("selectores: ultimo recurso, con URL relativa y precio sucio", () => {
  const html = `<html><body>
    <article class="item">
      <a href="/oferta/123">
        <h2>Volkswagen Golf 2.0 TDI</h2>
      </a>
      <p class="price">17.250 €</p>
      <span class="km">120.000 km</span>
      <span class="ez">05/2018</span>
      <span class="fuel">Diesel</span>
      <span class="pw">150 PS</span>
      <img src="/img/123.jpg">
    </article>
  </body></html>`;

  const [l] = desdeSelectores(html, "https://portal.example/lst?x=1", {
    kind: "selectors",
    item: "article.item",
    fields: {
      url: { sel: "a", attr: "href" },
      title: { sel: "h2" },
      price: { sel: ".price" },
      km: { sel: ".km" },
      year: { sel: ".ez" },
      fuel: { sel: ".fuel" },
      power: { sel: ".pw" },
      image: { sel: "img", attr: "src" },
    },
  });

  assert.equal(l!.url, "https://portal.example/oferta/123", "la relativa se resuelve contra la pagina");
  assert.equal(l!.title, "Volkswagen Golf 2.0 TDI");
  assert.equal(l!.price, 17250);
  assert.equal(l!.km, 120000);
  assert.equal(l!.year, 2018);
  assert.equal(l!.fuel, "diesel");
  assert.equal(l!.power, 150);
  assert.equal(l!.images?.[0], "https://portal.example/img/123.jpg");
});

test("una pagina sin nada devuelve vacio, no un error", () => {
  assert.deepEqual(extraerJsonLd("<html></html>", ["Car"]), []);
  assert.deepEqual(extraerEmbebido("<html></html>", "__NEXT_DATA__", "a.b"), []);
});
