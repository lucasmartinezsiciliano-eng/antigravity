# MiroFish — Simulaciones pre-lanzamiento Centrum

> 5 simulaciones priorizadas para validar el sistema **antes** de abrir el grifo de leads reales. Todas corren en DGX Spark con Gemma local. Coste: 0 €. Tiempo total: ~6-10 horas en batch nocturno.

---

## SIM 1 — Validación del script Call IA

**Pregunta a resolver:** ¿El script extrae los 13 datos en <7 minutos sin abandono masivo?

**Setup:**
- **Seed:** script Call IA completo + 6 variantes apertura + 5 variantes aviso grabación + 5 variantes "ahora no puedo"
- **Agentes:** 50 perfiles deudores hipotecarios
  - 10× Paralizado por miedo
  - 8× Desconfiado ("¿esto es legal?")
  - 8× Apurado sin tiempo
  - 6× Listo para hablar
  - 6× Vergüenza absoluta (resiste dar banco)
  - 6× Ya habló con otro broker
  - 6× Mayor 60+ con dificultad audio

**Output esperado:**
- Matriz `subperfil × variante apertura` con tasa de continuación
- Datos que más resistencia generan (banco, judicial, avalistas)
- Puntos exactos del script con drop-off >30%
- Recomendación de qué variantes mantener y cuáles descartar

**Comando:**
```bash
hermes profile use centrum
hermes chat "Lanza MiroFish SIM 1 (call-ia-script) con 50 agentes según el setup documentado en mirofish-sims-prelaunch.md. Guarda output en Obsidian Vault > Centrum/Simulaciones/[fecha]-sim1-call-ia.md"
```

**Trigger:** antes de la primera llamada real con Twilio
**Coste cómputo:** ~90 min en DGX Spark
**Umbral de éxito:** tasa de extracción completa de los 13 datos ≥ 75% en subperfiles A+B+E (los que importan)

---

## SIM 2 — Validación del clasificador A/B/C/D/E

**Pregunta a resolver:** ¿El clasificador acierta o tiene sesgo en algún subperfil?

**Setup:**
- **Seed:** skill `centrum/clasificacion-ae` + 100 casos sintéticos generados a partir de combinaciones de las 13 variables
- **Casos:**
  - 20 casos claros A (subasta <60 días o demanda judicial)
  - 20 casos claros B (1-12 meses sin pagar, sin demanda)
  - 15 casos C (sin hipoteca, fuera de zona)
  - 15 casos D (juicio fijado, plazo procesal corto)
  - 15 casos E (cliente quiere entregar)
  - 15 casos ambiguos a propósito (A o B / B o C / etc)

**Output esperado:**
- Matriz de confusión: predicho vs etiqueta correcta
- Casos donde el clasificador se equivoca → reglas a refinar
- Detección de sesgos por género/edad/banco (no debería haber)
- En casos ambiguos: ¿el clasificador escala correctamente a Mariano?

**Comando:**
```bash
hermes chat --profile centrum "Lanza MiroFish SIM 2 (clasificador-ae) con 100 casos sintéticos. Compara predicción vs etiqueta. Guarda confusión + análisis en Centrum/Simulaciones/[fecha]-sim2-clasificador.md"
```

**Trigger:** antes de activar el pipeline de leads reales
**Coste cómputo:** ~30 min
**Umbral de éxito:** ≥ 90% accuracy en casos claros, escalación correcta en 100% de ambiguos

---

## SIM 3 — Pre-matching de estrategias

**Pregunta a resolver:** Cuando el sistema sugiere "E5 cláusulas + E3 venta", ¿es una sugerencia razonable o disparatada para Mariano?

**Setup:**
- **Seed:** skill `centrum/8-estrategias` + 20 casos con datos completos (banco, deuda, valor, año hipoteca, situación, etc)
- **Casos pensados para activar combinaciones:**
  - 5 casos pre-2013 con CaixaBank → debería sugerir E5 + E3
  - 3 casos con fondo buitre + deuda alta → debería sugerir E2 + E7 (+8a oportunidad)
  - 3 casos con familiar solvente → debería incluir E4
  - 3 casos sin equity y sin recursos → debería incluir E9 (red de seguridad)
  - 3 casos urgentes con demanda → debería incluir E6 (defensa) + E5
  - 3 casos múltiples deudas inasumibles → debería incluir E8 (segunda oportunidad)

**Output esperado:**
- Tabla `caso → estrategias sugeridas en orden de viabilidad`
- Validación humana por Mariano: ¿estás de acuerdo con cada match?
- Tasa de "matchea razonable" / "matchea incorrectamente" / "matchea pero le falta una estrategia obvia"

**Comando:**
```bash
hermes chat --profile centrum "Lanza MiroFish SIM 3 (pre-matching) con los 20 casos sintéticos. Genera la tabla caso → estrategias sugeridas. Después yo (Mariano) la valido caso a caso."
```

**Trigger:** una vez que la SIM 2 esté validada
**Coste cómputo:** ~45 min
**Umbral de éxito:** ≥ 85% de matches considerados razonables por Mariano

---

## SIM 4 — Validación del quiz/formulario web

**Pregunta a resolver:** ¿Las 6 preguntas (vs 4) generan más abandono que cualificación añadida?

**Setup:**
- **Seed:** 3 variantes del formulario
  - A: actual 4 preguntas
  - B: 4 preguntas + "con qué banco"
  - C: 6 preguntas (las 4 + banco + vivienda habitual)
- **Agentes:** 30 perfiles
  - 10× alta urgencia (rellenan aunque sean 10 preguntas)
  - 10× urgencia media (abandonan si suena interrogatorio)
  - 10× baja urgencia / curiosos (abandonan en pregunta 3 si incómoda)

**Output esperado:**
- % abandono por variante × subperfil
- Pregunta exacta que dispara más abandono
- Recomendación: ¿el banco va en pregunta 2 o pregunta 6?
- Tasa cualificación esperada por variante (cuántos leads A/B aprovechables se ganan o se pierden)

**Comando:**
```bash
hermes chat --profile centrum "Lanza MiroFish SIM 4 (quiz-form) con las 3 variantes y 30 agentes. Output: tabla abandono × variante × subperfil + recomendación final del orden de preguntas."
```

**Trigger:** antes de publicar la web v2 con quiz nuevo
**Coste cómputo:** ~30 min
**Umbral de éxito:** la variante elegida cualifica más leads A/B aunque tenga ligeramente más abandono total

---

## SIM 5 — Validación del auto-responder + notificación a Mariano

**Pregunta a resolver:** ¿La firma "El equipo de Centrum" genera la misma confianza que la firma personal de Mariano? ¿Cómo de transparente debemos ser sobre el call IA?

**Setup:**
- **Seed:** 4 versiones del auto-responder
  - V1 actual: firma equipo, "a la brevedad"
  - V2: firma Mariano personal, "te llamo en breve"
  - V3: firma equipo + timing concreto, "te llamo en los próximos 90 min"
  - V4: firma equipo + transparencia, "primero te llamará nuestra asistente IA en 2 min para preparar tu caso, luego Mariano te llama personalmente"
- **Agentes:** 25 perfiles del avatar (mismos del SIM 1)

**Output esperado:**
- Tasa "answer-rate del call IA" predicha por variante
- Análisis: ¿la transparencia sobre IA (V4) ayuda o asusta?
- Diferencia de comportamiento por categoría (A / B / E)
- Versión ganadora con argumentación

**Comando:**
```bash
hermes chat --profile centrum "Lanza MiroFish SIM 5 (auto-responder) con 4 variantes × 25 agentes. Output: ranking de variantes por answer-rate + análisis de sentiment."
```

**Trigger:** antes de activar n8n + auto-responder en producción
**Coste cómputo:** ~30 min
**Umbral de éxito:** answer-rate del call IA proyectado ≥ 65% con la versión elegida

---

## Orden de ejecución y dependencias

```
Día 1 — noche
  SIM 1 (call-ia-script)    [90 min]
  SIM 4 (quiz-form)         [30 min]
  SIM 5 (auto-responder)    [30 min]

Día 2 — noche (revisión humana día siguiente)
  Lucas + Mariano revisan outputs SIM 1, 4, 5
  Se aplican cambios al script / formulario / auto-responder

Día 3 — noche
  SIM 2 (clasificador-ae)   [30 min]
  SIM 3 (pre-matching)      [45 min]

Día 4 — revisión + ajustes finales
  Mariano valida pre-matching caso a caso
  Se documenta qué reglas necesitan refinarse

Día 5 — GO/NO-GO
  Si todas las sims pasan umbral → lanzar smoke test con leads reales (5-10)
  Si no → iterar
```

---

## Almacenamiento de resultados

Cada simulación deja:

```
~/Documents/Obsidian Vault/Broker/Centrum/Simulaciones/
  2026-05-30-sim1-call-ia.md       # tabla + análisis
  2026-05-30-sim2-clasificador.md
  2026-05-30-sim3-pre-matching.md
  2026-05-30-sim4-quiz-form.md
  2026-05-30-sim5-auto-responder.md
```

Y un engram PLUR:
```
mirofish:run:2026-05-30:sim-pre-launch
```

Para que las próximas iteraciones (mes 2, mes 3) puedan comparar contra esta baseline y detectar si algo se ha degradado.

---

## Qué hacer si una sim falla el umbral

| SIM | Fallo posible | Acción |
|---|---|---|
| 1 | Abandono >40% en alguna apertura | Reescribir esa variante, re-simular |
| 2 | Accuracy <85% | Refinar skill `clasificacion-ae` con reglas más específicas |
| 3 | Mariano marca >20% de matches como "incorrectos" | Refinar skill `8-estrategias` con su feedback |
| 4 | Abandono >25% en variante recomendada | Considerar quitar una pregunta o cambiar orden |
| 5 | Answer-rate proyectado <55% | Probar combinación de elementos de V3+V4 |

En cada caso: corregir → re-simular → no avanzar hasta pasar.

---

## Lo que estas sims NO validan (recordatorio)

- Que Twilio llama de verdad → smoke test con número real
- Que el calendario reserva slots → smoke test con Google Calendar
- Que Mariano recibe el Telegram → smoke test con bot
- Que el cliente realmente firma el RGPD → flow test con Signaturit
- Que el cobro funciona → flow test con Stripe

Eso es la **Fase 1 (integration tests)**. MiroFish es **Fase 2 (behavioral validation)**.

---

← [[Broker/Centrum/index]]
