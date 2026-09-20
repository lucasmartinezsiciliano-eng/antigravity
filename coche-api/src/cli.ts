/**
 * Sonda de adaptadores.
 *
 * Sirve para lo que no se puede hacer desde un despacho: comprobar que un
 * descriptor sigue funcionando contra el portal de verdad. Dice que estrategia
 * ha entrado, cuantos anuncios ha sacado y ensena el primero campo a campo,
 * para ver de un vistazo si el mapeo esta bien o hay que tocar selectores.
 *
 *   npm run probe                                   lista los proveedores
 *   npm run probe -- ebay --make BMW --priceTo 20000
 *   npm run probe -- autoscout24-html --make BMW --model "Serie 3"
 *   npm run probe -- --all --make Volkswagen --model Golf
 */

import { search } from "./engine.ts";
import { Fetcher } from "./http/fetcher.ts";
import { ALL, byId, enabled } from "./registry.ts";
import { configFromEnv } from "./server.ts";
import { parseQuery, type Listing } from "./schema.ts";
import type { Provider } from "./providers/types.ts";

const COLOR = process.stdout.isTTY;
const c = (code: string, s: string) => (COLOR ? `\x1b[${code}m${s}\x1b[0m` : s);
const verde = (s: string) => c("32", s);
const rojo = (s: string) => c("31", s);
const ambar = (s: string) => c("33", s);
const gris = (s: string) => c("90", s);
const negrita = (s: string) => c("1", s);

function parseArgs(argv: string[]) {
  const ids: string[] = [];
  const flags: Record<string, string | boolean> = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]!;
    if (a.startsWith("--")) {
      const k = a.slice(2);
      const v = argv[i + 1];
      if (v && !v.startsWith("--")) {
        flags[k] = v;
        i++;
      } else flags[k] = true;
    } else ids.push(a);
  }
  return { ids, flags };
}

function listar() {
  const activos = new Set(enabled().map((p) => p.meta.id));
  console.log(negrita("\nProveedores\n"));
  const ancho = Math.max(...ALL.map((p) => p.meta.id.length));

  for (const p of ALL) {
    const on = activos.has(p.meta.id);
    const estado = on ? verde("activo  ") : gris("apagado ");
    const busca = p.search ? "busca   " : gris("enlace  ");
    const faltan = (p.meta.requiresEnv ?? []).filter((k) => !process.env[k]);
    const nota = faltan.length ? ambar(`faltan ${faltan.join(",")}`) : gris(p.meta.compliance);
    console.log(`  ${estado} ${busca} ${p.meta.id.padEnd(ancho)}  ${nota}`);
  }
  console.log(gris("\n  Para probar uno:  npm run probe -- <id> --make BMW --model 'Serie 3'\n"));
}

function ficha(l: Listing) {
  const campos: [string, unknown][] = [
    ["title", l.title], ["price", l.price], ["year", l.year], ["km", l.km],
    ["power", l.power], ["co2", l.co2], ["fuel", l.fuel], ["gearbox", l.gearbox],
    ["make", l.make], ["model", l.model], ["country", l.country], ["city", l.city],
    ["seller", l.seller], ["vin", l.vin], ["images", l.images?.length], ["url", l.url],
  ];
  for (const [k, v] of campos) {
    const vacio = v === undefined || v === null || v === "";
    const valor = vacio ? rojo("(vacio)") : String(v).slice(0, 72);
    console.log(`    ${k.padEnd(10)} ${valor}`);
  }
  const rellenos = campos.filter(([, v]) => v !== undefined && v !== null && v !== "").length;
  const pct = Math.round((rellenos / campos.length) * 100);
  const color = pct >= 70 ? verde : pct >= 40 ? ambar : rojo;
  console.log(`    ${gris("cobertura")}  ${color(`${pct}% de campos`)}`);
}

async function main() {
  const { ids, flags } = parseArgs(process.argv.slice(2));

  if (!ids.length && !flags.all) return listar();

  const { query, warnings } = parseQuery({
    make: flags.make, model: flags.model, q: flags.q,
    priceFrom: flags.priceFrom, priceTo: flags.priceTo,
    yearFrom: flags.yearFrom, yearTo: flags.yearTo, kmTo: flags.kmTo,
    countries: flags.countries ?? "DE,FR",
    limit: flags.limit ?? 10,
  });

  let objetivo: Provider[];
  if (flags.all) {
    objetivo = enabled();
  } else {
    objetivo = ids.map((id) => {
      const p = byId(id);
      if (!p) {
        console.error(rojo(`No existe el proveedor "${id}".`));
        process.exit(1);
      }
      return p;
    });
  }

  const cfg = configFromEnv();
  const fetcher = new Fetcher({
    userAgent: cfg.userAgent,
    ignoreRobots: cfg.ignoreRobots,
    log: flags.verbose ? (m) => console.log(gris(`  ${m}`)) : undefined,
  });

  console.log(negrita(`\nConsulta: ${JSON.stringify(query)}`));
  for (const w of warnings) console.log(ambar(`  aviso: ${w}`));
  console.log();

  const r = await search(objetivo, query, warnings, {
    fetcher,
    providerTimeoutMs: Number(flags.timeout ?? cfg.providerTimeoutMs),
    log: flags.verbose ? (m) => console.log(gris(`  ${m}`)) : undefined,
  });

  let problemas = 0;
  for (const p of r.providers) {
    const icono =
      p.status === "ok" ? verde("OK   ")
      : p.status === "vacio" ? ambar("VACIO")
      : p.status === "solo-enlace" || p.status === "sin-credenciales" ? gris("--   ")
      : rojo("FALLO");
    if (p.status !== "ok" && p.status !== "solo-enlace" && p.status !== "sin-credenciales") problemas++;

    console.log(`${icono} ${negrita(p.name.padEnd(24))} ${String(p.count).padStart(3)} anuncios  ${gris(`${p.ms}ms`)}`);
    if (p.message) console.log(gris(`       ${p.message}`));
    if (p.searchUrl) console.log(gris(`       ${p.searchUrl.slice(0, 110)}`));
  }

  console.log();
  if (r.listings.length) {
    console.log(negrita(`${r.listings.length} anuncios (${r.deduped} duplicados fusionados). El primero:\n`));
    ficha(r.listings[0]!);
  } else {
    console.log(ambar("Ningun anuncio. Si esperabas resultados, revisa el descriptor con --verbose."));
  }
  console.log(gris(`\n${r.ms} ms en total\n`));

  process.exit(problemas ? 1 : 0);
}

main().catch((e) => {
  console.error(rojo(String(e)));
  process.exit(1);
});
