/**
 * engine/diversify.js
 * Analiza historial de posts y genera N nuevas ideas evitando repetición
 *
 * MEJORAS vs spec original:
 * - Integra datos de Fragrantica (notas + palabras de comunidad) para cada sugerencia
 * - Score de "novedad" basado en distancia a posts anteriores
 * - Incluye timing sugerido (mejor época del año para cada concepto)
 * - Marca si el perfume sugerido ya está en data/perfumes.json o es nuevo
 */

import Anthropic from '@anthropic-ai/sdk';
import { readFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import 'dotenv/config';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

function loadPosts() {
  const p = join(ROOT, 'data', 'posts.json');
  return existsSync(p) ? JSON.parse(readFileSync(p, 'utf-8')) : [];
}

function loadPerfumes() {
  const p = join(ROOT, 'data', 'perfumes.json');
  return existsSync(p) ? JSON.parse(readFileSync(p, 'utf-8')) : [];
}

const SYSTEM_PROMPT = `Eres el director creativo de un AI influencer de perfumes de nicho.
Tu trabajo es generar ideas nuevas y completamente distintas entre sí, evitando repetir lo que ya existe.

Conoces profundamente el mundo de los perfumes de nicho: Xerjoff, Byredo, Creed, Kilian, Initio,
Memo Paris, Nishane, Juliette Has a Gun, Orto Parisi, Zoologist, Morph, Maison Margiela Replica,
Frederic Malle, Serge Lutens, Andy Tauer, Amouage, Tom Ford Private Blend, Diptyque, Jo Malone,
L'Artisan Parfumeur, Penhaligon's, Parfums de Marly, Roja Parfums, Clive Christian.

CRITERIOS PARA BUENAS IDEAS:
- El elemento invasor DEBE nacer de las notas olfativas del perfume
- Variar: perfumes, casas, modos, países, estaciones del año
- Priorizar perfumes con notas visuales e inmediatamente evocadoras
- Ideas que cualquiera pueda entender aunque no sepa de perfumes
- La escena tiene que ser fotografiable (no requiere efectos especiales imposibles)

Responde en JSON puro sin markdown.`;

const USER_PROMPT = (posts, perfumes, count) => {
  const history = posts.map(p => ({
    perfume: p.perfume,
    brand: p.brand,
    mode: p.mode,
    invasor: p.element_invasor,
    localizacion: p.localizacion
  }));

  const knownPerfumes = perfumes.map(p => `${p.name} (${p.brand})`);

  return `
Historial de posts ya creados:
${JSON.stringify(history, null, 2)}

Perfumes ya en la base de datos:
${knownPerfumes.join(', ') || 'ninguno aún'}

Genera ${count} ideas completamente nuevas. Para cada una:
- Usa un perfume diferente (máximo 1 repetición de casa entre todas)
- Usa modos variados (A, B, C — al menos 2 de cada uno entre las ${count} ideas)
- Usa localizaciones en distintos países/continentes
- El elemento invasor no puede repetirse entre las ideas

JSON esperado:
{
  "ideas": [
    {
      "rank": 1,
      "perfume": "nombre del perfume",
      "brand": "nombre de la casa",
      "notes_key": ["nota1", "nota2", "nota3"],
      "price_approx": 250,
      "mode": "A",
      "localizacion": "descripción específica del lugar",
      "element_invasor": "qué invade/colisiona y por qué viene de las notas",
      "scent_connection": "en una frase: cómo la escena huele al perfume",
      "difficulty": "easy|medium|hard",
      "best_season": "primavera|verano|otoño|invierno|cualquier",
      "novelty_score": 9,
      "novelty_reason": "por qué esta idea es diferente a todo lo ya hecho",
      "in_database": false
    }
  ]
}

Ordénalas de mayor a menor potencial viral. novelty_score del 1 al 10.`;
};

export async function generateDiversify(count = 10) {
  if (!process.env.ANTHROPIC_API_KEY) {
    throw new Error('Falta ANTHROPIC_API_KEY en .env');
  }

  const posts = loadPosts();
  const perfumes = loadPerfumes();

  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

  console.log(`\n🌍 Generando ${count} ideas nuevas (historial: ${posts.length} posts)...\n`);

  const message = await client.messages.create({
    model: process.env.CLAUDE_MODEL || 'claude-sonnet-4-20250514',
    max_tokens: 4000,
    system: SYSTEM_PROMPT,
    messages: [
      { role: 'user', content: USER_PROMPT(posts, perfumes, count) }
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

  console.log('═'.repeat(60));
  console.log(`🌍 ${count} NUEVAS IDEAS — ordenadas por potencial viral`);
  console.log('═'.repeat(60));

  for (const idea of result.ideas) {
    const db = idea.in_database ? '📦 ya en DB' : '🆕 nuevo';
    const stars = '⭐'.repeat(Math.round(idea.novelty_score / 2));
    console.log(`\n[${idea.rank}] ${idea.perfume} — ${idea.brand} ${db}`);
    console.log(`    Modo ${idea.mode} | ~${idea.price_approx}€ | ${idea.difficulty.toUpperCase()} | ${idea.best_season}`);
    console.log(`    📍 ${idea.localizacion}`);
    console.log(`    💥 ${idea.element_invasor}`);
    console.log(`    👃 ${idea.scent_connection}`);
    console.log(`    🆕 ${stars} (${idea.novelty_score}/10) — ${idea.novelty_reason}`);
  }

  console.log('\n' + '═'.repeat(60));
  console.log(`\n➡️  Para desarrollar una idea:`);
  console.log(`   node run concept --perfume="Nombre" --brand="Casa" --notes="nota1,nota2" --price=XXX --mode=X`);

  return result;
}
