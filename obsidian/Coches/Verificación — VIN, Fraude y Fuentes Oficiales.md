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

---

## 5. Lo que puede automatizar la app

### 5.1 Validación del VIN y dígito de control

**Formato.** 17 caracteres. **Nunca contiene I, O ni Q.** Solo letras mayúsculas
y dígitos. Estructura ISO 3779: posiciones 1–3 **WMI** (fabricante y país de
fabricación), 4–9 **VDS** (descriptor del vehículo), 9 **dígito de control**,
10 **año-modelo**, 11 **planta**, 12–17 **número de serie**.

**Algoritmo del dígito de control** (posición 9), según ISO 3779 / 49 CFR 565:

1. **Transliterar** cada carácter a número:
   - Dígitos `0-9` → su propio valor.
   - `A=1 B=2 C=3 D=4 E=5 F=6 G=7 H=8`
   - `J=1 K=2 L=3 M=4 N=5 P=7 R=9`
   - `S=2 T=3 U=4 V=5 W=6 X=7 Y=8 Z=9`
   - (`I`, `O`, `Q` no existen en un VIN)
2. **Multiplicar** cada posición por su peso, en orden 1→17:
   `8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2`
   (la posición 9 pesa **0**: es el propio dígito de control)
3. **Sumar** los 17 productos y calcular el **resto de dividir entre 11**.
4. Ese resto es el dígito de control. **Si el resto es 10, el dígito es la letra
   `X`.**

```ts
const MAP: Record<string, number> = {
  A:1,B:2,C:3,D:4,E:5,F:6,G:7,H:8, J:1,K:2,L:3,M:4,N:5,P:7,R:9,
  S:2,T:3,U:4,V:5,W:6,X:7,Y:8,Z:9,
};
const W = [8,7,6,5,4,3,2,10,0,9,8,7,6,5,4,3,2];

function vinCheckDigit(vin: string): string {
  const v = vin.toUpperCase();
  let sum = 0;
  for (let i = 0; i < 17; i++) {
    const c = v[i];
    const n = /[0-9]/.test(c) ? Number(c) : MAP[c];
    if (n === undefined) throw new Error("caracter invalido en VIN");
    sum += n * W[i];
  }
  const r = sum % 11;
  return r === 10 ? "X" : String(r);
}
```

> ⚠️ **AVISO CRÍTICO, y es el error que comete casi todo el que implementa
> esto:** el dígito de control **solo es obligatorio en vehículos fabricados
> para el mercado norteamericano** (49 CFR 565). **Muchísimos coches europeos
> vendidos en Europa NO tienen un dígito de control válido y son perfectamente
> legítimos.**
>
> **En la app: un dígito de control que no cuadra NO puede mostrarse como
> "VIN falso" ni bloquear nada.** Como mucho, una nota informativa. Lo que sí
> debe bloquear: longitud distinta de 17, o presencia de I/O/Q.
>
> Donde sí es útil: si el dígito **sí valida**, es un indicio fuerte de que el
> coche es **de origen norteamericano** → cruzar con el WMI (§5.2).

### 5.2 Decodificación del VIN: qué API usar para qué

| Fuente | Coste | Cobertura | ¿Da CO2? | Para qué la usamos |
|---|---|---|---|---|
| **Tabla WMI propia** (estática, 3 primeros caracteres) | **0 €** | Global | No | **Detección de importación de EE. UU.**: WMI que empieza por **1, 4, 5** (EE. UU.), **2** (Canadá) o **3** (México) en un coche vendido en la UE → **bandera roja automática**. Es gratis, instantáneo y detecta el fraude de subasta |
| **NHTSA vPIC** `vpic.nhtsa.dot.gov/api` | **0 €, sin registro, 24/7** | **Solo vehículos vendidos o importados en EE. UU.** | **No** | Decodificación completa **únicamente si el coche resultó ser americano**. Para un Golf alemán no devuelve nada útil |
| **Vincario / vindecoder.eu** | **3 consultas/mes gratis** sin tarjeta; después **~0,20–0,50 €/consulta** según volumen. Se pausa sola al agotar cuota | **Mercado europeo** — ~40 campos de media | **Sí: "average CO2 emission (g/km)"** | La **única API VIN→CO2 europea** encontrada. Ver caveat abajo |
| **RDW Open Data** `opendata.rdw.nl` | **0 €**, licencia **CC0**, token gratis, SODA/SoQL | **Solo Países Bajos**, por **matrícula** (el RDW no publica VIN, por privacidad) | **Sí: CO2 NEDC + `Emissie co2 gecombineerd wltp`** | Enriquecimiento **completo y gratis** de cualquier anuncio holandés |
| **Base CO2 de la AEMA/EEA** (Reglamento (UE) 2019/631) | **0 €**, descarga masiva CSV/TXT/SQL/Access | **UE-27 + Reino Unido + Islandia**, todas las matriculaciones nuevas desde 2010 | **Sí: CO2 NEDC y WLTP oficiales**, más masas, batalla, cilindrada, potencia, combustible, ecoinnovaciones, consumo eléctrico | **La joya.** Ver §5.3 |

**Caveat que hace o rompe la calculadora de impuestos:** una API que devuelve el
**"CO2 medio"** de un VIN está dando la media del **modelo**, no el valor
homologado de **esa variante y versión concretas** con esas llantas y ese
equipamiento. Nuestros tramos son **<120 / 120-159 / 160-199 / ≥200**, y un
mismo modelo puede cruzar un tramo solo por la medida de llanta. **Un error de
15 g/km puede significar pasar del 4,75 % al 9,75 %.** Por tanto:

> **Un CO2 obtenido por API se muestra siempre como *orientativo* y nunca se
> usa como valor definitivo del cálculo del IEDMT.** El valor bueno es el del
> documento.

### 5.3 CO2: la cadena de confianza, de mejor a peor

Dado que la app aplica **el tramo máximo (14,75 %) cuando no hay dato de CO2**
—como hace Hacienda—, acertar aquí vale literalmente miles de euros. Orden de
prioridad que debería implementar la app:

1. **Campo `V.7` del permiso de circulación.** El certificado de matriculación
   está **armonizado en toda la UE**, y **`V.7` es el CO2 en g/km**. En el
   Fahrzeugschein alemán (Zulassungsbescheinigung Teil I) es la base legal del
   impuesto de circulación desde 2021. **Es el dato oficial de ese coche
   concreto.** → **La app debe pedir una foto del permiso y extraer `V.7`.**
   Es la mejora de mayor impacto y menor coste técnico de todo este informe.
2. **COC (certificado de conformidad), apartado `V.7`** — mismo valor, ya
   contemplado en la checklist.
3. **Base de datos CO2 de la AEMA (Reglamento (UE) 2019/631).** Cada Estado
   miembro está **obligado a reportar, por cada turismo nuevo matriculado**:
   fabricante, **número de homologación de tipo**, **tipo, variante y versión**,
   marca, nombre comercial, **CO2 NEDC y WLTP**, masas, batalla, cilindrada,
   potencia, combustible y consumo eléctrico. Y resulta que el permiso de
   circulación trae exactamente esas claves:
   - **`K`** = número de homologación de tipo
   - **`D.2`** = tipo / variante / versión
   → **Con `K` + `D.2` leídos del permiso se localiza el registro oficial y se
   obtiene el CO2 WLTP exacto.** Es gratis, es la fuente legal original, y
   funciona para **los ocho países**. Se descarga una vez y se carga en nuestra
   base (Supabase/Postgres) como tabla de consulta.
   - Visor: `co2cars.apps.eea.europa.eu` · Datos: EEA DataHub.
4. **RDW** (solo NL, gratis, por matrícula) — CO2 NEDC y WLTP directos.
5. **Decodificadores alemanes gratuitos** (`fahrzeugschein.de`,
   `checkdenwagen.de`): dan consumo y valores de CO2 del KBA a partir del VIN,
   sin registro. ⚠️ Sin API documentada; habría que negociar o descartar.
6. **Vincario** (~0,30 €/consulta) como último recurso, **etiquetado como
   estimación**.

⚠️ **No confirmado en esta investigación:** la API **DVLA Vehicle Enquiry
Service** del Reino Unido, que devuelve `co2Emissions` gratis por matrícula.
Sería irrelevante para nuestros ocho países, pero conviene anotarlo.

### 5.4 Enriquecimiento automático de un anuncio: lo que ya es posible hoy

Con solo **VIN + matrícula + país**, sin pagar nada:

- Validar formato del VIN, letras prohibidas, longitud.
- **WMI → país de fabricación → bandera de importación norteamericana.**
- Si es **NL**: llamada al RDW y se rellena solo **marca, modelo, ficha técnica,
  CO2 WLTP, vencimiento de APK, número de titulares, historial de kilómetros con
  la marca de "ilógico", estado WOK, robado y exportado**. Un anuncio holandés
  queda **verificado en un segundo y gratis**.
- Construir los **enlaces profundos** a la fuente oficial del país con los datos
  que el usuario ya ha metido (HistoVec, historiapojazdu, kfzgutachten.at,
  Portale dell'Automobilista, sede DGT).
- **Motor de coherencia de kilómetros**: el usuario introduce las lecturas de
  cada ITV y la app calcula km/año por tramo, marca **cualquier retroceso** y
  señala **los tramos anómalos**, no solo la media.
- **Generar el mensaje al vendedor en su idioma** con la lista exacta de fotos y
  documentos (§4.1). Cero coste, altísimo valor percibido.

---

## Ranking de riesgo por país

Hay que separar dos cosas que se confunden siempre: **cuánto fraude hay** y
**cuánto puedes comprobar tú**. Un país con fraude medio pero verificación total
(Países Bajos) es mucho más seguro que uno con fraude medio y cero verificación
(Alemania).

| # | País | Prevalencia de fraude | Verificabilidad | Riesgo neto | El dato que lo respalda |
|---|---|---|---|---|---|
| 1 | 🇩🇪 **Alemania** | Alta | **Nula** | **🔴 El más alto para nuestro usuario** | **1 de cada 3** usados con cuentakilómetros falseado (ADAC), ~6.000 M €/año de daño. **No hay registro público** (el ZFZR del KBA está cerrado) **y la protección de datos impide a carVertical/autoDNA obtener historiales alemanes reales** (motor-talk). Es el único de los ocho donde **ni pagando** consigues historial fiable |
| 2 | 🇵🇱 **Polonia** | **La más alta de la UE** | Buena y gratis | 🔴 Alto | **62,1–62,5 % de coches con daño registrado**, el peor de Europa (carVertical 2025, con el sesgo de muestra advertido). **Hub de reventa de salvamento estadounidense** (Copart/IAA exportan allí de forma regular) y **~20 % de su parque usado viene de Alemania**. Mitigante fuerte: `historiapojazdu.gov.pl` es **gratis y da los km de cada inspección** |
| 3 | 🇮🇹 **Italia** | **Baja (2,9 % km)** | Mala a distancia | 🟠 Medio-alto | Poco fraude de kilómetros, pero el riesgo es **jurídico**: el **fermo amministrativo** y las hipotecas solo se ven en la **visura PRA**, que cuesta 6 € y **exige SPID/CIE italiano**, que un comprador español **no tiene**. Dependes de que el vendedor te la saque |
| 4 | 🇵🇹 **Portugal** | **Muy baja (2,3 % km)** | Mala | 🟠 Medio | De los mercados **más limpios** de Europa en kilometraje, pero **no hay consulta pública de historial**: solo la certidão permanente del IRN, de pago y presencial. Mercado pequeño, poca oferta interesante |
| 5 | 🇦🇹 **Austria** | Media-baja ⚠️ | **Buena, por 0,99 €** | 🟡 Medio-bajo | La base **§57a** de `kfzgutachten.at` entrega **defectos y kilómetros de cada inspección por 0,99 €**. Pega: hay que saber la **fecha de primera matriculación**. Ojo con el **granizo** reparado sin pintura |
| 6 | 🇧🇪 **Bélgica** | Media ⚠️ | **Muy buena, por ley** | 🟡 Medio-bajo | El **Car-Pass es obligatorio en toda venta de usado**, incluso entre particulares: **11,10 €** (gratis con menos de 4 lecturas), **lo tramita el vendedor** y recoge todos los kilometrajes oficiales. **Si no te lo dan, están incumpliendo la ley.** Contra: **óxido por la sal** del invierno |
| 7 | 🇫🇷 **Francia** | Media ⚠️ | **Excelente y gratis** | 🟢 Bajo | **Triple obligación legal** que juega a favor del comprador: **HistoVec** gratis del Ministerio del Interior (siniestros con peritaje, CT, **historial de km**, gage, oposición, robo), **certificat de non-gage < 15 días** obligatorio, y **contrôle technique < 6 meses** obligatorio para vender |
| 8 | 🇳🇱 **Países Bajos** | Baja **en coches de origen holandés** | **La mejor de Europa** | **🟢 El más seguro** | **RDW / OVI: público, gratuito, sin permiso del vendedor y por matrícula.** Da APK, **historial completo de tellerstanden con la marca oficial de "ilógico"**, nº de titulares, **robado**, **exportado**, **WOK** y **CO2**. Solo **1,8 % del parque** con lectura ilógica; 5,5 % entre los de origen holandés. **PERO ⚠️ el 30–50 % de los coches IMPORTADOS a Holanda tienen el cuentakilómetros retocado → hay que comprar coche holandés de origen y mirar el número de titulares** |

**Conclusión operativa:**

- **Comprar en Países Bajos o Francia es medible.** Ahí la app puede dar una
  respuesta casi definitiva antes de que el usuario salga de casa.
- **Comprar en Alemania es apostar**, salvo que se añada **inspección
  profesional presencial** (DEKRA/TÜV, 30–150 €) y **los tres últimos informes
  HU**. Y Alemania es donde está el 60 % de la oferta interesante, así que **ahí
  es donde la app tiene que ser más dura**: en Alemania, la inspección
  profesional no debería ser una sugerencia sino un punto crítico.
- **Polonia tiene la peor materia prima pero buenas herramientas gratis.** Con
  `historiapojazdu` + bandera de WMI americano + informe VIN con fotos de
  subasta, el riesgo se controla razonablemente. Sin eso, es el peor sitio de
  los ocho.

---

## Correcciones a la checklist

Referidas a `coche-europa/lib/checklist.ts`. Ordenadas por impacto.

### A. Cambios en puntos existentes

| `id` | Qué cambiar | Por qué |
|---|---|---|
| **`informe-vin`** | **Quitar `critical: true`** y reescribir el `detail`. Nuevo texto: *"Un apartado de daños vacío NO significa 'sin daños': significa 'sin datos'. En DE la protección de datos deja los informes casi ciegos; allí valen más los informes HU. En NL, FR, PL y BE la fuente oficial gratuita da más que cualquier informe de pago."* Precios reales: carVertical ⚠️16–34 €, autoDNA 24,99 €, CARFAX hasta 39,99 € | Un informe limpio **no prueba nada** (caso documentado en Trustpilot: informe "clear" y el coche tenía financiación viva). Marcarlo como crítico da una falsa seguridad que es peor que no tenerlo |
| **`km-coherentes`** | Añadir **la fuente de km por país** y la regla del **tramo anómalo**: no basta la media, hay que mirar km/año **entre cada par de lecturas**. Exigir **mínimo 3 lecturas** de 3 años distintos | El fraude típico no baja el total: **aplana el último tramo**. Una media de 18.000 km/año puede esconder un tramo de 3.000 seguido de uno de 28.000 |
| **`vin-anuncio`** | Añadir: **17 caracteres, nunca I/O/Q**. Y la advertencia de que **un dígito de control que no valida es normal en coches europeos** | Evita falsos positivos que harían descartar coches buenos |
| **`obd`** | Corregir: **un dongle de 15 € NO lee ABS, airbag ni cambio**. Añadir: **comparar el VIN que devuelve la centralita con el del chasis**, y que **leer el km de varias centralitas requiere VCDS/ODIS/ISTA/XENTRY** — taller o perito, no el comprador | El punto actual promete algo que el aparato recomendado no puede hacer |
| **`medidor-pintura`** | Sustituir la cifra fija por el **método relativo**: fijar la línea base con techo y pilares, y buscar desviaciones (**×2–3 = repintado**, **>500 µm = masilla**, **>700 µm = reparación fuera de norma** según Cesvimap). Avisar de que **hace falta medidor Fe + no-Fe** y de que **los paragolpes de plástico no se pueden medir** | Las "80-150 micras" no son universales (Cesvimap da 30–40 µm de media de fábrica). Y medio coche premium es de aluminio: con un medidor magnético barato no se mide |
| **`doc-de-hu`** | Marcar **`critical: true`** y exigir **los 3 últimos informes HU**, no solo el último | En Alemania es **la única prueba de kilometraje que existe**. Sin registro público y con los informes VIN ciegos, esto es todo lo que hay |
| **`doc-fr-nongage`** | Añadir que el vendedor debe compartir además el **informe HistoVec** completo (no solo el non-gage): trae siniestros con peritaje, CT e historial de km | El non-gage solo cubre cargas; HistoVec cubre el historial entero y es igual de gratis |
| **`doc-nl`** | Añadir la **consulta previa y gratuita en `ovi.rdw.nl`** antes de viajar, y **mirar el número de titulares y si el coche es importado** | El 30–50 % de los importados a NL están clocados, frente al 5,5 % de los holandeses de origen |
| **`doc-be`** | Convertir el Car-Pass en punto propio y **`critical: true`**: *"Es obligatorio por ley en toda venta, también entre particulares. Cuesta 11,10 € y lo saca el vendedor. Validez 2 meses. Si no te lo da, está incumpliendo la ley."* | Hoy el punto belga solo pide el certificado de matriculación y el de conformidad. Se deja fuera **la mejor herramienta antifraude de Bélgica** |
| **`doc-at`** | Añadir `kfzgutachten.at` — **0,99 €**, defectos y km de cada §57a; hace falta la **fecha de primera matriculación** | Es barato y da lo que en Alemania no existe |
| **`doc-pl`** | Añadir `historiapojazdu.gov.pl` (gratis, EN disponible) y avisar de que **hay que pedirle al vendedor la fecha de primera matriculación**, porque sin ella la consulta no funciona | Es la barrera real de uso del sistema polaco |
| **`doc-it`** | Precisar: la **visura PRA cuesta 6 €** y **requiere SPID italiano** → **hay que exigírsela al vendedor**, el comprador español no puede sacarla | Hoy el punto dice "comprueba en el PRA" sin decir que el comprador **no puede hacerlo** |
| **`sin-cargas`** | Convertirlo en **`detail` por país** con la prueba concreta que hay que exigir en cada uno (ver tabla §1.4) | "Sin cargas" sin decir cómo se prueba no es accionable |
| **`co2-oficial`** | Añadir que el campo es **`V.7`** del permiso de circulación en **cualquier país de la UE** (no solo en el COC), y que se puede verificar con **`K` + `D.2`** contra la base de la AEMA | Sube la fiabilidad del dato que decide entre 0 % y 14,75 % de impuesto |

### B. Puntos nuevos que faltan

| Fase | `id` propuesto | Punto | `critical` / `weight` |
|---|---|---|---|
| `antes` | `fuente-oficial-pais` | **Consultada la fuente oficial gratuita del país** (HistoVec / RDW-OVI / historiapojazdu / Car-Pass / kfzgutachten / Portale dell'Automobilista). Con `onlyCountry` por variante | **crítico**, 3 |
| `antes` | `sin-senal` | **No has pagado ni pagarás ninguna señal antes de ver el coche en persona.** Ni 100 € "para reservarlo" | **crítico**, 3 |
| `antes` | `transportista-propio` | **El transporte lo eliges y contratas tú, después de tener el coche.** Si el vendedor propone la agencia de transporte, es el *phishing-car*: la agencia no existe | **crítico**, 3 |
| `antes` | `origen-usa` | **El VIN no empieza por 1, 2, 3, 4 ni 5.** Si empieza así, el coche se fabricó para Norteamérica: alta probabilidad de subasta de aseguradora (Copart/IAA) reparada y revendida | **crítico**, 3 |
| `antes` | `titulares-flota` | **El número de titulares y el uso anterior cuadran** (no ex-alquiler, taxi, VTC, autoescuela ni flota vendido como "de particular") | 2 |
| `antes` | `inspeccion-destino` | **Inspección profesional reservada en destino** (DEKRA 49–150 € · TÜV Rheinland 29,90 € · TÜV Nord 89 € · ADAC 128–160 € · Francia 200–350 €). `onlyCountry: ["DE"]` → **crítico** | crítico en DE, 3; recomendado en el resto |
| `documentos` | `vin-multiples-puntos` | **El VIN coincide en los TRES sitios**: salpicadero, vano motor y etiqueta del marco de puerta. Busca punzonado desigual, tipografía distinta o remaches nuevos | **crítico**, 3 |
| `documentos` | `cuenta-titular` | **La cuenta bancaria del pago es del titular y del mismo país del coche.** IBAN de otro país o a nombre de un tercero = estafa | **crítico**, 3 |
| `interior` | `vin-obd` | **El VIN que devuelve la centralita por OBD coincide con el del chasis.** Si no, es cuadro cambiado o coche clonado | **crítico**, 3 |
| `interior` | `monitores-emisiones` | **Monitores de emisiones en "ready", no "not ready".** Hasta 11 autodiagnósticos; si están incompletos, la memoria se borró hace horas | **crítico**, 3 |
| `exterior` | `granizo` | **Sin marcas de granizo reparado** en techo, capó y portón. Se mira con luz rasante y el coche seco: el medidor de pintura **no lo detecta** porque se repara sin pintar. `onlyCountry: ["DE","AT"]` | 2, `repairCost: 700` |
| `interior` | `inundacion` | **Sin señales de inundación**: óxido en tornillería y raíles de asiento bajo la moqueta, barro fino en el hueco de la rueda, condensación en relojes y faros, exceso de ambientador | **crítico**, 3 |
| `mecanica` | `dpf-contadores` | **Contadores de regeneración del DPF y distancia desde la última, leídos por OBD.** Regeneraciones muy frecuentes = diésel urbano con el DPF al límite. `onlyFuel: ["diesel"]` | 3, `repairCost: 1400` |
| `mecanica` | `dpf-vaciado` | **DPF y catalizador presentes y no vaciados**, sin remapeo que oculte el error. Motivo de rechazo en la ITV de importación | **crítico** en diésel, 3 |
| `cierre` | `informe-carfax-propio` | **El informe VIN lo has pedido tú con el VIN.** Un PDF que te manda el vendedor no vale: circulan falsificaciones de informes CARFAX | 2 |

### C. Una nota de tono para toda la fase `antes`

La fase se llama *"Antes de coger el avión"*, pero **cuatro de los fraudes más
caros ocurren antes incluso de comprar el billete**: la señal, el transportista
falso, la cuenta bancaria de un tercero y el coche que no existe. Merece la pena
**dividir la fase en dos bloques visuales**: **"Que el vendedor sea real"**
(antifraude) y **"Que el coche sea bueno"** (técnico). Hoy están mezclados y el
usuario los lee con el mismo peso, cuando el primero es el que le puede costar
el 50 % del precio del coche sin haber visto nada.

---

## Qué implica para la app

### 1. Lo que se puede automatizar ya, sin coste y sin permisos

| Función | Cómo | Coste |
|---|---|---|
| **Validación de VIN** (17 chars, sin I/O/Q, dígito de control informativo) | Cliente, ~30 líneas de TS (§5.1) | 0 € |
| **Bandera de importación norteamericana** | Tabla WMI estática: primer carácter 1/2/3/4/5 | 0 € |
| **Enriquecimiento total de anuncios holandeses** | **API SODA del RDW**, CC0, token gratis: marca, modelo, ficha técnica, **CO2 NEDC + WLTP**, APK, **nº de titulares**, **historial de km con marca de "ilógico"**, robado, exportado, WOK, recalls | 0 € |
| **CO2 oficial desde el permiso de circulación** | Foto del documento → **campo `V.7`** (armonizado en toda la UE). Con OCR o entrada manual guiada | 0 € |
| **Verificación del CO2 contra la fuente legal** | Campos **`K`** (nº de homologación) + **`D.2`** (tipo/variante/versión) contra la **base CO2 de la AEMA** (Reglamento (UE) 2019/631), descargada e indexada en Supabase | 0 € |
| **Enlaces profundos a fuentes oficiales** | Con los datos que el usuario ya tiene: HistoVec, `ovi.rdw.nl`, historiapojazdu, kfzgutachten.at, Portale dell'Automobilista, sede DGT | 0 € |
| **Motor de coherencia de kilómetros** | El usuario mete las lecturas de cada ITV; la app calcula km/año **por tramo**, marca retrocesos y anomalías | 0 € |
| **Mensaje al vendedor en su idioma** | Plantillas DE/FR/IT/NL/PL/PT con la lista exacta de fotos y documentos (§4.1) | 0 € |

**La función con mejor relación impacto/esfuerzo es la del campo `V.7`.** La app
ya aplica el tramo máximo del 14,75 % cuando no hay CO2; conseguir el dato real
de una foto puede ahorrarle al usuario **miles de euros** y es lo que mejor
justifica que la app exista.

### 2. APIs que integrar, y en qué orden

1. **RDW Open Data** (gratis, CC0). **Primera, sin discusión.** Convierte
   cualquier anuncio holandés en un expediente verificado.
2. **Base CO2 de la AEMA** (gratis, descarga masiva). Segunda. Es la única forma
   de dar un CO2 **oficial y exacto** para los ocho países.
3. **NHTSA vPIC** (gratis). Tercera, y **solo** cuando el WMI delate origen
   norteamericano.
4. **carVertical API** — la integración de pago que tiene sentido: la **alerta
   de origen EE. UU. es gratis para partners** y trae **fotos de subasta**.
5. **Vincario** (~0,20–0,50 €/consulta, 3 gratis/mes) — solo como **respaldo
   etiquetado como estimación** cuando no hay documento ni homologación.
6. ⚠️ **autoDNA WebAPI** — evaluar; es la más fuerte en Polonia, que es
   justamente el mercado con peores cifras.

### 3. Dónde están los ingresos

| Vía | Economía | Valoración |
|---|---|---|
| **Afiliación carVertical** | **Desde 25 % del valor de venta, mínimo 4 €/venta**, escalado por volumen, **sin tope**, **5 %** de sub-afiliados, **cookie de 90 días**, pago mínimo 50 €, gestor dedicado. Disponible también en **Awin** | **🟢 La mejor opción, con diferencia.** Sobre un informe de ~25 €, son **6–8 € por venta**. Encaja natural en el punto `informe-vin` de la checklist |
| **API de carVertical con margen propio** | Compramos al precio de partner y lo revendemos dentro de la app | **🟢 Mejor que la afiliación si hay volumen**: el usuario no sale de la app, controlamos la presentación (y podemos poner el aviso de "vacío ≠ limpio", que ellos no ponen) |
| **Afiliación autoDNA** | `afilio.autodna.com`, ⚠️ comisión sin confirmar. Tienen **WebAPI** | 🟡 Evaluar. Complemento natural para coches polacos |
| **CARFAX** | **0,40–0,80 $ por venta** | **🔴 No merece la pena**: **30–50 veces menos** que carVertical. Pero su **comprobación de disponibilidad gratuita** (te dice cuántos registros hay antes de pagar) es una idea de producto que deberíamos copiar |
| **Inspección profesional en destino** | DEKRA 49–150 € · TÜV Rheinland 29,90 € · TÜV Nord 89 € · ADAC 128–160 € · Francia 200–350 € | **🟢 El mayor potencial, y el menos explorado.** Es la función que de verdad resuelve el problema alemán. ⚠️ **Hay que confirmar primero si se puede contratar desde España y con cuánta antelación** — no hay programa de afiliados público; sería acuerdo B2B o comisión sobre reserva |
| **Hardware (Amazon Afiliados)** | Medidor de espesor 20–60 €, lector OBD 15–40 € | 🟡 Comisión pequeña pero **conversión alta**: son los dos puntos de la checklist donde el usuario necesita comprar algo sí o sí |
| **Gestoría de matriculación** | ⚠️ Fuera del alcance de esta investigación | 🟡 A explorar |

### 4. La función que diferenciaría de verdad a la app

Nadie está haciendo esto: **un semáforo de verificabilidad por país**, calculado
antes de que el usuario se enamore de un anuncio.

> *"Este coche está en Alemania. Aquí no existe registro público y los informes
> VIN salen casi vacíos por la protección de datos. Para este coche necesitas:
> los 3 últimos informes HU y una inspección DEKRA (49-150 €). Sin eso, estás
> comprando a ciegas."*
>
> *"Este coche está en Países Bajos. Dame la matrícula y en 2 segundos te digo
> los kilómetros oficiales de toda su vida, si hay alguna lectura ilógica,
> cuántos dueños ha tenido, si está robado y su CO2 exacto. Gratis."*

Eso es lo que convierte el buscador en un producto con criterio propio, y es
**todo implementable con las fuentes gratuitas de este documento**.

---

## Fuentes

**Fraude — institucional**
- Parlamento Europeo / EPRS, *Odometer manipulation in motor vehicles in the EU* (STU 2018/615637) — `europarl.europa.eu/RegData/etudes/STUD/2018/615637/EPRS_STU(2018)615637_EN.pdf`
- EPRS, briefing *Odometer manipulation in motor vehicles* (ATAG 2018/621883)
- Pregunta parlamentaria E-000378/2025, *European scheme to prevent odometer manipulation*
- ETSC — `etsc.eu/eu-should-act-against-mileage-tampering-on-second-hand-cars/`
- ADAC — `adac.de/rund-ums-fahrzeug/auto-kaufen-verkaufen/gebrauchtwagenkauf/tacho-manipulation/` y `presse.adac.de/meldungen/adac-ev/technik/tachobetrug.html`
- Verivox, *ADAC: Bei jedem dritten Gebrauchten ist der Tacho manipuliert*
- ANWB — `anwb.nl/auto/kopen/teruggedraaide-kilometerstand`
- Autoverleden / Blik op Nieuws — *RDW registreert zeker 163.000 voertuigen met tellerfraude*

**Fraude — índices comerciales (con sesgo de muestra)**
- carVertical, *European Market Transparency Index 2025* — `carvertical.com/en/blog/eu-market-transparency-index-2025` (⚠️ bloqueado por el proxy; citado vía resultados de búsqueda)
- carVertical, *Countries With the Highest Percentage of Cars With a Fake Mileage*, *The hidden cost of odometer fraud in Europe*, *Most damaged cars in 2025*
- Fleet Europe, *Mileage fraud affects 1 in 20 used cars*

**Opiniones de usuarios**
- Trustpilot carVertical — `trustpilot.com/review/carvertical.com` · `es.trustpilot.com/review/carvertical.com`
- Trustpilot VIN-Info — `trustpilot.com/review/vin-info.com`
- **motor-talk.de** (protección de datos alemana e informes vacíos) — `motor-talk.de/forum/fahrzeugbericht-t8443549.html` y `motor-talk.de/forum/erfahrung-mit-de-vin-info-com-autodna-de-...-t6617498.html`
- PistonHeads UK, *Car history checking - was going to use CarVertical*
- `fahrzeugschein.de/blog/artikel/carvertical-erfahrungen`

**Servicios VIN**
- carVertical: `carvertical.com/en/affiliate-program` · `carvertical.com/en/business/api` · programa DE en Awin
- autoDNA: `autodna.com/blog/individual-packages/` · `autodna.com/company/partners-area` · `autodna.com/business-packages` · `afilio.autodna.com`
- CARFAX Europe: `carfax.eu` · `carfax.eu/pricing` · `carfax.eu/preview-page` · `carfax.eu/cheap-carfax` · `carfax.com/company/partners`
- VIN-Info: `vin-info.com`

**Fuentes oficiales**
- 🇫🇷 `histovec.interieur.gouv.fr` · `service-public.gouv.fr/particuliers/vosdroits/F1360` · `justice.fr` (ficha HistoVec) · `interieur.gouv.fr` (nota de lanzamiento)
- 🇳🇱 `ovi.rdw.nl` · `opendata.rdw.nl` (datasets `m9d7-ebf2`, `8ys7-d773`, `7ich-qprq`) · `rdw.nl/over-rdw/dienstverlening/open-data/algemene-informatie` · `data.overheid.nl`
- 🇵🇱 `historiapojazdu.gov.pl` · `moj.gov.pl` · `github.com/krzksz/historia-pojazdu`
- 🇧🇪 `car-pass.be/en/about-car-pass/what-is-a-car-pass` · Moniteur Automobile
- 🇦🇹 `portal.kfzgutachten.at` · `pickerlcheck.autoscout24.at` · ÖAMTC · Arbeiterkammer OÖ
- 🇮🇹 `aci.gov.it/pratica-auto/fermo-amministrativo-informazioni-utili/` · ACI Visurenet / ACI Space · Portale dell'Automobilista
- 🇵🇹 `imt-ip.pt/veiculos/matriculas-e-registo-de-veiculos/` · `gov.pt/servicos/saber-se-uma-matricula-foi-cancelada`
- 🇩🇪 `kba.de/EN/Themen_en/ZentraleRegister_en/ZFZR_en/` · `fahrzeugschein.de` · `checkdenwagen.de`
- 🇪🇸 `sede.dgt.gob.es/es/vehiculos/informacion-de-vehiculos/informe-de-un-vehiculo/` · `dgt.es`

**Técnica y herramientas**
- Cesvimap vía Autopos, *El espesor de pintura adecuado*
- DeFelsko, *How to use paint thickness gauges*
- OBD Auto Doctor, *OBD2 Readiness Monitors Explained*
- THINKCAR, *Used Car OBD2 Scan Checklist*
- `fahrzeugschein.de/blog/artikel/gebrauchtwagencheck-kosten` · `checkdenwagen.de/vergleich/anbieter-uebersicht` · `autobild.de/artikel/gebrauchtwagen-check-219434.html` · `adac.de`
- `wearebargain.com/blog/acheter-verifier/expert-automobile-independant-avant-achat-2026` · `autocopilot.fr/guides/expertise-voiture-avant-achat` · `dekra.be`

**VIN, decodificación y CO2**
- NHTSA vPIC — `vpic.nhtsa.dot.gov/api/`
- Vincario / vindecoder.eu — `vindecoder.eu/api/` · `vincario.com/pricing/` · `vincario.com/blog/vin-decoder-api-pricing/`
- AEMA/EEA, *Monitoring of CO2 emissions from passenger cars — Regulation (EU) 2019/631* — `eea.europa.eu/en/datahub/` · `co2cars.apps.eea.europa.eu/`
- Wikibooks, *Vehicle Identification Numbers (VIN codes)/Check digit*
- KBA, *Leitfaden zur Ausfüllung der Zulassungsbescheinigung Teil I und II* · `autohero.com/de/beratung/kaufen/co2-effizienzklasse/`

**Estafas y salvamento**
- El Economista, *Las estafas más habituales en la compra de coches por internet*
- Autopista / Diario de Transporte, *Phishing-car*
- Coches.net, *Guía de seguridad compra-venta*
- WCShipping, *Copart vs IAA Comparison for Salvage Car Importers* · auto4export, *Avoiding Scams on Copart & IAAI*
- ASM Auto Recycling, *Clocking, Cloning, Ringing and Cut & Shut* · Autotrader UK
