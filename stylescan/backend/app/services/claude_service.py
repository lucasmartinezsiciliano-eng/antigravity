"""
StyleScan — Claude Report Generation Service

Converts raw FaceMetrics + quiz answers into a professional, personalized
hair analysis report in Spanish. Output is structured JSON consumed by the app.

Prompt strategy:
- System prompt: persona + science framework + format constraints (CACHED)
- User prompt: metrics + quiz (factual, dense, specific)
- Model: claude-haiku-4-5-20251001 (cost-efficient for structured output)
- Caching: System prompt cached (saves ~70% of prompt tokens on repeats)
- Fallback: If JSON parse fails, retry with explicit correction prompt

Science basis:
- Rule of thirds (not golden ratio) for facial balance assessment
- fWHR (facial Width-to-Height Ratio) — dominance signal, not classical beauty
- Jawline prominence = primary masculine attractiveness marker
- Fade vs taper: fade elongates/slims; taper adds width — opposite effects
- Weight line = visual mass band created by the length transition zone
- Heavy stubble (10-day) = peak attractiveness in controlled studies
- Asymmetry compensation via parting strategy
- Age-appropriate texture and length guidance
"""

import json
import logging
import re
from typing import Any

import anthropic

from app.core.config import settings
from app.services.face_analysis import FaceMetrics

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

# ---------------------------------------------------------------------------
# Static descriptors (used in prompt construction)
# ---------------------------------------------------------------------------
FACE_SHAPE_ES = {
    "oval":     "Ovalada — longitud ~1.5× anchura, frente ligeramente más ancha que mentón. La forma más versátil: casi cualquier corte funciona, el reto es destacar en vez de ser genérico.",
    "round":    "Redonda — longitud ≈ anchura (<1.28 ratio), rasgos suaves sin ángulos marcados. Objetivo: crear ilusión de verticalidad y definir la mandíbula visualmente.",
    "square":   "Cuadrada — frente, pómulos y mandíbula con anchuras similares, ángulos marcados y mandíbula horizontal prominente. Objetivo: suavizar ángulos con transiciones, no eliminar la fortaleza que aporta.",
    "oblong":   "Alargada — ratio >1.78, claramente más larga que ancha. Objetivo: añadir anchura lateral y nunca subir volumen en el tope, que ya existe de sobra.",
    "heart":    "Corazón — frente ancha que se estrecha hacia el mentón. Objetivo: equilibrar la base (añadir anchura bajo los pómulos) y reducir visualmente la anchura de la frente.",
    "diamond":  "Diamante — pómulos prominentes con frente y mentón más estrechos. Objetivo: añadir anchura en línea de frente y suavizar la proyección de los pómulos.",
    "triangle": "Triangular — mandíbula más ancha que frente. Objetivo: añadir volumen en la zona superior y reducir peso visual en la mandíbula.",
}

CRANIAL_ES = {
    "balanced":  "Proporciones craneales equilibradas. Ni añade ni resta restricciones al estilo.",
    "elongated": "Cráneo relativamente estrecho y largo (tendencia dolicocéfala). Evitar volumen vertical; los lados más abiertos (degradados altos) pueden compensar.",
    "wide":      "Cráneo relativamente ancho (tendencia braquicéfala). El volumen en el tope alarga visualmente; los lados cerrados lo acentúan positivamente.",
}

# Jawline threshold — below this, beard is primary recommendation
_JAW_WEAK_THRESHOLD = 0.88
# Asymmetry threshold — above this, parting strategy is mandatory
_ASYMMETRY_NOTABLE_THRESHOLD = 0.15

# ---------------------------------------------------------------------------
# SYSTEM PROMPT (cached by Anthropic — only billed once per cache window)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """Eres el motor de análisis de StyleScan. Tu función es convertir métricas faciales reales \
(obtenidas por visión artificial con 468 puntos de MediaPipe) en un informe capilar masculino de máxima \
precisión, personalizado, útil y diferenciador.

════════════════════════════════════════
CIENCIA DEL ATRACTIVO MASCULINO FACIAL
════════════════════════════════════════
Incorpora estos principios en CADA recomendación. Nunca los menciones explícitamente: \
aplícalos de forma que el usuario perciba el resultado sin ver la fórmula.

1. REGLA DE TERCIOS (no el ratio áureo — está refutado como predictor universal)
   - Cara equilibrada: frente / zona media (cejas-nariz) / zona inferior (nariz-mentón) en proporciones ~iguales.
   - El corte puede compensar desequilibrios: volumen en frente compensa tercio superior corto; \
     lado largo en la nuca compensa tercio inferior largo.

2. MANDÍBULA = MARCADOR PRIMARIO DE ATRACTIVO MASCULINO
   - Mandíbula ancha y definida es el rasgo facial más correlacionado con atractivo en estudios de percepción.
   - Ratio mandíbula/pómulos (jaw_to_face_ratio):
     * <0.88 → mandíbula débil: la barba es la herramienta nº1, no el corte. Menciónalo.
     * 0.88–0.96 → mandíbula media: el corte puede enmarcarla.
     * >0.96 → mandíbula fuerte: destacarla con lados cortos es el principio guía.
   - Una mandíbula fuerte + sienes limpias = marco facial clásico y dominante.

3. FWHR (RATIO ANCHURA/ALTURA FACIAL) — señal de dominancia percibida
   - fWHR alto (cara ancha en relación a su longitud) = percepción social de liderazgo y fortaleza.
   - Cortes que aumentan anchura visual (degradados bajos, sienes abiertas) elevan fWHR percibido.
   - En caras ya muy anchas, esto puede añadir dureza; en caras ovaladas/alargadas, es positivo.

4. DEGRADADO (FADE) vs DEGRADADO CORTO (TAPER) — efectos opuestos
   - FADE (piel o nº 0 en algún punto, sube >2 números hasta el tope):
     * Elimina peso lateral → cara parece más esbelta y larga.
     * Ideal: caras redondas, anchas, cuadradas.
     * Contraindicado: caras ya alargadas/diamante (las estira más).
   - TAPER (gradual, nunca llega a piel, borde limpio en nuca/sienes):
     * Mantiene algo de anchura lateral → añade fWHR visual.
     * Ideal: caras alargadas, diamante, ovaladas que quieren añadir anchura.
   - Recuerda: el mismo cliente con fade o taper parece una persona diferente.

5. LÍNEA DE PESO (WEIGHT LINE)
   - Es la banda visual donde el cabello pasa de corto a largo.
   - Alta (por encima de los pómulos): aumenta proporción superior, alarga cara.
   - Media (a nivel de pómulos): equilibrada, la más versátil.
   - Baja (por debajo de pómulos): acorta cara visualmente, añade anchura.
   - Úsala conscientemente según la forma y objetivos del cliente.

6. BARBA — herramienta de remodelación facial
   - Barba de varios días (~10 días, "heavy stubble"): máximo atractivo en estudios de percepción \
     (Dixson & Brooks 2013). Más que barba completa y que cara afeitada.
   - Barba en zona mandíbula/mentón: define y proyecta mandíbula débil (la principal función correctiva).
   - Barba cuadrada (bordes definidos): añade ángulo a caras redondas.
   - Sin barba en mejillas / solo en mandíbula y mentón: máximo efecto de definición.
   - Barba en cara ya angular/cuadrada: puede añadir dureza excesiva — recomendar con matiz.

7. COMPENSACIÓN DE ASIMETRÍA
   - Asimetría ≥0.15: el lado más lleno/alto proyecta más visualmente.
   - Raya: siempre al lado del hemisferio más lleno (no al contrario).
   - Volumen: dirigirlo hacia el lado menos proyectado para compensar.
   - Entradas: si una entra más, el corte puede equilibrarlo con la dirección del peinado.

8. TEXTURA Y PESO VISUAL DEL CABELLO
   - Cabello fino + poca densidad: evitar cortes con mucho volumen en el tope (se hunde al mediodía).
     Cortes con más movimiento lateral o textura en superficie (desmechado) funcionan mejor.
   - Cabello grueso/rizado: enorme potencial de volumen. La forma del volumen importa más que la longitud.
   - Ondulado: el "peso" propio del ondulado puede usarse como herramienta de diseño.

9. MEDIDAS CONCRETAS PARA EL BARBERO
   Siempre incluye:
   - Número de máquina en laterales (1/1.5/2/3/4) o "a piel" / "navaja"
   - Número o longitud en la transición
   - Longitud en cm en el tope (con tijera o navaja)
   - Tipo de degradado exacto: skin fade, zero fade, low fade, mid fade, high fade, taper
   - Técnica en el tope: tijera sobre peine, navaja, o clipper over comb
   - Si se pide textura/desmechado/vaciado de peso
   - Cómo tratar las patillas y la nuca

════════════════════════════════════════
REGLAS DE FORMATO (ABSOLUTAS)
════════════════════════════════════════
1. Responde ÚNICAMENTE con JSON válido. Sin markdown, sin texto fuera del JSON.
2. El JSON debe seguir EXACTAMENTE el esquema indicado en el prompt.
3. Los 3 cortes recomendados deben ser DISTINTOS en estilo, longitud y técnica.
4. Nunca uses frases genéricas. Di POR QUÉ, basándote en los números concretos.
5. Tono: asesor experto que habla directamente al usuario. Cercano pero preciso.
6. Si confianza <0.70, sé honesto sin alarmar — sugiere repetir el proceso con mejor iluminación.
7. No menciones "estudio", "ciencia" ni "ratio áureo" en el texto final. Solo resultados aplicados.
8. Si jaw_to_face_ratio < 0.88, la sección de barba en `consejos_especificos` es OBLIGATORIA y prioritaria."""


# ---------------------------------------------------------------------------
# Main generation function
# ---------------------------------------------------------------------------
def generate_report(metrics: FaceMetrics, quiz: dict[str, Any]) -> dict:
    """
    Generate full analysis report via Claude.
    Returns structured dict with all report sections.
    Raises ValueError if Claude returns unparseable output after retries.
    """
    user_prompt = _build_user_prompt(metrics, quiz)
    try:
        return _call_claude(user_prompt)
    except Exception as e:
        logger.error("Claude report generation failed: %s", e)
        raise


def _call_claude(user_prompt: str, retry: bool = True) -> dict:
    response = _client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=settings.CLAUDE_MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()
    logger.debug("Claude raw output length: %d chars", len(raw))

    # Strip markdown code fences if present (```json ... ``` or ``` ... ```)
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to extract the outermost JSON object
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        if retry:
            logger.warning("Claude JSON parse failed, retrying with strict correction prompt")
            correction = (
                "Tu respuesta anterior contenía texto fuera del JSON (como bloques ```json```). "
                "Devuelve ÚNICAMENTE el objeto JSON, sin ningún texto, sin markdown, sin ```.\n\n"
                f"Corrige y devuelve solo el JSON:\n\n{raw[:800]}"
            )
            return _call_claude(correction, retry=False)

        raise ValueError(f"Claude returned non-JSON output: {raw[:200]}")


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------
def _build_user_prompt(metrics: FaceMetrics, quiz: dict) -> str:
    face_desc = FACE_SHAPE_ES.get(metrics.face_shape, metrics.face_shape)
    cranial_desc = CRANIAL_ES.get(metrics.cranial_proportion, metrics.cranial_proportion)

    # Derived clinical flags (pre-computed so Claude has explicit guidance)
    jaw_flag = ""
    if metrics.jaw_to_face_ratio < _JAW_WEAK_THRESHOLD:
        jaw_flag = (
            f"\n  ⚠ MANDÍBULA DÉBIL (ratio {metrics.jaw_to_face_ratio:.3f} < 0.88): "
            "la barba es la recomendación nº1 para este usuario. "
            "Inclúyela de forma prioritaria en consejos_especificos."
        )
    elif metrics.jaw_to_face_ratio > 0.96:
        jaw_flag = (
            f"\n  ✓ MANDÍBULA FUERTE (ratio {metrics.jaw_to_face_ratio:.3f} > 0.96): "
            "los lados cortos (fade/taper alto) maximizan este rasgo. Destácalo."
        )

    asym_flag = ""
    if metrics.asymmetry_score >= _ASYMMETRY_NOTABLE_THRESHOLD:
        asym_flag = (
            f"\n  ⚠ ASIMETRÍA NOTABLE ({metrics.asymmetry_score:.3f}): "
            "indicar en consejos_especificos la estrategia de raya y dirección del volumen "
            "para compensar. Lado más lleno = lado hacia el que va la raya."
        )

    # Fade vs taper guidance based on face shape
    fade_guidance = _fade_guidance(metrics.face_shape)

    notes_text = ""
    if metrics.analysis_notes:
        notes_text = "\n\nNOTAS DEL ANÁLISIS:\n" + "\n".join(f"  - {n}" for n in metrics.analysis_notes)

    quiz_lines = _format_quiz(quiz)

    # Beard context from quiz
    beard_from_quiz = quiz.get("beard", "none")
    beard_context = {
        "none":    "actualmente sin barba",
        "stubble": "barba de pocos días (óptimo según estudios de percepción)",
        "short":   "barba corta (<2 cm)",
        "full":    "barba completa",
    }.get(beard_from_quiz, beard_from_quiz)

    return f"""════ MÉTRICAS FACIALES (MediaPipe 468 puntos) ════

Forma facial: {metrics.face_shape.upper()}
Descripción: {face_desc}

Ratios biométricos:
  - Ratio longitud/anchura: {metrics.length_width_ratio:.3f}
    (Referencia: oval≈1.50 | redondo<1.28 | alargado>1.78)
  - Ratio frente/pómulos (forehead_to_face_ratio): {metrics.forehead_to_face_ratio:.3f}
    (>1.0 = frente más ancha; 1.0 = igual; <1.0 = frente más estrecha que pómulos)
  - Ratio mandíbula/pómulos (jaw_to_face_ratio): {metrics.jaw_to_face_ratio:.3f}
    (>0.96 = mandíbula fuerte; 0.88–0.96 = media; <0.88 = débil){jaw_flag}
  - Asimetría facial: {metrics.asymmetry_score:.3f} / 1.00
    ({metrics.asymmetry_description}){asym_flag}

Proporciones craneales: {cranial_desc}
Fotos procesadas: {metrics.photos_used}/5 | Confianza: {metrics.confidence:.0%}

Recomendación técnica de base:
  {fade_guidance}{notes_text}

════ PREFERENCIAS DEL USUARIO (quiz) ════

{quiz_lines}
  - Barba actual: {beard_context}

════ INSTRUCCIÓN ════

Genera el informe en este JSON exacto. Sin texto fuera del JSON.

{{
  "resumen_facial": "string — 3-4 frases. Describe la forma facial y los ratios más relevantes \
de forma empática y directa. No uses términos médicos. Explica qué implica para las \
recomendaciones. Si confianza <0.70, añade honestamente que el análisis puede ganar en \
precisión con mejor iluminación o más fotos.",

  "proporciones_craneales": "string — 2 frases. Explica en términos visuales (no médicos) \
las proporciones craneales y su implicación específica para el volumen y estructura del peinado.",

  "ventaja_facial": "string — 1-2 frases. Identifica el rasgo facial más favorecedor de \
este usuario y explica cómo el corte puede potenciarlo. Sea mandíbula, pómulos, \
línea de frente, simetría, etc. Tono positivo y directo.",

  "cortes_recomendados": [
    {{
      "nombre": "string — nombre del corte en español (ej: 'Degradado Bajo con Textura Casual')",
      "nombre_tecnico": "string — en inglés para pedir en cualquier barbería (ej: 'Low Fade with Textured Top')",
      "nivel_estilo": "string — exactamente uno de: 'clásico' | 'moderno' | 'atrevido'",
      "nivel_mantenimiento": "string — exactamente uno de: 'bajo' | 'medio' | 'alto'",
      "descripcion_favorece": "string — 3-4 frases. POR QUÉ este corte favorece ESTA forma facial. \
Menciona el efecto concreto del fade/taper elegido, la línea de peso, y cómo los ratios biométricos \
del usuario hacen que este corte funcione. Sé específico: 'el degradado medio elimina el peso \
lateral que acentúa tu anchura de pómulos, mientras los 5cm en el tope crean verticalidad...'",
      "como_pedirlo_al_barbero": "string — instrucciones exactas. OBLIGATORIO incluir: \
número de máquina en laterales, tipo de degradado exacto (skin/zero/low/mid/high fade o taper), \
longitud en cm en el tope, técnica en el tope (tijera, navaja, clipper over comb), \
si quiere textura/desmechado/vaciado, cómo tratar patillas y nuca. \
Ejemplo: 'Pide un mid fade: empieza en 1 (o 0.5) en la parte más baja del lateral, sube \
gradualmente a 2 a mitad de la cabeza. En el tope, 5-6 cm con tijera, desmechado para \
quitar peso y aportar movimiento. Patillas limpias con navaja. Nuca cuadrada.'",
      "mantenimiento_casa": "string — 2-3 frases. Productos por tipo (no marca: 'cera mate', \
'aceite de argán', 'espuma de volumen'...), frecuencia de lavado y técnica de secado.",
      "frecuencia_barberia": "string — cada cuánto ir a retocar y qué deteriora primero."
    }},
    {{...segundo corte, estilo y técnica claramente diferentes al primero...}},
    {{...tercer corte, el más diferente — puede ser más largo, rizado natural, texturizado, clásico si los otros son modernos, etc...}}
  ],

  "cortes_a_evitar": [
    "string — nombre del corte + razón exacta basada en los ratios del usuario. \
No genérica: 'El bowl cut / corte tazón añade anchura horizontal justo a la altura \
de tus pómulos (ratio {metrics.forehead_to_face_ratio:.2f}), acentuando lo que queremos reducir.'",
    "string — segundo corte a evitar con razón igualmente específica"
  ],

  "consejos_especificos": "string — 4-5 consejos concretos para este usuario. OBLIGATORIO incluir: \
(1) si la raya conviene y en qué lado [menciona asimetría si ≥0.15]; \
(2) consejo de barba adaptado a su jaw_to_face_ratio {metrics.jaw_to_face_ratio:.3f} y barba actual; \
(3) cómo trabajar el volumen según sus proporciones craneales; \
(4) si hay textura o rizos, cómo aprovecharlos; \
(5) cualquier observación específica derivada de las notas del análisis. \
Cada consejo en una frase accionable. Sin repetir lo dicho en las secciones anteriores."
}}"""


def _fade_guidance(face_shape: str) -> str:
    """Returns specific fade vs taper guidance for the given face shape."""
    guidance = {
        "oval": (
            "Forma oval: ambas técnicas funcionan. Fade medio o bajo maximiza fWHR si se quiere "
            "aspecto más dominante. Taper si prefiere look más clásico/conservador. "
            "Línea de peso: media (a nivel de pómulos)."
        ),
        "round": (
            "Forma redonda: FADE (preferiblemente mid o high fade) es la herramienta principal. "
            "Elimina el peso lateral que aumenta la percepción de anchura. "
            "Línea de peso alta (por encima de pómulos). Evitar taper — mantiene anchura que sobra."
        ),
        "square": (
            "Forma cuadrada: degradado suave (low-to-mid fade o taper largo) para mantener algo "
            "de masa lateral que suavice los ángulos. Un skin fade en cara cuadrada puede resultar "
            "excesivamente duro. Línea de peso media o ligeramente baja."
        ),
        "oblong": (
            "Forma alargada: TAPER (nunca fade alto/skin) para conservar anchura lateral. "
            "Línea de peso baja (por debajo de pómulos) para acortar visualmente. "
            "NUNCA añadir volumen en el tope. Los lados abiertos son el principio clave."
        ),
        "heart": (
            "Forma corazón: taper o low fade. Añadir volumen bajo (flequillo lateral, textura lateral baja) "
            "para equilibrar la base. Línea de peso media-baja. Reducir volumen en frente."
        ),
        "diamond": (
            "Forma diamante: taper para conservar anchura en línea de frente. "
            "Textura en el flequillo para añadir visualmente anchura al tercio superior. "
            "Línea de peso media. Evitar fade alto que estrecha sienes ya estrechas."
        ),
        "triangle": (
            "Forma triangular: volumen en el tope (el único caso donde se justifica explícitamente). "
            "Low fade o taper para reducir peso visual en la zona de mandíbula. "
            "Línea de peso media-alta."
        ),
    }
    return guidance.get(face_shape, "Consultar forma facial para guía de fade/taper específica.")


def _format_quiz(quiz: dict) -> str:
    LABELS = {
        "hair_texture": ("Textura del cabello", {
            "straight": "Liso",
            "wavy":     "Ondulado",
            "curly":    "Rizado",
            "coily":    "Muy rizado / afro",
        }),
        "hair_density": ("Densidad del cabello", {
            "thin":   "Fino / escaso",
            "medium": "Normal",
            "thick":  "Grueso / abundante",
        }),
        "preferred_length": ("Longitud preferida", {
            "very_short": "Muy corto (<1 cm)",
            "short":      "Corto (1-3 cm)",
            "medium":     "Medio (3-6 cm)",
            "long":       "Largo (>6 cm)",
        }),
        "maintenance_willingness": ("Disposición al mantenimiento", {
            "low":    "Mínimo — quiero olvidarme del pelo",
            "medium": "Moderado — algo de rutina está bien",
            "high":   "Alto — me gusta cuidar mi imagen",
        }),
        "style_preference": ("Estilo preferido", {
            "classic": "Clásico / conservador",
            "modern":  "Moderno / urbano",
            "trendy":  "A la moda / atrevido",
        }),
        "beard": ("Barba", {
            "none":    "Sin barba",
            "stubble": "Barba de pocos días",
            "short":   "Barba corta (<2 cm)",
            "full":    "Barba completa",
        }),
        "problematic_areas": ("Zonas problemáticas", None),
        "additional_notes":  ("Observaciones adicionales", None),
    }

    lines = []
    for key, value in quiz.items():
        if key not in LABELS:
            continue
        label, mapping = LABELS[key]
        if key == "beard":
            continue  # beard handled separately in the prompt with more context
        if mapping and isinstance(value, str):
            display = mapping.get(value, value)
        elif isinstance(value, list):
            display = ", ".join(value) if value else "Ninguna"
        else:
            display = str(value) if value else "—"
        lines.append(f"  - {label}: {display}")

    return "\n".join(lines) if lines else "  Sin preferencias especificadas"
