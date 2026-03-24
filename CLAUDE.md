# CLAUDE.md — Proyecto Antigravity

## Descripción del proyecto

**Antigravity** es el sistema central de automatización de la empresa, construido sobre **n8n (self-hosted)**. Contiene flujos de trabajo que gestionan operaciones de e-commerce, procesamiento de pedidos, notificaciones, generación de contenido y tareas recurrentes del negocio.

---

## Stack tecnológico

- **Motor principal**: n8n (self-hosted, Docker)
- **Integraciones habituales**: Google Sheets, Telegram, Shopify, Gmail, Notion, ElevenLabs, Creatomate, APIs externas (REST/JSON)
- **Credenciales**: gestionadas dentro de n8n (nunca hardcodear en el código)
- **Infraestructura**: Oracle Cloud / Docker Swarm

---

## Reglas generales

### ⚠️ NUNCA hacer sin confirmación explícita
- Modificar o eliminar flujos de trabajo existentes y activos
- Cambiar credenciales o variables de entorno
- Desactivar un workflow en producción
- Borrar nodos de un flujo ya funcionando
- Modificar webhooks activos (pueden romper integraciones en vivo)

### ✅ Puedes hacer libremente
- Crear flujos nuevos desde cero
- Añadir nodos a flujos que estén en modo borrador / inactivos
- Crear subworkflows reutilizables
- Documentar flujos existentes
- Proponer mejoras sin aplicarlas directamente

---

## Cómo crear flujos nuevos

1. **Siempre empezar con un nodo trigger claro**: Webhook, Schedule, o llamada desde otro flujo
2. **Naming convention para nodos**: `[Acción] [Objeto]` → ej. `Get Orders Shopify`, `Send Telegram Alert`, `Update Sheet Row`
3. **Naming convention para flujos**: `[Área] - [Función]` → ej. `Ecom - Process New Order`, `Ecom - Generate TikTok Video`, `Broker - New Lead Notification`, `Broker - Follow Up Pipeline`
4. **Añadir siempre un nodo de manejo de errores** al final o mediante "Error Workflow" global
5. **Usar Set nodes** para limpiar y estructurar datos antes de pasarlos al siguiente paso
6. **Nunca mezclar lógica de negocio compleja dentro de un Code node** — si es largo, dividir en subworkflows

---

## Estructura de carpetas (si se usan archivos externos)

```
antigravity/
├── workflows/
│   ├── ecom/           # Flujos de TikTok Shop / Shopify
│   ├── broker/         # Flujos del broker hipotecario
│   └── shared/         # Subworkflows reutilizables por ambos
├── scripts/            # Scripts auxiliares (Node.js / Python)
├── docs/               # Documentación de cada flujo
└── CLAUDE.md           # Este archivo
```

---

## Patrones preferidos en n8n

### Notificaciones
- Usar **Telegram** para alertas operativas en tiempo real
- Formato del mensaje: siempre incluir emoji de estado, nombre del flujo y dato relevante
  ```
  ✅ [Orders] Nuevo pedido #1234 — €49.99
  ❌ [Content] Error al generar vídeo — revisar ElevenLabs
  ```

### Datos y hojas de cálculo
- **Google Sheets** es la fuente de verdad para catálogos, pedidos y registros
- Siempre hacer un `Get Row` antes de un `Update Row` para no sobreescribir datos no relacionados

### Manejo de errores
- Todo flujo productivo debe tener un handler de errores que notifique por Telegram
- Usar `continueOnFail: true` con criterio — solo cuando el error es esperado y manejable

### Credenciales
- Nunca escribir API keys, tokens ni contraseñas en nodos `Code` o `Set`
- Usar siempre las credenciales almacenadas en n8n

---

## Contexto del negocio

Antigravity da soporte a **dos líneas de negocio** distintas:

### 🛒 E-commerce (Lucas)
- **Plataforma de venta**: TikTok Shop + Shopify
- **Producto principal**: e-commerce con proveedor chino (DDP)
- **Contenido**: generación automatizada de vídeos con IA (ElevenLabs + Creatomate)
- **Operaciones**: procesamiento de pedidos, contabilidad básica, alertas de stock

### 🏠 Broker Hipotecario (padre)
- **Actividad**: intermediación hipotecaria — captación de leads, seguimiento de clientes, gestión de operaciones con bancos
- **Flujos típicos**: captura de leads (formularios / anuncios), notificaciones de nuevos contactos, seguimiento automático por email o WhatsApp, pipeline de operaciones (estado: lead → análisis → banco → firmado)
- **Datos sensibles**: los flujos de esta línea manejan datos personales y financieros de clientes — aplicar especial cuidado con privacidad y RGPD
- **Objetivo**: automatizar el seguimiento para que ningún lead se pierda y reducir el trabajo administrativo del broker

### Objetivo global
Que ambos negocios funcionen con el mínimo trabajo manual, compartiendo infraestructura n8n pero con flujos bien separados y etiquetados por área.

---

## Qué hacer cuando no estés seguro

1. **Pregunta antes de actuar** si el cambio afecta a un flujo activo
2. **Crea una copia** del workflow antes de modificarlo (`[nombre] - BACKUP DD/MM`)
3. **Propón la solución** y espera confirmación antes de aplicarla en producción
4. Si encuentras un flujo sin documentación, **documentarlo** antes de tocarlo

---

## Objetivo final

Que el negocio funcione solo. Cada flujo nuevo debe reducir intervención manual, ser robusto ante errores y estar documentado para que cualquiera (o Claude) pueda entenderlo sin contexto adicional.
