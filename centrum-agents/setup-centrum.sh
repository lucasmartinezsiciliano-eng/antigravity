#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# CENTRUM DE LA VIVIENDA — Despliegue en Hermes Agent (NousResearch)
# ═══════════════════════════════════════════════════════════════════════════════
# Ejecutar en Ubuntu local (PC casa, 100.119.47.93) como el usuario que correrá Hermes:
#   scp -r centrum-agents/ lucas@100.119.47.93:/tmp/
#   ssh lucas@100.119.47.93 "bash /tmp/centrum-agents/setup-centrum.sh"
#
# Crea 3 perfiles Hermes (centrum, centrum-intel, centrum-content) con sus SOULs,
# skills compartidas, config.yaml y cron jobs.
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
LOG_FILE="/tmp/centrum-setup.log"

PROFILES=("centrum" "centrum-intel" "centrum-content")

# ── Colores ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
ok()    { echo -e "${GREEN}[OK]${NC}    $1"   | tee -a "$LOG_FILE"; }
info()  { echo -e "${BLUE}[INFO]${NC}  $1"   | tee -a "$LOG_FILE"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1" | tee -a "$LOG_FILE"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $1"    | tee -a "$LOG_FILE"; exit 1; }

# ── Cabecera ──────────────────────────────────────────────────────────────────
echo "════════════════════════════════════════════════════════════" | tee "$LOG_FILE"
echo "  CENTRUM — Deploy en Hermes Agent (NousResearch)"            | tee -a "$LOG_FILE"
echo "  $(date)"                                                    | tee -a "$LOG_FILE"
echo "  Host: $(hostname)  User: $USER  HERMES_HOME: $HERMES_HOME"  | tee -a "$LOG_FILE"
echo "════════════════════════════════════════════════════════════" | tee -a "$LOG_FILE"

# ── 1. Verificar / instalar Hermes ───────────────────────────────────────────
if ! command -v hermes &> /dev/null; then
    info "Hermes no encontrado. Instalando..."
    if command -v pipx &> /dev/null; then
        pipx install hermes-agent || fail "pipx install hermes-agent falló"
    else
        python3 -m pip install --user hermes-agent || fail "pip install hermes-agent falló"
    fi
    ok "Hermes instalado"
else
    ok "Hermes ya instalado: $(hermes --version 2>/dev/null || echo 'versión desconocida')"
fi

# ── 2. Crear estructura base ──────────────────────────────────────────────────
mkdir -p "$HERMES_HOME/skills/governance/guardrails"
mkdir -p "$HERMES_HOME/skills/centrum/8-estrategias"
mkdir -p "$HERMES_HOME/skills/centrum/perfil-deudor"
mkdir -p "$HERMES_HOME/skills/centrum/3-reglas"
mkdir -p "$HERMES_HOME/skills/centrum/clasificacion-ae"
mkdir -p "$HERMES_HOME/skills/centrum/youtube-intel"
mkdir -p "$HERMES_HOME/skills/centrum/case-kanban"
mkdir -p "$HERMES_HOME/skills/centrum/thinking-mode"
mkdir -p "$HERMES_HOME/skills/centrum/case-agents-writer"
mkdir -p "$HERMES_HOME/skills/centrum/manejo-objeciones"
mkdir -p "$HERMES_HOME/skills/centrum/psicologia-venta-consultiva"
mkdir -p "$HERMES_HOME/skills/centrum/empatia-crisis"
mkdir -p "$HERMES_HOME/skills/centrum/escalacion-mariano"
mkdir -p "$HERMES_HOME/skills/centrum/legal-rgpd"
mkdir -p "$HERMES_HOME/skills/centrum/datos-para-analisis"
mkdir -p "$HERMES_HOME/skills/centrum/contexto-hipotecario-espana"
mkdir -p "$HERMES_HOME/skills/centrum/objetivo-cliente"

# ── 3. Copiar skills compartidas ─────────────────────────────────────────────
info "Copiando skills compartidas..."

cp "$SCRIPT_DIR/skills/governance/guardrails/SKILL.md"     "$HERMES_HOME/skills/governance/guardrails/SKILL.md"
cp "$SCRIPT_DIR/skills/centrum/8-estrategias/SKILL.md"     "$HERMES_HOME/skills/centrum/8-estrategias/SKILL.md"
cp "$SCRIPT_DIR/skills/centrum/perfil-deudor/SKILL.md"     "$HERMES_HOME/skills/centrum/perfil-deudor/SKILL.md"
cp "$SCRIPT_DIR/skills/centrum/3-reglas/SKILL.md"          "$HERMES_HOME/skills/centrum/3-reglas/SKILL.md"
cp "$SCRIPT_DIR/skills/centrum/clasificacion-ae/SKILL.md"  "$HERMES_HOME/skills/centrum/clasificacion-ae/SKILL.md"
cp "$SCRIPT_DIR/skills/centrum/youtube-intel/SKILL.md"        "$HERMES_HOME/skills/centrum/youtube-intel/SKILL.md"
cp "$SCRIPT_DIR/skills/centrum/case-kanban/SKILL.md"          "$HERMES_HOME/skills/centrum/case-kanban/SKILL.md"
cp "$SCRIPT_DIR/skills/centrum/thinking-mode/SKILL.md"        "$HERMES_HOME/skills/centrum/thinking-mode/SKILL.md"
cp "$SCRIPT_DIR/skills/centrum/case-agents-writer/SKILL.md"   "$HERMES_HOME/skills/centrum/case-agents-writer/SKILL.md"
# Skills de Ana (call-vendedor) — voz IA del bloque 3
cp "$SCRIPT_DIR/skills/centrum/manejo-objeciones/SKILL.md"            "$HERMES_HOME/skills/centrum/manejo-objeciones/SKILL.md"
cp "$SCRIPT_DIR/skills/centrum/psicologia-venta-consultiva/SKILL.md"  "$HERMES_HOME/skills/centrum/psicologia-venta-consultiva/SKILL.md"
cp "$SCRIPT_DIR/skills/centrum/empatia-crisis/SKILL.md"               "$HERMES_HOME/skills/centrum/empatia-crisis/SKILL.md"
cp "$SCRIPT_DIR/skills/centrum/escalacion-mariano/SKILL.md"           "$HERMES_HOME/skills/centrum/escalacion-mariano/SKILL.md"
cp "$SCRIPT_DIR/skills/centrum/legal-rgpd/SKILL.md"                   "$HERMES_HOME/skills/centrum/legal-rgpd/SKILL.md"
# Skills de recogida → análisis (Ana + dm-qualifier): qué preguntar y para qué
cp "$SCRIPT_DIR/skills/centrum/datos-para-analisis/SKILL.md"          "$HERMES_HOME/skills/centrum/datos-para-analisis/SKILL.md"
cp "$SCRIPT_DIR/skills/centrum/contexto-hipotecario-espana/SKILL.md"  "$HERMES_HOME/skills/centrum/contexto-hipotecario-espana/SKILL.md"
cp "$SCRIPT_DIR/skills/centrum/objetivo-cliente/SKILL.md"             "$HERMES_HOME/skills/centrum/objetivo-cliente/SKILL.md"

# La constitución también vive como skill (cargada por todos los perfiles)
cp "$SCRIPT_DIR/CENTRUM-GUARDRAILS.md" "$HERMES_HOME/skills/governance/guardrails/CENTRUM-GUARDRAILS.md"

ok "17 skills instaladas en $HERMES_HOME/skills/"

# Inicializar Kanban board para pipeline de casos
if command -v hermes &> /dev/null; then
    info "Inicializando Kanban board centrum-cases..."
    hermes kanban init 2>/dev/null || true
    hermes kanban boards create centrum-cases \
        --name "Pipeline de Casos Centrum" \
        --icon "🏠" \
        --switch 2>/dev/null \
        && ok "Kanban board centrum-cases creado" \
        || info "Kanban board ya existe o requiere gateway activo"
fi

# Instalar youtube-transcript-api (dependencia del built-in media/youtube-content)
info "Instalando dependencia youtube-transcript-api..."
python3 -m pip install --user youtube-transcript-api yt-dlp 2>/dev/null \
    && ok "youtube-transcript-api + yt-dlp instalados" \
    || warn "No se pudo instalar youtube-transcript-api — instalar manualmente antes del deploy"

# ── PLUR — memoria compartida entre perfiles (cross-agent engrams) ───────────
# Benchmark: Haiku+PLUR supera a Opus sin PLUR (2.6x mejor, 10x más barato)
# Los engrams aprendidos en centrum-intel (patrones de mercado, clientes) se
# propagan automáticamente a centrum y centrum-content.
info "Instalando PLUR (cross-agent memory)..."
if command -v node &> /dev/null && command -v npm &> /dev/null; then
    python3 -m pip install --user plur-hermes==0.9.4 2>/dev/null \
        && ok "plur-hermes instalado" \
        || warn "pip install plur-hermes falló — instalar manualmente"

    npm install -g @plur-ai/cli@0.9.4 2>/dev/null \
        && ok "@plur-ai/cli instalado" \
        || warn "npm install @plur-ai/cli falló — instalar manualmente"

    # Inicializar PLUR para el proyecto Centrum
    mkdir -p "$HOME/.plur"
    if [[ ! -f "$HOME/.plur/config.yaml" ]]; then
        cat > "$HOME/.plur/config.yaml" <<'PLUREOF'
domain: centrum
scope_hierarchy:
  - global
  - project:centrum
  - project:centrum-intel
  - project:centrum-content

index: true   # SQLite index para stores > 1k engrams

# Decay model ACT-R: los engrams se debilitan sin uso
decay:
  half_life_days: 90
  min_strength: 0.1

sync:
  enabled: false   # no sync en cloud — todo local en DGX Spark
PLUREOF
        ok "PLUR config creado en ~/.plur/config.yaml"
    else
        info "PLUR config ya existe — no se toca"
    fi

    # Registrar PLUR en cada perfil Hermes
    for profile in "${PROFILES[@]}"; do
        profile_dir="$HERMES_HOME/profiles/$profile"
        mkdir -p "$profile_dir"
        if [[ ! -f "$profile_dir/.plur.yaml" ]]; then
            cat > "$profile_dir/.plur.yaml" <<PEOF
domain: centrum
scope: project:$profile
PEOF
            ok "PLUR scope configurado para $profile"
        fi
    done
else
    warn "Node.js no encontrado — instalar con: curl -fsSL https://deb.nodesource.com/setup_20.x | bash && apt-get install -y nodejs"
    warn "Luego: pip install plur-hermes==0.9.4 && npm install -g @plur-ai/cli@0.9.4"
fi

# ── 4. Crear perfiles ────────────────────────────────────────────────────────
for profile in "${PROFILES[@]}"; do
    profile_dir="$HERMES_HOME/profiles/$profile"

    if [[ -d "$profile_dir" ]]; then
        warn "Perfil ya existe: $profile — preservando .env y memoria, sobreescribiendo SOUL/config"
    else
        info "Creando perfil: $profile"
        if command -v hermes &> /dev/null; then
            hermes profile create "$profile" --no-interactive 2>/dev/null \
                || mkdir -p "$profile_dir"
        else
            mkdir -p "$profile_dir"
        fi
    fi

    mkdir -p "$profile_dir/memories" "$profile_dir/sessions" "$profile_dir/logs"

    # config.yaml
    if [[ -f "$SCRIPT_DIR/config/$profile/config.yaml" ]]; then
        cp "$SCRIPT_DIR/config/$profile/config.yaml" "$profile_dir/config.yaml"
        ok "config.yaml → $profile"
    else
        warn "No hay config.yaml para $profile en $SCRIPT_DIR/config/$profile/"
    fi

    # SOUL.md
    case "$profile" in
        centrum)
            soul_src="$SCRIPT_DIR/orquestador/centrum-orchestrator/SOUL.md"
            extras_dir="cases"
            ;;
        centrum-intel)
            soul_src="$SCRIPT_DIR/perfiles/centrum-intel/SOUL.md"
            extras_dir="observations"
            ;;
        centrum-content)
            soul_src="$SCRIPT_DIR/perfiles/centrum-content/SOUL.md"
            extras_dir="batch"
            ;;
    esac

    if [[ -f "$soul_src" ]]; then
        cp "$soul_src" "$profile_dir/SOUL.md"
        ok "SOUL.md → $profile"
    else
        warn "No hay SOUL.md para $profile en $soul_src"
    fi

    # AGENTS.md — auto-inyectado por Hermes en cada sesión del perfil
    case "$profile" in
        centrum)       agents_src="$SCRIPT_DIR/orquestador/centrum-orchestrator/AGENTS.md" ;;
        centrum-intel) agents_src="$SCRIPT_DIR/perfiles/centrum-intel/AGENTS.md" ;;
        centrum-content) agents_src="$SCRIPT_DIR/perfiles/centrum-content/AGENTS.md" ;;
    esac
    if [[ -f "$agents_src" ]]; then
        cp "$agents_src" "$profile_dir/AGENTS.md"
        ok "AGENTS.md → $profile"
    fi

    mkdir -p "$profile_dir/$extras_dir"

    # .env placeholder (no sobreescribir si ya existe)
    if [[ ! -f "$profile_dir/.env" ]]; then
        cat > "$profile_dir/.env" <<EOF
# === Perfil: $profile ===
# Editar después de la instalación.

OPENROUTER_API_KEY=

EOF
        if [[ "$profile" == "centrum" ]]; then
            cat >> "$profile_dir/.env" <<EOF
# Telegram (operativa Mariano + alertas Lucas)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
TELEGRAM_CHAT_ID_LUCAS=

# Comunicaciones (activar cuando esté listo)
SMTP_HOST=
SMTP_USER=
SMTP_PASS=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=

# Google Calendar (call IA)
GOOGLE_CALENDAR_CREDENTIALS=
EOF
        elif [[ "$profile" == "centrum-intel" ]]; then
            cat >> "$profile_dir/.env" <<EOF
# Telegram (sólo alertas técnicas a Lucas)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID_LUCAS=
EOF
        elif [[ "$profile" == "centrum-content" ]]; then
            cat >> "$profile_dir/.env" <<EOF
# Meta + TikTok
META_ACCESS_TOKEN=
META_AD_ACCOUNT_ID=
TIKTOK_ACCESS_TOKEN=
GOOGLE_ADS_DEVELOPER_TOKEN=
EOF
        fi
        chmod 600 "$profile_dir/.env"
        ok ".env placeholder → $profile (chmod 600)"
    else
        info ".env ya existe en $profile — no se toca"
    fi
done

# ── 5. Registrar cron jobs (vía hermes cron nativo) ──────────────────────────
info "Registrando cron jobs nativos de Hermes..."

if command -v hermes &> /dev/null; then
    hermes cron add "0 7 * * *"  "centrum-intel: barrido diario fuentes públicas (BOE, INE, CGPJ, foros)" \
        2>/dev/null && ok "cron diario centrum-intel registrado" || warn "cron centrum-intel ya existe o falló"

    hermes cron add "0 8 * * 1"  "centrum: /weekly report — informe del lunes a Mariano" \
        2>/dev/null && ok "cron lunes weekly-report registrado" || warn "cron weekly-report ya existe o falló"

    hermes cron add "0 10 * * 0" "centrum-content: /batch semanal — 25 vídeos + copy Meta/Google" \
        2>/dev/null && ok "cron domingo batch contenido registrado" || warn "cron batch ya existe o falló"

    hermes cron add "0 9 1 * *"  "centrum: /memory health — revisión memoria mensual" \
        2>/dev/null && ok "cron mensual memory-health registrado" || warn "cron memory-health ya existe o falló"
else
    warn "hermes no en PATH — registrar cron manualmente con 'hermes cron add'"
fi

# ── 6. Verificación final ────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════════" | tee -a "$LOG_FILE"
echo "  Verificación final"                                         | tee -a "$LOG_FILE"
echo "════════════════════════════════════════════════════════════" | tee -a "$LOG_FILE"

for profile in "${PROFILES[@]}"; do
    profile_dir="$HERMES_HOME/profiles/$profile"
    soul="$profile_dir/SOUL.md"
    cfg="$profile_dir/config.yaml"
    env_file="$profile_dir/.env"

    if [[ -f "$soul" && -f "$cfg" && -f "$env_file" ]]; then
        ok "$profile  ✓ SOUL.md  ✓ config.yaml  ✓ .env"
    else
        warn "$profile incompleto"
        [[ -f "$soul" ]]     || warn "  falta SOUL.md"
        [[ -f "$cfg" ]]      || warn "  falta config.yaml"
        [[ -f "$env_file" ]] || warn "  falta .env"
    fi
done

skill_count=$(find "$HERMES_HOME/skills" -name "SKILL.md" | wc -l)
ok "Skills instaladas: $skill_count (esperado: 17)"

# ── 7. Pinning de skills críticas (Curator no puede archivarlas) ──────────────
# El Curator borra skills sin uso en 90 días. Las skills de Centrum son permanentes.
if command -v hermes &> /dev/null; then
    info "Fijando skills críticas (inmunes al Curator)..."
    for skill in \
        "governance/guardrails" \
        "centrum/3-reglas" \
        "centrum/8-estrategias" \
        "centrum/perfil-deudor" \
        "centrum/clasificacion-ae" \
        "centrum/youtube-intel" \
        "centrum/case-kanban" \
        "centrum/thinking-mode" \
        "centrum/case-agents-writer" \
        "centrum/manejo-objeciones" \
        "centrum/psicologia-venta-consultiva" \
        "centrum/empatia-crisis" \
        "centrum/escalacion-mariano" \
        "centrum/legal-rgpd" \
        "centrum/datos-para-analisis" \
        "centrum/contexto-hipotecario-espana" \
        "centrum/objetivo-cliente"
    do
        hermes curator pin "$skill" 2>/dev/null \
            && ok "Pinned: $skill" \
            || warn "No se pudo fijar: $skill (ejecutar manualmente si es necesario)"
    done
else
    warn "Ejecutar después de instalar Hermes:"
    warn "  hermes curator pin governance/guardrails"
    warn "  hermes curator pin centrum/3-reglas"
    warn "  hermes curator pin centrum/8-estrategias"
    warn "  hermes curator pin centrum/perfil-deudor"
    warn "  hermes curator pin centrum/clasificacion-ae"
    warn "  hermes curator pin centrum/youtube-intel"
fi

# ── Cierre ───────────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════════"
ok "Despliegue completado."
echo ""
echo "Próximos pasos:"
echo "  1. nano $HERMES_HOME/profiles/centrum/.env          # Telegram + Twilio + SMTP"
echo "  2. nano $HERMES_HOME/profiles/centrum-intel/.env    # solo Telegram Lucas"
echo "  3. nano $HERMES_HOME/profiles/centrum-content/.env  # Meta + TikTok tokens"
echo "  4. bash vllm-start.sh                               # levantar Nano + Pro"
echo "  5. hermes profile use centrum && hermes chat 'ping' # smoke test"
echo "  6. hermes gateway start --platform telegram         # activar bot Mariano"
echo ""
echo "Log completo: $LOG_FILE"
echo "════════════════════════════════════════════════════════════"
