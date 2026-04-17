# Contexto del negocio — Antigravity

## 🛒 E-commerce — Lucas

- **Plataforma**: TikTok Shop + Shopify
- **Producto**: e-commerce con proveedor chino (DDP)
- **Contenido**: vídeos automatizados con IA — ElevenLabs (voz) + Creatomate (render)
- **Operaciones**: procesamiento de pedidos, contabilidad básica, alertas de stock
- **Flujos típicos**: `Ecom - Process New Order`, `Ecom - Generate TikTok Video`

## 🏠 Broker Hipotecario — Padre (Mediterrane Firmax SL)

- **Actividad**: intermediación hipotecaria
- **Pipeline**: lead → análisis → banco → firmado
- **Captación**: formularios web, anuncios Meta/Google
- **Seguimiento**: email + WhatsApp automático
- **Datos**: personales y financieros → cumplimiento RGPD obligatorio
- **Objetivo**: cero leads perdidos, mínimo trabajo administrativo
- **Flujos típicos**: `Broker - New Lead Notification`, `Broker - Follow Up Pipeline`
- **Colaboración Lucenathor** (Adrián Lucena, abril-julio 2026): marca personal + captación leads, funnel, viralización RRSS. Referencia a replicar y sistematizar.

## 🔴 Captación de Deudores Hipotecarios — Padre (nuevo proyecto)

- **Actividad**: llegar a deudores hipotecarios antes de que el proceso llegue a juicio
- **Propuesta de valor**: salida negociada (venta, renegociación, dación en pago) antes de perder la vivienda
- **Estado**: idea definida, canal de captación y posicionamiento por definir
- **Reto principal**: captar a personas que aún no saben que necesitan ayuda
- **Contexto detallado**: `docs/padre_broker.md`

## Objetivo global

Los tres negocios funcionan con mínima intervención manual. Infraestructura n8n compartida, flujos separados y etiquetados por área (`ecom/`, `broker/`, `deudores/`).
