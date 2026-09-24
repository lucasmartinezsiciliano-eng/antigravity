/**
 * robots.txt no es decorativo: es el mecanismo que evita que esto se comporte
 * como un scraper. Si se rompe, se rompe en silencio, asi que va con tests.
 */

import { test } from "node:test";
import assert from "node:assert/strict";
import { parseRobots, permitido } from "../src/http/robots.ts";

const UA = "coche-api/0.1";

test("sin reglas, todo permitido", () => {
  assert.equal(permitido(parseRobots("", UA), "https://x.example/lst"), true);
});

test("Disallow generico bloquea la ruta", () => {
  const r = parseRobots("User-agent: *\nDisallow: /lst", UA);
  assert.equal(permitido(r, "https://x.example/lst?a=1"), false);
  assert.equal(permitido(r, "https://x.example/otra"), true);
});

test("gana la regla mas especifica, y a igual longitud gana Allow", () => {
  const r = parseRobots("User-agent: *\nDisallow: /lst\nAllow: /lst/publico", UA);
  assert.equal(permitido(r, "https://x.example/lst/privado"), false);
  assert.equal(permitido(r, "https://x.example/lst/publico/1"), true);
});

test("un grupo que nos nombra pesa mas que el comodin", () => {
  const txt = "User-agent: *\nDisallow:\n\nUser-agent: coche-api\nDisallow: /";
  assert.equal(permitido(parseRobots(txt, UA), "https://x.example/lo-que-sea"), false);
});

test("los comodines y el ancla final funcionan", () => {
  const r = parseRobots("User-agent: *\nDisallow: /*.json$\nDisallow: /a/*/b", UA);
  assert.equal(permitido(r, "https://x.example/datos.json"), false);
  assert.equal(permitido(r, "https://x.example/datos.json.html"), true, "el $ ancla el final");
  assert.equal(permitido(r, "https://x.example/a/cualquier/b"), false);
});

test("'Disallow:' vacio significa permitir todo, no bloquear todo", () => {
  assert.equal(permitido(parseRobots("User-agent: *\nDisallow:", UA), "https://x.example/x"), true);
});

test("los comentarios y los espacios no confunden al parser", () => {
  const r = parseRobots("  # comentario\nUser-agent: *   # otro\n  Disallow: /lst  # y otro", UA);
  assert.equal(permitido(r, "https://x.example/lst"), false);
});

test("se lee el Crawl-delay del grupo que nos aplica", () => {
  assert.equal(parseRobots("User-agent: *\nCrawl-delay: 10", UA).crawlDelay, 10);
});
