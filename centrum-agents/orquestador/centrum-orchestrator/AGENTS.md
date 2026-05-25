# AGENTS.md — Centrum Orchestrator
# Auto-inyectado por Hermes en cada sesión de este perfil.
# Máximo 20.000 caracteres. Mantener conciso — cada caracter consume tokens.

## Sistema
- Framework: Hermes Agent (NousResearch)
- Hardware: DGX Spark (GB10, 128GB unified memory)
- Modelos: Gemma 4 local vía vLLM (sin OpenRouter, €0 en inferencia)
- Endpoint Max (31B): http://localhost:8003/v1
- Endpoint Pro (26B): http://localhost:8002/v1

## Rutas de trabajo
- Casos activos: ~/.hermes/profiles/centrum/cases/CTR-<id>/
- Workspace temporal: ~/.hermes/profiles/centrum/workspace/
- Memoria: ~/.hermes/profiles/centrum/memories/

## Convenciones de casos
- ID formato: CTR-YYYYMMDD-NNN (ej: CTR-20260525-001)
- Cada caso es un directorio aislado — nunca mezclar datos entre casos
- Archivos del caso: ficha.json, historial.md, documentos/, analisis/

## Delegación
- max_spawn_depth: 2 (yo → director → especialista)
- max_concurrent_children: 3
- Pasar siempre contexto explícito al sub-agente: caso_id, rutas, objetivo concreto
- Sub-agentes no ven esta conversación — siempre incluir el contexto mínimo necesario

## Aprobación Mariano (obligatorio antes de ejecutar)
- Envío de email o WhatsApp a cliente
- Informe de opciones (estrategias) al cliente
- Cambio de categoría de caso (A→B, etc.)
- Plazos legales o de subasta comunicados al cliente
- Cierre de caso

## Escalación técnica → Lucas (no Mariano)
- Fallo de sub-agente 2 veces seguidas
- vLLM no responde
- Error de filesystem o permisos

## Formato output Telegram
```
🏠 CTR-<id> · <cliente> · CAT-<A/B/C/D/E>
Estado: <fase>
Acción ahora: <una línea>
Pendiente Mariano: <sí + qué / no>
Urgencia: <ALTA/MEDIA/BAJA>
Próximo hito: <fecha + evento>
```
