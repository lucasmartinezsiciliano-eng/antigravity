/**
 * engine/prompts.js
 * Concepto → Prompts para Higgsfield Nano Banana + Kling AI
 *
 * MEJORAS vs spec original:
 * - Fórmula 6-variable de Nano Banana Pro (Subject + Composition + Action + Location + Style + Constraints)
 * - Incluye seed_suggestion para consistencia de personaje entre sesiones
 * - Negative constraints explícitos (lo que NO debe aparecer)
 * - Especificaciones técnicas por frame: focal length, aperture, motion type
 * - Kling prompt incluye camera movement type y audio direction
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

const SYSTEM_PROMPT = `Eres un experto en generar prompts para modelos de imagen IA, especializado en fotografía editorial de moda oscura y lujosa.

Conoces a fondo Higgsfield Nano Banana Pro (modelo de imagen) y Kling AI (modelo de video).

ESTÉTICA DEL PROYECTO:
- Fotografía editorial de moda, nunca CGI o render 3D
- Film grain visible, no perfecto digitalmente
- Iluminación: nocturna artificial dura O luz natural dura de mediodía (nunca suave, nunca estudio)
- Fondo: siempre oscuro, texturas ricas, nunca blanco, nunca gris neutro
- El avatar: mujer, seria, sin sonreír, actitud indiferente al caos que la rodea
- El frasco: siempre en foco perfecto, nunca borroso, nunca tapado

FÓRMULA NANO BANANA PRO (6 variables, SIEMPRE incluir todas):
1. SUBJECT: Descripción exacta del sujeto principal con detalles específicos
2. COMPOSITION: Tipo de lente, encuadre, relación espacial de elementos
3. ACTION: Qué está haciendo el sujeto o elemento (evitar estático)
4. LOCATION: Contexto físico detallado con texturas y atmósfera
5. STYLE: Medium fotográfico, referencias, mood
6. CONSTRAINTS: Lo que explícitamente NO debe aparecer (muy importante)

ESTILO DE PROMPT: Command-line syntax, no conversacional. Denso, específico, sin florituras.
Referencia de cámara recomendada: "shot on 35mm film, f/1.8 aperture, natural harsh backlight"

Responde SIEMPRE en JSON puro sin markdown.`;

const USER_PROMPT = (post) => `
Genera los prompts para este concepto de post:

Perfume: ${post.perfume} de ${post.brand}
Modo: ${post.mode}
Título: ${post.title}
Resumen: ${post.concept_summary}
Invasor: ${post.element_invasor}
Localización: ${post.localizacion}
Conexión olfativa: ${post.scent_connection}

FRAMES:
${post.frames.map(f => `[${f.number}] ${f.description}`).join('\n')}

Genera los prompts siguiendo la fórmula 6-variable para cada frame de Higgsfield.
Para el frame 1, genera también el prompt de Kling AI (animación).

JSON esperado:
{
  "concept_id": "${post.id}",
  "seed_suggestion": "número entre 1000-9999 para usar en todos los frames y mantener consistencia del avatar",
  "seed_rationale": "por qué este seed (describe el tipo de look del avatar que evoca)",
  "higgsfield_prompts": [
    {
      "frame": 1,
      "focal_length": "ej: 35mm",
      "aperture": "ej: f/1.8",
      "prompt": "prompt completo listo para pegar en Nano Banana — 80-150 palabras",
      "negative_prompt": "lista de lo que NO debe aparecer: smiling, studio lighting, white background, CGI, etc."
    }
  ],
  "kling_prompt": {
    "frame": 1,
    "duration_seconds": 15,
    "camera_movement": "static|slow_push_in|slow_pan_left|slow_pan_right|slow_tilt_down",
    "motion_subject": "qué elemento se mueve y cómo",
    "prompt": "prompt completo para Kling AI — incluir movimiento específico, velocidad, atmósfera",
    "audio_note": "instrucción para la música/audio que se añadirá en edición"
  }
}`;

export async function generatePrompts(id) {
  if (!process.env.ANTHROPIC_API_KEY) {
    throw new Error('Falta ANTHROPIC_API_KEY en .env');
  }

  const post = loadPost(id);

  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

  console.log(`\n🎨 Generando prompts para concepto #${id}: "${post.title}"...\n`);

  const message = await client.messages.create({
    model: process.env.CLAUDE_MODEL || 'claude-sonnet-4-20250514',
    max_tokens: 4000,
    system: SYSTEM_PROMPT,
    messages: [
      { role: 'user', content: USER_PROMPT(post) }
    ]
  });

  const raw = message.content[0].text.trim();

  let result;
  try {
    result = JSON.parse(raw);
  } catch {
    const cleaned = raw.replace(/^```json\n?/, '').replace(/\n?```$/, '');
    result = JSON.parse(cleaned);
  }

  // Imprimir prompts en consola listos para copiar
  console.log('═'.repeat(60));
  console.log(`🎨 PROMPTS HIGGSFIELD — Concepto #${id}: "${post.title}"`);
  console.log('═'.repeat(60));
  console.log(`\n🔒 SEED SUGERIDO: ${result.seed_suggestion}`);
  console.log(`   (${result.seed_rationale})`);
  console.log(`   → Usa este seed en TODOS los frames para consistencia del avatar\n`);
  console.log('─'.repeat(60));

  for (const p of result.higgsfield_prompts) {
    console.log(`\n📸 FRAME ${p.frame} — ${p.focal_length}, ${p.aperture}`);
    console.log('─'.repeat(40));
    console.log('POSITIVE:');
    console.log(p.prompt);
    console.log('\nNEGATIVE:');
    console.log(p.negative_prompt);
    console.log('');
  }

  console.log('═'.repeat(60));
  console.log('🎬 PROMPT KLING AI (animación Frame 1)');
  console.log('═'.repeat(60));
  console.log(`Duración: ${result.kling_prompt.duration_seconds}s`);
  console.log(`Cámara: ${result.kling_prompt.camera_movement}`);
  console.log(`Movimiento: ${result.kling_prompt.motion_subject}`);
  console.log('\nPROMPT:');
  console.log(result.kling_prompt.prompt);
  console.log(`\n🎵 Audio en edición: ${result.kling_prompt.audio_note}`);
  console.log('═'.repeat(60));
  console.log(`\n➡️  Siguiente paso: node run captions --id=${id}`);

  return result;
}
