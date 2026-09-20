# Coche Europa

Buscar un coche en Alemania o Francia, saber lo que cuesta de verdad traerlo, y
revisarlo paso a paso antes de soltar el dinero. Las tres cosas en una app.

```
npm install
npm run dev     # http://localhost:3000
```

Next.js 16 · React 19 · TypeScript · sin base de datos: todo lo que guarda el
usuario vive en su navegador.

---

## Las cuatro piezas

| Ruta | Que hace |
|------|----------|
| `/buscar` | Un formulario de filtros que se lanza contra 13 portales de 9 paises a la vez |
| `/coste` | Precio del anuncio -> coste real matriculado en Espana |
| `/revision` | 103 puntos de revision guiada, filtrados al coche concreto |
| `/informe` | Veredicto, defectos, cuanto negociar y precio maximo a pagar |

---

## Como funciona la busqueda multiportal

Ni AutoScout24, ni mobile.de, ni Leboncoin tienen API publica, y rascar sus webs
va contra sus condiciones y se rompe cada dos semanas. Asi que la app hace tres
cosas a la vez:

**1. Enlaces profundos (siempre activo, sin configurar nada).**
Tus filtros se traducen a la URL de busqueda de cada portal y se abren con un
clic — o los 13 de golpe con *Abrir los N portales*. Incluye traduccion del
nombre del modelo a cada mercado: buscar *Clase C* manda `C-Klasse` a mobile.de
y `Classe C` a Leboncoin, que es lo unico que entienden.

**2. Fuentes en vivo (opcional).**
Si defines credenciales, esos resultados aparecen mezclados en una sola lista,
deduplicados y ordenados por coste puerta a puerta:

- `EBAY_CLIENT_ID` / `EBAY_CLIENT_SECRET` — eBay Browse API, oficial y gratis.
- `BRIDGE_URL` / `BRIDGE_TOKEN` — tu propio servicio. Ver abajo.

**3. Fichas de ejemplo.**
Si no hay ninguna fuente en vivo, la lista se rellena con coches inventados y
etiquetados como EJEMPLO, para poder probar el flujo. Nunca se mezclan con
anuncios reales.

### El puente (`BRIDGE_URL`)

El hueco para meter tu propia fuente. La app le manda:

```http
POST {BRIDGE_URL}
Authorization: Bearer {BRIDGE_TOKEN}

{ "filters": { "make": "BMW", "model": "Serie 3", "priceTo": 20000, ... },
  "portals": ["autoscout24-es", "mobile-de", ...] }
```

y espera `{ "listings": [...] }` o `{ "results": [{ "portal", "listings" }] }`.

En `n8n/coche-europa-bridge.json` tienes el flujo de n8n que implementa ese
contrato, listo para importar. El nodo `Fetch Listings From Source` esta vacio a
proposito: ahi enchufas lo que tengas (un feed de concesionario, una API con
credenciales, tu propia base de anuncios).

### Cuando un portal cambia sus parametros

Todas las URLs se construyen en **`lib/portals.ts`**, un builder por portal. Si
un enlace deja de funcionar, se arregla ahi y en ningun sitio mas. Anadir un
portal nuevo son 15 lineas.

Portales incluidos: AutoScout24, mobile.de, Kleinanzeigen, Leboncoin, La
Centrale, Subito, Marktplaats, 2dehands, Otomoto, Standvirtual, eBay Motors, y
Coches.net + Milanuncios como referencia de precio en Espana.

---

## La calculadora de costes

`lib/import-cost.ts`. Lo que entra en el total:

- **Impuesto de matriculacion (IEDMT)** por tramo de CO2: 0 / 4,75 / 9,75 /
  14,75 % en peninsula y Baleares; 0 / 3,75 / 8,75 / 13,75 % en Canarias; exento
  en Ceuta y Melilla. Sin dato de CO2 aplicamos el tramo maximo, que es lo que
  hara Hacienda si no puedes acreditarlo.
- **IVA del 21 %** solo si el coche es *medio de transporte nuevo*: menos de 6
  meses o menos de 6.000 km. Mucha gente se entera de esto tarde.
- **ITP** de tu comunidad autonoma, opcional. En compras UE entre particulares es
  discutido: hay comunidades que lo reclaman y gestorias que sostienen que no
  procede. Va activado por defecto para no quedarse corto en el presupuesto.
- Transporte (camion o ir a buscarlo con placas temporales), COC, ficha tecnica
  reducida, ITV de importacion, tasa DGT, gestoria e informe de VIN.

Dos avisos que la app repite porque importan:

1. La base imponible del impuesto **no es lo que pagas**, es el valor de las
   tablas de precios medios de Hacienda. Hay un estimador a partir del precio del
   modelo nuevo y los coeficientes de antiguedad.
2. Los importes de transporte, ITV, homologacion y gestoria son medias de
   mercado. Los tipos impositivos son norma; el resto, orientativo.

Revisado en `DATOS_ACTUALIZADOS` (`lib/import-cost.ts`). Cuando cambie el BOE, se
toca esa constante y los tramos.

---

## La revision guiada

`lib/checklist.ts`. Nueve fases en el orden en que hay que hacerlas:

1. **Que el vendedor sea real** — antifraude puro. Los timos que mas dinero se
   llevan (la senal, el transportista falso, la cuenta de un tercero) ocurren
   antes de comprar el billete de avion, asi que van separados y todos son
   motivo para irse.
2. **Que el coche merezca el viaje** — la fuente oficial de historial de cada
   pais, el CO2 real, las reformas, y si tienes el dinero: ningun banco espanol
   financia un coche sin matricula espanola.
3. **Arranque en frio** — lo primero al llegar. Es perecedero: solo funciona una
   vez y solo con el motor parado toda la noche, asi que va antes que los
   papeles.
4. **Papeles** — cambian por pais: Teil II aleman, HistoVec frances, visura del
   PRA italiana, tenaamstellingscode holandes, Car-Pass belga.
5. **Chapa y pintura** · 6. **Interior y electronica** · 7. **Motor y fluidos**
8. **Prueba en carretera** · 9. **Cerrar la compra**

La lista se adapta al coche: un diesel anade filtro de particulas y AdBlue, un
automatico anade DSG, un electrico anade salud de bateria.

Cada punto tiene `weight` (cuanto pesa en la nota), `critical` (si falla, te
vas) y `repairCost` (lo que cuesta arreglarlo, que alimenta la negociacion). El
veredicto sale de `lib/scoring.ts`, y separa lo que es cuestion de precio de lo
que es motivo para levantarse de la silla.

---

## Estructura

```
app/
  page.tsx            portada y lista de coches seguidos
  buscar/             buscador multiportal
  coste/              calculadora de importacion
  revision/           revision guiada por fases
  informe/            veredicto e informe imprimible
  api/search/         fan-out a todas las fuentes
lib/
  portals.ts          URLs de busqueda de cada portal  <- editar aqui
  import-cost.ts      fiscalidad y gastos de importacion
  checklist.ts        los 103 puntos de revision
  scoring.ts          nota, veredicto y descuento
  search.ts           orquestador: paralelo, dedupe, orden
  adapters/           bridge (n8n), eBay, ejemplos
  storage.ts          expedientes en localStorage
n8n/                  flujo del puente, listo para importar
```

## Desplegar

Sale en cualquier sitio que corra Next.js (Netlify, Vercel, un contenedor en
Oracle). La ruta `/api/search` necesita servidor: si exportas estatico, pierdes
las fuentes en vivo pero los enlaces a portales siguen funcionando.

## Lo que esto no es

No es una gestoria ni un mecanico. Evita los errores de bulto y te da los
numeros para decidir, pero si el coche pasa de 15.000 euros, una inspeccion
profesional en destino cuesta 150 y los vale.
