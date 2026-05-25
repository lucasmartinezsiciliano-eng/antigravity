# thinking-mode — Separar razonamiento profundo de uso de herramientas

> Skill de orquestación interna. Resuelve un conflicto técnico real de Gemma 4 + vLLM.

---

## El problema que esto resuelve

Gemma 4 soporta thinking tokens (razonamiento interno antes de responder). Pero hay un conflicto conocido en vLLM:

**`enable_thinking: true` + tool calling activo → JSON malformado / tags de razonamiento que se cuelan en la respuesta**

La solución es separar las tareas en dos fases:
1. **Fase de razonamiento** (`enable_thinking: true`, sin tools) → el modelo piensa profundo
2. **Fase de ejecución** (`enable_thinking: false`, con tools) → el modelo actúa

Por defecto, todos los servidores vLLM de Centrum tienen thinking desactivado (`--default-chat-template-kwargs '{"enable_thinking": false}'`). Solo se activa per-request cuando conviene.

---

## Cuándo activar thinking mode

### Activar (`enable_thinking: true`, sin tools)
| Tarea | Por qué |
|-------|---------|
| `debt-analyzer` analizando el cálculo de deuda real | Razonamiento matemático con múltiples variables |
| `solutions-director` evaluando las 8 estrategias | Necesita pesar trade-offs sin distracciones |
| `legal-risk-assessor` interpretando una sentencia | Razonamiento jurídico denso |
| `clause-detector` revisando una escritura de hipoteca | Leer entre líneas en documentos complejos |
| `recommendation-agent` construyendo el informe final | Síntesis de análisis paralelos |

### No activar (dejar `enable_thinking: false`, con tools)
| Tarea | Por qué |
|-------|---------|
| Cualquier tarea que necesite llamar a APIs externas | Thinking + tools = conflicto vLLM |
| Routing/clasificación | No necesita razonamiento profundo |
| Notificaciones Telegram | Pura ejecución |
| Guardar/leer archivos del caso | Operación mecánica |
| `dm-qualifier` en conversación con lead | Respuesta rápida, context ya está |

---

## Implementación: Two-Phase Pattern

Para tareas que necesitan AMBAS cosas (pensar Y luego actuar), usar este patrón en dos llamadas:

```
┌─────────────────────────────────────────────────────────┐
│ FASE 1 — RAZONAMIENTO (thinking=true, tools=none)       │
│                                                         │
│ Prompt: "Analiza la deuda de CTR-001 y determina        │
│ qué estrategia recomiendas. Razona internamente.        │
│ Output: JSON con tu decisión y justificación."          │
│                                                         │
│ extra_body: {                                           │
│   "chat_template_kwargs": {"enable_thinking": true}     │
│ }                                                       │
│ tools: []  ← VACÍO, sin herramientas                   │
└─────────────────────────────────────────────────────────┘
                        ↓
         { decision: "estrategia-3", rationale: "..." }
                        ↓
┌─────────────────────────────────────────────────────────┐
│ FASE 2 — EJECUCIÓN (thinking=false, tools=activas)     │
│                                                         │
│ Prompt: "Con base en esta decisión: [decisión fase 1], │
│ ejecuta: escribe el informe en el archivo del caso,    │
│ prepara el mensaje para Mariano."                      │
│                                                         │
│ extra_body: {                                           │
│   "chat_template_kwargs": {"enable_thinking": false}    │
│ }                                                       │
│ tools: [filesystem, telegram]  ← tools activas         │
└─────────────────────────────────────────────────────────┘
```

---

## Cómo lo implementa el orquestador

El `solutions-director` y el `analysis-director` usan two-phase cuando el caso es categoría A o tiene subasta activa:

```python
# Fase 1: delegación pura de razonamiento (sin tools)
sintesis = delegate_task(
    prompt=f"""
    Analiza el caso {caso_id} con los datos en:
    {analisis_path}
    
    Evalúa las 8 estrategias de Centrum contra este caso específico.
    Razona con profundidad. Devuelve JSON:
    {{
      "estrategia_principal": N,
      "estrategia_alternativa": N,
      "razon_principal": "...",
      "riesgos": ["..."],
      "datos_faltantes": ["..."]
    }}
    """,
    toolsets=[],                 # sin tools — puro razonamiento
    extra_body={"chat_template_kwargs": {"enable_thinking": True}}
)

# Fase 2: ejecución con tools
delegate_task(
    prompt=f"""
    Ejecuta con base en esta síntesis: {sintesis}
    
    1. Escribe el informe en {caso_path}/informe-estrategias.md
    2. Prepara el mensaje Telegram para Mariano
    """,
    toolsets=["filesystem", "telegram"]
    # thinking=False por defecto
)
```

---

## Modelos por fase

| Fase | Modelo recomendado | Puerto |
|------|-------------------|--------|
| Razonamiento puro (casos A, subasta activa) | Max 31B | 8003 |
| Razonamiento estándar (categorías B-C) | Pro 26B | 8002 |
| Ejecución (escritura archivos, Telegram, APIs) | Pro 26B o Nano | 8002/8001 |

El coste de una sesión de thinking en 31B es ~3x mayor. Solo activarlo en casos que lo justifican (categoría A, subastas, demandas judiciales).

---

## Señal de que thinking mode ayudó

Si en el informe de estrategias aparecen matices como:
- "El banco X históricamente acepta quitas en casos con IRPH, pero no con cláusula suelo activa"
- "Aunque la estrategia 3 parece mejor, el perfil psicológico del cliente (miedo a perder la casa vs. miedo a la deuda) indica que estrategia 8 generará más confianza inicial"

→ El thinking mode funcionó. Guardar ese patrón en memoria/PLUR.
