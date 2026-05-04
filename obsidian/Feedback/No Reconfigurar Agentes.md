---
tags: [feedback, openclaw, agentes, reglas]
type: feedback
updated: 2026-04-08
related:
  - "[[OpenClaw — Reglas de Config]]"
---

# No Reconfigurar Agentes Existentes

---

## Regla

**NUNCA** ejecutar `openclaw agents add` en agentes que ya tienen workspace y configuración, aunque no aparezcan en el panel.

**Por qué:** Causa que OpenClaw pregunte proveedor de modelo, auth, etc., rehaciendo configuración que ya existe.

---

## Flujo correcto

```bash
# 1. Verificar primero
ls /root/.openclaw/agents/

# 2. Si el directorio existe → NO ejecutar agents add
# 3. Buscar otro diagnóstico para el problema del panel
```

Si el agente ya tiene carpeta en `/root/.openclaw/agents/[nombre]/`, está registrado. El problema del panel es independiente del registro.
