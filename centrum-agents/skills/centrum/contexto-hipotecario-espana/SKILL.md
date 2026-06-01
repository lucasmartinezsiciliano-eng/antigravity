---
name: centrum-contexto-hipotecario-espana
description: Base de conocimiento del contexto hipotecario español para que Ana (call-vendedor) y el dm-qualifier RECONOZCAN señales y pregunten con criterio, sin asesorar. Cubre cláusulas abusivas, fases de la ejecución hipotecaria, banca vs fondos buitre, protecciones de vivienda habitual y vocabulario clave. Se activa en captación, llamada IA y DM. NO es asesoramiento jurídico.
version: 1
---

# Contexto hipotecario España — para reconocer, no para asesorar

> **Para qué sirve:** que Ana entienda de qué le habla el cliente, reconozca señales relevantes y haga la pregunta adecuada en el momento adecuado. Cuanto mejor entienda el terreno, mejor recoge → mejor análisis.
>
> **Límite absoluto (guardrails + legal-rgpd):** este conocimiento es para que Ana ESCUCHE y PREGUNTE mejor, **nunca** para diagnosticar, citar artículos como certeza ni prometer resultados. Si el cliente pide criterio legal → "eso te lo confirma Mariano y el abogado". Casi todo aquí es "casi siempre / suele / a menudo", nunca "seguro".

---

## 1. Cláusulas potencialmente abusivas (las que infla la deuda)

| Cláusula | Qué es, en cristiano | Señal que el cliente puede dar |
|---|---|---|
| **Cláusula suelo** | Un mínimo al interés: aunque el Euríbor baje, la cuota no baja de cierto punto | "Cuando bajó el Euríbor, mi cuota no bajó" |
| **IRPH** | Un índice distinto del Euríbor, típico 2004-2012; cuota más cara | "No iba con Euríbor", "me hablaron de otro índice" |
| **Gastos hipotecarios** | Notaría, registro, gestoría cargados al cliente cuando tocaban al banco (pre-2013) | "Pagué yo todos los gastos al firmar" |
| **Vencimiento anticipado** | El banco reclama TODA la deuda con pocos impagos | "Por dejar de pagar unos meses me reclaman todo" |
| **Intereses de demora** | Recargo por impago; si es desproporcionado, posiblemente abusivo | "Me han disparado lo que debo desde que dejé de pagar" |
| **Comisión de apertura / reclamación** | Cobros que pueden no corresponder a un servicio real | "Me cobran 30-35€ cada vez que se me pasa una cuota" |

> **Pista temporal clave:** hipoteca **anterior a 2013** = probabilidad muy alta de alguna de estas. Por eso el **año de firma** es un dato extendido valioso (ver `datos-para-analisis`). Conecta con la Regla 1: "la deuda casi siempre está inflada".

---

## 2. Fases de la ejecución hipotecaria (de menos a más urgente)

1. **Impago sin comunicación** — meses de margen.
2. **Cartas de reclamación del banco** — semanas hasta el burofax.
3. **Burofax / requerimiento notarial** — empieza lo formal.
4. **Demanda de ejecución interpuesta** (hay nº de procedimiento) — meses hasta subasta según juzgado.
5. **Inscrito en el Registro de la Propiedad** — más difícil de parar.
6. **Fecha de subasta anunciada (BOE)** — urgencia MÁXIMA → escalación en caliente a Mariano.
7. **Subasta celebrada** — durísimo, pero aún hay ventanas (segunda oportunidad, post-subasta).

> Lo que Ana necesita distinguir al oído: **¿cartas del banco** (fases 1-3, menos urgente) **o ya algo del juzgado** (fases 4+, urgente)? Esa sola distinción cambia el riesgo y la velocidad de respuesta. La fase fina la determina `legal-risk-assessor`.

---

## 3. Quién es el acreedor: banco vs fondo buitre

- **Bancos negociadores** (CaixaBank, Santander, BBVA, Sabadell): suelen negociar antes de subasta; aceptan quitas/refinanciación para evitar coste judicial.
- **Fondos buitre** (Cerberus, Lone Star, Blackstone, Cabot, Hoist): compran la deuda con descuento. A veces más negociables (compraron barato), a veces más agresivos (quieren liquidar).
- **Señal clave a recoger:** "¿Sigues tratando con tu banco, o te llaman de otra empresa con otro nombre?" → si es otra empresa, probablemente la deuda se ha **cedido a un fondo**. Esto lo explota `bank-behavior-analyst`.

---

## 4. Protecciones del cliente (para reconocer, no para prometer)

- **Vivienda habitual** vs segunda residencia: la habitual suele tener más protección. Por eso se pregunta "¿es la casa donde vivís?".
- **Colectivos vulnerables** (familias con menores, dependientes, sin ingresos): pueden tener protecciones adicionales y, a veces, paralizaciones. Relevante para clasificación y tono.
- **Código de Buenas Prácticas bancario / dación en pago**: existen mecanismos, pero su aplicabilidad la valora el abogado. Ana no los promete.

---

## 5. Vocabulario que Ana debe entender (y traducir a lenguaje sencillo)

| Término | En cristiano |
|---|---|
| **Quita** | Que el banco perdone una parte de la deuda |
| **Dación en pago** | Entregar la casa y quedar sin deuda (no siempre posible) |
| **Subrogación** | Que otra persona/entidad entre en la hipoteca |
| **Carencia** | Periodo pagando solo intereses (o nada) un tiempo |
| **Segunda oportunidad** | Ley para cancelar deudas cuando no hay forma de pagar |
| **Lanzamiento / desahucio** | La fecha en que te obligan a salir de la casa |
| **Subasta** | Venta forzosa del inmueble por el juzgado |

> Ana usa estas palabras solo si el cliente las usa primero, y siempre las traduce a lenguaje llano. Nunca suena a abogada.

---

## Cierre de criterio

Este contexto es el "oído entrenado" de Ana. Le permite: (a) entender al cliente sin pedirle que se explique mil veces, (b) saber qué señal vale oro para el análisis, (c) reconocer urgencia real. **Lo que NO le permite:** asesorar. Esa raya no se cruza nunca — la cruza Mariano con el abogado.
