---
tags: [coches, importacion, usuarios, producto, investigacion]
status: investigacion
updated: 2026-09-20
related:
  - "[[Coche Europa — Proyecto]]"
---

# Usuarios — Necesidades y dolor real al importar un coche a España

> Investigación de campo sobre lo que dice en público la gente que importa (o
> intenta importar) un coche de Europa a España, y qué implica para
> [[Coche Europa — Proyecto]].

---

## Nota de método — leer antes que nada

**Lo que se pudo hacer:** ~25 búsquedas dirigidas en español y alemán sobre
experiencias, estafas, fiscalidad, homologación, garantías, financiación,
seguros, reventa y segmentos.

**Lo que NO se pudo hacer, y es una limitación seria de este informe:** el
proxy de red del contenedor bloqueó **todos** los intentos de abrir páginas
(`WebFetch` devolvió `EGRESS_BLOCKED` en el 100% de los casos, incluidos
`forocoches.com`, `reddit.com`, `bmwfaq.org`, `mbfaq.com`,
`audisport-iberica.com`, `clubvwgolf.com`, `burbuja.info`, `europa.eu` y
`agenciatributaria.es`). Reddit además bloquea al crawler del buscador por
robots.

Consecuencia práctica: **no he podido copiar ni una sola cita verbatim leyendo
el hilo original.** Todo lo entrecomillado aquí llega a través del resumidor
del buscador, que sí leyó esas páginas. Lo marco así:

- **「vía buscador」** — frase que el buscador extrajo de la página. Fiable en
  el fondo, no garantizado palabra por palabra. **No la pegues en un anuncio
  ni en la app como cita literal sin volver a verificarla.**
- **⚠️** — dato no confirmado o que deduzco yo, no encontrado.
- Sin marca — dato coincidente en varias fuentes independientes.

**Canales que no dieron nada utilizable:** Reddit (r/es, r/spain, r/Coches,
r/askspain) — bloqueado por robots, cero contenido recuperable. TikTok e
Instagram — solo títulos de vídeo, sin comentarios. X/Twitter — nada. Grupos
de Facebook — nada, son cerrados. **No relleno esos huecos con suposiciones:
simplemente no los tengo.**

Los hilos de Forocoches sí están **indexados** (tengo los títulos y las URLs,
que ya dicen mucho) pero el contenido no es accesible desde aquí. Quedan
listados abajo como pista para una segunda vuelta desde una red sin filtro.

---

## 1. El dolor real, con nombres y cifras

### 1.1 El mercado es mucho más grande de lo que pensábamos — y mucho más viejo

Dato duro, y probablemente el más importante de todo el informe:

> Las importaciones de vehículos usados **crecieron un 32% en 2025 hasta las
> 137.122 unidades, y 51.000 superaban los diez años** — un 46% más que en
> 2024. La DGT añade que **la edad media de los turismos comprados fuera era de
> 10,4 años**.
> — [motor16.com](https://www.motor16.com/las-ultimas-noticias/coches-usados-importados-espana/) (datos ANFAC/DGT), 「vía buscador」

Esto rompe nuestra hipótesis implícita. El README dice *"si el coche pasa de
15.000 euros, una inspección profesional en destino cuesta 150 y los vale"*:
estamos diseñando para el comprador de premium. **El volumen real está en
coches de más de 10 años.** Y en ese tramo, un imprevisto de 1.400 € (DPF) o de
2.500 € (homologación individual) no es un disgusto: es el 30% del precio del
coche y se carga la operación entera.

### 1.2 El titular que resume por qué la gente lo hace

> **"El mismo BMW, pero lleno de extras y un 10% más barato que en España"**
> — Carlos Aragón, 50 años, fundador de Car&Car, que importó **123 vehículos en
> 2023**. [eleconomista.es](https://www.eleconomista.es/motor/noticias/12854540/06/24/asi-funciona-el-negocio-de-importar-coches-a-la-carta-desde-alemania-el-mismo-bmw-pero-lleno-de-extras-y-un-10-mas-barato-que-en-espana.html), 「vía buscador」

Fíjate en la formulación: **no dice "más barato", dice "lleno de extras"**. Esa
es la motivación real de la mitad del mercado: en Alemania el mismo dinero
compra un coche con equipamiento que en España no existe o es inencontrable de
segunda mano. Nuestro buscador está optimizado para precio; el usuario compra
**configuración**.

### 1.3 Los números reales de una operación buena

Caso citado en contenido de importadores (Golf 7 1.4 TSI):

> 8.990 € en Alemania + **1.338 € de costes de importación** = **10.328 €**
> matriculado en España. El mismo coche aquí, 12.600 € o más. Ahorro real:
> ~2.272 €. 「vía buscador」

Y el contraste, de otra fuente:

> "Un coche de 20.000 € en Alemania puede costarte entre **22.000 € y 24.000 €**
> con todos los trámites". 「vía buscador」

Es decir: **el sobrecoste real está entre el 10% y el 20% del precio del
anuncio**, no en una cifra fija. Nuestra calculadora suma partidas fijas, lo
cual está bien, pero debería mostrar también ese **porcentaje**, porque es la
forma en que la gente piensa y compara.

Del blog personal [cochedesdealemania.wordpress.com](https://cochedesdealemania.wordpress.com/2016/06/02/prueba-1/)
(2016, único relato paso a paso que el buscador pudo leer entero):

> "Llevé todos los papeles a Tráfico y pagué la tasa de solicitud de
> matriculación de **95,80 €**. Al día siguiente volví a Tráfico a recoger el
> permiso de circulación y luego fui a hacer las placas (**29,80 €**) y llamé al
> seguro para dar de alta el coche". 「vía buscador」

Las placas físicas (~30 €) **no están en nuestra calculadora**. Es calderilla,
pero es exactamente el tipo de detalle que hace que un presupuesto se sienta
real.

### 1.4 El miedo número uno, y está justificado: los kilómetros

El caso concreto mejor documentado que he encontrado:

> Un **Audi S3** a la venta en **mobile.de con 245.000 km por 12.700 €**
> apareció simultáneamente en **Milanuncios con 125.000 km y 19.900 €**. En el
> trayecto de Alemania a España el coche iba a **reducir su kilometraje en
> 114.467 km**, "un afeitado que se traduce inmediatamente en un sobreprecio de
> **7.200 euros**".
> — [eldebate.com](https://www.eldebate.com/motor/20230601/sorprendente-caso-coche-afeitado-tiene-100-000-km-menos-espana-alemania_118432.html), 「vía buscador」

Y el porqué estructural, que explica por qué el fraude se concentra
precisamente en la importación:

> "En los coches importados es mucho más complicado llegar a conocer el
> kilometraje real, pues en la ITV o red de concesionarios oficiales **no hay
> informes hasta la primera vez que pasa por ellos**, mientras que el proceso de
> afeitado es previo."
> — [motorpasion.com](https://www.motorpasion.com/compra-coches/ojo-importar-coche-usado-estos-paises-se-detectan-rebajas-kilometraje-asi-puedes-evitar-esa-estafa), 「vía buscador」

Escala: la Comisión Europea cifra el daño del fraude de cuentakilómetros en
**~9.600 millones de euros al año**, y "la mayoría de los fraudes se hacen en
los coches vendidos en otro país que el de origen". 「vía buscador」

**Veredicto: el miedo está totalmente justificado y es el dolor mejor
documentado de todos.** Nuestra checklist ya lo ataca bien (VIN, informe,
HU anteriores, desgaste coherente, OBD). Es nuestra mejor baza.

### 1.5 El dolor que no habíamos visto: **el historial español empieza de cero**

> "Cuando un coche importado llega a España y se matricula, **el historial DGT
> español comienza desde cero**. Todo lo que le ocurrió al vehículo en el país de
> origen — accidentes, siniestros totales, kilómetros reales, propietarios
> anteriores, uso como taxi o flota — **no aparece en los registros de la DGT**."
> — [dealcar.io](https://dealcar.io/blog/vender-coche-importado) / [comprocoches.org](https://comprocoches.org/vender-coche-extranjero-espana/), 「vía buscador」

Esto tiene dos caras y las dos son oportunidad de producto:

1. **Para el que importa:** el día que venda, no podrá demostrar nada. Debería
   **archivar y conservar todo el historial de origen** (informes HU, facturas,
   Scheckheft, informe de VIN con fecha) como activo de reventa. Nadie se lo
   dice.
2. **Para el que compra en España un coche ya importado:** está comprando a
   ciegas. Es un segmento entero que no estamos atendiendo y que es
   probablemente más grande que el de los que importan.

### 1.6 La desconfianza en la reventa, con las palabras del mercado

> "Muchos compradores particulares en España desconfían de los coches
> importados: posible manipulación de kilómetros en el país de origen,
> accidentes no declarados, diferencias de equipamiento… y la percepción general
> de que **'si era tan buen coche, ¿por qué lo vendían barato en Alemania?'**"
> — [dealcar.io](https://dealcar.io/blog/vender-coche-importado), 「vía buscador」
>
> "Vender a un profesional da mejor resultado que intentar convencer a un
> particular que desconfía de entrada."

⚠️ **No he encontrado ninguna cuantificación fiable del descuento de reventa de
un coche importado en España.** Varias fuentes comerciales dicen "se vende
peor" pero ninguna da un porcentaje verificable. No lo inventemos.

### 1.7 La trampa alemana que no conocíamos: el **Agenturgeschäft**

Esta es, de lejos, la cosa nueva más valiosa que ha salido de la investigación.

Un profesional alemán que vende a un consumidor **no puede excluir la garantía
legal**; como mucho puede reducirla a **1 año** en un usado. Pero existe una
forma perfectamente legal de esquivarla:

> El **Agenturgeschäft** (o *Verkauf im Kundenauftrag*) es una forma de venta
> muy extendida en el mercado alemán de ocasión, en la que un **comerciante
> vende el coche no como propietario, sino en nombre y por cuenta de un
> particular** — el dueño real. "Como el vendedor es un particular, la venta se
> considera privada, **con la posibilidad de excluir completamente la garantía
> legal**."
> — [juraforum.de](https://www.juraforum.de/news/ausschluss-der-gewaehrleistung-bei-agenturgeschaeften-im-gebrauchtwagenhandel_375) / [autokaufrecht-frankfurt.de](https://autokaufrecht-frankfurt.de/agenturgeschaeft-eigengeschaeft-und-umgehungsgeschaeft-im-kfz-handel/), 「vía buscador」

Es decir: **vas a una compraventa con nave, escaparate y vendedor con polo
corporativo, y firmas una compra "entre particulares" sin garantía ninguna.**

Y la variante aún más sucia, reportada en foros españoles:

> "Algunos distribuidores intentan eludir sus obligaciones de garantía
> incorporando en sus formularios modificaciones contractuales difíciles de
> entender, mediante declaraciones como **'Por la presente declaro comprar el
> vehículo en cuestión en mi calidad de comerciante'**, o el comerciante declara
> que está vendiendo el vehículo de su propiedad privada y, por lo tanto, **finge
> una compra de particular a particular**." 「vía buscador, foro BMW FAQ/MBFAQ」

Hay una **señal de detección** muy operativa, y es regalo para la checklist:

> "Si el vendedor está dispuesto a negociar el precio **sin consultar al
> propietario**, eso indica que es él quien soporta el riesgo económico de la
> venta y que el 'contrato de agencia' **no es admisible**" (sería un
> *Umgehungsgeschäft*, y entonces la garantía sí te cubre). 「vía buscador」

Complemento: la fórmula **"gekauft wie gesehen"** que aparece en casi todos los
contratos privados alemanes **no sirve para lo que la gente cree**:

> "'Gekauft wie gesehen' cubre típicamente solo **defectos visibles** y
> reconocibles en la inspección. **No cubren defectos ocultos ni daños técnicos
> internos.** La exclusión es además nula (§ 444 BGB) si el vendedor ocultó
> dolosamente un defecto."
> — [fachanwalt.de](https://www.fachanwalt.de/ratgeber/gekauft-wie-gesehen), 「vía buscador」

### 1.8 Y aunque tengas razón, no la vas a cobrar

> "El problema **no es que te den la razón**, sino que tiene que hacerse a través
> de **un abogado aquí en Alemania**, y ello conlleva unos costes, tiempo y la
> posibilidad de que luego **el vendedor sea insolvente**."
> 「vía buscador, foro Audisport Ibérica / MBFAQ」
>
> "Lo más importante si compras un coche de segunda mano en Alemania es:
> **¿te va a compensar ir a Alemania a reclamar?**" 「vía buscador」

Hay incluso una ruta documentada por usuarios, que merece ser contenido de la
app: notificar por escrito → presupuestar en taller propio → dar plazo con el
informe → reparar y enviar factura → mediación en consumo → **juzgado, y por
menos de 2.000 € sin abogado ni procurador**. 「vía buscador」

### 1.9 Las estafas de señal, con cifras judiciales

> Doce detenidos de una organización criminal dedicada a publicar anuncios
> falsos de coches de segunda mano. **175 víctimas y más de 380.000 €** de
> perjuicio. Publicaban anuncios "con precios muy por debajo del mercado",
> forzaban a seguir la conversación por mensajería instantánea y pedían "una o
> varias transferencias **para la reserva del coche**".
> — [cope.es](https://www.cope.es/actualidad/tecnologia/noticias/doce-detenidos-estafar-anuncios-falsos-venta-coches-segunda-mano-175-victimas-380-000-euros-20250617_3171376.html), 「vía buscador」

Señales de alerta recogidas: vendedor que no da teléfono y solo escribe por
email, anuncio mal redactado o en otro idioma, presión ("hay más interesados",
"me voy mañana"), y **señal por transferencia, Bizum o Western Union que suele
rondar la mitad del precio**. 「vía buscador」

**Confirmado: "pagar señal antes de ver el coche" era una sospecha nuestra y es
real, masiva y con sentencias.** Pero nuestra app la tiene en la **fase 8**
(Cerrar la compra) — es decir, **después** de que el usuario ya haya perdido el
dinero. Error de diseño, ver sección de correcciones.

---

## 2. Dónde se atascan, qué les sale caro y qué pasa después

### 2.1 El punto de abandono real: **el dinero en efectivo**

Esto no estaba en nuestra lista de hipótesis y creo que es el cuello de botella
número uno:

> "Los bancos españoles pueden requerir el coche **ya matriculado en España**
> para conceder el préstamo. (…) Los bancos suelen ser reticentes a financiar un
> bien que **legalmente no 'existe' todavía** en el sistema español. Uno de los
> mayores obstáculos es el tiempo que transcurre desde la compra en el
> extranjero hasta que el coche tiene sus placas definitivas españolas. Durante
> este periodo el coche se encuentra en un **'limbo' administrativo**."
> — [caralyze.es](https://caralyze.es/blog/financiar-coche-importado-espana-2026) / [cvgcars.com](https://www.cvgcars.com/guias/financiar-un-coche-de-importacion), 「vía buscador」
>
> "La financiera **no financia 'una importación'**: financia un coche con
> matrícula española que compras a un concesionario español."

Traducción: para importar tienes que **poner entre 10.000 y 40.000 € en
efectivo, de golpe, en una transferencia internacional a un desconocido**, y
esperar semanas antes de poder refinanciarlo. Eso elimina de un plumazo a la
mayoría del mercado español de coche de ocasión, que compra a plazos.

⚠️ **No tengo confirmación directa** (por el bloqueo de foros) de que éste sea
el momento exacto en que la gente abandona; lo deduzco de la combinación de (a)
la imposibilidad estructural de financiar, (b) el volumen de contenido
comercial dedicado justo a esa pregunta y (c) que existen entidades
especializadas cobrando 4–7% TAE por resolverlo. Es una hipótesis fuerte, pero
es hipótesis. **Vale la pena validarla con una pregunta directa a usuarios.**

### 2.2 Los tres errores caros que confirmamos

| Sospecha nuestra | Veredicto | Matiz importante |
|---|---|---|
| No pedir el CO2 y pasarse de tramo | **Real y grave** | Confirmado 2026: 0 / 4,75 / 9,75 / 14,75% en 120/160/200 g/km. "**Un solo gramo de diferencia puede moverte de tramo** y subir la factura un 5% sobre la base imponible" 「vía buscador」 |
| El Teil II en el banco | **Real** | "Cuando un coche está financiado en Alemania, **el banco retiene el Teil II** hasta que la financiación está completamente pagada, lo que hace imposible matricularlo en España" 「vía buscador」 |
| Kilómetros manipulados | **Real y masivo** | Ver 1.4 |
| Pagar señal antes de ver el coche | **Real, con sentencias** | Ver 1.9. Nuestra fase está mal colocada |
| Ficha técnica reducida | **MAL PLANTEADO por nosotros** | Ver abajo, 2.3 |
| Plazos de matriculación | **Real pero mal redactado** | Ver abajo, 2.5 |

### 2.3 Nos hemos equivocado con la ficha técnica reducida

Nuestra app dice, en el punto `coc` de la checklist: *"Sin él, ficha técnica
reducida: +250 EUR y semanas de espera"*, y la calculadora lleva
`fichaTecnica: 250`.

Los dos datos están mal, y el error es doble:

1. **La ficha técnica reducida cuesta entre 39 € y 90 € (+IVA) y tarda entre 1
   hora y 72 horas**, no 250 € ni semanas.
   > "El precio para un coche de importación perteneciente al EEE y con
   > contraseña de Homologación Europea es de **45 € + IVA**". "Suelen enviar la
   > documentación en un plazo de **1 a 3 horas**, siempre en menos de 8 horas
   > hábiles."
   > — [ingeniauto.es](https://ingeniauto.es/ficha-tecnica-reducida/precio-ficha-tecnica-reducida/), [homologarfacil.es](https://homologarfacil.es/ficha-reducida/), [fichatecnicacoche.com](https://www.fichatecnicacoche.com/ficha-reducida/), 「vía buscador」

2. **La ficha reducida hace falta igualmente, con COC o sin él.** Es el
   documento que la ITV necesita para verificar el vehículo antes de
   matricularlo. No es la penalización por no tener COC.

**Lo que sí es la penalización por no tener COC (y no habíamos modelado en
absoluto) es la homologación individual:**

> "Para una homologación individual completa, el coste mínimo oscila entre
> **2.500 y 3.000 euros (+IVA)**, y pueden subir más dependiendo del tipo de
> vehículo, sus modificaciones y si hay que hacer ensayos adicionales."
> — [gdphomologaciones.es](https://gdphomologaciones.es/blog/coste-homologacion-vehiculo-espana/) / [homologatotal.es](https://homologatotal.es/homologacion-unitaria/), 「vía buscador」

Y el COC, cuando hay que pedirlo al fabricante: **109 € para un Volkswagen**,
más caro en premium, y "para marcas alemanas como VW o BMW **menos de una
semana**; en otras marcas **hasta 20 días hábiles**".
— [coc-online.com](https://www.coc-online.com/es/products/certificado-oficial-de-conformidad-coche-volkswagen), [juanjohomologaciones.es](https://juanjohomologaciones.es/como-se-consigue-el-coc-guia-completa-paso-a-paso/), 「vía buscador」

**Conclusión: nuestro número está inflado x5 en el caso normal y es 10 veces
demasiado bajo en el caso malo.** Es el peor error de la calculadora.

### 2.4 El error caro que NO teníamos ni en el radar: **el coche modificado**

Alemania es el país europeo donde más habitual es que un usado lleve
modificaciones legalizadas (llantas, suspensión, escape, tintados) anotadas en
el TÜV. Y:

> "Muchos compradores asumen que si un coche trae la TÜV alemana se matriculará
> sin problemas en España, pero **esto es falso**. España **no convalida
> automáticamente** las reformas anotadas en fichas extranjeras; deben ser
> revisadas, calculadas y **ensayadas de nuevo** bajo la normativa nacional a
> través del Laboratorio Oficial."
> — [ingeniauto.es](https://ingeniauto.es/matricular-vehiculos/matricular-coche-alemania-espana/), 「vía buscador」
>
> "Si el vehículo presenta modificaciones que rompen su homologación
> (suspensión, llantas no equivalentes, cambios de carrocería, camperizaciones…)
> **no podrá matricularse directamente**."

Con ensayos en pista concretos: "ensayos de Dirección y Cinemática si trae
llantas con distinto ET o separadores, y ensayos de Suspensión si lleva muelles
o roscadas". 「vía buscador」

Esto es **un error de 2.500–3.000 € que se descubre cuando el coche ya está en
España**, y golpea justo al perfil más entusiasta (el que compra el GTI o el M
con extras). Nuestra checklist **no lo menciona en ningún punto**.

### 2.5 El plazo: lo decimos mal

Nuestro punto `plazo-30-dias` dice "**30 días hábiles**". Las fuentes dicen
otra cosa:

> "En los supuestos de circulación o utilización en España de los medios de
> transporte, cuando no se haya solicitado su matriculación definitiva, deberá
> realizarse **en el plazo de los 30 días siguientes al inicio de su utilización
> en España**."
> — [administracion.gob.es](https://administracion.gob.es/pag_Home/Tu-espacio-europeo/derechos-obligaciones/ciudadanos/vehiculos/traslado/impuesto.html) / [DGT](https://www.dgt.es/nuestros-servicios/tu-vehiculo/quieres-traer-o-llevarte-un-vehiculo-del-extranjero/matricular-un-vehiculo-proveniente-de-la-ue/), 「vía buscador」

Son **30 días naturales desde que empiezas a usarlo en España**, no hábiles, y
el disparador es el **uso**, no la entrada. Además la autoliquidación del IEDMT
va **antes** de la matriculación definitiva. Hay que reescribirlo.

### 2.6 El atasco operativo que ningún artículo cuenta y sí cuenta un foro

> "Es recomendable **reservar hora en la ITV incluso antes de ir a recoger el
> vehículo** en Alemania, ya que las horas para «reforma» suelen ser **escasas**
> en las estaciones de ITV." 「vía buscador, hilo de foro」

Es el tipo de consejo que solo da alguien que lo ha vivido, y es exactamente lo
que una app puede automatizar (recordatorio + enlace a cita previa por
provincia). No está en nuestra checklist.

### 2.7 Qué pasa DESPUÉS de comprar

**Seguro.** Confirmado y peor de lo que pensábamos:

> "La mayoría de las compañías de seguro de España **no permiten la
> contratación de una póliza si el coche está registrado en el extranjero**, sean
> cuales sean las coberturas requeridas."
> — [Tuio](https://blog.tuio.com/coche/seguro-coche-matricula-extranjera-en-espana-2026/) / [RACC](https://www.racc.es/blog/coche/asegurar-un-coche-con-matricula-extranjera-como-hacerlo/) / [MAPFRE](https://www.mapfre.es/particulares/seguros-de-coche/articulos/asegurar-coche-matricula-extranjera/), 「vía buscador」

Hay que ir a **seguros temporales** para el periodo de tránsito. Nuestro punto
`seguro-traslado` existe pero no avisa de que el problema sigue **después** de
llegar, hasta tener matrícula española.

**Garantía oficial.** Aquí hay buenas noticias que deberíamos contar:

> "Un BMW comprado en Alemania con garantía de fábrica vigente **puede ser
> atendido en cualquier concesionario oficial BMW en España sin problemas**. Esto
> aplica a otras grandes marcas alemanas con redes integradas en toda Europa."
> 「vía buscador」

Es decir: **la garantía de fábrica sí viaja; la garantía del vendedor
(Gewährleistung) no, en la práctica** (ver 1.8). Son dos cosas distintas y la
gente las confunde. Contenido de producto claro.

**ZBE y etiqueta ambiental.** Dato con fecha, y crítico en 2026:

> "A partir del **1 de enero de 2026 se pone fin a la moratoria** que permitía
> circular a los vehículos sin etiqueta ambiental, y las cámaras de la ZBE
> empezarán a multar automáticamente" (200 €, 100 € con pronto pago). Y: "**la
> DGT no puede expedir distintivos ambientales españoles a vehículos con
> matrícula extranjera**".
> — [carwow.es](https://www.carwow.es/noticias/6443/madrid-2026-restricciones-etiquetas-fin-moratoria) / [cea-online.es](https://www.cea-online.es/blog/1159-pueden-los-coches-con-matricula-extranjera-obtener-la-etiqueta-ambiental), 「vía buscador」

Consecuencia directa: **entre que el coche llega y se matricula, no puedes
entrar en Madrid ni Barcelona**. Y si vives dentro de una ZBE, el coche está
parado. ⚠️ No he podido confirmar el otro riesgo que sospecho — que una
matriculación con datos mal trasladados asigne una etiqueta peor de la que
corresponde; lo dejo marcado como no verificado.

**Traducción jurada.** Coste que no tenemos:

> "La traducción jurada al español de todos los documentos es un requisito
> **obligatorio** para matricular un vehículo importado. (…) coste entre
> **50 € y 200 €** por documento" / "traducción jurada y gestoría: **200–450 €**".
> — [traductoresjuradositrad.com](https://traductoresjuradositrad.com/que-documentos-necesito-traducir-para-traerme-un-coche-del-extranjero/) / [tevagui.com](https://tevagui.com/como-matricular-un-vehiculo-importado-en-espana/), 「vía buscador」

⚠️ Matiz: varias gestorías afirman que para documentos **UE armonizados** (COC,
permiso de circulación con códigos armonizados) muchas jefaturas **no** exigen
traducción jurada, y sí para el contrato de compraventa. No he podido
verificarlo en fuente oficial. Merece un aviso con condicional, no una
afirmación.

---

## 3. Los segmentos

Ordenados por lo que he podido documentar. **Volumen y disposición a pagar son
estimación mía salvo donde cito dato.**

### A. El que busca ahorro en un coche normal — **el de más volumen**

Dato: 137.122 importaciones de usados en 2025, edad media 10,4 años.
Ahorro típico documentado: **~2.272 € en un Golf de ~10.000 €** (22%), o
"10% en un BMW". Es un ahorro **real pero frágil**: un DPF (1.400 €) o una
homologación (2.500 €) se lo comen entero.

- **Necesita:** saber si el ahorro sobrevive a los costes ANTES de viajar, y
  no meter la pata en nada.
- **Pagaría poco.** Es un comprador sensible al precio por definición. Modelo
  freemium o ingreso por afiliación (informe VIN, transporte, gestoría).

### B. El que busca la versión que aquí no existe — **el que más disfruta**

Es el perfil del reportaje de El Economista (un Golf GMK G60 "que en nuestro
país no existía") y del que hoy compra un M/RS/AMG con extras. Compra
**configuración**, no precio.

- **Necesita:** búsqueda por **equipamiento y códigos de opción**, no por
  marca/modelo/precio. Nuestro buscador no hace esto y es su necesidad central.
- **Riesgo específico:** es el que más probablemente compra un coche
  **modificado** → bomba de 2.500 € (ver 2.4).
- **Pagaría medio-alto.** Tiquets altos, mucha implicación emocional.

### C. Eléctrico / híbrido enchufable — **el de mejor ratio esfuerzo/valor**

- **Fiscalidad a favor:** CO₂ = 0 → **0% de impuesto de matriculación**. El
  ahorro es el precio puro.
- Precios en Alemania **8–15% más bajos** que en España, con mucho stock de
  seminuevo. 「vía buscador」
- **Trampa concreta y barata de resolver:** "En Alemania muchos coches vienen
  con **cargador Schuko de emergencia en vez de cargador Tipo 2**, que puede
  requerir compra adicional de **200–500 €**".
  — [importyourcar.es](https://www.importyourcar.es/importar-coche-electrico-alemania-2026/), 「vía buscador」
- **Trampa cara:** salud de batería y **validez de la garantía de batería en
  España**. Nuestra checklist ya cubre el SOH, y bien.
- ⚠️ No he podido verificar si un EV usado importado puede acceder a ayudas
  MOVES (mi lectura es que **no**, porque MOVES exige compra a punto de venta
  en España, pero no lo he confirmado y no debe afirmarse en la app).
- **Pagaría medio.** Tiquet alto, comprador informado, decisión muy numérica.

### D. Furgoneta / camper — **el de más riesgo de ruina**

Aviso literal del sector:

> "Es muy frecuente comprar una furgoneta en el extranjero para después
> camperizarla en España, pero (…) **el trámite de homologación puede costar
> mucho más dinero que la propia furgoneta**."
> — [homologatucamper.es](https://www.homologatucamper.es/matricular-una-furgoneta-importada/) / [inaga.es](https://inaga.es/importar-una-furgoneta-camper-o-autocaravana-pasos-y-requisitos-para-legalizarla-en-espana/), 「vía buscador」

Una camper ya homologada como vivienda en Alemania **hay que rehomologarla en
España**: certificación de gas, electricidad y mobiliario por ingeniero + ITV.

- **Necesita:** una calculadora completamente distinta, con la rehomologación
  como partida principal.
- **Pagaría alto**, porque el error le cuesta miles. Pero es **nicho** y exige
  contenido especializado. **Recomendación: no atacarlo todavía; sí poner un
  aviso rojo si el usuario marca "furgoneta/camper".**

### E. El que vuelve a España con su coche — **caso fiscal distinto y muy valioso**

Confirmado: **existe exención del impuesto de matriculación por traslado de
residencia**, con requisitos concretos:

- Haber residido fuera **≥ 12 meses consecutivos**.
- Ser propietario del vehículo **≥ 6 meses antes del traslado** y haberlo usado
  allí para uso personal.
- Solicitar la exención ante la AEAT **dentro de los 60 días** siguientes al
  cambio de residencia.
- **Trampa:** no se puede **enajenar (vender, alquilar o ceder) durante los 12
  meses siguientes** a la matriculación, o Hacienda reclama el impuesto.
— [administracion.gob.es](https://administracion.gob.es/pag_Home/Tu-espacio-europeo/derechos-obligaciones/ciudadanos/vehiculos/traslado/impuesto.html), [gestoriamasaga.es](https://www.gestoriamasaga.es/blog-trafico/excencion-del-impuesto-matriculacion-al-importar-vehiculo/), [mciconsulting.com](https://mciconsulting.com/importacion-de-vehiculos-por-traslado-de-residencia/), 「vía buscador」

**Nuestra calculadora no contempla este caso en absoluto y le cobra el IEDMT
completo a alguien que está exento.** Es el peor falso positivo posible: le
decimos a un retornado que pagará 3.000 € cuando paga 0.

- **Volumen:** menor que A, pero **conversión altísima** — esta persona ya tiene
  el coche, ya va a hacer el trámite, y busca activamente. Es el segmento con
  **mejor intención de búsqueda** de todos.
- **Pagaría alto** por un checklist de plazos (60 días / 12 meses) que le evite
  perder la exención.

### F. El profesional / semiprofesional

Referencia: Car&Car, **123 vehículos importados en 2023**. Márgenes citados de
"2.000 € a 5.000 € por operación" ⚠️ (fuente de formación, sesgada al alza, no
fiable). Régimen fiscal propio: **REBU**, IVA sobre el margen, no deducible.

- **Necesita:** volumen, no guía. Alertas de oportunidad, comparativa
  automática contra precio español, gestión de expedientes múltiples.
- **Es quien más pagaría por ayuda, y con diferencia.** Para él la app es una
  herramienta de trabajo y el coste se amortiza en una sola operación.

### Respuesta directa a la pregunta

- **Más volumen: el segmento A** (ahorro en coche normal, ~10 años de edad).
- **Más pagaría: el F** (profesional), y en segundo lugar el **E** (retornado),
  porque en ambos el coste del error es enorme y el valor está concentrado.
- **Mejor encaje con lo que YA tenemos: el C** (eléctrico) — fiscalidad
  sencilla, comprador numérico, nuestra checklist ya cubre lo importante.

---

## 4. Hilos e índices pendientes de leer desde una red sin filtro

No los he podido abrir. Quedan aquí como cola de trabajo, porque los títulos ya
dicen dónde está el dolor:

- `forocoches.com/foro/showthread.php?t=8923516` — **"Problema ITV coche
  importado Alemania + Homologación individual"** ← el más valioso de todos
- `forocoches.com/foro/showthread.php?t=4963622` — "Matricular en España un
  coche alemán. He hecho el SUBNORMAL?"
- `forocoches.com/foro/showthread.php?t=9790769` — "Importar un vehículo de
  Alemania actualmente - Mi experiencia"
- `forocoches.com/foro/showthread.php?t=6599103` — "Importar coche que está
  modificado de Alemania, ¿Estaría homologado en España?"
- `foro.clubvwgolf.com/topic/199475-...` — "Por qué no traer un coche de
  importación. Experiencia propia de compra horrible"
- `mbfaq.com/viewtopic.php?t=284562` — "Ojo con la garantía si quieres comprar
  coche en Alemania"
- `bmwfaq.org/threads/denuncia-a-compra-venta-en-alemania.41777/`
- `bmwfaq.org/threads/de-como-ganar-la-partida-a-un-compra-venta-ante-su-negativa-a-pagar-las-averias.1061944/`
- `audisport-iberica.com/foro/topic/388863-garantía-coche-alemania/`

---

## Pendiente de validar

- ⚠️ **Tipos autonómicos del IEDMT** (¿Cataluña al 16%?) — verificar en BOE
  antes de tocar la calculadora.
- ⚠️ **Traducción jurada**: ¿obligatoria también para COC y permisos UE
  armonizados, o solo para el contrato?
- ⚠️ **MOVES para EV importado usado** — mi lectura es que no aplica, sin
  confirmar.
- ⚠️ **Punto exacto de abandono** — mi hipótesis es la financiación. Se
  confirma con una sola pregunta a usuarios reales.
- ⚠️ **Descuento de reventa** de un coche importado en España — nadie da un
  número fiable.
- **Toda la sección de citas** debería re-verificarse abriendo los hilos desde
  una red sin filtro antes de usar cualquier frase en marketing.

---

## Los 10 errores que más caro salen

Ordenados por coste del error. La última columna es lo que hace **hoy** la app.

| # | Error | Coste típico | Qué hace la app hoy |
|---|---|---|---|
| 1 | **Comprar un coche modificado** (llantas, suspensión, escape) creyendo que el TÜV alemán vale aquí | **2.500–3.000 € +IVA** de homologación individual, o revertirlo todo | **Nada.** Ni un punto en la checklist, ni una línea en la calculadora. Es nuestro mayor agujero |
| 2 | **Comprar sin COC** un coche sin homologación europea equivalente | **2.500–3.000 €** (homologación individual) | Mal: lo tasamos en **250 €**, un factor 10 por debajo |
| 3 | **Ser víctima de estafa de señal** (anuncio falso, transferencia antes de ver el coche) | **Todo lo transferido.** Caso judicial: 175 víctimas, >380.000 € | El punto existe (`pago-seguro`) pero está en la **fase 8**, cuando el daño ya está hecho |
| 4 | **Kilómetros manipulados** | **7.200 €** de sobreprecio en el caso Audi S3 documentado | **Bien cubierto:** VIN, informe de historial, HU anteriores, desgaste coherente, OBD. Nuestro punto fuerte |
| 5 | **Pasarse de tramo de CO₂** por no acreditarlo | **~5% de la base imponible por tramo**; miles de euros en un diésel >200 g/km | **Bien:** punto crítico `co2-oficial` + la calculadora aplica el tramo máximo sin dato. Correcto |
| 6 | **No saber que el vendedor retiene el Teil II** por financiación | Operación entera muerta + viaje perdido (~400 €) o pago perdido | **Bien:** punto crítico `doc-de-2`. Solo para Alemania; falta el equivalente en otros países |
| 7 | **Firmar un contrato de "Agenturgeschäft"** o declararse comerciante → cero garantía | **El importe de la primera avería seria: 1.500–3.000 €** | **Nada.** No lo conocíamos |
| 8 | **Ir con vehículo nuevo fiscal** (<6 meses o <6.000 km) sin contar el IVA | **21% del valor.** En un coche de 25.000 €, 5.250 € | **Bien:** la calculadora lo detecta y avisa. De lo mejor que tenemos |
| 9 | **Retornado que paga el IEDMT estando exento** por no pedir la exención en 60 días, o que vende antes de 12 meses | **El impuesto entero: 1.000–5.000 €** | **Nada.** La calculadora le cobra igualmente |
| 10 | **Averiarse y descubrir que reclamar exige abogado en Alemania** | Coste de la avería + honorarios, con riesgo de vendedor insolvente | Parcial: el contrato bilingüe está; el aviso de que la garantía no es ejecutable en la práctica, no |

**Errores menores pero muy frecuentes (no entran en el top 10 por importe, sí
por volumen):**

- Traer **Kurzzeitkennzeichen (amarilla, 5 días, pensada para Alemania)** en vez
  de **Ausfuhrkennzeichen (roja, ~30 días, validez internacional)**. La app trata
  las "placas temporales" como una sola cosa.
- No reservar **cita de ITV antes de viajar** (las horas de "reforma" escasean).
- No presupuestar **traducción jurada** (50–200 €/documento).
- No contar el **IVTM municipal**, que hay que pagar antes de matricular.
- No contar las **placas físicas** (~30 €).
- **Vivir en una ZBE**: desde el 1/1/2026 el coche con matrícula extranjera no
  puede entrar en Madrid, y la DGT no da etiqueta hasta matricularlo.

---

## Correcciones a la checklist

Sobre `coche-europa/lib/checklist.ts`.

### Puntos que FALTAN (por orden de importancia)

**En la fase `antes` (antes de coger el avión):**

1. **`reformas`** — *"El coche está de serie: sin llantas no originales,
   suspensión, escape, tintados ni cambios de potencia"*. `critical: true`,
   `weight: 3`, `repairCost: 2500`. **Es el punto que más dinero va a ahorrar de
   toda la checklist.** Pedir foto del Fahrzeugschein completo y de cualquier
   anexo TÜV/ABE.
2. **`financiacion`** — *"Tienes el dinero disponible en efectivo o
   transferencia"*. `critical: true`, `weight: 3`. Ningún banco español financia
   un coche sin matrícula española. Si no puedes pagarlo a tocateja, no hay
   viaje. **Probable punto de abandono número uno.**
3. **`senal-nunca`** — *"No has pagado NI UN EURO de señal"*. `critical: true`,
   `weight: 3`. Hoy esto vive en la fase 8 y llega tarde. **Duplicarlo aquí, no
   moverlo.**
4. **`anuncio-legitimo`** — *"El anuncio no tiene las señales del clonado"*:
   precio muy por debajo de mercado, vendedor sin teléfono que solo escribe por
   email, prisa artificial, petición de reserva. `weight: 3`.
5. **`valor-tablas`** — *"Has mirado el valor del coche en las tablas de precios
   medios de Hacienda, no solo el precio del anuncio"*. `weight: 3`. Es la base
   imponible real y la sorpresa más cara y repetida. Hoy solo tenemos
   `precio-mercado`, que compara con España — que es otra cosa.
6. **`cita-itv`** — *"Has mirado la disponibilidad de cita de ITV de
   matriculación en tu provincia"*. `weight: 2`. Las horas de "reforma" escasean.
7. **`seguro-espana`** — *"Una aseguradora española te ha confirmado que te
   asegura el coche, y con qué matrícula"*. `weight: 2`. La mayoría no aseguran
   matrícula extranjera.
8. **`residencia-exencion`** — solo si el usuario vuelve de vivir fuera:
   *"¿Cumples 12 meses fuera + 6 meses de propiedad? Tienes 60 días para pedir
   la exención y no puedes vender en 12 meses"*. `weight: 3`.

**En la fase `documentos`:**

9. **`contrato-agencia`** — *"El contrato NO dice 'Verkauf im Kundenauftrag' /
   'Agenturgeschäft', ni te hace declararte 'Gewerbetreibender'"*.
   `critical: true`, `weight: 3`. Señal de detección: si el vendedor negocia el
   precio sin consultar al propietario, no es una agencia legítima y la garantía
   sí te cubre.
10. **`historial-para-reventa`** — *"Te llevas copia de TODO el historial de
    origen"*. `weight: 2`. El historial DGT español empieza de cero; esos papeles
    son tu único activo el día que vendas.

**En la fase `mecanica`:**

11. **`cable-tipo2`** — *"Incluye cable de carga Tipo 2, no solo el Schuko de
    emergencia"*. `onlyFuel: ["electrico","phev"]`, `weight: 1`,
    `repairCost: 350`.
12. **`garantia-bateria-es`** — *"La garantía de batería es transferible y
    válida en la red española, y no hay campañas pendientes"*.
    `onlyFuel: ["electrico","phev"]`, `weight: 2`.

**En la fase `cierre`:**

13. **`traduccion-jurada`** — *"Sabes qué documentos hay que traducir y cuánto
    cuesta"*. `weight: 1`, `repairCost: 150`.
14. **`placas-correctas`** — *"Si vuelves conduciendo, llevas
    Ausfuhrkennzeichen (roja, validez internacional), NO Kurzzeitkennzeichen
    (amarilla, 5 días)"*. `critical: true`, `weight: 3`.
15. **`zbe`** — *"Si vives en ZBE, sabes que no podrás entrar con el coche hasta
    matricularlo"*. `weight: 2`. Desde el 1/1/2026 se multa automáticamente.

### Puntos MAL CALIBRADOS

| Punto | Qué falla | Corrección |
|---|---|---|
| `coc` | `repairCost: 250` y "ficha técnica reducida: +250 € y semanas de espera". **Dos errores en una frase**: la ficha reducida cuesta 39–90 € y tarda horas, y hace falta igual con COC | Subir a `weight: 3` y `repairCost: 2500`. Reescribir: *"El COC son 109–250 € y de 1 a 20 días. Sin COC y sin homologación europea equivalente, homologación individual: 2.500–3.000 €"* |
| `plazo-30-dias` | Dice "30 días **hábiles**". Son **30 días naturales desde el inicio del uso en España**, y el IEDMT se autoliquida **antes** de la matriculación | Corregir el texto y subir a `weight: 3` |
| `faros` | `repairCost: 900` pero su propio `detail` dice "puede costar **más de 1.500 €**". Se contradice | Subir a 1.300 |
| `dos-llaves` | `repairCost: 250`. En 2026 una llave keyless de premium alemán está en 300–500 € | Subir a 350 |
| `neumaticos` | `repairCost: 500`. Un juego de 4 en 18–19" premium (que es el coche típico de este flujo) está en 600–900 € | Subir a 700 |
| `informe-vin` | `critical: true` está bien, pero falta el matiz: **la ausencia de datos en carVertical/autoDNA no significa coche limpio**, significa que no hay datos de ese mercado | Añadir al `detail` |
| `pago-seguro` | Correcto, pero está solo en la fase 8 | Duplicar en la fase 1 como `senal-nunca` |

### Costes de reparación que SÍ están bien para 2026

Los he contrastado y aguantan: `distribucion` 900 € (rango real 600–1.200),
`dsg` 1.800 € (mecatrónica 1.500–2.500), `dpf-egr` 1.400 € (1.200–2.000),
`adblue` 1.000 € (800–1.500), `arranque-limpio` 1.800 € (cadena TSI/N47
1.500–2.500). **No tocar.**

### El orden de las fases: hay una contradicción interna

Hoy la fase 2 es **Papeles**, con subtítulo *"Lo primero al llegar, antes de
mirar el coche"*, y la fase 3 es **Arranque en frío**, con subtítulo *"Lo
PRIMERO que haces al llegar"*. **Las dos dicen ser la primera.** Y el propio
punto `motor-frio` es `critical: true`.

**El arranque en frío es perecedero: solo funciona una vez y solo si el motor
lleva horas parado.** Los papeles se pueden leer con el motor ya frío
comprobado. Si el comprador se sienta a revisar documentación media hora, el
vendedor tiene todo el tiempo del mundo para "ir a por un café" con el coche
encendido.

**Corrección: intercambiar las fases 2 y 3.** Orden correcto: 1 Antes de
viajar → **2 Arranque en frío** → **3 Papeles** → 4 Chapa → 5 Interior →
6 Motor → 7 Carretera → 8 Cierre. Y ajustar los dos subtítulos para que solo
uno diga "lo primero".

El resto del orden es correcto y coincide con cómo lo cuenta la gente.

---

## Qué implica para la app

Priorizado por impacto/esfuerzo. "Impacto" = cuánto dinero o abandono evita.

| # | Funcionalidad | Segmento | Impacto | Esfuerzo |
|---|---|---|---|---|
| 1 | **Detector de coche modificado** en la fase 1 + partida de "homologación individual 2.500 €" en la calculadora, activada por una casilla | B, D, todos | **Muy alto** — es el error nº1 y hoy no hacemos nada | **Bajo** — un punto de checklist y una línea de coste |
| 2 | **Arreglar `fichaTecnica` (250 → 60 €) y separar COC / homologación individual** | Todos | **Muy alto** — hoy mentimos en los dos sentidos | **Muy bajo** |
| 3 | **Modo "vuelvo a España" en la calculadora**: exención de IEDMT por cambio de residencia + recordatorios de los 60 días y de los 12 meses sin vender | E | **Muy alto** — pasamos de cobrar 3.000 € de más a ser la única herramienta que lo contempla | **Bajo** |
| 4 | **Plantillas de mensaje al vendedor en alemán/francés/italiano** (pedir VIN, CO₂, COC, fotos concretas, historial HU, confirmar que no hay Agenturgeschäft) | Todos, sobre todo A | **Alto** — desbloquea al que no habla idiomas, que hoy simplemente no escribe | **Bajo** — texto, cero lógica |
| 5 | **Aviso anti-señal en la fase 1** + checklist de anuncio legítimo | Todos | **Alto** — evita el 100% de la pérdida | **Muy bajo** |
| 6 | **Comparador automático contra el precio en España** (ya tenemos Coches.net y Milanuncios en `portals.ts`): "este coche en España sale por X, ahorras Y, que es el Z% del precio" | A, F | **Alto** — es la pregunta que de verdad se hace la gente | **Medio** — hay que estimar precio español sin scraping |
| 7 | **Contrato de compraventa bilingüe descargable** (ES/DE y ES/FR), con la cláusula de "libre de cargas" y **sin** cláusula de agencia | Todos | **Alto** — resuelve un punto crítico y da sensación de producto serio | **Bajo** — es un PDF generado |
| 8 | **Línea de tiempo con recordatorios de plazos legales**: 30 días naturales para matricular, 60 días para la exención por residencia, 12 meses sin vender, validez del non-gage (15 días) y del Ausfuhrkennzeichen | Todos, crítico en E | **Alto** | **Medio** — necesita notificaciones o calendario exportable |
| 9 | **Lista de qué llevar al viaje**: medidor de espesor de pintura, lector OBD, linterna, imán, el contrato impreso por duplicado, justificante de transferencia | Todos | **Medio-alto** — muy querida, poco esfuerzo | **Muy bajo** |
| 10 | **Guía de placas: Ausfuhr (roja) vs Kurzzeit (amarilla)**, con coste y qué cubre el seguro | A, B | **Medio-alto** | **Muy bajo** |
| 11 | **"Reserva la cita de ITV antes de viajar"** con enlace a cita previa por provincia | Todos | **Medio** — desatasca el final del proceso | **Bajo** |
| 12 | **Partidas que faltan en la calculadora**: traducción jurada, IVTM municipal, placas físicas (~30 €), y el **porcentaje** de sobrecoste sobre el precio del anuncio | Todos | **Medio** — precisión y credibilidad | **Bajo** |
| 13 | **Tipos autonómicos del IEDMT** ⚠️ (una fuente indica que Cataluña llega al 16% en el tramo alto; hoy solo distinguimos península/Canarias/Ceuta-Melilla) | Todos | **Medio** — pero si es cierto, es un error de miles de euros | **Bajo** — verificar primero en el BOE |
| 14 | **Búsqueda por equipamiento / códigos de opción**, no solo marca-modelo-precio | B | **Medio** — es LA necesidad del entusiasta | **Alto** — los portales no lo exponen igual |
| 15 | **Integración de informes de VIN** (carVertical/autoDNA) desde la ficha, con afiliación | Todos | **Medio** — ingreso + fricción eliminada | **Medio** |
| 16 | **Carpeta de reventa**: al cerrar el expediente, generar un PDF con todo el historial de origen para el día que venda | A, B, F | **Medio** — el historial DGT empieza de cero y nadie lo avisa | **Bajo** |
| 17 | **Modo furgoneta/camper**: aviso rojo de rehomologación como vivienda | D | **Alto para ese segmento**, nicho en volumen | **Medio** |
| 18 | **Modo profesional**: expedientes múltiples, alertas de oportunidad, exportación | F | **Alto en ingreso**, bajo en volumen de usuarios | **Alto** |
| 19 | **Conversor km/precio y de unidades** | Todos | **Bajo** — es cómodo, no cambia decisiones | **Muy bajo** |

### Si solo se pueden hacer tres cosas

**1, 2 y 3.** Las tres son de esfuerzo bajo, las tres corrigen un error nuestro
que hoy le cuesta dinero real al usuario, y ninguna requiere infraestructura
nueva. Después, la 4 y la 5, que son texto puro y desbloquean al usuario que
hoy no se atreve ni a escribir al vendedor.

### Lo que NO deberíamos hacer todavía

Camper (17) y modo profesional (18) son segmentos con necesidades tan distintas
que exigen producto propio. Y la búsqueda por equipamiento (14) es la
funcionalidad más deseada del segmento B, pero es la más cara de todas y
choca con la decisión de no hacer scraping.
