---
tags: [coches, importacion, fraude, vin, verificacion]
status: investigacion
updated: 2026-09-20
related:
  - "[[Coche Europa — Proyecto]]"
---

# Verificación — VIN, fraude y fuentes oficiales

> Investigación de campo para la fase de revisión de [[Coche Europa — Proyecto]].
> Responde a tres preguntas: **cuánto fraude hay de verdad**, **qué herramienta
> merece la pena pagar**, y **qué de todo esto puede hacer la app sola**.

---

## Aviso de método (léelo antes de citar cifras)

Hay dos clases de números en este documento y no valen lo mismo:

- **Estudios institucionales** (Parlamento Europeo, ADAC, RDW). Muestra amplia,
  metodología publicada. Son los que hay que usar para decidir.
- **Índices de las empresas de informes VIN** (sobre todo carVertical). Son
  *marketing de contenidos*: la muestra son **las consultas de sus propios
  clientes**, no el mercado. Quien paga 20 € por un informe ya sospecha del
  coche, así que esas cifras están infladas por selección. Sirven para ordenar
  países entre sí, no como prevalencia real.

Los datos con ⚠️ no se han podido confirmar en fuente primaria durante esta
investigación. **Limitación técnica de este trabajo:** el proxy del contenedor
bloqueó por 403 el acceso directo a `carvertical.com`, `autodna.com`,
`carfax.eu`, `vindecoder.eu`, `opendata.rdw.nl`, `car-pass.be`,
`historiapojazdu.gov.pl`, `europarl.europa.eu` y `wikipedia.org`. Todo lo que
sigue viene de resultados de búsqueda y de prensa/foros que citan esas fuentes.
**Antes de publicar precios en la app hay que reconfirmarlos en la web del
proveedor.**

---

## 1. El fraude: cuánto hay y de qué tipo

### 1.1 Kilómetros manipulados — el fraude dominante

El dato que manda, y el que explica por qué existe esta app:

> **Entre el 30 % y el 50 % de los coches usados vendidos en operaciones
> transfronterizas dentro de la UE tienen el cuentakilómetros manipulado.
> En ventas domésticas, entre el 5 % y el 12 %.**
> — Estudio del Servicio de Estudios del Parlamento Europeo
> (EPRS STU 2018/615637, "Odometer manipulation in motor vehicles in the EU")

Es decir: **cruzar una frontera multiplica por 4–6 el riesgo**. No porque el
coche cambie, sino porque el historial se pierde al cruzar. El mismo estudio
cifra en **5.600–9.600 millones de euros al año** el daño económico en la UE,
sobre un mercado de **más de 60 millones de coches de segunda mano al año**.

Agravante regulatorio: **manipular el cuentakilómetros solo es delito penal en
6 de los 27 Estados miembros**. En el resto es, como mucho, una infracción
civil. Solo dos países tienen un sistema nacional de registro de kilómetros que
funcione: **Car-Pass** (Bélgica) y **Nationale Auto Pas / RDW** (Países Bajos).

**Alemania, el mercado grande.** El ADAC estima que **uno de cada tres coches
usados en Alemania circula con el cuentakilómetros falseado**, con un daño anual
en el país de unos **6.000 millones de euros** y una revalorización media del
coche manipulado de **+3.000 € por unidad**. La estimación se apoya en los
resultados de una macrorredada policial de 2011 — es una extrapolación, no un
censo, y conviene decirlo. Lo que sí está medido y es reciente: los ensayos del
ADAC demuestran que **prácticamente ningún coche actual es a prueba de
manipulación**; se hace **en menos de 60 segundos por unos 50 €** con un
aparato que se compra por internet, pese al Reglamento UE de 2017.

**Países Bajos, el mercado transparente.** El RDW registra **~163.000 vehículos
(1,8 % del parque) con lectura "ilógica"** del cuentakilómetros. Sobre coches
de origen holandés, el porcentaje con lectura ilógica es del **5,5 %**. Pero
**en coches importados a Holanda el riesgo sube a un 30–50 %** según las propias
autoridades de matriculación — hasta un "40 % de probabilidad" según la ANWB.
Traducción para nosotros: **en Holanda hay que comprar un coche holandés de
origen, no un importado revendido allí**.

**Ranking por país** (carVertical, índice 2025 — recordar el sesgo de muestra):

| Posición | País | % km manipulados |
|---|---|---|
| Peores | Letonia | 10,8 % (12,92 % sobre todos los consultados) |
| | Ucrania | 9,5 % ⚠️ (otra cita del mismo informe da 9,1 %) |
| | Lituania | 7,8 % |
| | Rumanía | 6,5 % |
| Mejores | Suiza | 1,6 % ⚠️ (otra cita da 2,1 %) |
| | Reino Unido | 2,1 % |
| | **Portugal** | **2,3 %** |
| | **Italia** | **2,9 %** |

El patrón que identifica el propio informe es sólido y coincide con el del
Parlamento Europeo: **cuantos más coches importa un país y peor está su
economía, más fraude de kilómetros tiene**. Los coches no se manipulan donde se
fabrican, se manipulan donde se revenden.

carVertical cifra la pérdida europea por kilometraje falseado en **~5.300
millones €/año** y calcula que el comprador europeo **sobrepaga un 26,3 % de
media** por un coche clocado.

### 1.2 Siniestrados reparados y vendidos como sanos

Aquí el dato de carVertical es el más llamativo del sector y el que más cuidado
hay que tener al citarlo:

| País | % de coches con daño registrado (carVertical 2025) |
|---|---|
| Polonia | **62,1 – 62,5 %** ⚠️ (las dos cifras aparecen en distintas citas) |
| Eslovaquia | 62 % |
| Alemania | 23,8 % (22,77 % en el índice 2024) |

⚠️ **Caveat obligatorio:** "daño registrado" incluye desde un parte de chapa de
300 € hasta una pérdida total. No significa "62 % de los coches polacos son
siniestros graves". Y la muestra son consultas de clientes de carVertical.
Circula también una cifra de **"84 % de los coches importados de Alemania
tienen algún daño registrado"** — procede de un blog de un concesionario bosnio
(gaga.ba), **no está verificada y no debe usarse en la app**.

**Cómo se detecta un siniestrado reparado, por orden de fiabilidad:**

1. **Medidor de espesor de pintura** — es el único método que detecta chapa
   repintada en 5 minutos sin desmontar nada (ver §4.2).
2. **Holguras asimétricas** de puertas/capó/portón → tiro de bancada.
3. **Tornillería de aletas, capó y bisagras** marcada o repintada → desmontaje.
4. **Fechas y marcas de las lunas y de los cinturones**: si un cinturón es
   posterior al coche, hubo despliegue de airbags.
5. **Soldaduras que no son de fábrica** en bajos, torretas y largueros.
6. **Informe VIN**: solo ve el siniestro si pasó por aseguradora, por taller de
   red o por subasta. **Un siniestro pagado en efectivo en un taller de barrio
   no aparece en ningún informe, nunca.** Esto es lo que explica la mitad de las
   quejas de "el informe salió limpio y el coche estaba roto".

### 1.3 El caso concreto: coches de subasta de aseguradora

Es un circuito industrial, no un caso aislado. **Copart** e **IAA (Insurance
Auto Auctions)** dominan el mercado estadounidense de salvamento y **exportan de
forma regular a Polonia, Alemania, Países Bajos, Lituania, Georgia y Ucrania**.
El ciclo es: aseguradora estadounidense declara siniestro total → subasta online
→ contenedor a Klaipeda, Gdansk, Bremerhaven o Rotterdam → reparación barata →
matriculación en la UE → reventa "sin accidentes" a 1.500–3.000 km de allí.

Un coche con **salvage title** o **rebuilt title** americano, una vez
matriculado en la UE, **empieza con el historial en blanco**: los registros
nacionales europeos no importan el título americano.

**Señales para detectarlo — y esto sí es automatizable:**

- **El WMI (3 primeros caracteres del VIN)**. Si empieza por **1, 4 o 5**
  (EE. UU.), **2** (Canadá) o **3** (México), el coche fue fabricado para el
  mercado norteamericano. Un BMW o un Mercedes con WMI americano vendido en
  Polonia es, con altísima probabilidad, un coche de subasta.
- **Detalles de homologación US**: intermitentes traseros rojos, faros con
  marcado DOT/SAE en lugar de E-mark, kilómetros en millas convertidos, ausencia
  de COC europeo, marcador de temperatura en °F.
- carVertical vende específicamente un **"US-origin alert"** y **regala esa
  función a sus partners de API** — señal de que el problema es lo bastante
  grande como para montar un producto alrededor.
- **Fotos de subasta**: es la baza real de carVertical y autoDNA. Si el coche
  pasó por Copart/IAA, el informe puede traer **las fotos del estado en que
  estaba destrozado**. Es la prueba más contundente que existe y la razón
  principal para pagar un informe en coches de Polonia, Lituania o Países Bajos.

⚠️ No se ha encontrado una cifra oficial del número de coches de salvamento
estadounidense matriculados en la UE por año.

### 1.4 Coches robados, con cargas, embargo o reserva de dominio

Es el riesgo que **no se negocia**: si el coche tiene carga, no lo matriculas en
España; si es robado, lo pierdes y pierdes el dinero.

| Riesgo | Dónde se ve | País |
|---|---|---|
| Financiación pendiente | El **Fahrzeugbrief (Teil II) está en el banco**. Si el vendedor no te da el original, hay financiación. Sin Teil II original **no hay matriculación en España** | DE |
| Gage / oposición / robo | **Certificat de situation administrative (non-gage)**, < 15 días, obligatorio por ley | FR |
| **Fermo amministrativo** (embargo) e hipotecas | Visura PRA (6 €) o consulta gratuita de existencia de gravamen en ACI | IT |
| Robo, exportación, **WOK** (prohibido circular hasta nueva inspección) | RDW / OVI, gratis y público | NL |
| Penhora / reserva de propriedade | Certidão permanente do registo automóvel (IRN) | PT |
| Zastaw rejestrowy (prenda registral) | ⚠️ Registro de prendas polaco, no verificado en esta investigación | PL |
| Cargas, precintos, embargos, concursal | Informe de cargas DGT (8,67 €) | ES |

**La base de datos de vehículos robados de Interpol (SMV) no es pública** ⚠️ —
solo accesible a fuerzas policiales; lo mismo EUCARIS, la red de intercambio
entre registros nacionales de la UE. **No hay ninguna consulta paneuropea de
robo abierta al ciudadano.** Por eso los informes VIN comerciales tienen valor
justo aquí: son el único agregador multipaís al que puede llegar un particular.

### 1.5 Fraude documental: VIN regrabado, clonado y "cut and shut"

Tres cosas distintas que se confunden:

- **Clonado (cloning)**: se copia el VIN de un coche legal y matriculado para
  tapar la identidad de uno robado o de desguace. El "original" existe y circula
  por ahí; tú compras el gemelo.
- **Ringing**: el paso siguiente — se regraba físicamente el VIN en el chasis
  para que coincida con los papeles falsificados.
- **Cut and shut**: se sueldan las mitades de dos o más coches siniestrados para
  fabricar uno "entero". Es la variante peligrosa: **el chasis no absorbe un
  impacto y en muchos casos no hay airbag**.

**Consecuencia legal, y hay que decirla sin adornos:** si compras un coche
clonado que resulta robado, **pierdes el coche y pierdes el dinero**. El
vehículo se devuelve al propietario original o a la aseguradora, y es el
comprador quien tiene que demostrar su buena fe.

**Detección (todo verificable en el sitio, y algo por foto):**

- El VIN está grabado en **varios sitios**: salpicadero (visible desde fuera del
  parabrisas), vano motor / torreta, bajo el asiento del copiloto o en el
  maletero, y en **etiquetas adhesivas de fábrica en los marcos de puerta**.
  Todos tienen que coincidir entre sí y con los papeles.
- **Marcas alrededor del VIN**: golpes de punzón desiguales, tipografía distinta,
  chapa repintada solo en esa zona, remaches nuevos en la placa, pegatina
  levantada o recolocada.
- **El VIN que devuelve la centralita por OBD** debe coincidir con el del chasis.
  Es el mejor detector de cuadro de instrumentos cambiado y de clonado, y **casi
  nadie lo comprueba**. Un lector OBD de 15 € lo lee.
- **Número de motor** y su coincidencia con la ficha.
- **Letras prohibidas**: un VIN de 17 caracteres **nunca** contiene **I, O ni Q**
  (para no confundirlas con 1 y 0). Si el "VIN" del anuncio las lleva, está
  transcrito mal o inventado.

### 1.6 Estafas puras en la compra a distancia

Es el fraude que **más dinero hace perder por operación** y el único que ocurre
**antes de ver el coche**. En España se conoce como **"phishing-car"** y la
Policía Nacional lo tiene tipificado.

**El guion, siempre el mismo:**

1. Anuncio con precio claramente por debajo de mercado. Coche "en el
   extranjero" — trabajo, traslado, divorcio, militar destinado fuera.
2. Solo responde por **email o WhatsApp**. Nunca llamada, nunca videollamada.
3. Propone una **empresa de transporte** que "hace de intermediaria y garantiza
   la operación". **La agencia no existe**, o es un clon de una real con nombre
   y logo copiados y un dominio parecido.
4. Pide una **señal** — típicamente el **50 % del precio** — por transferencia a
   una cuenta en el extranjero, a veces a nombre de un tercero.
5. Manda **documentación falsificada** del coche (permiso de circulación
   fotoshopeado, contrato con membrete) para dar credibilidad antes de la
   transferencia.
6. Cobra y desaparece.

**Reglas que no admiten excepción y que deberían ser puntos críticos de la app:**

- **Nunca una señal antes de ver el coche.** Ninguna. Ni 100 € "para
  reservarlo".
- **El transportista lo eliges tú, y lo pagas tú, después de tener el coche.**
  Si el vendedor propone la agencia, es una estafa. Sin excepciones.
- **La cuenta bancaria tiene que ser del titular** que figura en los papeles y
  del mismo país donde está el coche. IBAN de otro país = alarma.
- **Nada de Bizum, cripto, tarjetas regalo, Western Union ni "escrow"** que
  proponga el vendedor.
- **Videollamada obligatoria**: que enseñe el VIN del salpicadero y arranque el
  coche en directo. El estafador no tiene el coche y se descuelga aquí.

### 1.7 Fraudes que no estaban en nuestra lista

- **Coches inundados.** Reaparecen en otro país "ópticamente impecables y con
  ITV recién pasada". El agua deja fallos eléctricos intermitentes para siempre.
  Se detecta por óxido en tornillería bajo la moqueta, barro fino en los raíles
  de los asientos y en el hueco de la rueda de repuesto, condensación en faros y
  relojes, y olor a humedad o a exceso de ambientador.
- **Granizo reparado.** Enorme en Alemania y Austria. Se repara sin pintar
  (debolladura sin pintura) así que **el medidor de espesor no lo ve**. Se mira
  con el coche seco y luz rasante en techo, capó y portón.
- **Flota encubierta.** Coche de alquiler, taxi, VTC, autoescuela o flota
  comercial revendido como "de particular, primera mano". Desgaste que no cuadra
  con los km, restos de adhesivos, taladros tapados en el techo.
- **Borrado de memoria de averías la misma mañana.** Ver §4.2: los monitores de
  emisiones en "not ready" lo delatan.
- **DPF o catalizador vaciados** y centralita remapeada para que no dé error.
  No sale en ningún informe y es motivo de rechazo en la ITV de importación.
- **"Vendo para un amigo".** Intermediario sin factura: si el coche tiene una
  carga, no hay nadie a quien reclamar. En Alemania es además la forma habitual
  de esquivar la garantía legal del profesional (vender "como particular" un
  coche que es de un compraventa).
- **Falsos informes CARFAX.** La propia CARFAX mantiene una página avisando de
  webs que venden "informes CARFAX" baratos que son falsificaciones. Si el
  vendedor te manda un PDF de informe, **no vale**: hay que pedirlo uno mismo
  con el VIN.

---

## 2. Servicios de informe por VIN — comparativa

### 2.1 Tabla comparativa

| | **carVertical** | **autoDNA** | **CARFAX Europe** | **VIN-Info** |
|---|---|---|---|---|
| Precio informe único | ⚠️ **muy variable por mercado**: 15,99 € (DE) · 33,99 £ (UK) · rango citado 15–30 € | **24,99 €** | **hasta 39,99 €** | ⚠️ **5,90 €** |
| Packs | ⚠️ 3 y 5 informes con descuento; importes no confirmados | Packs individuales y de empresa | ⚠️ no publicados | ⚠️ — |
| Cobertura declarada | Europa + importaciones de EE. UU./Canadá | **26+ países** (Europa, EE. UU., Canadá), 15 años de datos, 50.000+ proveedores de servicio | **30 países europeos** + EE. UU. y Canadá | "casi todos los países europeos" |
| Fuerte de verdad en | Báltico, Polonia, Europa del Este, **importados de EE. UU.** (fotos de subasta) | **Polonia** (es polaca), Europa Central y del Este, EE. UU. | Amplitud europea; es la marca con más recorrido | ⚠️ sin evidencia |
| Flojo en | **Alemania** (ver abajo), Portugal, Austria | Alemania, Europa del Sur ⚠️ | ⚠️ inconsistente según mercado | ⚠️ |
| Fotos de subasta | **Sí** — su mejor baza | Sí | Parcial ⚠️ | ⚠️ |
| Alerta de origen EE. UU. | **Sí**, producto propio | ⚠️ | ⚠️ | ⚠️ |
| Comprobación previa gratis | ⚠️ | Decodificador VIN gratis | **Sí** — "free availability check": te dice **cuántos registros tiene antes de pagar** | ⚠️ |
| Valoración pública | **3,6/5 en Trustpilot ES**; ~19.000 reseñas globales | ⚠️ no recogida | ⚠️ no recogida | **Mala** — reseñas de cargos no autorizados e informes no entregados |
| **Afiliación** | **Sí, y es la mejor**: desde **25 % del valor de venta** (mín. **4 €/venta**), escalado por volumen, **sin tope**, **5 %** de sub-afiliados, cookie de **90 días**, pago mínimo **50 €**, gestor de cuenta dedicado. También vía **Awin** (programa carVertical DE) | **Sí** — `afilio.autodna.com` ⚠️ comisión no confirmada | **Débil**: programa US paga **0,40 $** por informe único y **0,80 $** por el ilimitado. ⚠️ Programa específico de la entidad europea no confirmado | ⚠️ |
| **API** | **Sí**, API de negocio; la alerta de origen EE. UU. es **gratis para partners** | **Sí** — paquete **WebAPI** con decodificador y buscadores empotrables | **Sí**, pero B2B por suscripción, contacto comercial directo, sin coste de integración pero pagando el acceso a datos | ⚠️ |

**Alternativas menores encontradas** (⚠️ ninguna verificada en profundidad):
Carlytics (8,90 €, europea, reciente — aparece publicando comparativas contra
todos los demás, así que su contenido es marketing competitivo y no fuente
neutral), Autoviza, EpicVIN, vinspy.eu, y los checks gratis alemanes
`fahrzeugschein.de` y `checkdenwagen.de` (decodifican VIN con datos técnicos del
KBA, consumo/CO2 y estado de llamadas a revisión, sin registro).

### 2.2 Cobertura real por país: lo que dicen los usuarios

**Esta es la parte que el marketing nunca cuenta, y es la más importante para
nosotros porque Alemania es nuestro mercado principal.**

> **En Alemania la protección de datos impide que ningún proveedor comercial
> obtenga historiales reales de vehículos alemanes.** Quien lo anuncia, en la
> práctica solo comprueba si el año de fabricación cuadra con los kilómetros.
> — Discusión en **motor-talk.de** (el foro de automoción más grande de
> Alemania)

Corolario, también recogido en foros alemanes: **el informe funciona mucho mejor
para coches que estuvieron matriculados en el extranjero antes de llegar a
Alemania**. Si compras un coche que ha pasado toda su vida registrado en
Alemania y reparado en efectivo, el informe sale casi vacío. carVertical afirma
haber ampliado su cobertura alemana en 2025 ⚠️ (afirmación de la propia empresa,
sin verificación independiente).

**El error de lectura más caro:** un apartado de daños vacío **no significa
"sin daños"**. Significa **"no se han encontrado datos"**. La app tiene que
decir esto de forma explícita cada vez que muestre un informe.

**Quejas documentadas en Trustpilot (carVertical):**

- Informe que salió **completamente limpio, sin financiación pendiente y con
  estado "HPI clear"**, y semanas después llegó la carta de la financiera: el
  coche **sí tenía financiación viva**.
- Informe que decía que el coche "pudo tener 20.000 £ de reparaciones" **sin dar
  un solo dato** de qué daño ni qué reparación.
- Informes que **no mostraban accidentes que el coche sí había tenido**.
- **Datos técnicos erróneos**: asientos traseros con función masaje en un
  roadster de dos plazas. Anecdótico, pero mina la confianza en todo lo demás.
- Cobros con el informe **nunca entregado**.
- La crítica más repetida y más justa: **"no aprendí gran cosa que no pudiera
  conseguir gratis en otro sitio"**.

**Veredicto honesto:** los informes VIN **no son humo, pero están mal vendidos**.
Valen mucho en un caso concreto —coche con vida en varios países, o con sospecha
de origen estadounidense— y valen poco o nada en otro —coche alemán de un solo
dueño alemán—. La regla operativa para la app:

> **El informe VIN es un complemento de la fuente oficial del país, nunca un
> sustituto.** En NL, FR, PL y BE la fuente oficial gratuita da más y mejor
> información que cualquier informe de pago. En DE, AT, IT y PT, donde no hay
> fuente pública buena, es cuando el informe se gana los 20–30 €.

### 2.3 Afiliación y API: qué nos interesa

**carVertical es, con diferencia, el mejor socio de afiliación** de los
analizados: 25 % desde el primer euro (mínimo 4 € por venta), escalado por
volumen, sin tope, cookie de 90 días, pago mínimo 50 € y un 5 % adicional por
sub-afiliados. Frente a eso, CARFAX paga **0,40–0,80 $** por venta: es
**30–50 veces menos**. autoDNA tiene programa propio pero no se ha podido
confirmar la comisión.

Lo interesante es que **los tres tienen API**, así que la integración no tiene
por qué ser un enlace de afiliado: se puede consumir el informe dentro de la app
y revenderlo con margen. El modelo API además desbloquea la alerta de origen
EE. UU. de carVertical **sin coste extra para partners**, que es justo la señal
de fraude más difícil de detectar a ojo.

---

## 3. Fuentes oficiales y gratuitas por país

### 3.1 Tabla resumen

| País | Fuente | URL | ¿Gratis? | ¿Qué da? | ¿Hace falta el titular? | ¿API? |
|---|---|---|---|---|---|---|
| **NL** 🇳🇱 | **RDW / OVI** | `ovi.rdw.nl` · datos en `opendata.rdw.nl` | **Sí, total** | Marca/modelo, **vencimiento APK**, **historial de tellerstanden con marca de "ilógico"**, **nº de titulares**, datos fiscales, ficha técnica, **CO2 NEDC y WLTP**, **robado**, **exportado**, **estado WOK**, llamadas a revisión | **No.** Basta la matrícula | **Sí — SODA/Socrata, licencia CC0, token gratis.** La mejor de Europa |
| **FR** 🇫🇷 | **HistoVec** | `histovec.interieur.gouv.fr` | **Sí** | Estado administrativo (**gage**, oposición, **robo**), **siniestros con reparación controlada por perito (VGE/VEI)**, fechas y resultados del **contrôle technique**, **historial de kilómetros**, cronología de cartes grises | **Sí.** El **vendedor** genera el informe y comparte un enlace. Ministerio del Interior, basado en el SIV | ⚠️ No pública |
| **FR** 🇫🇷 | **Certificat de situation administrative (non-gage)** | vía HistoVec / `service-public.gouv.fr` | **Sí** | Que el coche no tiene prenda ni oposición a la transferencia (OTCI) | Matrícula + datos del titular | No |
| **PL** 🇵🇱 | **Historia Pojazdu (CEPiK)** | `historiapojazdu.gov.pl` (PL/EN) | **Sí** | Ficha técnica, **todas las inspecciones**, **kilómetros anotados en cada una**, seguro OC en vigor, **nº de propietarios**, voivodato, historial de propiedad | **VIN + matrícula + fecha de la primera matriculación.** Esa fecha es la barrera: casi nunca está en el anuncio → **hay que pedírsela al vendedor** | ⚠️ No oficial. Existe un script comunitario (`github.com/krzksz/historia-pojazdu`) que prueba fechas por fuerza bruta |
| **BE** 🇧🇪 | **Car-Pass** | `car-pass.be` | **11,10 € IVA incl.** (gratis si tiene menos de 4 lecturas) | **Todos los kilometrajes oficialmente registrados** (talleres, centros de neumáticos, contrôle technique) | **Lo tramita y lo entrega el vendedor** — es **obligatorio por ley** en toda venta de usado, particular o profesional. Validez **2 meses** | ⚠️ No |
| **AT** 🇦🇹 | **Base §57a ("Pickerl")** | `kfzgutachten.at` · front-end `pickerlcheck.autoscout24.at` | **0,99 € + IVA** por informe | **Defectos y kilómetros registrados en cada inspección §57a**, seudonimizado (sin datos personales) | **Fecha de primera matriculación + matrícula o VIN** | ⚠️ No |
| **IT** 🇮🇹 | **Visura PRA (ACI)** | `aci.gov.it` · Visurenet · app ACI Space | **6 €** fijos online | Situación jurídica completa: propiedad, **fermo amministrativo**, hipotecas | **Requiere SPID / CIE / CNS** — identidad digital italiana, que un comprador español **no tiene** → hay que exigírsela al vendedor | No |
| **IT** 🇮🇹 | Consulta de gravámenes ACI | `aci.gov.it` | **Sí** | Solo **si existe o no** fermo/gravamen, sin detalle | ⚠️ | No |
| **IT** 🇮🇹 | **Portale dell'Automobilista** | `ilportaledellautomobilista.it` | **Sí** | **Revisione** (ITV italiana) y **cobertura del seguro** por matrícula | No | ⚠️ |
| **PT** 🇵🇹 | **IMT — matrícula cancelada** | `gov.pt` → "Saber se uma matrícula foi cancelada" | **Sí** | Solo si la matrícula está **cancelada** | No | No |
| **PT** 🇵🇹 | **Certidão permanente do registo automóvel (IRN)** | IRN / Loja do Cidadão | **De pago** (⚠️ importe no confirmado). Identificar titular actual **5 €**, anteriores **7 €** en Loja do Cidadão | Titular, **reserva de propriedade**, **penhoras** | Presencial o con identidad digital portuguesa | No |
| **DE** 🇩🇪 | **NO EXISTE registro público** | — | — | El **ZFZR del KBA está cerrado**: solo autoridades y organismos públicos, y solo con fin legal. **El mercado más grande de Europa es el menos verificable** | — | No |
| **DE** 🇩🇪 | Sucedáneos: **informe HU/AU** (TÜV, DEKRA, GTÜ, KÜS) + **Scheckheft** + decodificadores gratis (`fahrzeugschein.de`, `checkdenwagen.de`) | — | Informe HU: lo tiene el vendedor. Decodificadores: gratis | **El informe HU lleva los km anotados en cada inspección** → es la mejor prueba contra el maquillaje en Alemania. Los decodificadores dan datos técnicos del KBA, consumo/**CO2** y llamadas a revisión | El HU lo aporta el vendedor | No |
| **ES** 🇪🇸 | **Informe de vehículo DGT** | `sede.dgt.gob.es` | **8,67 €** (tasa 4.1, vigente a **septiembre 2026**) | Tipos: Reducido · **Completo** · Datos técnicos · **Cargas** · A mi nombre · Sin matricular. El **Completo** trae: datos administrativos, titular, municipio, **historial de ITV**, **kilometraje**, **nº de titulares**, **cargas**, datos técnicos, **llamadas a revisión pendientes**, puntuación **EuroNCAP** y mantenimiento | **Certificado digital o Cl@ve** | ⚠️ No pública |

### 3.2 Lo que hay que retener

**Solo tres países de los ocho dan historial de kilómetros gratis y sin permiso
del vendedor:** Países Bajos (RDW, el mejor con diferencia), Polonia (con la
pega de la fecha de primera matriculación) y, a 0,99 €, Austria.

**Francia y Bélgica son los mejores legalmente:** el vendedor está **obligado**
a entregar documentación que prueba el historial (non-gage < 15 días y CT
< 6 meses en Francia; Car-Pass en Bélgica). Si no la entrega, no es que sea
sospechoso: es que **está incumpliendo la ley**, y eso es información suficiente.

**Alemania es el agujero negro.** Mercado más grande, mejor oferta, y **ni
registro público ni informes comerciales fiables** por la protección de datos.
La única defensa real allí son los **informes HU sucesivos** (llevan los km) más
una **inspección profesional presencial**.

---

## 4. Verificación técnica: remota y en el sitio

### 4.1 Sin estar delante del coche

**Fotos concretas que hay que pedir** (y que la app debería generar como mensaje
listo para copiar, en el idioma del vendedor):

1. **VIN del salpicadero** fotografiado desde fuera del parabrisas, **legible y
   completo**.
2. **VIN del vano motor / torreta** y **etiqueta adhesiva del marco de puerta**.
   Los tres tienen que coincidir.
3. **Permiso de circulación completo**, las dos caras. En Alemania **Teil I y
   Teil II**. Aquí se leen los campos que valen dinero (§5.3).
4. **Cuadro de instrumentos con el motor en marcha**: kilómetros + todos los
   testigos apagados. Y otra **con el contacto dado y el motor parado**: ahí
   deben encenderse **todos** los testigos. Si falta alguno, le han quitado la
   bombilla.
5. **Informes de ITV local de los últimos 3 ciclos**, no solo el último:
   HU-Bericht (DE), procès-verbal de contrôle technique (FR), protocollo di
   revisione (IT), APK (NL), badanie techniczne (PL), §57a Gutachten (AT).
   **Cada uno lleva el kilometraje anotado** → tres puntos en una recta.
6. **Los cuatro bajos de puerta y los cuatro pasos de rueda**, con el coche seco.
7. **Hueco de la rueda de repuesto levantado** (agua, soldaduras, chapa nueva).
8. **Tapón de llenado de aceite por dentro** (emulsión = junta de culata).
9. **Última factura de taller** con fecha y kilometraje.
10. **Etiqueta de fabricación de las lunas** (marca + año) y **fecha grabada en
    los cinturones**.

**Cómo cruzar kilómetros entre revisiones (el cálculo que delata el fraude):**

- Ordena cronológicamente todas las lecturas que tengas: cada ITV, cada factura,
  el Car-Pass, el RDW, el anuncio.
- **Cualquier lectura menor que una anterior = fraude probado.** No hay
  explicación inocente salvo cambio de cuadro documentado con factura.
- Calcula **km/año entre cada par de lecturas**. La media europea está en
  15.000–20.000 km/año. **Un tramo de 3.000 km/año seguido de otro de 28.000 es
  más sospechoso que una media plana de 18.000.** El fraude típico no reduce el
  total: aplana un tramo concreto, normalmente el último.
- Contrasta con el **desgaste físico**: volante, pedales, brillo del cuero del
  asiento del conductor, reposapiés, botones más usados.

**Qué se ve en una videollamada (y no en fotos):**

- **Arranque en frío sin avisar** — pídelo por sorpresa, no concertado. Los
  3 primeros segundos: cascabeleo de cadena, humo azul/blanco/negro.
- **Ralentí** con el micro cerca del capó.
- **El VIN en directo**, que el vendedor recorra con la cámara del salpicadero
  al vano motor sin cortar.
- **Que el vendedor exista y sea el de los papeles**: que enseñe su documento de
  identidad junto al permiso de circulación. Un estafador no pasa de aquí.

### 4.2 Herramientas físicas que merecen la pena

**Medidor de espesor de pintura — la mejor inversión del viaje.**

- **Precio:** desde ~20 € los básicos; con **sonda en cable** (más precisa y
  llega a huecos) sobre 40–60 €. Rango de medida típico **0–2000 µm**.
- **Compra el que mida Fe y no-Fe**: los magnéticos baratos **no miden aluminio
  ni plástico**. Muchos capós, aletas y puertas de coches premium alemanes son
  de aluminio, y **los paragolpes son plástico y no se pueden medir con ninguno**.
  Este detalle no suele contarse y hace que medio coche quede sin medir.
- **Valores:** ⚠️ **cuidado con las cifras absolutas, varían mucho por marca y
  por capa.** Cesvimap sitúa el espesor medio de pintura de fábrica en
  **30–40 µm** (y 35–50 µm en piezas interiores), mientras que la referencia de
  campo que se maneja habitualmente para el conjunto (cataforesis + aparejo +
  base + barniz) es de **80–150 µm**. Cesvimap sí fija un techo claro:
  **una reparación no debe superar las 700 µm** de espesor total.
- **Por eso el método correcto no es el valor absoluto, es la comparación
  relativa**: mide **todas** las piezas, establece la línea base del propio
  coche (techo y pilares, que casi nunca se pintan) y busca desviaciones.
  - Pieza al doble o triple de la base del coche → **repintada**.
  - Por encima de ~500 µm → **hay masilla debajo**.
  - Diferencia grande **entre los dos lados del coche** → golpe lateral.
- **Lo que el medidor NO ve:** granizo reparado por **desabollado sin pintura**,
  y piezas **sustituidas por recambio nuevo pintado en fábrica**. Para eso, las
  holguras y la tornillería.

**Lector OBD — y aquí hay que corregir una creencia extendida.**

- Un **ELM327 Bluetooth de 15 €** con Torque, Car Scanner o OBD Auto Doctor
  **solo lee los códigos genéricos de motor y emisiones**. **No lee ABS, airbag
  (SRS) ni cambio automático**, que es exactamente donde están las averías
  caras. Para una decisión de compra **hace falta un escáner que lea todos los
  módulos**, o la app específica de marca.
- **Lo que hay que mirar, más allá de los códigos de error:**
  - **Monitores de disponibilidad de emisiones ("readiness monitors")**. El coche
    ejecuta hasta **11 autodiagnósticos**. Si aparecen en **"not ready" /
    incompletos**, la memoria se ha borrado hace poco — o se desconectó la
    batería. **Combinación letal: testigos apagados + memoria vacía + monitores
    not ready = le han borrado los fallos esta mañana.**
  - **Freeze frame** (fotograma congelado): guarda las condiciones exactas del
    último fallo. Sobrevive a veces al borrado superficial.
  - **VIN leído de la centralita vs. VIN del chasis.** Si no coinciden:
    cuadro cambiado o coche clonado. Es la comprobación de 30 segundos que más
    fraude destapa y casi nadie hace.
  - **Diésel: contadores de regeneración del DPF**, distancia desde la última
    regeneración y masa de hollín. Regeneraciones muy frecuentes o una distancia
    corta desde la última = coche de ciudad con el DPF al límite. Existen PIDs
    específicos de contador de regeneración (cuentan de 0 a 255 durante el
    proceso y vuelven a 0 al terminar).
  - **Datos en vivo** con el motor en marcha: correcciones de combustible, valores
    de sonda lambda, presión de raíl.
- ⚠️ **Corrección importante:** **leer el kilometraje real de varias centralitas
  NO se puede hacer con un OBD genérico.** Requiere software de marca —
  **VCDS/ODIS** (grupo VAG), **ISTA** (BMW), **XENTRY** (Mercedes)— que lee el km
  almacenado en motor, cambio, ABS y módulo de confort. Si esos valores no
  coinciden con el cuadro, el fraude está probado. **Esto lo hace un taller o un
  perito, no el comprador con un dongle**, y es una de las razones de peso para
  contratar inspección profesional.

### 4.3 Inspección profesional en destino

**Alemania (precios 2026):**

| Servicio | Precio |
|---|---|
| TÜV Rheinland **Proficheck** | **29,90 €** |
| DEKRA **Technik-Check** (módulo básico) | **49 €** |
| DEKRA **check completo de usado** | **90–150 €** (según paquete; los superiores incluyen **medición de espesor de pintura** y análisis detallado de accidente) |
| TÜV Nord **Complete** (~80 puntos) | **~89 €** |
| TÜV Süd | **79–300 €** según delegación |
| ADAC | **128–160 €** (turismo estándar, Renania del Norte); **ADAC Premium Múnich 299 €**. **Socios: 15–20 % de descuento**. **El ADAC es regional: no hay precio nacional único** |
| Horquilla total del mercado alemán 2026 | **29,90 € – 299 €** |

**Francia:**

| Nivel | Precio |
|---|---|
| Diagnóstico visual en taller | **80–150 €** |
| **Inspección profesional de ~100 puntos** (DEKRA, Norauto Pré-Achat, Cartem) | **200–350 €** |
| Expertise completa con informe | **200–400 €**, +20–50 % en coches premium o antiguos, **+30–80 €** de desplazamiento |
| Por zona | Metrópolis regionales (Lyon, Marsella, Burdeos, Toulouse, Lille) **270–340 €**; zona rural **230–290 €** |
| Expertise contradictoria con desmontaje ligero | **400–600 €** |

**Bélgica:** DEKRA Belgique ofrece evaluación de vehículos de ocasión
(`dekra.be`). ⚠️ Precio no confirmado.
**Austria:** ÖAMTC y la Arbeiterkammer ofrecen servicios a socios (la AK regala
el "Pickerl-Protokoll" a sus afiliados). ⚠️ Precios de inspección no confirmados.
**Italia y Portugal:** ⚠️ no se ha localizado un equivalente estandarizado y
contratable a distancia. Es un hueco real.

⚠️ **No se ha podido confirmar** si estos servicios se pueden contratar y pagar
**desde España** ni con cuánta antelación hay que reservar. **Es la primera cosa
que hay que verificar antes de convertirlo en función de la app**, porque de eso
depende todo el modelo.

**El cálculo que hay que enseñarle al usuario:** 90 € de DEKRA en Múnich frente
a un viaje de 400 € en avión, hotel y tren, o frente a un DSG de 1.800 €. **Es
la inversión con mejor retorno de toda la operación**, y es precisamente en
Alemania —donde no hay registro público ni informe VIN fiable— donde más falta
hace.
