# LEARNINGS.md — Forge
# Append-only. No borrar entradas.

---

## 2026-09-21

**Señales evaluadas:** 12
**Incluidas en informe:** 3
**Ratio:** 25%

**Señales incluidas:**
1. Qwen3-TTS (Alibaba, ene 2026) — TTS local > ElevenLabs, español, 3s cloning
2. Gemma 4 12B (Google, abr 2026) — audio nativo local, primera vez posible
3. Granite 4.1 8B (IBM, abr 2026) — 8B ≈ 32B rendimiento, tool calling local

**Señales descartadas (motivo):**
- LFM2.5-2.6B: datos insuficientes para comparar vs stack actual
- JSON2Video/Revideo: esfuerzo medio, no justifica migración de Creatomate hoy
- Fish Audio: gratuidad no confirmada
- LiveKit: redundante — Pipecat ya en evaluación
- Reddit r/LocalLLaMA: limitado por indexación 2026

**Patrón detectado:**
Qwen3-TTS confirma patrón clave: el stack de TTS open source ya supera comerciales en benchmarks ciegos — la brecha técnica que justificaba ElevenLabs ha cerrado. Próximo ciclo: monitorizar Fish Audio y F5-TTS para confirmar cuál es el líder actual en español.

**Bloqueadores de fuente:**
- HuggingFace trending: bloqueado por proxy (egress)
- picuki.com + imginn.com: bloqueados por proxy
- Twitter/X site: operator ineficaz en 2026

**Ajuste recomendado para próximo ciclo:**
Sustituir WebFetch a HuggingFace/picuki/imginn por WebSearch equivalente ya que esos dominios están bloqueados en este entorno.

---

## 2026-09-22

**Señales evaluadas:** 12
**Incluidas en informe:** 2
**Ratio:** 17%

**Señales incluidas:**
1. PhoneLLM Alpha 1 (Pipecat/Daily, sep 2026) — LLM 30B open-weight para voice agents, directo en evaluación Pipecat→Retell de Centrum
2. Qwen3.8-27B (Alibaba, ago 2026) — mejor modelo multimodal local <30B, sustituye Claude Sonnet no-crítico

**Señales descartadas (motivo):**
- Remotion: esfuerzo ALTO para migrar Creatomate — requiere React pipeline completo
- Wireflow: pricing gratuito no verificado
- Kimi K2.6: probablemente >70B, overkill para agentes actuales de Lucas
- Fish Audio: tercer ciclo sin confirmar gratuidad → añadir a anti-patrones próximo domingo
- GitHub trending AI agent tools: orientados a Claude Code CLI, no a stack n8n/Oracle
- Nuevos modelos Ollama cloud-tagged: no añaden valor local (deepseek-v4.1-flash, glm-5.3, kimi-k3, minimax-m3)

**Patrón detectado:**
Pipecat continúa consolidándose como el eje de sustitución de Retell AI — con PhoneLLM ahora completan el trío: Pipecat (framework) + PhoneLLM (LLM) + Chatterbox/Qwen3-TTS (voz). Stack completo OSS para Centrum call agent ya tiene todos los componentes. Señal de convergencia alta.

**Confirmaciones de LEARNINGS anteriores:**
- Ajuste WebSearch en lugar de WebFetch para HuggingFace/picuki/imginn funcionó correctamente hoy (señal HF trending capturada)
- Fish Audio sigue sin confirmar gratuidad → considerar añadir a anti-patrones si tercer descarte consecutivo

**Bloqueadores de fuente (mismo patrón):**
- picuki.com + imginn.com: bloqueados (confirmado)
- Twitter/X site:operator: no retorna resultados útiles en 2026
