---
tags: [openclaw, agentes, hardware, modelos]
status: pendiente
updated: 2026-04-08
related:
  - "[[Agentes — Estado Actual]]"
  - "[[Ecosistema GitHub]]"
---

# Agentes — Upgrade Plan

> Plan completo de mejoras para OpenClaw. Acciones técnicas + hardware + modelos por agente.

---

## Acciones técnicas pendientes

### 1. Bug crítico Ollama

Verificar URL en `openclaw.json`. Debe ser:
```
http://localhost:11434
```
**SIN** `/v1` al final — con `/v1` el function calling falla silenciosamente.

### 2. Actualizar OpenClaw

```bash
openclaw update
openclaw doctor --fix
```

### 3. Activar `/dreaming`

Consolida memoria sola cada noche a las 2AM.

```json
"plugins": {
  "entries": {
    "memory-core": {
      "config": {
        "dreaming": {
          "enabled": true,
          "timezone": "Europe/Madrid",
          "frequency": "0 2 * * *"
        }
      }
    }
  }
}
```

### 4. Activar agentToAgent

```json
"tools": {
  "agentToAgent": {
    "enabled": true,
    "allow": [
      {"from": "*", "to": "iris"},
      {"from": "iris", "to": "*"},
      {"from": "kaz", "to": "pixel"},
      {"from": "pixel", "to": "reel"},
      {"from": "reel", "to": "nova"},
      {"from": "nova", "to": "iris"},
      {"from": "trend", "to": "iris"},
      {"from": "rival", "to": "iris"},
      {"from": "scout", "to": "iris"}
    ]
  }
}
```

### 5. Instalar freepik-mcp

Repo: `MCERQUA/freepik-mcp` — permite a pixel/reel llamar Freepik directamente sin n8n.

### 6. Crear contexto compartido

Archivos que todos los agentes cargan al arrancar:
- `THESIS.md` — norte estratégico de xi.parfum y vi.parfumm
- `SIGNALS.md` — trend/rival escriben señales; kaz/reel/pixel leen antes de generar
- `FEEDBACK-LOG.md` — cuando Lucas corrige algo, dm lo anota y todos aprenden

### 7. Monitorización

```bash
openclaw monitor
```

Dashboard: [tugcantopaloglu/openclaw-dashboard](https://github.com/tugcantopaloglu/openclaw-dashboard)

---

## Stack de modelos definitivo

| Agente | Modelo | Razón |
|--------|--------|-------|
| iris | `claude-sonnet-4-6` | Estrategia |
| nova | `claude-sonnet-4-6` | Dirección creativa |
| kaz | `ollama/qwen3.5:27b` | Captions + tool use fiable |
| pixel | `ollama/qwen3.5:27b` | Imágenes Freepik MCP |
| reel | `ollama/qwen3.5:27b` | Vídeo Freepik MCP |
| trend | `ollama/gemma4:e4b` | Monitorización |
| rival | `ollama/gemma4:e4b` | Análisis competencia |
| scout | `ollama/gemma4:e4b` | Outreach |
| pulse | `ollama/gemma4:e4b` | Analytics |
| dm | `ollama/gemma4:e4b` | Comentarios |
| flow | `ollama/gemma4:e4b` | Distribución |

> [!tip] En Qwen3.5 añadir `reasoning: false` en config — evita chain-of-thought innecesario

**Por qué Qwen3.5 (no Haiku) para kaz/pixel/reel:** 72.2% BFCL-V4 (tool calling benchmark), rival de Claude Haiku, 100% gratis local.
**Por qué no Gemma para pixel/reel:** E4B falla en multi-tool chains complejas (bug confirmado GitHub).

---

## Novedades OpenClaw 2026.4.5

| Feature | Descripción |
|---------|-------------|
| `/dreaming` | Memoria con fases light/REM/deep. Escribe en `DREAMS.md` y `MEMORY.md` automáticamente |
| Video nativo | Runway, xAI, Wan — **NO Kling** (seguir con Freepik para Kling) |
| Topic routing | Múltiples agentes en mismo grupo Telegram sin interferencia |
| `/tasks` | Tablero de tareas en background dentro del chat |

---

## Hardware PC de casa

**Specs actuales (CPU-Z confirmado):**
- CPU: Intel Core i5-8400 (Coffee Lake, 6 núcleos)
- RAM: 8GB DDR4 canal simple — **cuello de botella principal**
- Placa: MSI B360M PRO-VH — 2 slots RAM, aguanta 32GB DDR4
- GPU: desconocida (pendiente ver pestaña Graphics)

### Plan de compra (máx 200€)

**RAM — 80€ en PCComponentes:**
- Kingston FURY Beast 8GB DDR4 3200MHz CL16 — 79.95€
- Enchufar en segundo slot = 16GB dual channel (+30% rendimiento)

**GPU — ~100-120€ en Wallapop/eBay:**
- Buscar: GTX 1070 (8GB) o GTX 1080 (8GB)
- **NVIDIA obligatorio** (CUDA). AMD no funciona bien con Ollama en Windows (ROCm limitado)
- NO comprar en PCComponentes — 2-3x más caro que segunda mano

**Con 200€ conseguimos:**
- Gemma 4 E4B: trend, rival, scout, pulse, dm, flow ✅
- Gemma 4 26B MoE: posible si GPU tiene 12GB+ ✅
- Qwen3.5 27B: necesita más VRAM, pendiente upgrade futuro

**Futuro (cuando haya presupuesto):**
- RTX 3090 24GB usada (~600-800€): Qwen3.5 27B Q4 + Gemma 26B MoE simultáneo
- RTX 5060 Ti 16GB nueva (~430-480€): sweet spot 2026
