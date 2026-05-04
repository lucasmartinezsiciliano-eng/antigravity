---
tags: [openclaw, arquitectura, agentes]
status: activo
updated: 2026-04-08
related:
  - "[[Agentes — Estado Actual]]"
---

# Arquitectura General de Agentes

> Estructura jerárquica del sistema OpenClaw para todos los proyectos de Antigravity.

---

## Jerarquía principal

```
Lucas
  └── Iris (estrategia, coordinación global)
        ├── Nova   (dirección creativa)
        │     ├── Kaz    (captions)
        │     ├── Pixel  (imágenes)
        │     └── Reel   (vídeo)
        ├── Trend  (monitorización mercado)
        ├── Rival  (análisis competencia)
        ├── Scout  (outreach / marcas)
        ├── Pulse  (analytics)
        ├── DM     (comentarios / comunidad)
        └── Flow   (distribución / n8n)
```

---

## Proyecto Firmax (broker hipotecario)

Arquitectura original definida para Firmax:

| Agente | Rol |
|--------|-----|
| **Jarvis** | Director General. Lucas solo habla con Jarvis |
| **Rex** | Broker. Pipeline leads: captación → clasificación → seguimiento → cierre |
| **Nova** | Marketing. Contenido Instagram para Firmax |
| **Flow** | Técnico n8n. Crea y mantiene workflows de Rex y Nova |

Nova (Firmax) usa: Higgsfield + Kling + Chatterbox TTS + CapCut
Estrategia de contenido: TOFU / MOFU / BOFU

---

## Proyecto xi.parfum / vi.parfumm (perfumes AI)

Ver [[../Perfumes/Estrategia de Canales]] para el sistema completo.

El equipo de agentes para perfumes es el mismo stack (iris, nova, kaz, pixel, reel, trend, rival, scout, pulse, dm, flow) gestionando dos identidades separadas por canal.
