/**
 * outreach/finder.js
 * Genera lista de marcas candidatas para outreach basado en perfil de la cuenta
 *
 * Criterios para una buena marca target:
 * - Nicho / indie / lujo accesible (no mass market)
 * - Instagram < 500k seguidores (más receptivos a nano/micro influencers)
 * - No tienen AI influencer todavía (ventaja de ser los primeros)
 * - Precio >80€ / fragancia (señal de nicho real)
 * - Notas visuales (perfumes que se pueden representar físicamente)
 */

import Anthropic from '@anthropic-ai/sdk';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import 'dotenv/config';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

function loadBrands() {
  const p = join(ROOT, 'data', 'brands.json');
  return existsSync(p) ? JSON.parse(readFileSync(p, 'utf-8')) : [];
}

function saveBrands(brands) {
  writeFileSync(join(ROOT, 'data', 'brands.json'), JSON.stringify(brands, null, 2));
}

const SYSTEM_PROMPT = `Eres un estratega de marketing para un AI influencer de perfumes de nicho en Instagram.
Tu trabajo es identificar casas de perfumería de nicho que serían candidatas perfectas para una colaboración.

Criterios clave:
- Casas nicho / indie con precios >80€/fragancia
- Instagram entre 10k-500k seguidores (receptivas a nano-influencers con engagement alto)
- Aún no han trabajado con AI influencers (ventana de oportunidad)
- Fragancias con notas visuales y fotogénicas
- Preferiblemente europeas (España, Francia, Italia, UK, Alemania, Países Nórdicos)

NUNCA sugerir: LVMH/Puig/Coty mainstream, drugstore brands, marcas de supermercado.

Responde en JSON puro sin markdown.`;

export async function findBrands(limit = 20) {
  if (!process.env.ANTHROPIC_API_KEY) {
    throw new Error('Falta ANTHROPIC_API_KEY en .env');
  }

  const existing = loadBrands();
  const existingNames = existing.map(b => b.name);

  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

  console.log(`\n🔍 Buscando ${limit} marcas candidatas para outreach...`);
  console.log(`   Ya en base de datos: ${existingNames.join(', ')}\n`);

  const message = await client.messages.create({
    model: process.env.CLAUDE_MODEL || 'claude-sonnet-4-20250514',
    max_tokens: 3000,
    system: SYSTEM_PROMPT,
    messages: [{
      role: 'user',
      content: `Genera ${limit} casas de perfumería de nicho candidatas para outreach.

Ya tenemos en nuestra base de datos: ${existingNames.join(', ')}
NO repetir ninguna de estas.

Para cada marca, proporciona:
{
  "brands": [
    {
      "name": "nombre exacto de la marca",
      "instagram": "@handle",
      "email_guess": "formato típico — ej: info@marca.com o press@marca.com",
      "price_range": "ej: 120-250",
      "followers_ig": 85000,
      "country": "país de origen",
      "notable_fragrances": ["frag1", "frag2"],
      "visual_notes": ["nota1 fotogénica", "nota2"],
      "why_perfect": "en 1 frase: por qué son candidatos perfectos para este tipo de contenido",
      "contact_angle": "el ángulo específico con el que pitchear a esta marca",
      "has_ai_influencer": false,
      "priority": "high|medium|low"
    }
  ]
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

  // Añadir a brands.json solo las nuevas
  const brands = loadBrands();
  let added = 0;

  for (const b of result.brands) {
    if (!brands.find(existing => existing.name === b.name)) {
      brands.push({
        id: `brand_${String(brands.length + 1).padStart(3, '0')}`,
        name: b.name,
        instagram: b.instagram,
        email: b.email_guess || '',
        price_range: b.price_range,
        followers_ig: b.followers_ig,
        country: b.country,
        notable_fragrances: b.notable_fragrances,
        visual_notes: b.visual_notes,
        why_perfect: b.why_perfect,
        contact_angle: b.contact_angle,
        has_ai_influencer: b.has_ai_influencer || false,
        status: 'pending',
        priority: b.priority || 'medium',
        notes: '',
        notion_page_id: null
      });
      added++;
    }
  }

  saveBrands(brands);

  // Imprimir resultados
  console.log('═'.repeat(60));
  console.log(`🔍 ${result.brands.length} marcas encontradas — ${added} nuevas añadidas a brands.json`);
  console.log('═'.repeat(60));

  const sorted = result.brands.sort((a, b) => {
    const order = { high: 0, medium: 1, low: 2 };
    return order[a.priority] - order[b.priority];
  });

  for (const b of sorted) {
    const prio = b.priority === 'high' ? '🔴' : b.priority === 'medium' ? '🟡' : '🟢';
    console.log(`\n${prio} ${b.name} (${b.country}) — ${b.instagram}`);
    console.log(`   Seguidores: ~${b.followers_ig?.toLocaleString()} | Precio: ${b.price_range}€`);
    console.log(`   Notas visuales: ${b.visual_notes?.join(', ')}`);
    console.log(`   Por qué: ${b.why_perfect}`);
    console.log(`   Ángulo: ${b.contact_angle}`);
  }

  console.log('\n' + '═'.repeat(60));
  console.log(`\n➡️  Para generar pitch de una marca:`);
  console.log('   node run outreach pitch --brand=brand_XXX');

  return result.brands;
}
