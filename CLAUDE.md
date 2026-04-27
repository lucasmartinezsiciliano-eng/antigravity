# CLAUDE.md — Antigravity

## Stack
- **Motor**: n8n self-hosted (Docker, Oracle Cloud)
- **Integraciones**: Google Sheets, Telegram, Shopify, Gmail, Notion, Chatterbox TTS, Creatomate
- **Credenciales**: siempre en n8n, nunca hardcodeadas

## Reglas críticas
**NUNCA sin confirmación**: modificar/eliminar workflows activos, cambiar credenciales, desactivar producción, tocar webhooks activos.
**Libre**: crear flujos nuevos, añadir nodos a borradores, documentar, proponer mejoras.
**Ante dudas**: pregunta → propón → espera confirmación → aplica. Backup antes de tocar workflow activo: `[nombre] - BACKUP DD/MM`.

## Naming
- Nodos: `[Acción] [Objeto]` → `Get Orders Shopify`, `Send Telegram Alert`
- Flujos: `[Área] - [Función]` → `Ecom - Process New Order`, `Broker - New Lead Notification`

## Usuarios
- **Lucas**: técnico, lleva ecom + infraestructura
- **Padre (Mariano)**: broker hipotecario, no técnico. Sus conversaciones alimentan los agentes de OpenClaw.

## Contexto detallado → Obsidian vault

**Ruta base:** `C:/Users/Pc2025/Documents/Obsidian Vault/`

**OBLIGATORIO** antes de responder cualquier pregunta de negocio, técnica o de agentes:

1. Leer `🗺️ MOC — Antigravity.md` para orientación general
2. Leer el `index.md` de la sección relevante (Broker, OpenClaw, Infraestructura, etc.)
3. Leer las páginas específicas que necesite la pregunta

Referencias rápidas:

- Negocio global: `OpenClaw/Negocio — Contexto Global.md`
- Broker + padre: `Broker/Padre — Contexto Proyectos.md`
- Plan Lucas: `OpenClaw/Plan Lucas.md`
- Agentes OpenClaw: `OpenClaw/Agentes — Estado Actual.md`
- Centrum completo: `Broker/index.md` (sección Centrum)
- Arquitectura + n8n: `OpenClaw/Arquitectura General.md`
- Gobernanza wiki: `SCHEMA.md` · `log.md`

**Al final de cada conversación relevante:** actualizar las páginas afectadas del vault, añadir entrada en `log.md`, y hacer git commit + push del vault para sincronizar con el agente de Oracle:
```
cd "C:/Users/Pc2025/Documents/Obsidian Vault"
git add .
git commit -m "claude-code: [resumen breve]"
git push origin main
```

## Memoria — Obsidian como fuente de verdad

El vault es la memoria compartida entre Claude Code y el agente de Telegram (Oracle). Lo que se escribe aquí lo lee el agente. Lo que escribe el agente aparece aquí.

**Regla:** si algo vale la pena recordar entre conversaciones, va al vault. Si no está en el vault, no existe.
