# INTEL-FEEDBACK-LOG.md
# Log de reacciones de Lucas a los informes diarios forge + horizon
# SOLO APPEND — nunca borrar entradas
# Formato estandarizado para que los agentes puedan parsearlo automáticamente

---

## FORMATO DE ENTRADA

```
---
DATE: [DD/MM/YYYY]
AGENT: [forge | horizon]
SIGNAL_ID: [fecha-agente-N, ej: 20260521-forge-1]
SIGNAL_TITLE: [título corto de la señal]
REACTION: [👍 | 👎 | 💬 | ⚡ | ❓]
COMMENT: [comentario de Lucas si lo hay — puede estar vacío]
ACTION_TAKEN: [sí/no/pending — rellenar cuando se confirme]
---
```

### Leyenda de reacciones
- 👍 Útil, lo tengo en cuenta
- 👎 No relevante / no me interesa
- 💬 Interesante pero necesito más info
- ⚡ Actúo ahora mismo
- ❓ No entiendo o necesito explicación

---

## CÓMO SE RELLENA ESTE LOG

### Opción A — Via Telegram (automático via n8n)
Lucas responde al mensaje del digest diario con:
- Un emoji de la leyenda + número de señal: `👍1 👎2 ⚡3`
- O un comentario libre: `"el punto 1 es muy interesante, seguir monitorizando"`
- n8n workflow `Intel - Feedback Logger` parsea el mensaje y escribe aquí

### Opción B — Manual (fallback)
Lucas o el sistema añade entradas directamente en este fichero siguiendo el formato.

---

## CICLO DE CALIBRACIÓN DOMINICAL

Cada domingo, el agente (forge o horizon) lee este log y:
1. Agrupa por REACTION
2. Calcula ratios por fuente (para actualizar INTEL-CALIBRATION.md)
3. Detecta anti-patrones (señales ignoradas ≥3 veces)
4. Detecta nuevos patrones de gusto (señales actuadas ≥2 veces)
5. Escribe resumen de calibración al final de este mismo archivo

---

## ENTRADAS

<!-- Las entradas empiezan aquí. El sistema las añade cronológicamente. -->

<!-- SEMANA 1 — 2026-05-21 al 2026-05-25 -->

<!-- [las entradas se añadirán automáticamente] -->

---

## CALIBRACIONES DOMINICALES

<!-- El resumen semanal de calibración se añade aquí cada domingo -->

<!-- CALIBRACIÓN SEMANA 0 — 2026-05-25
Sin datos todavía. Sistema arrancando.
-->
