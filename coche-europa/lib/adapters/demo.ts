/**
 * Fichas de ejemplo.
 *
 * NO son coches reales: existen para que se pueda probar la lista unificada,
 * el orden por coste puerta a puerta y el paso al expediente de revision
 * mientras no haya ninguna fuente en vivo configurada. Van marcadas con
 * `demo: true` y la interfaz las etiqueta como EJEMPLO en todas partes.
 */

import type { CountryCode, Fuel, Gearbox, Listing, SearchFilters } from "../types";

const CATALOGO: {
  make: string;
  model: string;
  fuel: Fuel;
  co2: number;
  power: number;
  base: number;
}[] = [
  { make: "BMW", model: "Serie 3", fuel: "diesel", co2: 128, power: 190, base: 21000 },
  { make: "BMW", model: "Serie 1", fuel: "gasolina", co2: 139, power: 140, base: 17500 },
  { make: "Audi", model: "A4", fuel: "diesel", co2: 134, power: 190, base: 22500 },
  { make: "Audi", model: "A3", fuel: "gasolina", co2: 126, power: 150, base: 19000 },
  { make: "Volkswagen", model: "Golf", fuel: "gasolina", co2: 122, power: 150, base: 16500 },
  { make: "Volkswagen", model: "Passat", fuel: "diesel", co2: 131, power: 150, base: 18500 },
  { make: "Mercedes-Benz", model: "Clase C", fuel: "diesel", co2: 142, power: 194, base: 24000 },
  { make: "Mercedes-Benz", model: "Clase A", fuel: "gasolina", co2: 133, power: 163, base: 20500 },
  { make: "Skoda", model: "Octavia", fuel: "diesel", co2: 119, power: 150, base: 15500 },
  { make: "Renault", model: "Megane", fuel: "gasolina", co2: 129, power: 140, base: 13500 },
  { make: "Peugeot", model: "308", fuel: "diesel", co2: 118, power: 130, base: 13000 },
  { make: "Toyota", model: "Corolla", fuel: "hibrido", co2: 102, power: 122, base: 17000 },
  { make: "Tesla", model: "Model 3", fuel: "electrico", co2: 0, power: 283, base: 24000 },
  { make: "Volvo", model: "XC60", fuel: "diesel", co2: 158, power: 190, base: 27000 },
  { make: "Porsche", model: "Macan", fuel: "gasolina", co2: 212, power: 265, base: 42000 },
];

const CIUDADES: Partial<Record<CountryCode, string[]>> = {
  DE: ["Munich", "Hamburgo", "Colonia", "Stuttgart", "Berlin"],
  FR: ["Lyon", "Toulouse", "Burdeos", "Lille", "Perpinan"],
  IT: ["Milan", "Turin", "Bolonia", "Verona"],
  NL: ["Rotterdam", "Utrecht", "Eindhoven"],
  BE: ["Amberes", "Gante", "Lieja"],
  AT: ["Viena", "Graz", "Linz"],
  PT: ["Oporto", "Lisboa", "Braga"],
  PL: ["Varsovia", "Poznan", "Cracovia"],
  LU: ["Luxemburgo"],
  ES: ["Madrid", "Barcelona", "Valencia"],
};

/** Mismos filtros, mismos resultados: nada de saltos raros al recargar. */
function seeded(seed: string) {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return () => {
    h ^= h << 13;
    h ^= h >>> 17;
    h ^= h << 5;
    return Math.abs(h % 10000) / 10000;
  };
}

export function demoListings(f: SearchFilters): Listing[] {
  const rnd = seeded(JSON.stringify(f));
  const year = new Date().getFullYear();

  const candidatos = CATALOGO.filter((c) => {
    if (f.make && !c.make.toLowerCase().includes(f.make.toLowerCase())) return false;
    if (f.model && !c.model.toLowerCase().includes(f.model.toLowerCase())) return false;
    if (f.fuel && c.fuel !== f.fuel) return false;
    return true;
  });

  const base = candidatos.length ? candidatos : CATALOGO.slice(0, 6);
  const paises = f.countries.length ? f.countries : (["DE", "FR"] as CountryCode[]);

  const out: Listing[] = [];
  for (let i = 0; i < Math.min(12, base.length * 2); i++) {
    const c = base[i % base.length];
    const country = paises[i % paises.length];
    const antiguedad = 2 + Math.floor(rnd() * 6);
    const anio = year - antiguedad;
    const km = Math.round((15000 + rnd() * 12000) * antiguedad);
    const precio = Math.round((c.base * Math.pow(0.88, antiguedad)) / 100) * 100;
    const gearbox: Gearbox = rnd() > 0.45 ? "automatico" : "manual";

    if (f.yearFrom && anio < f.yearFrom) continue;
    if (f.yearTo && anio > f.yearTo) continue;
    if (f.priceFrom && precio < f.priceFrom) continue;
    if (f.priceTo && precio > f.priceTo) continue;
    if (f.kmTo && km > f.kmTo) continue;
    if (f.gearbox && gearbox !== f.gearbox) continue;
    if (f.powerFrom && c.power < f.powerFrom) continue;

    const ciudades = CIUDADES[country] ?? ["-"];
    out.push({
      id: `demo_${i}_${c.make}_${anio}`,
      source: "demo",
      sourceName: "Ejemplo",
      title: `${c.make} ${c.model} ${c.power} CV`,
      make: c.make,
      model: c.model,
      price: precio,
      year: anio,
      km,
      fuel: c.fuel,
      gearbox,
      power: c.power,
      co2: c.co2,
      country,
      city: ciudades[i % ciudades.length],
      seller: rnd() > 0.5 ? "particular" : "profesional",
      url: "",
      demo: true,
    });
  }
  return out;
}
