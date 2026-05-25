# case-kanban — Gestión de casos como pipeline Kanban durable

> Skill exclusiva del orquestador `centrum`.
> Resuelve el problema de casos que duran días/semanas y no pueden vivir en una sesión de chat.

---

## Por qué Kanban y no solo `delegate_task`

| | `delegate_task` | Kanban |
|---|---|---|
| Persistencia | En memoria, muere con la sesión | SQLite en `~/.hermes/kanban.db`, sobrevive reinicios |
| Humano en loop | No | Sí: Mariano bloquea/desbloquea con `/aprobar CTR-NNN` |
| Audit trail | Se pierde al comprimir | Filas permanentes, historial completo |
| Crash recovery | Fallo = fallo | Dispatcher re-lanza en 60 segundos |
| Casos multi-día | No viable | Diseñado para esto |

**Regla**: `delegate_task` para sub-tareas que resuelven en una sesión (< 30 min). Kanban para el pipeline completo de un caso.

---

## Board principal: `centrum-cases`

```bash
hermes kanban init
hermes kanban boards create centrum-cases --name "Pipeline de Casos" --icon 🏠 --switch
```

### Columnas (estados)

```
triage → todo → ready → running → blocked → done → archived
```

Mapeadas a las fases de Centrum:
- `triage` = lead nuevo sin calificar
- `todo` = lead calificado, esperando llamada
- `ready` = documentación completa, análisis pendiente
- `running` = análisis en curso (agente trabajando)
- `blocked` = esperando Mariano (aprobación, decisión, datos)
- `done` = estrategia enviada, caso cerrado
- `archived` = caso histórico

---

## Crear un caso nuevo

```python
# Mariano manda lead por Telegram → centrum crea el card
kanban_create(
    title="CTR-20260525-001 · García Pérez · deuda 145K · Tarragona",
    assignee="centrum",
    body="""
    Cliente: María García Pérez
    Deuda estimada: 145.000€
    Vivienda: Tarragona capital, 3 hab
    Situación: 6 meses sin pagar, carta del banco recibida
    Urgencia: MEDIA — sin demanda activa
    Fuente: formulario web
    """,
    metadata={"caso_id": "CTR-20260525-001", "categoria": "pendiente", "urgencia": "MEDIA"}
)
```

---

## Flujo estándar de un caso (DAG de dependencias)

```python
# El orquestador descompone el caso en cards con dependencias:

t_intake = kanban_create(
    title="[CTR-001] Intake — ficha completa + datos faltantes",
    assignee="centrum",          # director intake
    parents=[]                   # arranca inmediatamente
)

t_analysis = kanban_create(
    title="[CTR-001] Análisis — deuda + legal + banco + cláusulas",
    assignee="centrum",          # director analysis
    parents=[t_intake]           # espera a que intake esté done
)

t_solutions = kanban_create(
    title="[CTR-001] Estrategias — matching 8 estrategias + informe",
    assignee="centrum",          # director solutions
    parents=[t_analysis]         # espera a analysis
)

t_approval = kanban_create(
    title="[CTR-001] APROBACIÓN MARIANO — revisar informe de opciones",
    assignee="centrum",
    parents=[t_solutions]
)
# → este card se pone en blocked automáticamente, Mariano lo desbloquea via Telegram

t_comms = kanban_create(
    title="[CTR-001] Comunicaciones — preparar email/WhatsApp cliente",
    assignee="centrum",
    parents=[t_approval]         # solo se activa tras aprobación Mariano
)
```

El dispatcher promueve automáticamente cada card cuando sus padres alcanzan `done`.

---

## Cómo un worker interactúa con su card

```python
# Al empezar cualquier tarea, SIEMPRE:
context = kanban_show()          # lee título, body, intentos previos, comentarios
caso_id = context.metadata["caso_id"]

# ... hacer el trabajo ...

# Operaciones largas (> 5 min):
kanban_heartbeat()               # señal de vida, evita que el dispatcher lo mate

# Al terminar:
kanban_complete(
    summary="Ficha CTR-001 completa. 2 datos faltantes: tasación y escritura.",
    metadata={
        "caso_id": "CTR-001",
        "ficha_path": "~/.hermes/profiles/centrum/cases/CTR-001/ficha.json",
        "datos_faltantes": ["tasacion", "escritura"],
        "categoria_preliminar": "B"
    },
    artifacts=["~/.hermes/profiles/centrum/cases/CTR-001/ficha.json"]
)

# Si necesita a Mariano:
kanban_block("Esperando documentos: tasación y escritura de la vivienda")
# Mariano ve el bloqueo en Telegram → envía docs → Lucas desbloquea: kanban_unblock(t_id)
```

---

## Comandos Telegram que Mariano puede usar

| Comando | Acción |
|---------|--------|
| `/pipeline` | Ver todos los casos activos con su estado |
| `/caso CTR-001` | Detalle del caso, últimas actualizaciones |
| `/aprobar CTR-001` | Desbloquea el card de aprobación (activa comms) |
| `/urgente CTR-001` | Mueve el caso a máxima prioridad |

El orquestador intercepta estos comandos del gateway Telegram y ejecuta los kanban_* correspondientes.

---

## Casos con subasta activa — prioridad absoluta

```python
# Si intake-director detecta subasta activa:
kanban_comment(
    "🚨 SUBASTA ACTIVA — fecha: 2026-06-15. Caso prioritario absoluto."
)
# El orquestador añade tag urgencia=CRITICA y mueve todas las cards a ready
# sin esperar dependencias
```

---

## Circuit breaker — fallos de sub-agentes

Si un card falla 2 veces seguidas (`failure_limit: 2` en config.yaml):
1. El dispatcher lo pone en `blocked` automáticamente
2. `centrum` recibe notificación y avisa a Lucas por Telegram
3. Lucas investiga el log: `hermes kanban runs <task_id>`
4. Tras arreglar el problema: `hermes kanban unblock <task_id>`

---

## Estado del board en Telegram — formato

```
📋 PIPELINE CENTRUM — 2026-05-25
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔵 ANÁLISIS (2):
  CTR-001 · García · ejecución hipotecaria
  CTR-004 · Martínez · 6 meses impago

🟡 BLOQUEADO / MARIANO (1):
  CTR-002 · López · informe pendiente aprobación

🟢 ACTIVOS TOTAL: 5 | CERRADOS HOY: 1
```
