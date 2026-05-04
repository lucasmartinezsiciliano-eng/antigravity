---
tags: [infraestructura, servidores, tailscale, oracle]
status: activo
updated: 2026-04-08
related:
  - "[[API Keys y Tokens]]"
---

# Servidores y Red

---

## Oracle Cloud — Producción

Gestionado con **Portainer** (UI web para Docker).

> [!tip] Cuando n8n u otro servicio esté caído, arrancarlo desde Portainer — no desde SSH ni comandos Docker directos.

Servicios en Docker: n8n, otros contenedores del proyecto.

---

## OpenClaw — PC de casa (Ubuntu)

| Campo | Valor |
|-------|-------|
| Hostname | DESKTOP-HV1UEJO |
| OS | Ubuntu |
| IP Tailscale | `100.119.47.93` |

---

## Red Tailscale

Tailscale conecta el PC de casa con el servidor Oracle Cloud de forma segura.

| Nodo | IP |
|------|----|
| PC de casa / OpenClaw | `100.119.47.93` |
| Oracle Cloud | Pendiente de confirmar |

---

## Hardware PC de casa

Ver [[../OpenClaw/Agentes — Upgrade Plan#Hardware PC de casa]] para specs completas y plan de compra.
