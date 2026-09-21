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
