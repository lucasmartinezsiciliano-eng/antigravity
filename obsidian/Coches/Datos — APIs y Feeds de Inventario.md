---
tags: [coches, importacion, apis, datos, tecnico]
status: investigacion
updated: 2026-09-20
related:
  - "[[Coche Europa — Proyecto]]"
---

# Datos — APIs y Feeds de Inventario

> **Respuesta corta:** no existe ninguna vía legal, asequible y estable para agregar
> el inventario de los grandes portales europeos. Ninguno vende acceso de lectura a
> terceros. Lo que sí existe, y es barato, es el dato técnico de CO2 — gratis y oficial.

**Nota metodológica.** Investigación hecha solo con documentación pública. El contenedor
bloquea por política de red (403) *todos* los dominios relevantes: `services.mobile.de`,
`developer.olxgroup.com`, `developer.ebay.com`, `apify.com`, `carapis.com`,
`b2b.autouncle.com`, `carapi.app`, `www.eea.europa.eu`, `discodata.eea.europa.eu`.
**No se ha podido probar ninguna API en vivo ni leer ningún T&C original.** Todo lo que
viene de resumen de buscador y no de la fuente primaria va marcado con ⚠️.

---

## 1. APIs oficiales de los portales

El patrón se repite en los once portales: **todos tienen API, todas son de escritura.**
Están hechas para que un concesionario (o su software) *meta* coches en el portal, no
para que nadie los *saque*.

### mobile.de — la única con una Search API documentada

Es la excepción interesante. mobile.de publica una familia de APIs REST en
[services.mobile.de](https://services.mobile.de/): Seller API, **Search API**, Ad Stream e
Insights API. La [documentación de la Search API](https://services.mobile.de/docs/search-api.html)
describe algo muy parecido a lo que necesitamos:

- REST, auth por HTTP Basic, respuesta en JSON o XML (legacy y nuevo).
- Traducción de los campos según cabecera `Accept-Language`.
- Paginación **limitada a 2.000 anuncios por búsqueda** (100 páginas de 20).
- Menos campos que la descarga directa por `ad-key`.

El problema es el acceso. Hay dos tipos de cuenta: *Dealer-Account* (credenciales
autoservicio desde el área de concesionario) y **API-Account**, que es la que puede tener
la Search-API activada y **solo se consigue contactando con atención al cliente**.

⚠️ Según fuentes secundarias, el acceso "está restringido a concesionarios registrados y
socios de software con fines de gestión de inventario, y **no está disponible para estudios
de mercado, inteligencia de precios ni recolección de datos por terceros**". No he podido
leer el [T&C original](https://www.mobile.de/en/service/agb_search_api_2016_en.pdf) —
dominio bloqueado. **Esta frase, si es literal, nos deja fuera.**

Coste: ⚠️ para un concesionario, el uso de la interfaz *sobre su propio stock* va incluido
en la cuota mensual del paquete (Silber/Gold/Platin), sin coste por vehículo ni por clic.
Para un tercero que quiera leer todo el marketplace **no hay precio publicado**: es contrato
comercial a medida.

**Lectura honesta:** la Search-API existe y técnicamente serviría. Pero el camino para
conseguirla es "llama a ventas de mobile.de y explícales que quieres construir un
buscador que compite con su buscador". No es un formulario de alta.

### AutoScout24 — API solo de escritura, más una interfaz de escaparate

La única superficie pública es la **Listing Creation API**
([swagger](https://listing-creation.api.autoscout24.com/assets/swagger/spec/index.html)):
crear anuncio, subir fotos, publicar, actualizar, borrar. **No hay endpoint de búsqueda ni
de navegación.** No se puede consultar precio, ficha ni vendedor por canal oficial.

Lo que sí hay para concesionarios, y es gratis, son las
[interfaces de socio](https://www.autoscout24.de/partner-infoportal/schnittstellen/), entre
ellas **HCI (Home Customer Interface)**, hoy **HCI-JSON v3+**: replica automáticamente *los
anuncios propios del concesionario* en la web del propio concesionario, en tiempo real.
Nueva versión desde abril 2025; la anterior se desconectó el 1 de octubre de 2025.

Es decir: **read access sí existe, pero con ámbito "mi stock", no "el mercado".** Eso es
justo lo que nos sirve para la vía 4 (feeds de concesionario) y lo que no nos sirve para
la vía 1 (agregar portales).

### Leboncoin — API de multidifusión, solo entrada

[leboncoin Solutions Pro](https://leboncoinsolutionspro.fr/logiciels-partenaires-api/) lista
los *logiciels partenaires* conectados a su API. Sin coste de conexión, y desde octubre de
2026 los anuncios publicados vía API tendrán un plus de visibilidad. Todo eso es para
**publicar**. Para leer no hay nada: guías francesas del sector lo dicen sin rodeos —
["Pourquoi l'API Leboncoin n'existe pas"](https://stream.estate/fr/blog/api-leboncoin-pourquoi-elle-n-existe-pas-et-les-alternatives-possibles).

### La Centrale, Otomoto, Standvirtual — ahora todos OLX Group

Cambio relevante de 2025: **OLX Group (Prosus) compró La Centrale por 1.100 M€** a
Providence ([nota de prensa](https://www.olxgroup.com/news/prosuss-olx-group-agrees-to-acquire-la-centrale-a-leading-motors-classifieds-platform-in-france-for-eur1-1-billion-from-providence/)),
cierre previsto a final de año. Con eso, Otomoto (PL), Standvirtual (PT), Autovit (RO) y
La Centrale (FR) quedan bajo el mismo paraguas.

OLX tiene un programa de desarrolladores de verdad:
[developer.olxgroup.com](https://developer.olxgroup.com/) con API Key + OAuth2,
[términos](https://developer.olxgroup.com/terms-and-conditions) y catálogo de
[productos](https://developer.olxgroup.com/products). Pero:

- **La documentación técnica solo se ve con la cuenta ya aprobada.**
- ⚠️ "No todos los partners registrados son elegibles para integrar."
- **No hay entorno de pruebas**: se integra directamente contra producción.
- Hay que pedir credenciales **por marketplace**, uno a uno; OLX y Motors van separados.
- El propósito declarado es que los clientes profesionales gestionen sus anuncios —
  otra vez, escritura.

⚠️ No he podido confirmar si existe algún endpoint de lectura/búsqueda: el hub está
bloqueado y los docs están tras aprobación.

### Subito, Marktplaats, 2dehands, Kleinanzeigen, coches.net, Milanuncios

Ninguno tiene API pública de lectura para terceros. Lo único que aparece buscando son
*scrapers* de Apify y proyectos de GitHub que hacen ingeniería inversa de la API interna
de la app (p. ej. [ebay-kleinanzeigen-api](https://github.com/DanielWTE/ebay-kleinanzeigen-api)),
que no es un canal oficial y se rompe cuando quieran.

En España, además, hay movimiento societario: coches.net, Milanuncios e InfoJobs
[pasan de Adevinta a EQT](https://www.eu-startups.com/2025/07/coches-net-infojobs-and-milanuncios-to-join-eqts-growing-southern-europe-portfolio/)
(acuerdo de julio 2025). En una transición de propiedad, la probabilidad de que abran una
API a terceros es todavía más baja.

---

## 2. Agregadores y revendedores de datos

### Los americanos no cubren Europa continental

- **Marketcheck** — el mejor del gremio, pero es **EE.UU. + Reino Unido y nada más**. En UK
  presume de [680.000 anuncios y 11.000 concesionarios](https://marketcheck.uk/products/used-car-market-data-api)
  con dos años de histórico de precio por anuncio. **Sin cobertura de DE / FR / ES / IT.**
  Sin precio publicado: "prueba gratis" y hablar con ventas.
- **Auto.dev** — millones de anuncios activos, VIN decode, recalls, pagos… mercado
  estadounidense. No sirve.
- **CarAPI (carapi.app)** — no es inventario, es catálogo de marcas/modelos/versiones.
  Precio claro y barato: **199 $/año (Base) y 249 $/año (Plus)**, con dataset público para
  prototipar. Centrado en year/make/model de EE.UU.
- **CarAPI.dev** — producto distinto del anterior, ⚠️ afirma VIN + matrícula + historial de
  inspecciones (MOT, TÜV) + valoraciones con cobertura US/CA/Europa y 20M+ registros.
  Afirmaciones de proveedor, sin verificar y sin precio localizado.
- **DataForSEO** — ⚠️ es un proveedor de datos de SERP/SEO. No he encontrado ningún
  producto suyo de anuncios de automoción. Descartado por irrelevante.

### El proveedor europeo de verdad: AutoUncle

[AutoUncle](https://www.autouncle.com/) (Aarhus, Dinamarca) es exactamente lo que nosotros
queremos ser: metabuscador que agrega **10,8 millones de anuncios de más de 2.600 fuentes
en 14 mercados europeos**, evaluando 8,6M+ anuncios vivos al día. Tiene
[oferta B2B/enterprise y una API de automoción](https://b2b.autouncle.com/en-gb/automotive-api),
y más de 1.000 concesionarios usan sus datos para fijar precio.

⚠️ No he podido leer su web (bloqueada): **no sé si licencian anuncios en bruto a terceros
ni a qué precio.** Es la llamada comercial más sensata que podríamos hacer, pero hay que
asumir que venden a concesionarios y OEMs, no a una app competidora, y que el precio es de
contrato anual enterprise.

### Los datos técnicos y de valoración: JD Power (ex-Autovista)

JD Power cerró en 2024 la compra de Autovista Group y con ella **Eurotax, Glass's y
Schwacke**: el oligopolio del dato técnico y de valor residual en Europa. Productos:
[AutovistaSPEC](https://www.jdpower.com/business/autovistaspec/) (fichas técnicas
paneuropeas, refresco diario, normalizadas entre mercados),
[AutovistaVALUATION](https://www.jdpower.com/business/autovista-valuation/) (valores
residuales armonizados) y [AutovistaAPI](https://www.jdpower.com/business/autovista-api/)
(identificación de cualquier vehículo europeo por código único). **DAT y JATO** juegan en
la misma liga.

**Ninguno publica precios.** Son contratos enterprise con comercial, mínimos anuales y
normalmente licencia por uso. ⚠️ Sin presupuesto real no me invento cifras, pero por el
tipo de producto y de cliente no es algo que encaje en un proyecto de una persona.

### Scraping como servicio: los precios sí son públicos

Aquí sí hay números concretos, y conviene mirarlos porque son la tentación:

| Proveedor | Precio | Nota |
|---|---|---|
| Apify — actores AutoScout24 | **0,49 – 2 $ / 1.000 anuncios** | varios actores: 0,002 $/resultado, 0,9 $/1.000, 0,49 $/1.000 |
| Apify — actor mobile.de | **~0,8 $ / 1.000 anuncios** | "Unlimited Search & Detail" |
| Apify — Subito, Marktplaats, Standvirtual, coches.net, Milanuncios, AutoUncle | similar | hay actor para casi cada portal |
| Bright Data | **desde 0,75 $ / 1.000 peticiones** con éxito; Web Scraper API **3 $ / 1.000 cargas** | sin compromiso mensual |
| Oxylabs | **~1,60 $ / 1.000 resultados** | |
| ScrapingBee | **desde 49 $/mes** por créditos | JS rendering y proxy premium multiplican el consumo |
| Carapis | ⚠️ sin precio público | revende datos raspados de mobile.de, AutoScout24, etc. |

**La cuenta que importa.** Dos modelos:

- **Bajo demanda** (raspar solo cuando el usuario busca): ~5 portales × 50 fichas = 250
  resultados ≈ **0,25 $ por búsqueda**. Con 1.000 búsquedas/mes son **~250 $/mes**. Asumible
  en dinero, pero cada búsqueda tarda 10–30 s por portal y el usuario se va.
- **Índice propio refrescado a diario**: 200.000 anuncios × 30 días = 6M resultados/mes ≈
  **6.000 $/mes**. Incluso una versión mini de 20.000 anuncios son **~600 $/mes**. Inviable.

Y esto es solo el coste en dinero. El coste real es otro: **rompe constantemente** (cambian
selectores, meten Cloudflare, rotan parámetros) y **nos traslada a nosotros la
responsabilidad legal** del proveedor. Apify o Bright Data no firman que tengamos derecho a
usar esos datos; solo nos venden la fontanería. Si llega la carta, llega a nuestro nombre.

**No recomiendo esta vía como base del producto.** Ni la de Carapis, que es lo mismo con
una capa de API encima para que parezca oficial.

---

## 3. eBay Browse API — la tenemos bien, pero el inventario es residual

**Lo bueno:**
- **Es gratis.** No hay tarifa por usar las Buy/Browse APIs del eBay Developers Program.
- **Límite por defecto: 5.000 llamadas/día por aplicación**, ampliable gratis vía
  *Application Growth Check*.
- **Cubre los marketplaces europeos**: `EBAY_DE`, `EBAY_FR`, `EBAY_IT` están en
  [MarketplaceIdEnum](https://developer.ebay.com/api-docs/buy/browse/types/ba:MarketplaceIdEnum),
  vía cabecera `X-EBAY-C-MARKETPLACE-ID` — que es justo lo que hace `lib/adapters/ebay.ts`.
- eBay confirma que en los marketplaces internacionales los vehículos se publican en las
  [categorías de automoción normales](https://developer.ebay.com/api-docs/user-guides/static/trading-user-guide/ebay-motors-categories.html)
  de ese sitio, no en un eBay Motors aparte.

**Dos fallos concretos de nuestra implementación:**

1. **Categoría equivocada.** Usamos `9800`, que en eBay.de es *"Auto & Motorrad: Fahrzeuge"* —
   incluye motos. La categoría de coches es **`9801` ("Automobile")**. Cambiando eso se
   quita ruido de golpe.
2. **Las categorías no son las mismas en cada marketplace.** `9801` vale para `EBAY_DE`;
   ⚠️ para `EBAY_FR` y `EBAY_IT` hay que mapear sus propios IDs (no verificado). Hoy el
   adaptador tiene el ID hardcodeado y el país fijado a `DE`.

**El límite de fondo, que no se arregla tocando código:** la Browse API filtra bien por
precio, país y tipo de compra, pero **km, año de matriculación, potencia y cambio no son
filtros de primera clase** — van como `aspect_filter`, que es específico de categoría y con
cobertura desigual en anuncios de coches. O sea: la mitad de nuestro formulario de filtros
no se puede trasladar a eBay.

**Y el inventario.** eBay.de tiene coches ([categoría 9800/9801](https://www.ebay.de/b/Automobile/9801/bn_1845328)),
pero en Alemania el mercado de coche usado es mobile.de (~1,3M anuncios) y AutoScout24
(~2,5M). Lo de eBay es marginal y sesgado: clásicos, siniestros, subastas raras.
⚠️ El único dato reciente que he encontrado es que Hertz abrió tienda en eBay con ~8.000
coches de alquiler certificados (mayo 2026), descrito como "vuelta de eBay al negocio del
automóvil" — pero parece operación estadounidense y no lo he podido confirmar para Europa.

**Veredicto eBay: enciéndela, porque es gratis y ya está escrita, pero no la vendas como
"búsqueda real".** Es un extra, no una fuente. Coste de arreglarla bien: media tarde.

---

## 4. Feeds de concesionarios — la única vía limpia, y es trabajo comercial

### Qué estándares hay

**No existe un estándar paneuropeo único.** No hay equivalente al ADF/IMT americano. Lo que
hay es una capa de traducción:

- **Cada portal define su formato de importación**: mobile.de (Seller API + Ad Stream,
  XML/JSON), AutoScout24 (Listing Creation API + HCI-JSON), OLX/Otomoto/Standvirtual
  (Partner APIs), Leboncoin (multidifusión).
- **Los DMS exportan a todos ellos.** Keyloop (ex-CDK International), Motiondata Vector,
  Autrado, attRiBut, incadea y los "Autohaus-Software" alemanes soportan SOAP/REST/XML/JSON
  y también el clásico fichero por FTP (CSV/XML). Ver p. ej. las
  [interfaces de exportación a portales de Autrado](https://www.autrado.de/schnittstellen.php).
- **Estándares de facto de marketing que el concesionario ya genera**: el *vehicle inventory
  feed* de Google Vehicle Ads y el catálogo de Meta Automotive Inventory Ads. ⚠️ No he podido
  leer la especificación (support.google.com bloqueado), pero es el formato que más
  proveedores de web de concesionario emiten hoy, y es el que yo pediría primero.

### ¿Puede un tercero acceder?

**Técnicamente, trivial.** El concesionario (o su proveedor de multidifusión) te da una URL
con un XML/CSV/JSON de su stock, con fotos, y se refresca cada pocas horas. Cero fricción
de ingeniería.

**Comercialmente, no hay atajo.** No existe ningún mercado abierto de feeds de concesionario
en la UE. Hay que firmar: o con cada concesionario, o con el proveedor de distribución que
le fanoutea el stock (que es el punto de integración inteligente, porque uno solo te trae
decenas de concesionarios).

### Cuánto trabajo comercial es: el dato que duele

**heycar** es el experimento controlado. Respaldado por Volkswagen, SEAT y Daimler, con
modelo gratis-para-el-concesionario (solo pagaban por lead), llegó en España a
[unos 600–650 concesionarios y ~30.000 coches](https://www.thenewbarcelonapost.com/heycar-plataforma-comprar-coches-segunda-mano-concesionarios/),
ocho de cada diez seminuevos de la red oficial. Y aun así
[cerró España en agosto de 2023](https://www.autofacil.es/heycar-cierra-espana/).

Si con dinero de tres fabricantes y un modelo sin coste para el concesionario no salió,
nosotros no vamos a construir "todos los portales de Europa" firmando concesionarios.

### Pero hay una versión pequeña que sí funciona

**No necesitamos toda Europa. Necesitamos concesionarios alemanes y franceses que quieran
vender a españoles.** Existen, están especializados en exportación, y para ellos somos un
canal, no un competidor:

- 10–30 concesionarios de exportación × 100–300 coches = **1.000–9.000 coches reales**.
- Todos precalificados para exportar: saben lo que es un COC, los papeles de aduana, las
  placas de tránsito y el transporte a España. Justo lo que nuestra checklist da por
  problemático.
- Coste de integración: **0 €** (ellos ya generan el feed).
- Coste comercial: llamadas, correo y paciencia. Semanas, no meses, para los primeros cinco.

Eso no es "buscar en todos los portales". Es otra cosa, y probablemente mejor: es
**inventario propio, exclusivo y legal** que ningún otro buscador español tiene.

---

## 5. Datos técnicos y CO2 — aquí sí hay una victoria gratis

El CO2 decide el tramo de IEDMT (0 / 4,75 / 9,75 / 14,75 %). Hoy la app aplica el tramo
máximo cuando no hay dato, que es lo correcto pero pesimista. Se puede hacer mejor, gratis.

### La mina: el dataset de CO2 de la Agencia Europea de Medio Ambiente

El Reglamento (UE) 2019/631 obliga a **cada Estado miembro a reportar, por cada turismo
nuevo matriculado**: fabricante, número de homologación, **tipo / variante / versión**,
marca y **nombre comercial**, **CO2 en NEDC y en WLTP**, masas, batalla, vía, cilindrada,
**potencia**, tipo y modo de combustible, ecoinnovaciones y consumo eléctrico.

La EEA lo publica **gratis y completo**:

- Ficha del dataset: <https://www.eea.europa.eu/en/datahub/datahubitem-view/fa8b1229-3db6-495d-b18e-9c9b3267c02b>
- Serie histórica: <https://www.eea.europa.eu/data-and-maps/data/co2-cars-emission-22>
- Visor interactivo: <https://co2cars.apps.eea.europa.eu/>
- **API (DISCODATA)**: SQL sobre REST devolviendo JSON — <https://discodata.eea.europa.eu/>
  (ayuda en `/Help.html`). Consultas del tipo:
  ```sql
  SELECT TOP 100 * FROM [CO2Emission].[latest].[co2cars_2025Pv31]
  SELECT TOP 1000 * FROM [CO2Emission].[latest].[co2cars] WHERE year = 2018 AND status = 'F'
  ```
  `status`: `P` = provisional, `F` = final. Conviene filtrar siempre uno u otro para no
  duplicar. Formatos de descarga: CSV/TXT/SQL y MS Access.

⚠️ **No verificado en vivo**: `discodata.eea.europa.eu` también está bloqueado en este
contenedor (403 en el CONNECT). Lo primero que hay que hacer al implementarlo es lanzar una
consulta real desde fuera.

**Tres avisos honestos sobre este dataset:**

1. **Es a nivel de matriculación, no de modelo.** Son decenas de millones de filas por año.
   No se empaqueta tal cual en la app: hay que pre-agregar a
   `(marca, nombre comercial, combustible, cilindrada, potencia, año)` → CO2 WLTP
   mínimo/mediano/máximo. Eso baja a unos pocos MB de JSON o un SQLite.
2. **El campo de nombre comercial lo rellena el fabricante y está sucio** ("GOLF",
   "Golf VII", "Golf 7"). Casar el título libre de un anuncio contra eso es *el* trabajo
   real. Normalización + fuzzy matching, y aun así habrá fallos: por eso el resultado debe
   presentarse como estimación, nunca como dato fiscal.
3. **WLTP solo existe de 2019–2020 en adelante.** Para un coche de 2015 solo hay NEDC, y los
   tramos españoles del IEDMT están definidos sobre WLTP. Convertir NEDC→WLTP con un factor
   es una aproximación grosera; para coches anteriores a 2020 seguimos dependiendo del papel.

### España: IDAE

[coches.idae.es](https://coches.idae.es/base-datos) — base de datos oficial de consumo,
emisiones y etiqueta energética de los turismos nuevos a la venta en España, con
[histórico](https://coches.idae.es/historico-emisiones-consumos) y
[búsqueda por intervalo de emisiones](https://coches.idae.es/base-datos/intervalo-de-emisiones).
Los datos los aportan fabricantes y distribuidores. Gratis de consultar y buena referencia
cruzada para la etiqueta. ⚠️ No he encontrado descarga masiva ni API documentada: hay guías
en PDF y consulta web.

### Lo más barato y más fiable de todo: el papel del coche

El **COC (Certificado de Conformidad)** lleva el CO2 WLTP oficial de ese vehículo concreto,
y es el documento que Tráfico y Hacienda aceptan. Y antes incluso del COC, el permiso de
circulación armonizado de la UE (Directiva 1999/37/CE) tiene códigos comunes: **el campo
`V.7` es el CO2 en g/km** — en la *Zulassungsbescheinigung Teil I* alemana, en la *carte
grise* francesa y en la *carta di circolazione* italiana. ⚠️ Conviene verificarlo contra un
documento real antes de ponerlo en la app.

Eso significa que **el mejor "API de CO2" que tenemos es pedirle al vendedor una foto del
permiso de circulación** y leer el campo V.7. Coste: 0 €. Fiabilidad: máxima. Y encaja con
lo que la checklist ya hace en la fase 1 ("todo por WhatsApp antes de coger el avión").

### Los de pago

**AutovistaSPEC / AutovistaAPI (JD Power)**, **DAT**, **Schwacke**, **JATO**: fichas técnicas
paneuropeas normalizadas y de calidad real. **Sin precio publicado**, venta enterprise. Para
nosotros, sobredimensionado: el 95 % del valor está en el dataset gratuito de la EEA más el
campo V.7 del permiso.

---

## 6. Legalidad

### Raspar portales: el matiz es quién raspa y para quién

La base de datos de anuncios de un portal **sí está protegida** por el derecho *sui generis*
de la Directiva 96/9/CE — los tribunales alemanes reconocieron expresamente que la de
AutoScout24 lo está. Extraer o reutilizar una **parte sustancial** está prohibido.

Pero hay dos sentencias que cambian el cuadro, y las dos nos favorecen *en un modelo
concreto*:

**BGH, 22.06.2011 — I ZR 159/10 ("AUTOBINGOOO").** El Tribunal Supremo alemán resolvió que
un **metabuscador de coches que lee AutoScout24 y otros portales por encargo de cada usuario
NO vulnera el derecho de base de datos ni compite deslealmente**, porque cada usuario
individual extrae solo una parte insustancial. Recorrido: LG Hamburg dio la razón al portal,
el OLG Hamburg la revocó (5 U 101/08 y 5 U 62/09) y el BGH lo confirmó.
[Resumen](https://www.dr-bahr.com/news/datenbankrecht-von-autoscout24de-nicht-durch-autobingooo-software-verletzt.html) ·
[texto](https://www.online-und-recht.de/urteile/Keine-Rechtsverletzung-der-Auto-Online-Boerse-AUTOBINGOOO-an-autoscout24-de-I-ZR-159-10-Bundesgerichtshof--20110622/)

**TJUE, 03.06.2021 — C-762/19 (CV-Online Latvia c. Melons).** Un metabuscador especializado
que indexa anuncios y enlaza de vuelta **solo infringe el derecho sui generis si perjudica la
inversión del fabricante de la base de datos**, privándole de los ingresos con los que la
amortiza. El Tribunal metió explícitamente en el test el acceso a la información y la
competencia. [Caso](https://ipcuria.eu/case?reference=C-762%2F19) ·
[análisis](https://www.twobirds.com/en/insights/2021/uk/cv-online-latvia-cjeu-complicates-the-enforcement-of-database-rights)

**La frontera que dibujan las dos, y que nos afecta directamente:**

| | Riesgo |
|---|---|
| Consulta bajo demanda, por usuario, que devuelve al portal | **Bajo** (AUTOBINGOOO + CV-Online) |
| Índice propio, rastreo masivo, el usuario se queda en nuestra app | **Alto** (parte sustancial + perjuicio a la inversión) |

Es decir: **justo el modelo que nos haría el producto bonito — índice propio, rápido, sin
salir de la app — es el que legalmente es peor.**

### Las condiciones de uso pesan aunque no haya derecho de base de datos

**TJUE C-30/14, Ryanair c. PR Aviation (2015)**: si la base **no** está protegida por copyright
ni por derecho sui generis, las excepciones de la Directiva no aplican y el operador **puede
restringir el uso por contrato**. Los T&C son exigibles.
[Resumen](https://www.pinsentmasons.com/out-law/news/website-operators-can-prohibit-screen-scraping-of-unprotected-data-via-terms-and-conditions-says-eu-court-in-ryanair-case)

En la UE, incumplir unos T&C es materia civil: requerimiento de cese, medidas cautelares y
costas. No es delito.

### El riesgo que de verdad corre una app pequeña

Por orden de probabilidad, y siendo realista:

1. **Bloqueo técnico** (casi seguro): Cloudflare, challenge, ban de IP. No es un riesgo
   legal, es que deja de funcionar.
2. **Carta de cese** (*Abmahnung* en Alemania) si crecemos lo bastante para que nos vean.
   ⚠️ Coste típico no verificado con fuente actual, pero está en el orden de miles de euros
   entre abogados y costas.
3. **Demanda** (raro para un proyecto pequeño, pero el que la pone es quien tiene abogados
   en nómina y nosotros no).
4. **Y el que más nos debería preocupar: RGPD.** Los anuncios de particulares contienen datos
   personales — nombre, teléfono, ubicación, a veces matrícula visible. Guardarlos en base
   propia es tratamiento de datos personales sin base jurídica y sin forma razonable de
   cumplir el deber de información del art. 14. Hay además
   [Directrices 03/2026 del CEPD sobre scraping](https://www.edpb.europa.eu/system/files/2026-07/edpb_guidelines_2020603_webscraping_v1_en_0.pdf).
   **Esto, para una app española, es más peligroso que el derecho de base de datos.**

### ¿Es legal lo que hacemos ahora? Sí, sin matices

Construir una URL de búsqueda y abrirla en una pestaña **no es extracción ni reutilización**.
No copiamos nada, no almacenamos nada, y mandamos al usuario al portal — que es exactamente
lo que el portal quiere. Enlazar a contenido libremente accesible no es comunicación al
público (TJUE C-466/12, *Svensson*) ⚠️ (cita de memoria, no re-verificada en esta sesión).

Lo único que hay que cuidar, y es fácil:

- **No enmarcar** (`iframe`) las páginas del portal dentro de la nuestra.
- **No usar sus logos ni sus marcas** como si hubiera acuerdo. Nombre en texto plano.
- **Decirlo**: una línea de "no estamos afiliados a ninguno de estos portales".
- No presentar sus resultados como nuestros.

---

## Tabla comparativa

| Fuente | Cobertura | Coste | Requisitos | Viabilidad para nosotros |
|---|---|---|---|---|
| **mobile.de Search API** | DE, ~1,3M anuncios | ⚠️ sin precio público (contrato) | API-Account aprobado por atención al cliente; ⚠️ T&C excluirían a terceros | ❌ Muy baja. Merece *una* llamada, no un plan |
| **AutoScout24 Listing Creation API** | 9 países | Gratis | Cuenta de concesionario | ❌ Solo escritura, no hay búsqueda |
| **AutoScout24 HCI-JSON** | Stock del concesionario | Gratis | Ser (o representar a) el concesionario | ✅ Útil, pero solo para la vía de feeds |
| **Leboncoin multidifusión** | FR | Gratis (sin coste de conexión) | Ser software partner | ❌ Solo publicación |
| **OLX Group Partner API** (Otomoto, Standvirtual, Autovit, La Centrale) | PL, PT, RO, FR | ⚠️ sin precio público | Alta aprobada por marketplace; sin entorno de pruebas | ❌ Baja. Orientada a gestión de inventario |
| **Subito, Marktplaats, 2dehands, Kleinanzeigen** | IT, NL, BE, DE | — | — | ❌ No hay API de lectura |
| **coches.net / Milanuncios** | ES | — | — | ❌ No hay API; además en cambio de dueño (EQT) |
| **eBay Browse API** | DE/FR/IT (y más) | **Gratis** · 5.000 llamadas/día | Alta en developer.ebay.com | 🟡 Sí, pero inventario residual y filtros pobres |
| **Marketcheck** | 🇺🇸 + 🇬🇧 solo | Sin precio público | Contrato | ❌ No cubre Europa continental |
| **Auto.dev / CarAPI / CarAPI.dev** | 🇺🇸 (specs) | CarAPI 199–249 $/año | Alta | ❌ Para inventario europeo, no |
| **AutoUncle B2B** | 14 países, 10,8M anuncios | ⚠️ sin precio público | Contrato enterprise | 🟡 La mejor llamada posible. Asumir que dirán que no |
| **Autovista / Eurotax / Schwacke / DAT / JATO** | Europa (fichas + valores) | Sin precio público, enterprise | Contrato anual | ❌ Fuera de escala para este proyecto |
| **Apify / Bright Data / Oxylabs / ScrapingBee** | Todos los portales | 0,49–3 $ / 1.000 resultados | Tarjeta | ⚠️ Barato bajo demanda (~0,25 $/búsqueda), caro en índice (600–6.000 $/mes). **Riesgo legal y de mantenimiento nuestro** |
| **Carapis** | 200+ marketplaces | ⚠️ sin precio público | Alta | ❌ Es scraping con capa de API. Mismo riesgo, menos control |
| **Feeds de concesionario (directo)** | El stock que firmes | **0 €** técnico | Acuerdo con cada concesionario o distribuidor | ✅ **La única vía limpia.** Trabajo comercial, no técnico |
| **EEA CO2 (Reg. 2019/631)** | Toda la UE, matriculaciones nuevas | **Gratis** | Ninguno | ✅✅ **Hacerlo ya** |
| **IDAE** | ES, turismos nuevos | **Gratis** | Ninguno | ✅ Buena referencia cruzada; ⚠️ sin API |
| **Campo V.7 del permiso de circulación** | El coche concreto | **0 €** | Pedir foto al vendedor | ✅✅ Lo más fiable de todo |
| **Enlaces profundos (lo que ya hacemos)** | 13 portales, 9 países | **0 €** | Ninguno | ✅ Legal, estable y honesto |

---

## Fuentes consultadas

Documentación técnica: [services.mobile.de](https://services.mobile.de/) ·
[Search API mobile.de](https://services.mobile.de/docs/search-api.html) ·
[Seller API mobile.de](https://services.mobile.de/docs/seller-api.html) ·
[AutoScout24 Listing Creation (Swagger)](https://listing-creation.api.autoscout24.com/assets/swagger/spec/index.html) ·
[AutoScout24 Schnittstellen](https://www.autoscout24.de/partner-infoportal/schnittstellen/) ·
[HCI-JSON](https://b2b.autoscout24.ch/neue-hci-json-schnittstelle-flexibler-schneller-zukunftssicher/) ·
[OLX Developer Hub](https://developer.olxgroup.com/) ·
[leboncoin Solutions Pro](https://leboncoinsolutionspro.fr/logiciels-partenaires-api/) ·
[eBay Browse API](https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search) ·
[eBay MarketplaceIdEnum](https://developer.ebay.com/api-docs/buy/browse/types/ba:MarketplaceIdEnum) ·
[eBay API call limits](https://developer.ebay.com/develop/get-started/api-call-limits)

Datos: [EEA datahub CO2](https://www.eea.europa.eu/en/datahub/datahubitem-view/fa8b1229-3db6-495d-b18e-9c9b3267c02b) ·
[DISCODATA](https://discodata.eea.europa.eu/Help.html) ·
[co2cars viewer](https://co2cars.apps.eea.europa.eu/) ·
[IDAE base de datos](https://coches.idae.es/base-datos) ·
[Reglamento (UE) 2019/631](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32019R0631) ·
[AutovistaSPEC](https://www.jdpower.com/business/autovistaspec/) ·
[Marketcheck UK](https://marketcheck.uk/products/used-car-market-data-api)

Legalidad: [BGH I ZR 159/10](https://www.online-und-recht.de/urteile/Keine-Rechtsverletzung-der-Auto-Online-Boerse-AUTOBINGOOO-an-autoscout24-de-I-ZR-159-10-Bundesgerichtshof--20110622/) ·
[TJUE C-762/19](https://ipcuria.eu/case?reference=C-762%2F19) ·
[Ryanair c. PR Aviation](https://www.pinsentmasons.com/out-law/news/website-operators-can-prohibit-screen-scraping-of-unprotected-data-via-terms-and-conditions-says-eu-court-in-ryanair-case) ·
[Directrices CEPD 03/2026](https://www.edpb.europa.eu/system/files/2026-07/edpb_guidelines_2020603_webscraping_v1_en_0.pdf)

Mercado: [OLX compra La Centrale](https://www.olxgroup.com/news/prosuss-olx-group-agrees-to-acquire-la-centrale-a-leading-motors-classifieds-platform-in-france-for-eur1-1-billion-from-providence/) ·
[EQT compra coches.net y Milanuncios](https://www.eu-startups.com/2025/07/coches-net-infojobs-and-milanuncios-to-join-eqts-growing-southern-europe-portfolio/) ·
[AutoUncle](https://www.autouncle.com/) ·
[heycar cierra España](https://www.autofacil.es/heycar-cierra-espana/)

---

## Veredicto: ¿se puede buscar en todos los portales de verdad?

**No.** Y no es cuestión de presupuesto ni de talento técnico: es que nadie vende lo que
necesitaríamos comprar.

Tres razones, por orden de peso:

1. **No hay producto que comprar.** De los once portales, **ninguno ofrece a un tercero una
   API de lectura de su inventario.** mobile.de tiene una Search API documentada, pero cerrada
   tras aprobación manual y ⚠️ con términos que, según las fuentes secundarias, excluyen
   expresamente el uso por terceros para agregación. AutoScout24 y Leboncoin solo tienen API
   de escritura. OLX tiene programa de partners, pero para gestionar anuncios y con
   documentación bajo aprobación. Los demás no tienen nada.

2. **Es estructural, no accidental.** El inventario *es* el producto de un portal. Una app
   que agrega los anuncios de mobile.de y AutoScout24 en una lista ordenada por precio les
   quita exactamente aquello por lo que sus clientes les pagan. No nos van a vender la cuerda.
   Y la consolidación de 2025 (OLX se lleva La Centrale por 1.100 M€, EQT se lleva coches.net
   y Milanuncios) empuja en la dirección contraria a abrir datos.

3. **La única vía técnica que existe — raspar — es la que peor combina con nuestro caso.**
   La jurisprudencia europea (AUTOBINGOOO, CV-Online) protege el metabuscador *bajo demanda
   que devuelve tráfico al portal*, y condena el *índice propio que retiene al usuario*.
   O sea: protege casi exactamente lo que ya hacemos con enlaces profundos, y no protege lo
   que querríamos hacer. Y por encima está el RGPD: los anuncios de particulares son datos
   personales y almacenarlos en base propia no tiene base jurídica defendible.

**Lo que sí se puede hacer, y es distinto:** tener inventario real, propio y exclusivo vía
feeds de concesionarios de exportación; y ser mucho mejores que nadie en la parte que sí
controlamos — coste real, CO2 y revisión.

---

## El camino recomendado

En este orden. El 1 y el 2 se pueden hacer esta semana; el 3 es un mes; el 4 solo si el 3 va bien.

### 0. Quedarnos como estamos, en lo que respecta a los portales — **sí, es lo correcto**

Los enlaces profundos de `lib/portals.ts` no son un apaño provisional: son **la solución
legalmente sólida** al problema, y la única que no se rompe cada dos semanas. La traducción
de modelo por mercado (`C-Klasse` / `Classe C`) es la parte difícil y ya está hecha.
**Coste: 0 €. Esfuerzo: 0. Decisión: mantener y dejar de buscarle sustituto.**

### 1. CO2 gratis desde el dataset de la EEA — **el mayor retorno de todo el informe**

Hoy, sin CO2, aplicamos el 14,75 % y la app dice a todo el mundo que el coche sale caro. Con
el dataset de la EEA acertaríamos el tramo en la mayoría de coches de 2020 en adelante.

- Descargar los años relevantes (2015–2025) desde DISCODATA o CSV.
- Pre-agregar a `(marca, nombre comercial, combustible, cilindrada, potencia, año)` →
  CO2 WLTP mediano + rango.
- Empaquetar como JSON/SQLite de pocos MB dentro de la app.
- Presentarlo siempre como **estimación** con su rango, y mantener el 14,75 % como
  supuesto cuando no haya match.

**Coste: 0 €. Esfuerzo: 2–3 días**, de los cuales el 80 % es normalizar nombres comerciales.

### 2. Arreglar y encender eBay — **media tarde**

Alta gratis en developer.ebay.com, `EBAY_CLIENT_ID` / `EBAY_CLIENT_SECRET` en el entorno,
cambiar la categoría de `9800` a `9801` y hacer el mapa de categoría por marketplace.
**Coste: 0 €. Esfuerzo: media tarde.** Expectativa: pocas decenas de coches útiles. Que
aparezca marcado como "eBay" y nada más.

### 3. Feeds de concesionarios de exportación — **el producto de verdad**

- Identificar 20–30 concesionarios alemanes y franceses que ya exporten a España.
- Pedirles su feed (Google Vehicle Ads, mobile.de export, HCI-JSON, o un CSV; todos tienen
  algo). A ellos no les cuesta nada y ganan un canal.
- Implementarlo **detrás del `BRIDGE_URL` que ya existe**: un flujo en n8n que lea los feeds,
  normalice al tipo `Listing` y los sirva. La app no se entera de nada.
- Objetivo realista: **1.000–5.000 coches reales** de vendedores que ya saben exportar.

**Coste: 0 € técnico** (el n8n del Oracle ya está). **Esfuerzo: semanas de trabajo comercial,
no de código.** Los primeros cinco concesionarios dirán cuánto vale la pena seguir.

### 4. Solo si el 3 funciona: una llamada a AutoUncle

⚠️ Sin precio público y con expectativa baja de que licencien a una app competidora. Pero es
la única empresa europea que tiene el dato agregado de 14 mercados. **Una llamada, y si la
respuesta es "contrato enterprise", se cierra la puerta y no se vuelve.**

### Lo que NO hay que hacer

- **No montar scraping propio ni contratar Apify/Bright Data/Carapis como base del producto.**
  Números: ~0,25 $ por búsqueda bajo demanda (lento y frágil) o 600–6.000 $/mes para un índice
  (inviable). Y nos comemos nosotros el riesgo de T&C y de RGPD que el proveedor no asume.
- **No pagar por Marketcheck, Auto.dev ni CarAPI** para inventario: no cubren Europa continental.
- **No perseguir la Search API de mobile.de como plan.** Si alguien quiere probar, que sea una
  llamada de 20 minutos, no una línea del roadmap.

---

## Qué implica para la app

### Cambios técnicos concretos

| Fichero | Cambio |
|---|---|
| `lib/adapters/ebay.ts` | Categoría `9800` → **`9801`** (coches, no motos) en `EBAY_DE`. Hacer `CATEGORIA_COCHES` un mapa por `X-EBAY-C-MARKETPLACE-ID`; ⚠️ falta confirmar los IDs de `EBAY_FR` / `EBAY_IT`. Derivar `country` del marketplace en vez de fijar `"DE"` |
| `lib/import-cost.ts` | Aceptar un CO2 **estimado con rango** además del introducido a mano. Que el coste se calcule con el tramo estimado pero muestre el peor caso al lado |
| `lib/` (nuevo) | `co2-db.ts` + dataset pre-agregado de la EEA. Función `estimarCO2(marca, modelo, año, combustible, potencia)` → `{ wltp, rango, confianza }` |
| `app/coste/` | Nuevo estado del CO2: *confirmado por el vendedor* (campo V.7) · *estimado EEA* · *desconocido → 14,75 %*. Que se vea cuál de los tres es |
| `lib/checklist.ts` | Añadir a la fase 1 (WhatsApp, antes de viajar): **"foto del permiso de circulación — campo V.7 = CO2 g/km"**. Es el dato que decide miles de euros de impuesto y cuesta un mensaje |
| `n8n/coche-europa-bridge.json` | Implementar `Fetch Listings From Source` como lector de feeds de concesionario (XML/CSV/JSON → `Listing`). El contrato del puente ya está bien diseñado: **no hay que tocar la app para enchufar inventario** |
| `app/buscar/` | Una línea visible de "no estamos afiliados a estos portales". Nombres de portal en texto plano, sin logos, sin `iframe` |

### ¿Hay que replantear la promesa del producto?

**Sí, y en dos frases.**

La promesa actual — *"pon los filtros una vez y busca en todos los portales europeos"* — no
se puede cumplir con una lista unificada de resultados, y lo que la app hace hoy (13 pestañas
con los filtros ya puestos) es honesto pero no es eso. El riesgo no es legal, es de
expectativa: el usuario lee "busca en todos" y espera una lista.

Dos ajustes, ninguno cosmético:

1. **Cambiar el verbo.** De *"buscamos en 13 portales"* a **"lanzamos tu búsqueda, ya
   filtrada y traducida, en 13 portales de 9 países"**. Es lo que hace, es útil de verdad, y
   la traducción de modelo por mercado (`Serie 3` → `3er`) es un valor real que ningún portal
   te da. Se cumple al 100 %.

2. **Mover el centro de gravedad del producto.** El buscador no es el foso defensivo —
   cualquiera abre trece pestañas. **El foso son las otras tres pantallas:** el coste real
   matriculado, el CO2 que decide el tramo, y los 70 puntos de revisión. Ahí es donde nadie
   más está, y ahí es donde el dataset de la EEA y el campo V.7 nos hacen objetivamente
   mejores que la alternativa.

Y si la vía 3 (feeds de exportadores) cuaja, la promesa cambia otra vez, pero a mejor y con
verdad detrás: **"coches de concesionarios alemanes y franceses que ya exportan a España,
con el coste final calculado"**. Eso no lo tiene ningún portal español, y no necesita permiso
de nadie.
