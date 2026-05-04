---
tags: [openclaw, agentes, infraestructura]
status: en-progreso
updated: 2026-04-08
related:
  - "[[Agentes — Upgrade Plan]]"
  - "[[Ecosistema GitHub]]"
---

# Agentes — Estado Actual

> Última verificación: 2026-04-06. Los 11 agentes tienen estructura de carpetas creada. **Pendiente confirmar en panel tras restart del gateway.**

---

## Estructura de cada agente en disco

```
/root/.openclaw/agents/[nombre]/
├── agent/         ← auth profiles + model config (2 JSON)
└── sessions/      ← historial de sesiones
```

### Cómo se crearon (método correcto)

```bash
for agent in nova pixel reel kaz trend rival scout pulse dm flow; do
  mkdir -p /root/.openclaw/agents/$agent/agent
  mkdir -p /root/.openclaw/agents/$agent/sessions
  cp /root/.openclaw/agents/iris/agent/* /root/.openclaw/agents/$agent/agent/
done
```

> [!warning] NO usar `openclaw agents add` si el directorio ya existe
> Ver [[../Feedback/No Reconfigurar Agentes]]

---

## Credenciales configuradas en openclaw.json

| Variable | Estado |
|----------|--------|
| `OPENROUTER_API_KEY` | ✅ |
| `GROQ_API_KEY` | ✅ |
| `OLLAMA_HOST` | ✅ |
| `TAVILY_API_KEY` | ✅ |
| `FREEPIK_API_KEY` | ✅ |

---

## Archivos IDENTITY.md

`/root/.openclaw/workspace-[agente]/IDENTITY.md` — los 11 archivos creados desde `JARVIS_SETUP.txt` ✅

---

## Imágenes de avatar

| Canal | Ruta | Imágenes |
|-------|------|----------|
| vi (mujer) | `/root/.openclaw/workspace-pixel/avatar-references/vi/` | 148 ✅ |
| xi (hombre) | `/root/.openclaw/workspace-pixel/avatar-references/xi/` | 16 ✅ |

---

## Ciclo de drops

- **xi.parfum**: drop el día **11** de cada mes
- **vi.parfumm**: drop el día **6** de cada mes

---

## Pendientes para producción

- [ ] Confirmar que los 11 agentes aparecen en el panel
- [ ] Verificar `openclaw tools list` — sin HTTP tool no pueden llamar a Freepik
- [ ] Conectar webhooks n8n
- [ ] Configurar embedding provider para memoria
