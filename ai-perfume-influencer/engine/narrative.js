/**
 * engine/narrative.js
 * Genera contenido Middle of Funnel — el avatar habla de perfumes
 *
 * NO es marketing. NO describe notas técnicas. NO explica el proceso.
 * ES la relación irracional del avatar con un perfume específico.
 *
 * Formatos:
 * - "opinion"   → opinión corta y directa sobre el perfume (para caption largo ocasional)
 * - "ranking"   → clasifica varios perfumes de una casa o familia olfativa
 * - "moment"    → qué situación/momento evoca este perfume, descrito deadpan
 * - "comparison"→ este perfume vs otro. Sin diplomacia.
 * - "obsession" → por qué llevas este perfume aunque no tenga sentido lógico
 * - "olfactory" → hace sentir el olor sin tenerlo físicamente. Sinestesia, memoria, sensación corporal.
 */

import Anthropic from '@anthropic-ai/sdk';
import { readFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import 'dotenv/config';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

function loadPerfumes() {
  const p = join(ROOT, 'data', 'perfumes.json');
  return existsSync(p) ? JSON.parse(readFileSync(p, 'utf-8')) : [];
}

const SYSTEM_PROMPT = `Eres el avatar de un AI influencer de perfumes de nicho en Instagram.
Tu voz es la de alguien que conoce profundamente los perfumes de nicho y tiene opiniones fuertes sobre ellos.

QUIÉN ERES:
- Llevas perfumes de nicho porque son los únicos que te dicen algo
- Tienes opiniones irracionales y las defiendes sin disculparte
- No usas vocabulario de perfumista. Nunca dices "notas de salida" ni "acorde".
- No explicas el perfume. Lo describes como si fuera una persona o una situación.
- Tu humor es seco. Tu amor por ciertos perfumes es absurdo y total.

REFERENCIAS DE VOZ (cómo suenas):
- "Llevo Torino 21 cuando quiero que la gente crea que tengo el control de algo."
- "Hay perfumes que huelen a dinero. Creed Aventus huele a alguien que habla de su dinero."
- "Si todavía llevas One Million en 2026 no me interesa lo que tengas que decir."
- "Sloth de Zoologist huele a lo que pasa si te quedas dormida en un bosque y nadie te busca."
- "Byredo Gypsy Water es el perfume de gente que llama 'bohemia' a no tener Wi-Fi."
- "Black Afgano de Nasomatto huele a una conversación que no recuerdas pero sabes que fue importante."

REGLAS:
- Máximo 4-5 frases por pieza
- Nunca mencionar precio salvo para hacer un punto sobre el absurdo de pagarlo
- Nunca comparar con perfumes de supermercado o mass market como referencia positiva
- Nunca sonar como una reseña ni como un anuncio
- Siempre en inglés o en español según se indique
- Si es un ranking, máximo 5 items, siempre con criterio absurdo pero coherente

Responde en JSON puro sin markdown.`;

const FORMATS = {
  opinion: (perfume, brand, notes) => `
Genera una opinión corta y directa sobre este perfume.
No describes notas. Describes lo que hace este perfume a quien lo lleva o a quien lo rodea.

Perfume: ${perfume} de ${brand}
Notas: ${notes?.join(', ') || 'no especificado'}

JSON:
{
  "format": "opinion",
  "perfume": "${perfume}",
  "brand": "${brand}",
  "text_es": "la opinión en español — 3-5 frases, voz del avatar",
  "text_en": "la opinión en inglés — 3-5 frases, voz del avatar",
  "caption_ig": "versión para caption de Instagram — máximo 3 frases + kcz ♦ @${brand.toLowerCase().replace(/\s+/g, '')}",
  "caption_ig_en": "versión en inglés para caption",
  "hook": "la primera frase sola — debe ser lo suficientemente rara para hacer que alguien pare el scroll"
}`,

  moment: (perfume, brand, notes) => `
Genera un "momento" — la situación/escena específica donde este perfume tiene sentido.
No es un momento romantico ni aspiracional. Es una situación concreta y ligeramente absurda.

Perfume: ${perfume} de ${brand}
Notas: ${notes?.join(', ') || 'no especificado'}

JSON:
{
  "format": "moment",
  "perfume": "${perfume}",
  "brand": "${brand}",
  "text_es": "el momento en español — describe la situación, 3-4 frases",
  "text_en": "en inglés",
  "caption_ig": "versión comprimida para Instagram — máximo 2 frases + kcz ♦ @${brand.toLowerCase().replace(/\s+/g, '')}",
  "caption_ig_en": "en inglés",
  "hook": "la primera frase — tiene que ser una situación específica que nadie esperaba"
}`,

  obsession: (perfume, brand, notes) => `
Genera el texto de "obsesión" — por qué el avatar lleva este perfume aunque no tenga sentido lógico.
El argumento tiene que ser irrefutable dentro de su lógica propia aunque suene absurdo.

Perfume: ${perfume} de ${brand}
Notas: ${notes?.join(', ') || 'no especificado'}

JSON:
{
  "format": "obsession",
  "perfume": "${perfume}",
  "brand": "${brand}",
  "text_es": "la obsesión en español — 3-5 frases, declaración irracional pero coherente",
  "text_en": "en inglés",
  "caption_ig": "comprimido para caption + kcz ♦ @${brand.toLowerCase().replace(/\s+/g, '')}",
  "caption_ig_en": "en inglés",
  "hook": "primera frase — debe sonar a declaración de amor ligeramente perturbadora"
}`,

  comparison: (perfume1, brand1, perfume2, brand2) => `
Genera una comparación entre dos perfumes. Sin diplomacia.
El avatar tiene una preferencia clara y la defiende.

Perfume A: ${perfume1} de ${brand1}
Perfume B: ${perfume2} de ${brand2}

JSON:
{
  "format": "comparison",
  "winner": "${perfume1} o ${perfume2}",
  "text_es": "la comparación en español — 4-5 frases, punto de vista claro y sin disculpas",
  "text_en": "en inglés",
  "caption_ig": "comprimido — la conclusión en 2 frases máximo + kcz ♦ @ganador",
  "caption_ig_en": "en inglés",
  "hook": "primera frase — debe iniciar el debate"
}`,

  olfactory: (perfume, brand, notes) => `
Genera una experiencia olfativa inmersiva. El objetivo es que alguien que NUNCA ha olido este perfume
sienta físicamente el olor en su nariz mientras lee. No uses vocabulario técnico de perfumería.
Usa sinestesia, memoria sensorial, temperatura, textura, sonido, color.
Haz que el lector sienta el perfume en el cuerpo aunque esté en casa.

Perfume: ${perfume} de ${brand}
Notas: ${notes?.join(', ') || 'no especificado'}

TÉCNICAS A USAR (elige las que funcionen mejor):
- Sinestesia: "huele como suena el silencio en un edificio vacío"
- Temperatura: "el primer segundo es frío como metal, luego calienta"
- Textura: "huele a terciopelo que se ha mojado"
- Color: "si el olor tuviera color sería marrón dorado con bordes negros"
- Memoria compartida: algo que todos hemos olido y que evoca la misma sensación
- Sensación corporal: dónde lo sientes físicamente (garganta, fosas nasales, pecho)
- Progresión en el tiempo: cómo cambia en los primeros 10 minutos en piel

JSON:
{
  "format": "olfactory",
  "perfume": "${perfume}",
  "brand": "${brand}",
  "first_impression": "lo que la nariz siente en el segundo 0 — 1 frase breve y física",
  "body": "la experiencia completa — 4-6 frases usando sinestesia y memoria corporal, en español",
  "body_en": "en inglés",
  "progression": "cómo evoluciona en los primeros 15 minutos en piel — 2 frases",
  "caption_ig": "versión comprimida para Instagram — máximo 3 frases que hagan oler al lector + kcz ♦ @${brand.toLowerCase().replace(/\s+/g, '')}",
  "caption_ig_en": "en inglés",
  "hook": "primera frase — tan física y concreta que quien la lea casi estornude"
}`,

  ranking: (perfumes_list, criterio) => `
Genera un ranking de estos perfumes con el criterio dado.
El criterio puede ser absurdo pero el ranking tiene que ser coherente dentro de esa lógica.

Perfumes: ${perfumes_list}
Criterio: ${criterio}

JSON:
{
  "format": "ranking",
  "criterio": "${criterio}",
  "ranking": [
    { "position": 1, "perfume": "nombre", "brand": "marca", "reason": "por qué en esta posición — 1 frase, seca" }
  ],
  "caption_ig": "el ranking completo formateado para Instagram — con números, frases cortas",
  "caption_ig_en": "en inglés",
  "hook": "frase de introducción al ranking — tiene que hacer que la gente quiera ver la lista completa"
}`
};

export async function generateNarrative({ format, perfume, brand, notes, perfume2, brand2, perfumes_list, criterio }) {
  if (!process.env.ANTHROPIC_API_KEY) {
    throw new Error('Falta ANTHROPIC_API_KEY en .env');
  }

  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

  let userPrompt;
  switch (format) {
    case 'opinion':
      userPrompt = FORMATS.opinion(perfume, brand, notes);
      break;
    case 'moment':
      userPrompt = FORMATS.moment(perfume, brand, notes);
      break;
    case 'obsession':
      userPrompt = FORMATS.obsession(perfume, brand, notes);
      break;
    case 'comparison':
      if (!perfume2 || !brand2) throw new Error('comparison requiere --perfume2 y --brand2');
      userPrompt = FORMATS.comparison(perfume, brand, perfume2, brand2);
      break;
    case 'olfactory':
      userPrompt = FORMATS.olfactory(perfume, brand, notes);
      break;
    case 'ranking':
      if (!perfumes_list || !criterio) throw new Error('ranking requiere --perfumes y --criterio');
      userPrompt = FORMATS.ranking(perfumes_list, criterio);
      break;
    default:
      throw new Error(`Formato desconocido: ${format}. Usa: opinion | moment | obsession | comparison | ranking`);
  }

  console.log(`\n🖊️  Generando ${format} — ${perfume || 'ranking'}...\n`);

  const message = await client.messages.create({
    model: process.env.CLAUDE_MODEL || 'claude-sonnet-4-20250514',
    max_tokens: 1000,
    system: SYSTEM_PROMPT,
    messages: [{ role: 'user', content: userPrompt }]
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
  console.log(`🖊️  NARRATIVA — ${format.toUpperCase()}`);
  if (perfume) console.log(`   ${perfume} · ${brand}`);
  console.log('═'.repeat(60));

  console.log('\n🪝 HOOK:');
  console.log(`   "${result.hook}"`);

  console.log('\n📝 TEXTO (ES):');
  console.log(result.text_es || result.caption_ig);

  if (result.text_en) {
    console.log('\n📝 TEXTO (EN):');
    console.log(result.text_en);
  }

  if (result.ranking) {
    console.log('\n🏆 RANKING:');
    result.ranking.forEach(r => console.log(`  ${r.position}. ${r.perfume} (${r.brand}) — ${r.reason}`));
  }

  console.log('\n📱 CAPTION INSTAGRAM (ES):');
  console.log(result.caption_ig);

  console.log('\n📱 CAPTION INSTAGRAM (EN):');
  console.log(result.caption_ig_en);

  console.log('═'.repeat(60));
  return result;
}
