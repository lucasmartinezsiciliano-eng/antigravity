/**
 * engine/drops.js
 * Genera un "drop" mensual completo: 4 posts del mismo perfume, distintas localizaciones
 *
 * La lógica: cada mes un perfume protagonista.
 * 4 posts = 4 localizaciones distintas en el mundo, 4 modos distintos, progresión narrativa.
 * El perfume se descubre desde ángulos completamente diferentes.
 *
 * Estructura de un drop:
 * - Post 1: HOOK — la primera impresión más impactante
 * - Post 2: ANIMAL — siempre el más viral, con animal como invasor
 * - Post 3: DECLARACIÓN — modo C, más íntimo y absurdo
 * - Post 4: CIERRE WTF — el más inesperado, deja a la gente queriendo el próximo mes
 */

import Anthropic from '@anthropic-ai/sdk';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import 'dotenv/config';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

function loadPosts() {
  const p = join(ROOT, 'data', 'posts.json');
  return existsSync(p) ? JSON.parse(readFileSync(p, 'utf-8')) : [];
}

const SYSTEM_PROMPT = `Eres el director creativo de un AI influencer de perfumes de nicho.
Tu trabajo es diseñar drops mensuales: 4 posts del mismo perfume en 4 localizaciones distintas del mundo.

FÓRMULA REAL DE @kczco (referencia):
- fishing time. → bosque/río en Suiza, oso grizzly en frame 7 → 110k likes
- too hot here. → Sahara Desert, camello con las llaves → 48k likes
- sorry i was hungry. → mercado de Barcelona, abuelos atacando con naranjas → 27k likes
- i love my chickens. → granja de Suiza, gallinas + huevos rotos en interior → 22k likes

ESTRUCTURA DEL DROP (4 posts):
Post 1 — HOOK GEOGRÁFICO: La localización más cinematográfica para este perfume. Modo A o B.
Post 2 — ANIMAL: El animal más inesperado que conecta con las notas del perfume. Siempre Modo A. El frame 7 tiene el punch line WTF con el animal.
Post 3 — DECLARACIÓN: Modo C. Sin caos externo. Solo ella y el frasco. La obsesión pura.
Post 4 — CIERRE WTF: La localización más absurda e inesperada. El concepto más difícil de predecir.

PARA CADA POST necesitas:
- Localización específica (ciudad/lugar real del mundo)
- El elemento invasor que nace de las notas del perfume
- La acción de la protagonista en frame 1
- El punch line WTF del frame 7
- La caption deadpan (2-4 palabras, minúsculas, punto)

Las 4 localizaciones deben ser en 4 continentes distintos cuando sea posible.
Los 4 captions deben tener voz coherente pero ninguno puede parecerse al otro.

Responde en JSON puro sin markdown.`;

export async function generateDrop({ perfume, brand, notes, price, moods = [], month }) {
  if (!process.env.ANTHROPIC_API_KEY) {
    throw new Error('Falta ANTHROPIC_API_KEY en .env');
  }

  const existingPosts = loadPosts();
  const usedLocations = existingPosts.map(p => p.localizacion).filter(Boolean);
  const usedInvasors = existingPosts.map(p => p.element_invasor).filter(Boolean);

  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

  console.log(`\n📦 Generando drop de ${month || 'este mes'} — ${perfume} · ${brand}...\n`);

  const message = await client.messages.create({
    model: process.env.CLAUDE_MODEL || 'claude-sonnet-4-20250514',
    max_tokens: 4000,
    system: SYSTEM_PROMPT,
    messages: [{
      role: 'user',
      content: `Genera el drop completo de 4 posts para este perfume.

Perfume: ${perfume}
Marca: ${brand}
Notas: ${notes.join(', ')}
Precio: ${price}€
Moods: ${moods.join(', ') || 'no especificado'}
Mes: ${month || 'próximo mes'}

Localizaciones ya usadas en posts anteriores (EVITAR): ${usedLocations.join(', ') || 'ninguna aún'}
Invasores ya usados (EVITAR REPETIR): ${usedInvasors.join(', ') || 'ninguno aún'}

Devuelve este JSON:
{
  "perfume": "${perfume}",
  "brand": "${brand}",
  "month": "${month || 'próximo mes'}",
  "drop_title": "nombre interno del drop — ej: 'Beaver Month' o 'El mes del desierto'",
  "drop_narrative": "en 2 frases: qué historia cuentan estos 4 posts juntos sobre el perfume",
  "posts": [
    {
      "position": 1,
      "type": "hook_geografico",
      "modo": "A",
      "localizacion": "lugar específico del mundo",
      "continent": "continente",
      "element_invasor": "qué invade y por qué viene de las notas",
      "accion_protagonista": "qué hace ella exactamente con las manos",
      "frames_summary": "descripción de los 7 frames en 1-2 frases cada uno",
      "punch_line_wtf": "el frame 7 — el elemento imposible",
      "caption": "2-4 palabras deadpan minúsculas con punto",
      "viral_mechanic": "por qué este post haría que la gente lo comparta"
    },
    {
      "position": 2,
      "type": "animal",
      "modo": "A",
      "localizacion": "lugar específico del mundo",
      "continent": "continente",
      "animal": "qué animal y por qué conecta con las notas del perfume",
      "element_invasor": "descripción del invasor con el animal protagonista",
      "accion_protagonista": "qué hace ella con el animal",
      "frames_summary": "descripción de los 7 frames",
      "punch_line_wtf": "el giro imposible con el animal en frame 7",
      "caption": "2-4 palabras deadpan",
      "viral_mechanic": "por qué este es el más viral del drop"
    },
    {
      "position": 3,
      "type": "declaracion",
      "modo": "C",
      "localizacion": "lugar específico",
      "continent": "continente",
      "element_invasor": "mínimo o nulo — es el post más limpio",
      "accion_protagonista": "qué hace ella sola con el frasco",
      "frames_summary": "descripción de los 7 frames — más íntimos",
      "punch_line_wtf": "el detalle absurdo que rompe la intimidad",
      "caption": "declaración de amor irracional — 3-4 palabras",
      "viral_mechanic": "por qué este post genera saves y comentarios de identificación"
    },
    {
      "position": 4,
      "type": "cierre_wtf",
      "modo": "B",
      "localizacion": "la más inesperada del drop",
      "continent": "continente",
      "element_invasor": "el más absurdo e impredecible del drop",
      "accion_protagonista": "qué hace ella",
      "frames_summary": "descripción de los 7 frames",
      "punch_line_wtf": "el cierre que deja a la gente queriendo el próximo drop",
      "caption": "2-4 palabras",
      "viral_mechanic": "cómo cierra la narrativa del mes"
    }
  ],
  "publishing_schedule": {
    "post_1": "semana 1 — lunes o martes",
    "post_2": "semana 2 — mejor día para el animal (normalmente martes o miércoles)",
    "post_3": "semana 3",
    "post_4": "semana 4 — cierre de mes"
  },
  "outreach_angle": "qué ángulo específico usar para pitchear a ${brand} con este drop como muestra"
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

  // Guardar el drop en un archivo
  const dropFile = join(ROOT, 'data', `drop_${brand.toLowerCase().replace(/\s+/g, '_')}_${Date.now()}.json`);
  writeFileSync(dropFile, JSON.stringify(result, null, 2));

  // Imprimir
  console.log('═'.repeat(60));
  console.log(`📦 DROP: ${result.drop_title}`);
  console.log(`   ${perfume} · ${brand} — ${result.month}`);
  console.log('═'.repeat(60));
  console.log(`\n📖 Narrativa: ${result.drop_narrative}\n`);

  for (const post of result.posts) {
    const icons = { hook_geografico: '🌍', animal: '🐾', declaracion: '❤️', cierre_wtf: '💣' };
    const icon = icons[post.type] || '📸';
    console.log(`${icon} POST ${post.position} — ${post.type.toUpperCase()} [Modo ${post.modo}]`);
    console.log(`   📍 ${post.localizacion} (${post.continent})`);
    console.log(`   💥 ${post.element_invasor}`);
    console.log(`   🙋 Ella: ${post.accion_protagonista}`);
    console.log(`   💣 WTF: ${post.punch_line_wtf}`);
    console.log(`   💬 "${post.caption}"`);
    console.log(`   🚀 ${post.viral_mechanic}\n`);
  }

  console.log('─'.repeat(60));
  console.log('📅 CALENDARIO:');
  Object.entries(result.publishing_schedule).forEach(([k, v]) => {
    const n = k.replace('post_', '');
    const post = result.posts.find(p => p.position === parseInt(n));
    console.log(`  Semana ${n}: "${post?.caption}" — ${v}`);
  });

  console.log('\n🤝 OUTREACH ANGLE:');
  console.log(`  ${result.outreach_angle}`);
  console.log('═'.repeat(60));
  console.log(`\n💾 Drop guardado en: data/drop_${brand.toLowerCase().replace(/\s+/g, '_')}_*.json`);
  console.log(`\n➡️  Para desarrollar cada post:`);
  console.log(`   node run concept --perfume="${perfume}" --brand="${brand}" --notes="${notes.join(',')}" --price=${price} --mode=A`);

  return result;
}
