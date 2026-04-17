/**
 * engine/hook.js
 * Dado un concepto, genera 5 variantes del frame 1 para elegir el mejor hook
 *
 * El frame 1 es el 80% del trabajo — si no para el scroll, el resto no importa.
 * Cada variante prueba un ángulo distinto del mismo concepto.
 */

import Anthropic from '@anthropic-ai/sdk';
import { readFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import 'dotenv/config';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

function loadPost(id) {
  const p = join(ROOT, 'data', 'posts.json');
  if (!existsSync(p)) throw new Error('data/posts.json no encontrado');
  const posts = JSON.parse(readFileSync(p, 'utf-8'));
  const post = posts.find(p => p.id === id);
  if (!post) throw new Error(`Concepto ID ${id} no encontrado`);
  return post;
}

const SYSTEM_PROMPT = `Eres un director de fotografía editorial especializado en el primer frame de carruseles virales.

Tu trabajo es generar 5 variantes del frame 1 de un post.
Cada variante prueba un ángulo psicológico distinto para parar el scroll.

LOS 5 ÁNGULOS (uno por variante):
1. ESCALA — algo de tamaño inesperado domina el encuadre
2. ACCIÓN CONGELADA — un momento imposible de predecir, capturado justo antes del impacto
3. CONTRASTE BRUTAL — dos cosas que no deberían coexistir, en la misma imagen
4. PUNTO DE VISTA — ángulo de cámara completamente inusual (desde abajo, desde arriba, POV del invasor)
5. TEXTO EN ESCENA — algo escrito en el entorno (polvo, condensación, tierra, pared) que plantea una pregunta

REFERENCIA REAL DE @kczco:
- "fishing time" frame 1: ella sentada en el maletero del Porsche verde en un río, con caña de pesca y un pez en la mano, mirada directa. La pregunta implícita: ¿qué hace un Porsche en un río?
- "sorry i was hungry" frame 1: ella comiendo una naranja apoyada en el Porsche mientras un grupo de abuelos furiosos la rodean con naranjas en la mano. La pregunta: ¿qué pasó?
- "too hot here" frame 1: ella sentada en rocas junto al Porsche, Porsche hundido parcialmente en un oasis del Sahara. La pregunta: ¿cómo llegó aquí?

CRITERIOS para un buen frame 1:
- La pregunta implícita debe ser imposible de responder sin hacer swipe
- Ella siempre hace algo con las manos — nunca brazos cruzados, nunca manos en bolsillos
- El frasco/objeto de lujo siempre visible y perfecto
- La destrucción o el caos ya empezado — no anticipado, ya en curso
- Encuadre 4:5 vertical (1080x1350) — pensar en móvil

Responde en JSON puro sin markdown.`;

export async function generateHooks(id) {
  if (!process.env.ANTHROPIC_API_KEY) {
    throw new Error('Falta ANTHROPIC_API_KEY en .env');
  }

  const post = loadPost(id);
  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

  console.log(`\n🪝 Generando 5 variantes de hook para concepto #${id}: "${post.title}"...\n`);

  const message = await client.messages.create({
    model: process.env.CLAUDE_MODEL || 'claude-sonnet-4-20250514',
    max_tokens: 2000,
    system: SYSTEM_PROMPT,
    messages: [{
      role: 'user',
      content: `Genera 5 variantes del frame 1 para este concepto.

Concepto: ${post.title}
Perfume: ${post.perfume} · ${post.brand}
Localización: ${post.localizacion}
Invasor: ${post.element_invasor}
Acción protagonista original: ${post.accion_protagonista || 'no especificada'}
Frame 1 original: ${post.frames?.[0]?.description || 'no generado aún'}
Punch line WTF (frame 7): ${post.punch_line_wtf || 'no especificado'}

Genera 5 variantes del frame 1, una por cada ángulo psicológico.
Cada variante es una descripción completa lista para usar como prompt en Higgsfield.

JSON:
{
  "concept_id": "${id}",
  "hooks": [
    {
      "variant": 1,
      "angle": "escala",
      "implicit_question": "la pregunta que se hace quien ve la imagen — debe ser imposible de no querer responder",
      "description": "descripción completa del frame 1 lista para prompt — 50-80 palabras, muy específica: posición de ella, posición del frasco, qué está pasando exactamente, luz, encuadre",
      "stop_scroll_reason": "por qué esta versión para el scroll mejor que las otras"
    }
  ],
  "recommended": 1,
  "recommended_reason": "cuál de las 5 abre el loop más irresistible y por qué"
}`
    }]
  });

  const raw = message.content[0].text.trim();
  let result;
  try {
    result = JSON.parse(raw);
  } catch {
    const cleaned = raw.replace(/^```json\n?/, '').replace(/\n?```$/, '');
    result = JSON.parse(cleaned);
  }

  console.log('═'.repeat(60));
  console.log(`🪝 5 VARIANTES DE HOOK — Concepto #${id}: "${post.title}"`);
  console.log('═'.repeat(60));

  for (const h of result.hooks) {
    const star = h.variant === result.recommended ? ' ⭐ RECOMENDADA' : '';
    console.log(`\n[${h.variant}] ${h.angle.toUpperCase()}${star}`);
    console.log(`❓ "${h.implicit_question}"`);
    console.log(`📸 ${h.description}`);
    console.log(`🛑 Para el scroll: ${h.stop_scroll_reason}`);
  }

  console.log('\n' + '═'.repeat(60));
  console.log(`⭐ RECOMENDADA: Variante ${result.recommended}`);
  console.log(`   ${result.recommended_reason}`);
  console.log('═'.repeat(60));

  return result;
}
