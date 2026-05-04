---
tags: [openclaw, github, referencia]
status: referencia
updated: 2026-04-08
related:
  - "[[Agentes — Estado Actual]]"
  - "[[Agentes — Upgrade Plan]]"
---

# Ecosistema OpenClaw — GitHub

> Mapa de repos clave y patrones del ecosistema que faltan en el proyecto actual.

---

## Repos clave

| Repo | Para qué |
|------|----------|
| `mergisi/awesome-openclaw-agents` | 199 SOUL.md de producción en 19 categorías |
| `MCERQUA/freepik-mcp` | MCP server para Freepik (Mystic, stock, status) |
| `tugcantopaloglu/openclaw-dashboard` | Dashboard live: feed, coste, memory browser, TOTP |
| `freddy-schuetz/n8n-claw` | OpenClaw reconstruido en n8n (solo referencia) |
| `shenhao-stu/openclaw-agents` | Config real de agentToAgent y bindings Telegram |
| `loongclaw-ai/loongclaw` | Versión didáctica para aprender arquitectura |

---

## Gap analysis — Proyecto vs Ecosistema

| Característica | Ecosistema | Proyecto actual |
|---|:---:|:---:|
| SOUL.md específico por agente | ✅ | ❌ Todos copia de Iris |
| agentToAgent configurado | ✅ | ❌ Solo en papel |
| /dreaming activo | ✅ (v2026.4.5) | ❌ Pendiente |
| THESIS.md + SIGNALS.md | ✅ | ❌ No existe |
| Freepik via MCP | ✅ | ❌ Sin conectar |
| Modelos diferenciados | ✅ | ❌ Todos igual |
| 3 variantes obligatorias en output | ✅ | ❌ No documentado |

---

## Estructura SOUL.md del ecosistema (patrón exacto)

```markdown
## Identity
name: "[nombre]" / role: "[rol]" / version: "1.0"

## Personality
[2-4 frases densas, segunda persona]

## Capabilities
- [Verbo + objeto]

## Rules
### Do:
### Don't:

## Integrations
- [tool]: [para qué]

## Example Interactions
User: [ejemplo]
Agent: [respuesta con formato EXACTO]
```

### Reglas clave de los mejores SOUL.md

- Siempre **3 variantes de output** (nunca una sola opción)
- Do/Don't explícitos — las reglas negativas importan igual que las positivas
- Example Interactions con formato de output exacto — el agente aprende el patrón
- Integraciones declaradas = el agente las usa proactivamente sin que se las pidas

---

## Archivos de contexto compartido

Todos los agentes los cargan al arrancar via `bootstrap-extra-files`:

| Archivo | Quién escribe | Quién lee |
|---------|--------------|-----------|
| `THESIS.md` | Lucas / Iris | Todos |
| `SIGNALS.md` | trend, rival | kaz, reel, pixel antes de generar |
| `FEEDBACK-LOG.md` | dm (cuando Lucas corrige) | Todos |

---

## Hooks importantes en openclaw.json

```json
"hooks": {
  "boot-md": true,           // carga SOUL.md, AGENTS.md, USER.md al arrancar
  "bootstrap-extra-files": true,  // carga THESIS.md, SIGNALS.md al arrancar
  "session-memory": true     // persiste MEMORY.md entre sesiones
}
```

---

## BOOTSTRAP.md pattern

Para configurar agentes sin hacer `agents add`:
1. Depositar `BOOTSTRAP.md` en el workspace del agente
2. El agente se auto-configura en primer arranque
3. El archivo se borra automáticamente tras la configuración
