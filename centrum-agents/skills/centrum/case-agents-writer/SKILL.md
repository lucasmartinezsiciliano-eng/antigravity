# case-agents-writer — AGENTS.md automático por caso

> Skill para el sub-rol `ficha-builder` (dentro de `intake-director`).
> Genera contexto auto-inyectable para cualquier sub-agente que trabaje en ese caso.

---

## El problema que resuelve

Los sub-agentes son ciegos: "subagents know absolutely nothing about your conversation" (doc oficial Hermes).

El patrón habitual es pasar el contexto en el prompt de cada delegación:
```python
delegate_task(prompt=f"caso_id={caso_id}, cliente={nombre}, deuda={deuda}...")
```

Esto es frágil: si el orquestador olvida un dato, el sub-agente trabaja en el vacío.

**La solución**: cuando `ficha-builder` completa la ficha del caso, genera automáticamente `cases/CTR-NNN/AGENTS.md`. Hermes lo inyecta en cualquier sub-agente que navegue a ese directorio.

---

## Cuándo crear/actualizar el AGENTS.md del caso

| Evento | Acción |
|--------|--------|
| `ficha-builder` completa la ficha inicial | Crear `cases/CTR-NNN/AGENTS.md` |
| `intake-director` detecta dato faltante importante | Actualizar la sección "Datos pendientes" |
| `analysis-director` completa el análisis | Añadir sección "Análisis completado" con hallazgos clave |
| `solutions-director` elige estrategia | Añadir sección "Estrategia elegida" |
| Mariano aprueba la estrategia | Añadir sección "Aprobado por Mariano" con fecha |
| Cambio de categoría (A→B) | Actualizar "Categoría" y añadir motivo |
| Subasta activa detectada | Añadir banner `🚨 SUBASTA ACTIVA` con fecha |

---

## Template del AGENTS.md por caso

```markdown
# CTR-{id} · {nombre_cliente} · CAT-{A/B/C/D/E}
# Generado por ficha-builder · Actualizado: {fecha}
# Este archivo es AUTO-INYECTADO por Hermes en cualquier agente que trabaje en este caso.

## Contexto esencial
- **Caso ID**: CTR-{id}
- **Categoría**: {A/B/C/D/E} — {descripción breve del criterio}
- **Urgencia**: {ALTA/MEDIA/BAJA} — {motivo}
- **Fase actual**: {intake/analysis/solutions/awaiting_mariano/comms/followup}

## Cliente
- Nombre: {nombre}
- Teléfono: {teléfono} | Email: {email}
- Vivienda: {dirección}, {ciudad} — {m2}, {habitaciones}
- Situación: {descripción 1 línea}

## Deuda y banco
- Banco: {banco}
- Deuda estimada: {importe}€ | Cuota: {cuota}€/mes
- Meses impagados: {N} | Fecha último pago: {fecha}
- Carta de banco: {sí/no} | Demanda activa: {sí/no}
- Subasta programada: {fecha o "no"}

## Alertas críticas
{si hay subasta: 🚨 SUBASTA ACTIVA — fecha: YYYY-MM-DD — PRIORIDAD ABSOLUTA}
{si hay demanda: ⚖️ DEMANDA JUDICIAL ACTIVA — fecha notificación: YYYY-MM-DD}
{si cliente vulnerable: 💛 CLIENTE VULNERABLE — {motivo}}

## Análisis completado (si procede)
- Cláusulas detectadas: {lista o "pendiente"}
- Estrategia principal: {N. Nombre} | Alternativa: {N. Nombre}
- Confianza recomendación: {ALTA/MEDIA/BAJA}

## Aprobaciones de Mariano
- Informe opciones: {aprobado/pendiente} — {fecha}
- Comunicación cliente: {aprobada/pendiente}

## Rutas de trabajo
- Ficha: ~/.hermes/profiles/centrum/cases/CTR-{id}/ficha.json
- Documentos: ~/.hermes/profiles/centrum/cases/CTR-{id}/documentos/
- Análisis: ~/.hermes/profiles/centrum/cases/CTR-{id}/analisis/
- Comunicaciones: ~/.hermes/profiles/centrum/cases/CTR-{id}/comms/

## Reglas para este caso
- NUNCA compartir con otros casos
- Cualquier comunicación externa → aprobación Mariano primero
- Si detectas cambio de categoría → notificar a centrum inmediatamente
```

---

## Cómo genera el archivo `ficha-builder`

```python
# ficha-builder, al completar la ficha:
caso_agents_content = f"""# CTR-{caso_id} · {nombre} · CAT-{categoria}
# Generado: {fecha_hoy}

## Contexto esencial
- Caso ID: CTR-{caso_id}
...
"""

# Escribir el archivo
filesystem_write(
    path=f"~/.hermes/profiles/centrum/cases/CTR-{caso_id}/AGENTS.md",
    content=caso_agents_content
)

# Confirmar en el kanban card
kanban_comment(f"AGENTS.md creado — sub-agentes futuros tendrán contexto automático")
```

---

## Qué NO incluir en el AGENTS.md del caso

- Datos de OTROS casos — contaminación cross-case es violación RGPD
- Instrucciones de sistema de Hermes — van en el SOUL.md del perfil
- Historial completo de conversación — para eso está SessionDB
- Documentos legales completos — solo referencia a la ruta, no el contenido

Límite: máximo 8.000 caracteres (límite de subdirectory hint injection de Hermes). Si el caso crece más, mover información a los archivos .json del caso y mantener solo el resumen en AGENTS.md.
