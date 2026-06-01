---
name: centrum-datos-para-analisis
description: Mapa que conecta lo que Ana (call-vendedor) y el dm-qualifier RECOGEN con lo que cada agente de análisis (bloque-5) y evaluación (bloque-6) NECESITA para acertar. Define los 13 datos núcleo + los datos extendidos, la pregunta natural para sacar cada uno y por qué importa. Se activa en captación, llamada IA y DM. Objetivo: que el análisis posterior sea el mejor y más acertado.
version: 1
---

# Datos para el análisis — qué preguntar y por qué

> **Idea central:** la calidad del análisis depende de la calidad de lo que Ana recoge en la llamada. Cada dato que falta es una conclusión que el analista tiene que estimar o que Mariano tiene que repreguntar. Esta skill le dice a Ana **qué sacar, cómo preguntarlo con naturalidad y para qué sirve después.**
>
> **Regla de oro al usar esta skill:** Ana RECOGE, no asesora. El "por qué importa" es para el razonamiento de Ana, **nunca** se le explica al cliente como si fuera un diagnóstico legal. Una pregunta por turno, sin interrogar, validando emoción primero (ver `empatia-crisis`).

---

## Cómo se prioriza en la llamada

1. **Críticos (siempre, aunque la llamada sea corta):** impago + banco + judicial. Con esos tres Mariano clasifica A/B/C/D/E.
2. **Núcleo (los 13):** se completan si la conversación da para ello.
3. **Extendidos:** se sacan **cuando fluye**. No se fuerzan. Cada uno que Ana consiga es oro para el análisis; si no sale, queda en `datos_pendientes` y Mariano o el `missing-data-detector` lo pedirán después.
4. **El objetivo del cliente** (ver más abajo y skill `objetivo-cliente`) es el dato que más cambia la estrategia: priorízalo en cuanto haya confianza.

---

## Los 13 datos núcleo (recordatorio)

`nombre · contacto · inmueble_ubicacion · deuda_capital · impago_cuotas · cuota_mensual · banco · titulares · avalistas · tipo_interes · plazo_restante · otras_deudas · judicial`

Detalle y prioridad en `call-vendedor/IDENTITY.md`. Lo que sigue son los **datos extendidos** que multiplican la precisión del análisis.

---

## Mapa dato → análisis (datos extendidos)

### Para `debt-analyzer` (calcula la deuda REAL, busca inflación)
| Dato extendido | Pregunta natural (ejemplo) | Por qué importa (interno) |
|---|---|---|
| ¿Le han añadido recargos/comisiones por los impagos? | "¿Te han ido sumando comisiones o recargos por las cuotas atrasadas?" | Comisiones de reclamación >30€ o intereses de demora >2x interés legal → posiblemente abusivos y reclamables |
| Seguros vinculados a la hipoteca | "¿Pagas algún seguro de vida o de hogar metido dentro de la hipoteca?" | Seguros cobrados indebidamente inflan la deuda |
| Importe que el banco dice que debe AHORA (vs capital) | "¿Te han dicho una cifra total de lo que reclaman ahora mismo?" | La diferencia con el capital es la inflación a auditar |

### Para `clause-detector` (cláusulas abusivas en la escritura)
| Dato extendido | Pregunta natural | Por qué importa |
|---|---|---|
| **Año de firma de la hipoteca** | "¿Te acuerdas más o menos de qué año firmasteis la hipoteca?" | Pre-2013 → probabilidad MUY alta de gastos/cláusulas abusivas |
| Señal de cláusula suelo | "¿Recuerdas si, cuando el Euríbor bajó mucho, tu cuota no llegaba a bajar?" | Síntoma clásico de cláusula suelo (recuperable retroactivo) |
| Tipo de interés con detalle (fijo/variable/**IRPH**) | "¿Sabes si tu hipoteca iba con Euríbor o con otro índice?" | IRPH y suelo son las dos grandes palancas; afina el dato núcleo `tipo_interes` |
| Banco **original** (si difiere del actual) | "¿Con qué banco la firmasteis al principio?" | Las cláusulas son de la escritura original, no del fondo actual |

### Para `bank-behavior-analyst` (margen real de negociación)
| Dato extendido | Pregunta natural | Por qué importa |
|---|---|---|
| **¿Quién tiene la deuda AHORA: el banco o un fondo?** | "¿Sigues tratando con {banco}, o te llaman de otra empresa distinta?" | Fondo buitre vs banco cambia por completo la estrategia de negociación |
| Contacto previo y postura del banco | "¿Has llegado a hablar con ellos? ¿Te ofrecieron algo?" | Marca el punto de partida de la negociación |

### Para `legal-risk-assessor` (fase judicial y plazos reales)
| Dato extendido | Pregunta natural | Por qué importa |
|---|---|---|
| Fase exacta: carta / burofax / demanda / nº procedimiento | "¿Lo que has recibido son cartas del banco, o ya algo del juzgado?" | Define el riesgo BAJO/MEDIO/ALTO y la ventana de acción |
| ¿Inscrito en el Registro de la Propiedad? | (normalmente lo deduce el analista; preguntar solo si el cliente lo sabe) | Tras inscripción es más difícil parar |
| **Fecha de subasta** (si anunciada) | "¿Te han dado alguna fecha concreta?" | Urgencia máxima → escalación en caliente a Mariano |
| Fecha de la última notificación | "¿Cuándo recibiste el último papel?" | Calcula plazos reales |

### Para `property-valuator` (valor de mercado y de subasta)
| Dato extendido | Pregunta natural | Por qué importa |
|---|---|---|
| Superficie (m²), habitaciones | "¿Cuántos metros tiene más o menos?" | Base de la valoración + comparables |
| Estado de conservación / reforma reciente | "¿Cómo está la casa, está para entrar a vivir o necesita arreglos?" | Ajuste ±15-25% sobre comparables |
| Tipo (piso/casa) y planta | (si fluye) | Afina comparables en Casafari/Idealista |

### Para `bloque-6` (evaluadores de solución) y `solution-matcher`
| Dato extendido | Pregunta natural | Alimenta a |
|---|---|---|
| **Objetivo del cliente** (quedarse / salir limpio / ganar tiempo / liquidez) | "¿Qué es lo que más te gustaría: quedarte en casa, o salir de esto sin deudas?" | TODOS los evaluadores + `solution-matcher` (driver nº1 de la estrategia) |
| ¿Vivienda habitual o segunda residencia? | "¿Es la casa donde vivís a diario?" | `legal-risk` (más protección si es habitual), `family-mortgage`, clasificación |
| Situación laboral / ingresos del hogar | "¿Cómo estáis ahora de ingresos, trabajáis?" | `time-gain-evaluator` (capacidad de ahorro), `family-mortgage` |
| Personas en el hogar (hijos, dependientes) | "¿Quién vive contigo en casa? ¿Tenéis hijos?" | Vulnerabilidad → protecciones legales + tono (`empatia-crisis`) |
| ¿Dispuesto a vender? | "¿Te habrías planteado vender si saliera a cuenta?" | `sale-evaluator` |
| ¿Familiares que puedan ayudar/subrogar? | "¿Tienes familia que pudiera echar una mano o entrar en la hipoteca?" | `family-mortgage-evaluator` |
| Capacidad de ahorro mensual | (se deduce de ingresos/gastos; preguntar suave) | `time-gain-evaluator` |

---

## Marcado en la ficha

- Todo dato extendido que se consiga va en `notas_emocionales` o en un bloque `datos_extendidos` de la ficha (call-prep lo recoge en la ficha de 1 página).
- Lo que NO se consiga → `datos_pendientes`. No pasa nada: es señal para `missing-data-detector` y `question-suggester`.
- **Nunca inventar un dato.** Si el cliente no lo sabe (p. ej. el año de la hipoteca), se marca "no lo recuerda", no se rellena a ojo.

## Límites (heredados de guardrails y legal-rgpd)
- Ana no diagnostica ("tienes cláusula suelo", "esto es abusivo", "esto se gana"). Solo recoge señales. El análisis lo hacen los agentes de bloque-5/6 y lo confirma Mariano/abogado.
- Datos sensibles a fondo (escrituras, nóminas, extractos) **no** se piden aquí: eso es tras la firma de Capa 2 (ver `legal-rgpd`). En la llamada solo se recoge lo que el cliente cuenta de palabra.
