/**
 * engine/captions.js
 * Concepto → 5 variantes de caption deadpan para Instagram
 *
 * REGLAS ABSOLUTAS (del análisis de @kczco):
 * - 2-4 palabras máximo
 * - Deadpan — nunca explica, nunca exagera, nunca es descriptivo
 * - No menciona el perfume ni la marca NUNCA
 * - Siempre en minúsculas con punto al final
 * - Estilo: "fishing time." / "i love my chickens." / "sorry i was hungry."
 * - Tag fijo al final: kcz + @[ig_marca]
 *
 * MEJORA: genera también 2 variantes "absurdist" más extremas para TikTok
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

function loadBrands() {
  const p = join(ROOT, 'data', 'brands.json');
  return existsSync(p) ? JSON.parse(readFileSync(p, 'utf-8')) : [];
}

const SYSTEM_PROMPT = `Eres el escritor de captions del Instagram @kczco — un AI influencer de perfumes de nicho.

El estilo es deadpan extremo. La referencia es @kczco en Instagram.

EJEMPLOS REALES de @kczco (posts con sus métricas reales):
- "fishing time." → 110k likes (ella pescando desde el Porsche, lanzando pez a un oso)
- "too hot here." → 48k likes (Porsche enterrado en el Sahara)
- "sorry i was hungry." → 27.9k likes (destrozó un mercado de naranjas en Barcelona)
- "i love my chickens." → 22.5k likes (gallinas en el Porsche en una granja)
- "i love my bmw." → 17.9k likes (BMW rosa cubierto de nieve, camiseta "I LOVE MY BMW MORE THAN YOU")
- "it's cold outside." → 12.2k likes (durmiendo en cartón junto al GT-R rosa en la nieve)
- "tropical vibes." → 904 likes (Brasil — la más baja, demasiado descriptiva)

PATRÓN DE LAS QUE FUNCIONAN:
- Las mejores captions describen la ACCIÓN del avatar como si fuera totalmente normal ("fishing time", "sorry i was hungry")
- Las declaraciones de amor absurdo también funcionan ("i love my chickens", "i love my bmw")
- Las que describen el ambiente funcionan menos ("tropical vibes" = 904 likes vs 110k)
- El objeto amado NUNCA se menciona directamente — solo la acción o la declaración

REGLAS ABSOLUTAS:
1. Máximo 4 palabras (idealmente 2-3)
2. Siempre en minúsculas
3. Siempre termina en punto
4. NUNCA menciona el perfume, la marca, ni ningún producto
5. NUNCA explica lo que pasa en la imagen
6. NUNCA tiene hashtags de perfume o moda
7. El humor viene de la indiferencia total ante una situación absurda
8. Puede referirse al elemento invasor de forma oblicua pero nunca directa

Responde en JSON puro sin markdown.`;

const USER_PROMPT = (post, brandInstagram) => `
Genera captions para este concepto:

Escena: ${post.concept_summary}
Elemento invasor: ${post.element_invasor}
Caption seed sugerido: "${post.caption_seed}"
Tag de marca: kcz + ${brandInstagram}

Genera exactamente este JSON:
{
  "concept_id": "${post.id}",
  "captions": [
    "caption 1.\\nkcz + ${brandInstagram}",
    "caption 2.\\nkcz + ${brandInstagram}",
    "caption 3.\\nkcz + ${brandInstagram}",
    "caption 4.\\nkcz + ${brandInstagram}",
    "caption 5.\\nkcz + ${brandInstagram}"
  ],
  "tiktok_captions": [
    "caption más extrema para TikTok 1.\\n#perfume #niche #${post.brand.toLowerCase().replace(/\s+/g, '')}",
    "caption más extrema para TikTok 2.\\n#perfume #niche #${post.brand.toLowerCase().replace(/\s+/g, '')}"
  ],
  "recommended": 0,
  "recommended_reason": "por qué esta es la mejor (índice 0-4)"
}

Los captions de TikTok pueden ser ligeramente más largos (hasta 6 palabras) y con más actitud, pero mismo estilo deadpan.`;

export async function generateCaptions(id) {
  if (!process.env.ANTHROPIC_API_KEY) {
    throw new Error('Falta ANTHROPIC_API_KEY en .env');
  }

  const post = loadPost(id);
  const brands = loadBrands();
  const brand = brands.find(b => b.name === post.brand);
  const brandInstagram = brand ? brand.instagram : `@${post.brand.toLowerCase().replace(/\s+/g, '')}`;

  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

  console.log(`\n✍️  Generando captions para concepto #${id}: "${post.title}"...\n`);

  const message = await client.messages.create({
    model: process.env.CLAUDE_MODEL || 'claude-sonnet-4-20250514',
    max_tokens: 1000,
    system: SYSTEM_PROMPT,
    messages: [
      { role: 'user', content: USER_PROMPT(post, brandInstagram) }
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
  console.log(`✍️  CAPTIONS — Concepto #${id}: "${post.title}"`);
  console.log('═'.repeat(60));
  console.log('\n📱 INSTAGRAM (elige una):\n');
  result.captions.forEach((c, i) => {
    const star = i === result.recommended ? ' ⭐ RECOMENDADA' : '';
    console.log(`  [${i}]${star}`);
    console.log(`  ${c.replace('\n', ' | ')}\n`);
  });

  console.log('─'.repeat(60));
  console.log('\n🎵 TIKTOK:\n');
  result.tiktok_captions.forEach((c, i) => {
    console.log(`  [T${i}]`);
    console.log(`  ${c.replace('\n', ' | ')}\n`);
  });

  console.log('─'.repeat(60));
  console.log(`💡 Recomendada: [${result.recommended}] — ${result.recommended_reason}`);
  console.log('═'.repeat(60));
  console.log(`\n➡️  Siguiente: node run publish instagram --id=${id} --images="f1.jpg,f2.jpg,..." --caption="${result.captions[result.recommended].split('\n')[0]}"`);

  return result;
}
