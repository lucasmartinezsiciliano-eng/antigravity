---
tags: [feedback, openclaw, config, reglas]
type: feedback
updated: 2026-04-08
related:
  - "[[No Reconfigurar Agentes]]"
---

# OpenClaw — Reglas de Config

---

## Regla: Verificar GitHub antes de tocar openclaw.json

Antes de enviar cualquier comando o modificar `openclaw.json` (gateway, plugins, tools, hooks), buscar primero en:

- `github.com/openclaw/openclaw`
- `docs.openclaw.ai`

**Por qué:** Los comandos de config mal formateados causan crashes del gateway (Zod schema validation failure, exit code 1). Ocurrió al añadir `tools.web.search` con formato incorrecto.

**Cómo aplicar:** Siempre hacer WebSearch en GitHub antes de modificar `openclaw.json` o ejecutar comandos openclaw que toquen configuración.

---

## Regla: URL de Ollama sin `/v1`

```
✅ http://localhost:11434
❌ http://localhost:11434/v1
```

Con `/v1` al final, el function calling falla silenciosamente sin error visible.
