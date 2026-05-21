# DEPLOY — Intel Agents (forge + horizon)

Sistema de inteligencia diaria con Claude SDK. Sin OpenClaw.

---

## Requisitos

- Python 3.11+
- `ANTHROPIC_API_KEY` — API key de Anthropic
- `BRAVE_API_KEY` — Brave Search API (gratuita: 2000 queries/mes, suficiente para uso diario)
  - Registrarse en: https://api.search.brave.com/register
- `TELEGRAM_BOT_TOKEN` — token del bot de Telegram (el mismo que ya usa el proyecto)

---

## Instalación en Ubuntu PC (100.119.47.93)

```bash
# 1. Clonar/actualizar repo
cd ~/ANTIGRAVITY
git pull

# 2. Crear entorno virtual
cd intel-agents
python3 -m venv .venv
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Variables de entorno (crear en ~/.intel-env)
cat > ~/.intel-env << 'EOF'
export ANTHROPIC_API_KEY="sk-ant-..."
export BRAVE_API_KEY="BSA..."
export TELEGRAM_BOT_TOKEN="..."
EOF
chmod 600 ~/.intel-env

# 5. Crear directorios de reports y LEARNINGS.md iniciales
mkdir -p ~/ANTIGRAVITY/intel-agents/forge/reports
mkdir -p ~/ANTIGRAVITY/intel-agents/horizon/reports
echo "# LEARNINGS.md — forge" > ~/ANTIGRAVITY/intel-agents/forge/LEARNINGS.md
echo "# LEARNINGS.md — horizon" > ~/ANTIGRAVITY/intel-agents/horizon/LEARNINGS.md

# 6. Test manual
source ~/.intel-env
source .venv/bin/activate
python3 forge/forge.py
python3 horizon/horizon.py
```

---

## Cron (ejecución automática diaria)

```bash
crontab -e
```

Añadir estas líneas:

```cron
# Intel agents — carga vars de entorno antes de cada ejecución

# Forge: 07:30 diario
30 7 * * * source ~/.intel-env && cd /root/ANTIGRAVITY/intel-agents && /root/ANTIGRAVITY/intel-agents/.venv/bin/python3 forge/forge.py >> /root/intel-logs/forge-$(date +\%Y\%m\%d).log 2>&1

# Horizon: 07:45 diario (después de forge para poder leer su salida)
45 7 * * * source ~/.intel-env && cd /root/ANTIGRAVITY/intel-agents && /root/ANTIGRAVITY/intel-agents/.venv/bin/python3 horizon/horizon.py >> /root/intel-logs/horizon-$(date +\%Y\%m\%d).log 2>&1

# Calibrador: domingos 08:30 (después del digest, con el feedback del domingo)
30 8 * * 0 source ~/.intel-env && cd /root/ANTIGRAVITY/intel-agents && /root/ANTIGRAVITY/intel-agents/.venv/bin/python3 calibrate.py >> /root/intel-logs/calibrate-$(date +\%Y\%m\%d).log 2>&1
```

Crear carpeta de logs:
```bash
mkdir -p /root/intel-logs
```

---

## Feedback loop (cómo aprende el sistema)

1. Cada mañana recibes dos mensajes Telegram: 🔧 forge + 🌅 horizon
2. Responde con emojis + número de señal: `👍1 👎2 ⚡3`
   - 👍 = útil, lo tengo en cuenta
   - 👎 = ruido, no me interesa
   - 💬 = interesante, dame más info
   - ⚡ = actúo ahora mismo
   - ❓ = no entiendo
3. Activa el n8n workflow `Intel - Feedback Logger` (ver `n8n-workflows/`) para capturar automáticamente las reacciones en Google Sheets
4. Cada domingo, `calibrate.py` lee el feedback y mejora los pesos automáticamente

---

## Importar el workflow n8n de feedback

1. Abrir n8n en https://n8n.lukimporta.es
2. Menú → Import from File → seleccionar `n8n-workflows/Intel - Feedback Logger.json`
3. Configurar credenciales en los nodos marcados con ⚠️ TODO
4. Crear Google Sheet con pestaña `Intel-Feedback` (columnas: date, agent, signal_id, reaction, comment, action_taken)
5. Activar el workflow

---

## Coste estimado

| Componente | Coste |
|------------|-------|
| Claude Haiku (forge + horizon) | ~€0.002/día × 30 = **€0.06/mes** |
| Claude Haiku (calibrador dominical) | ~€0.002/semana × 4 = **€0.008/mes** |
| Brave Search API | **€0/mes** (2000 queries gratis >> 600 usadas) |
| Total | **~€0.07/mes** |

Comparado con alternativas de inteligencia de mercado: **€0.07/mes vs €50-200/mes** de cualquier newsletter o herramienta de competitive intelligence.

---

## Estructura de archivos generados

```
intel-agents/
├── forge/
│   ├── forge.py
│   ├── IDENTITY.md
│   ├── LEARNINGS.md          ← acumula aprendizajes sesión a sesión
│   └── reports/
│       ├── forge-20260521.md ← informe del día (completo)
│       └── ...
├── horizon/
│   ├── horizon.py
│   ├── IDENTITY.md
│   ├── LEARNINGS.md
│   └── reports/
├── shared/
│   ├── tools.py
│   └── telegram.py
├── calibrate.py
├── requirements.txt
├── INTEL-CALIBRATION.md      ← actualizado cada domingo por calibrate.py
├── INTEL-FEEDBACK-LOG.md     ← append-only, alimentado por n8n
├── INTEL-GUARDRAILS.md
└── n8n-workflows/
    └── Intel - Feedback Logger.json
```
