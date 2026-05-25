# Centrum — Deploy en Hermes Agent (NousResearch)

> Despliegue del sistema Centrum en Hermes Agent, sin GPU local ni DGX Spark.
> Corre en Ubuntu (PC casa, IP Tailscale `100.119.47.93`) consumiendo OpenRouter como proveedor de modelos.

---

## 1. Arquitectura

```
Nvidia DGX Spark (128 GB unified memory)
   └── vLLM (3 servidores locales)
        ├── gemma-4-E4B-it      → puerto 8001  (Nano  ~10 GB — no usado por Centrum directamente)
        ├── gemma-4-26B-A4B-it  → puerto 8002  (Pro   ~52 GB — centrum-intel + centrum-content)
        └── gemma-4-31B-it      → puerto 8003  (Max   ~62 GB — centrum orchestrator + análisis)

        ↑ endpoint OpenAI-compatible
   Hermes Agent (instalado en DGX Spark)
        ├── perfil  centrum          → orquestador principal, Mariano lo usa por Telegram
        ├── perfil  centrum-intel    → inteligencia externa, autónomo vía cron diario
        └── perfil  centrum-content  → producción contenido, batch dominical
```

**Sin n8n para orquestación de agentes.** Hermes tiene `delegation_tool` nativo y cron interno. n8n se mantiene solo para integraciones externas (Shopify, Sheets, webhooks) que ya existen.

---

## 2. Coste mensual estimado

| Componente | Coste |
|---|---|
| Hermes Agent (open-source) | €0 |
| vLLM + Gemma 4 (modelos locales en DGX Spark) | €0 |
| Twilio WhatsApp (~calls/mes) | ~€5-15 |
| **Total estimado** | **~€5-15/mes (solo Twilio)** |

---

## 3. Prerequisitos

- DGX Spark conectado y accesible (SSH o pantalla)
- Python 3.11+ y pip/pipx instalados
- Cuenta HuggingFace con acceso a modelos Gemma 4 (requiere aceptar términos en hf.co)
- Bot Telegram creado + token + chat_id de Mariano y Lucas

---

## 4. Primera vez: descargar modelos Gemma 4

```bash
pip install huggingface_hub
huggingface-cli login   # introducir token HuggingFace con acceso a Gemma

# Nano (~10 GB) — tener siempre cargado
huggingface-cli download google/gemma-4-E4B-it

# Pro (~27 GB) — tener siempre cargado
huggingface-cli download google/gemma-4-26B-A4B-it

# Max (~31 GB) — on-demand con vllm-load-max.sh
huggingface-cli download google/gemma-4-31B-it
```

Solo hay que hacer esto una vez. Los modelos quedan en `~/.cache/huggingface/`.

---

## 5. Arrancar vLLM (cada boot)

```bash
bash /root/centrum-agents/vllm-start.sh
```

Espera hasta ver los 3 puertos `[OK]`. La primera vez tarda más (carga modelos en memoria).

Para verificar:
```bash
for p in 8001 8002 8003; do
  echo "Puerto $p:"; curl -s http://localhost:$p/v1/models | python3 -c \
    "import json,sys; d=json.load(sys.stdin); print('  ', d['data'][0]['id'])"
done
```

---

## 6. Instalar Hermes y desplegar los 3 perfiles

Desde Windows (PC Lucas), transferir y ejecutar:

```powershell
scp -r "C:\Users\Pc2025\Desktop\ANTIGRAVITY\centrum-agents\" root@<IP_DGX>:/tmp/
ssh root@<IP_DGX> "bash /tmp/centrum-agents/setup-centrum.sh"
```

El script `setup-centrum.sh`:
1. Instala Hermes Agent si no está
2. Crea los 3 perfiles (`centrum`, `centrum-intel`, `centrum-content`)
3. Copia SOUL.md a cada perfil
4. Copia las 5 skills compartidas a `~/.hermes/skills/`
5. Coloca `config.yaml` por perfil con el modelo correspondiente
6. Genera `.env` con placeholders (Lucas rellena después)
7. Registra los cron jobs (`centrum-intel` diario + `weekly-reporter` lunes 8:00)
8. Verifica la instalación

---

## 5. Configuración de credenciales (`.env`)

Después del script, editar el `.env` de cada perfil:

```bash
# Por cada perfil:
nano ~/.hermes/profiles/centrum/.env
nano ~/.hermes/profiles/centrum-intel/.env
nano ~/.hermes/profiles/centrum-content/.env
```

Valores mínimos:

```env
# Común a los 3 perfiles
OPENROUTER_API_KEY=sk-or-...

# Sólo en perfil centrum
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...           # Mariano (operativo)
TELEGRAM_CHAT_ID_LUCAS=...     # Lucas (técnico)

# Sólo en centrum (cuando se active el envío real)
SMTP_HOST=...
SMTP_USER=...
SMTP_PASS=...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=...
```

`security.redact_secrets: true` está activo: las claves nunca se incluyen en logs ni en respuestas del modelo.

---

## 6. Arranque y verificación

```bash
# Verificar instalación
hermes --version
hermes profile list
# → centrum
# → centrum-intel
# → centrum-content

# Smoke test en cada perfil
hermes profile use centrum && hermes chat "ping"
hermes profile use centrum-intel && hermes chat "estado actual"
hermes profile use centrum-content && hermes chat "estado del banco de guiones"
```

Salida esperada: cada perfil responde en español, carga `CENTRUM-GUARDRAILS` y muestra el coste de la llamada (`display.show_cost: true`).

---

## 7. Activar el gateway Telegram (perfil `centrum`)

Hermes tiene integración Telegram nativa. Una vez configurado `.env`:

```bash
hermes profile use centrum
hermes gateway start --platform telegram
```

A partir de aquí, Mariano escribe al bot y `centrum` responde delegando a sub-agentes según haga falta.

---

## 8. Cron jobs registrados por `setup-centrum.sh`

| Trigger | Cron | Acción |
|---------|------|--------|
| Diario inteligencia | `0 7 * * *` | `hermes profile use centrum-intel && hermes chat "barrido diario fuentes públicas"` |
| Lunes 8:00 | `0 8 * * 1` | `hermes profile use centrum && hermes chat "/weekly report"` |
| Domingo 10:00 | `0 10 * * 0` | `hermes profile use centrum-content && hermes chat "/batch semanal 25 vídeos"` |
| Revisión memoria mensual | `0 9 1 * *` | `hermes profile use centrum && hermes chat "/memory health"` |

Listar/editar/borrar:
```bash
hermes cron list
hermes cron add "0 8 * * 1" "centrum: /weekly report"
hermes cron delete <id>
```

---

## 9. Actualizar un SOUL.md o una skill

```bash
# SOUL.md de un perfil
scp orquestador/centrum-orchestrator/SOUL.md \
    lucas@100.119.47.93:~/.hermes/profiles/centrum/SOUL.md

# Skill compartida
scp skills/centrum/8-estrategias/SKILL.md \
    lucas@100.119.47.93:~/.hermes/skills/centrum/8-estrategias/SKILL.md
```

Hermes recarga los archivos en la siguiente sesión. No hace falta reiniciar gateway.

---

## 10. Roadmap futuro

| Hito | Acción |
|------|--------|
| DGX Spark llega | Añadir provider local a `config.yaml` (vLLM en `127.0.0.1:8003`), mantener OpenRouter como fallback |
| Volumen >100 leads/día | Promover sub-agentes calientes (debt-analyzer, lead-classifier) a perfiles independientes |
| Call IA en producción | Crear perfil `centrum-call` con Pipecat como tool externo |

---

## 11. Troubleshooting rápido

| Problema | Diagnóstico | Acción |
|----------|-------------|--------|
| `OPENROUTER_API_KEY missing` | `.env` no cargado | `hermes profile use centrum && cat .env` |
| Telegram no responde | Gateway parado | `hermes gateway status` |
| Coste subiendo demasiado | `display.show_cost: true` revela el agente caro | Mover ese rol a Gemma 3 27B |
| Memoria saturada | `compression.threshold` no se dispara | Bajar a `0.40` temporalmente |
| Sub-agente bucle infinito | `agent.max_turns` está en 90 | Reducir y revisar SOUL.md del rol |

---

*DEPLOY.md — v2.0 — 2026-05-25 — Antigravity / Mediterránea Firmax SL — Hermes Agent (NousResearch)*
