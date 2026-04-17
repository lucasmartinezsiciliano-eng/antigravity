# CLAUDE.md — Antigravity

## Stack
- **Motor**: n8n self-hosted (Docker, Oracle Cloud)
- **Integraciones**: Google Sheets, Telegram, Shopify, Gmail, Notion, ElevenLabs, Creatomate
- **Credenciales**: siempre en n8n, nunca hardcodeadas

## Reglas críticas
**NUNCA sin confirmación**: modificar/eliminar workflows activos, cambiar credenciales, desactivar producción, tocar webhooks activos.
**Libre**: crear flujos nuevos, añadir nodos a borradores, documentar, proponer mejoras.

## Naming
- Nodos: `[Acción] [Objeto]` → `Get Orders Shopify`, `Send Telegram Alert`
- Flujos: `[Área] - [Función]` → `Ecom - Process New Order`, `Broker - New Lead Notification`

## Patrones n8n
- Trigger claro siempre (Webhook / Schedule / Sub-workflow)
- Set node para limpiar datos antes de cada paso
- Error handler en todo flujo productivo → notifica por Telegram
- `Get Row` antes de `Update Row` en Sheets
- Code nodes cortos; lógica compleja → subworkflow
- `continueOnFail: true` solo si el error es esperado

## Telegram (formato alertas)
```
✅ [Orders] Nuevo pedido #1234 — €49.99
❌ [Content] Error al generar vídeo — revisar ElevenLabs
```

## Negocios
- 🛒 **Ecom** (Lucas): TikTok Shop + Shopify, vídeos IA, proveedor chino DDP
- 🏠 **Broker** (padre): leads hipotecarios → análisis → banco → firmado. Datos RGPD sensibles.
- 🔴 **Deudores** (padre): nuevo proyecto — captación de deudores hipotecarios antes del juicio

## Usuarios del proyecto

- **Lucas** (hijo): técnico, monta los sistemas, lleva el ecom y la infraestructura
- **Padre**: broker hipotecario con 20+ años de experiencia, no técnico. Usa Claude para pensar, plasmar ideas y orientar sus proyectos. Sus conversaciones son la fuente de datos para construir los agentes de OpenClaw.

## Dudas → docs/
- Contexto detallado del negocio: `docs/negocio.md`
- Plan Lucas: `docs/plan_lucas.md`
- Contexto broker + deudores (para el padre): `docs/padre_broker.md`

## Ante dudas
Pregunta → propón → espera confirmación → aplica. Si tocas un workflow activo, haz backup primero: `[nombre] - BACKUP DD/MM`.
