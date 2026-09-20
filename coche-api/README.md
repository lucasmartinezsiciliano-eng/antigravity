# coche-api

Metabúsqueda de coches usados en Europa. **Bajo demanda, sin índice propio.**

Pones los filtros una vez y consulta todas las fuentes a la vez: APIs oficiales
donde las hay, enlaces profundos donde no, y adaptadores de lectura para el
resto. Devuelve una sola lista, con el mismo vocabulario para todos los
mercados y sin anuncios repetidos.

```bash
npm install
npm start                    # http://localhost:8080
npm run probe                # qué fuentes hay y cuáles están activas
npm test
```

Node 22+. Sin paso de compilación: lo que se lee en el repo es lo que corre.

---

## Por qué no hay un índice

Esta es la decisión de diseño de la que cuelga todo lo demás, y no es estética.

El BGH alemán, en el caso **AUTOBINGOOO (I ZR 159/10, 2011)**, declaró que un
metabuscador que consulta **bajo demanda de un usuario concreto** no vulnera el
derecho *sui generis* de base de datos de un portal de coches. El TJUE, en
**CV-Online Latvia (C-762/19, 2021)**, va en la misma línea: sólo hay
infracción cuando se perjudica la inversión del fabricante de la base de datos.

Lo que esa jurisprudencia ampara es buscar **en el momento, para una persona**.
Lo que no ampara es copiarse el catálogo y montar una base de datos paralela.

De ahí salen tres reglas que el código cumple:

1. **Se consulta cuando alguien busca.** No hay rastreo programado ni cola de
   indexación.
2. **No se guarda nada.** Sólo una caché en memoria de 60 segundos, para no
   pedir dos veces lo mismo durante una misma sesión de búsqueda.
3. **Cada fuente declara bajo qué régimen opera**, y el motor lo respeta.

### Lo que esto NO resuelve

El derecho de bases de datos y las condiciones de uso de un portal son cosas
distintas. Ninguna sentencia anula un contrato: la mayoría de estos portales
prohíben el acceso automatizado en sus términos, y eso sigue siendo un riesgo
para quien despliegue esto con los adaptadores de HTML encendidos.

Por eso **esos adaptadores vienen apagados** y encenderlos es una decisión
explícita de quien opera el servicio, no del código:

```bash
PROVIDERS_ENABLED=autoscout24-html,mobile-de-html
```

No es un tecnicismo ni una forma de escurrir el bulto: es que esa decisión
depende de dónde estés, de para qué lo uses y de tu tolerancia al riesgo, y
ninguna de esas tres cosas las sabe un fichero de configuración por defecto.

---

## Regímenes

| Régimen | Qué es | ¿Encendido de fábrica? |
|---|---|---|
| `deeplink` | Construye la URL de búsqueda del portal. No descarga nada: es lo que hace un navegador. | Sí |
| `official-api` | API pública del portal, con credenciales propias. | Sí, si hay credenciales |
| `open-data` | Datos abiertos de un organismo público (RDW, AEMA). | Sí |
| `feed` | Feed que el vendedor publica para ser distribuido. | Sí |
| `html` | Lectura del HTML público bajo demanda. | **No** |

## Fuentes incluidas

**Enlace profundo (12)** — AutoScout24 (multipaís), mobile.de, Kleinanzeigen,
Leboncoin, La Centrale, Subito, Marktplaats, 2dehands, Otomoto, Standvirtual, y
Coches.net y Milanuncios como referencia de precio en España.

**API oficial** — eBay Browse API. Gratuita; alta en
[developer.ebay.com](https://developer.ebay.com).

**Lectura de HTML (apagados)** — AutoScout24 y mobile.de.

> Los descriptores de HTML están escritos sobre la estructura habitual de cada
> portal pero **no se han podido verificar contra las páginas reales**: el
> entorno donde se escribieron tiene esos dominios bloqueados. Antes de fiarte
> de ninguno, ejecútalo desde tu red con `npm run probe`.

---

## La API

### `GET /search`

```bash
curl "localhost:8080/search?make=BMW&model=Serie+3&priceTo=20000&countries=DE,FR"
```

También acepta `POST` con el mismo objeto en JSON. Parámetros: `make`, `model`,
`q`, `yearFrom/To`, `priceFrom/To`, `kmFrom/To`, `powerFrom/To`, `co2To`,
`fuel`, `gearbox`, `body`, `seller`, `countries`, `limit`, `sort`.

Respuesta:

```json
{
  "schemaVersion": "1.0",
  "listings": [ { "id": "ebay:12345", "title": "BMW 320d", "price": 24500, "km": 95000, "...": "..." } ],
  "providers": [ { "provider": "mobile-de", "status": "solo-enlace", "searchUrl": "https://suchen.mobile.de/..." } ],
  "deduped": 3,
  "ms": 842,
  "warnings": []
}
```

Cada fuente reporta su `status`: `ok`, `vacio`, `solo-enlace`,
`sin-credenciales`, `bloqueado-robots`, `limite-alcanzado`, `timeout` o
`error`. **Una fuente que falla no tumba la búsqueda**, y una lenta no la
bloquea: cada una tiene su plazo y la que no llega se reporta como `timeout`.

### `GET /providers` · `GET /health` · `POST /bridge`

`/providers` lista el catálogo con el régimen de cada fuente. `/bridge` habla
el contrato que espera [`coche-europa`](../coche-europa), para que la app se
conecte cambiando una variable:

```bash
BRIDGE_URL=http://localhost:8080/bridge
```

---

## El esquema

Está en [`src/schema.ts`](src/schema.ts) y es la parte que de verdad importa:
un mismo coche se describe de once maneras distintas según quién lo publique.

Tres reglas:

- **Unidades del SI y euros.** La conversión la hace el adaptador, no quien
  consume la API. Si el portal publica en kW, el adaptador da `power` en CV y
  `powerKw` en kW.
- **Lo que no se sabe es `undefined`**, nunca `0` ni `""`. Un coche sin precio
  publicado no vale cero euros.
- **Un campo presente es un dato observado.** Lo que se calcula o se deduce va
  en `derived`, con su fuente y su nivel de confianza.

La traducción de vocabulario vive en [`src/normalize.ts`](src/normalize.ts):
*Schaltgetriebe*, *boîte mécanique*, *cambio manuale* y *manual* son la misma
cosa, y hasta que no lo son de verdad no se pueden comparar dos anuncios. Ahí
está también el diccionario de modelos por mercado: buscar "Serie 3" en un
portal alemán no devuelve nada, porque allí es un **3er**.

---

## Añadir un portal

Un adaptador no es código, es un objeto que dice dónde mirar. Eso es lo que
decide si un proyecto así sobrevive: cuando un portal cambie su maquetación —y
lo hará— arreglarlo es editar tres selectores, no entender el motor entero.

En [`src/providers/html/descriptors.ts`](src/providers/html/descriptors.ts):

```ts
const miPortal: Descriptor = {
  meta: { id: "miportal", name: "MiPortal", countries: ["DE"], rateLimitPerMin: 6 },
  url: (q) => `https://miportal.example/buscar?q=${encodeURIComponent(queryText(q, "de"))}`,
  strategies: [
    { kind: "json-ld", types: ["Car", "Vehicle"] },
    { kind: "embedded-json", varName: "__NEXT_DATA__", path: "props.pageProps.listings" },
    { kind: "selectors", item: "article.anuncio", fields: {
        url:   { sel: "a", attr: "href" },
        title: { sel: "h2" },
        price: { sel: ".precio" },
        km:    { sel: ".km" },
    } },
  ],
};
```

Se prueban en ese orden y vale la primera que devuelve algo:

1. **`json-ld`** — schema.org en `<script type="application/ld+json">`. Es dato
   estructurado que el portal publica **a propósito** para Google: cambia
   poquísimo y viene ya etiquetado. Empieza siempre por aquí.
2. **`embedded-json`** — el estado que el portal deja en la página
   (`__NEXT_DATA__`, `__INITIAL_STATE__`). Muy completo y bastante estable.
3. **`selectors`** — CSS sobre el HTML. Lo último, porque es lo primero que se
   rompe. Usa atributos `data-*` antes que clases: las clases llevan hash y
   cambian en cada despliegue.

Luego compruébalo contra el portal de verdad:

```bash
npm run probe -- miportal --make BMW --model "Serie 3" --verbose
```

Dice qué estrategia entró, cuántos anuncios salieron y enseña el primero campo
a campo con un porcentaje de cobertura, para ver de un vistazo si el mapeo está
bien.

### Cómo portarse bien

Todo lo que sale a internet pasa por [`src/http/fetcher.ts`](src/http/fetcher.ts),
y ahí se cumplen cuatro cosas: identificarse de verdad, respetar `robots.txt`,
no pasarse de ritmo (serializado por host, con `Crawl-delay`) y no pedir dos
veces lo mismo. No es cortesía: es lo que separa una metabúsqueda de un scraper
que acaba bloqueado en una semana.

Si `robots.txt` no se puede leer, **no se asume permiso**: se reporta
`bloqueado-robots` y se sigue con el resto de fuentes.

---

## Lo que falta

- **CO2 por modelo desde el dataset de la AEMA** (Reglamento UE 2019/631):
  gratis, cubre todos los Estados miembros y es el dato que decide si en España
  pagas 0% o 14,75% de impuesto de matriculación. Hace falta pre-agregarlo,
  porque el original va a nivel de matriculación. Ojo: **WLTP sólo existe de
  2019-2020 en adelante**.
- **RDW de Países Bajos** como fuente de enriquecimiento: datos abiertos CC0
  con API, y da kilómetros oficiales con marca de "ilógico".
- **Feeds de concesionarios de exportación**, que es la vía limpia para tener
  inventario real: cero riesgo legal, pero es trabajo comercial, no técnico.
- Verificar los descriptores de HTML contra los portales reales.

## Licencia

MIT. Ver [LICENSE](LICENSE).

Esto es una herramienta de búsqueda; el uso que se le dé es responsabilidad de
quien la despliegue. Antes de encender los adaptadores de HTML, lee las
condiciones del portal en cuestión.
