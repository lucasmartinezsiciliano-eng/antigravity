/**
 * engine/concept.js
 * Perfume → Concepto completo con 8 frames (optimizado para algoritmo 2026)
 *
 * MEJORAS vs spec original:
 * - 8 frames (vs 6-7) → sweet spot algoritmo 2026: más swipe events = más distribución
 * - Open-loop technique: pregunta implícita en frame 1, respuesta en frame 5
 * - Escena inspirada en moods/palabras de comunidad Fragrantica, no solo notas
 * - Difficulty score para que el usuario planifique la sesión de rodaje
 * - Seed suggestion para consistencia de personaje en Higgsfield
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

function savePosts(posts) {
  writeFileSync(join(ROOT, 'data', 'posts.json'), JSON.stringify(posts, null, 2));
}

function loadPerfumes() {
  const p = join(ROOT, 'data', 'perfumes.json');
  return existsSync(p) ? JSON.parse(readFileSync(p, 'utf-8')) : [];
}

function savePerfumes(perfumes) {
  writeFileSync(join(ROOT, 'data', 'perfumes.json'), JSON.stringify(perfumes, null, 2));
}

function nextId(posts) {
  if (posts.length === 0) return '001';
  const last = Math.max(...posts.map(p => parseInt(p.id, 10)));
  return String(last + 1).padStart(3, '0');
}

const SYSTEM_PROMPT = `Eres el director creativo de un AI influencer de perfumes de nicho en Instagram.
Tu referencia exacta es @kczco — un AI influencer viral que colabora con Porsche y BMW.

FÓRMULA KCZCO ANALIZADA (posts reales ordenados por engagement):
- "fishing time." 110k likes: avatar pescando en un río desde el maletero del Porsche, interior inundado de agua y peces, en el último frame lanza un pez a un oso grizzly
- "too hot here." 48k likes: Sahara Desert, Porsche enterrado en arena, camello husmeando las llaves del coche, "TOO HOT HERE" escrito en el polvo del cristal, PS5 sobre el capó
- "sorry i was hungry." 27.9k likes: Barcelona mercado, avatar comiendo una naranja mientras abuelos la atacan con naranjas, rueda con naranjas aplastadas, abuela filmando desde el balcón
- "i love my chickens." 22.5k likes: granja de Suiza, gallinas por todas partes, interior del Porsche con huevos rotos en el cambio, gallina anidando en el alerón
- "i love my bmw." 17.9k likes: BMW rosa en Nueva York, camiseta "I LOVE MY BMW MORE THAN YOU", "I ❤️ BMW" escrito en la nieve del capó
- "it's cold outside." 12.2k likes: Nissan GT-R rosa en Suiza nevada, avatar durmiendo en cartón junto al coche, gato blanco en el alerón

FÓRMULA REAL EXTRAÍDA:
1. EL FRASCO = EL PORSCHE. Es el objeto de devoción absoluto. Siempre perfecto. Siempre presente. Nunca se toca, nunca se daña.
2. LA PROTAGONISTA HACE COSAS con el elemento invasor — no lo ignora pasivamente. Pesca activamente, come la naranja, sostiene la gallina. La indiferencia es tratar lo absurdo como completamente normal.
3. ANIMALES = elemento más viral. Gallinas, gatos, camello, oso grizzly. El animal interactúa con el coche/objeto como si fuera su territorio natural.
4. EL PUNCH LINE WTF en el ÚLTIMO FRAME es LO QUE HACE VIRAL. Debe ser un elemento completamente inesperado que recontextualiza todo. El oso recibiendo el pez = 110k. El camello con las llaves = 48k.
5. LOCALIZACIÓN ÉPICA REAL. La escena ocurre en un lugar específico del mundo con identidad propia: Sahara, favela de Brasil, granja de Suiza, mercado de Barcelona. La localización multiplica el alcance internacional.
6. CAPTION = describe la acción del avatar de forma que suena a excusa absurda o declaración de amor. "fishing time." "sorry i was hungry." "i love my chickens." "too hot here." Nunca describe lo que pasa visualmente.
7. EL INTERIOR DEL OBJETO DESTRUIDO es un frame obligatorio — interior del Porsche inundado, interior con huevos rotos, interior cubierto de arena. Contraste extremo entre el lujo del interior y la destrucción.

MODOS DE CONTENIDO:
MODO A — El perfume provoca un fenómeno físico/animal que invade el espacio lujoso
→ Las notas del perfume SE MATERIALIZAN físicamente y crean el caos
→ Ej: perfume de oud y madera → cedros del Líbano entran en el apartamento, ella sirviéndose té indiferente

MODO B — Colisión de clase/mundo
→ El frasco en una localización épica donde no debería existir, con elementos locales que lo adoptan como suyo
→ Ej: frasco de 400€ en un mercado de Marrakech, vendedores utilizándolo como pisapapeles

MODO C — Declaración de amor absurda
→ Sin caos externo. Solo la protagonista con una devoción irracional al frasco.
→ Caption = profesión de fe deadpan: "i love my [nombre]." o similar

REGLAS ABSOLUTAS (aprendidas del análisis):
- El frasco: NUNCA se daña, NUNCA se mancha, NUNCA está tapado o borroso
- Ella: SIEMPRE haciendo algo con las manos, NUNCA mirando el frasco con adoración, NUNCA posando estáticamente
- La destrucción/caos es siempre consecuencia de una ACCIÓN que ella hizo y considera completamente normal
- Un frame SIEMPRE muestra el interior del objeto de lujo destruido (equivalente al interior del Porsche)
- El último frame = punch line WTF con un elemento de vida animal o persona inesperada
- Fondo: noche natural, luz artificial dura o contraluz. NUNCA estudio, NUNCA blanco, NUNCA softbox visible
- La localización debe ser específica: una ciudad, un bioma, un lugar reconocible del mundo

ESTRUCTURA DE 7 FRAMES (formato real de kczco):
- Frame 1: HOOK. Ella + frasco + localización épica + elemento invasor ya en pleno caos. Ella haciendo algo con las manos.
- Frame 2: Interior del objeto de lujo destruido. Close-up del daño máximo.
- Frame 3: Ella de frente sosteniendo o interactuando con el elemento invasor. Mirada directa. Indiferente total.
- Frame 4: Close-up del elemento invasor en el punto de contacto con el frasco/objeto. Textura máxima.
- Frame 5: El frasco PERFECTO en primer plano en medio de la destrucción total. Contraste máximo.
- Frame 6: Reacción del entorno: terceros, animales, elementos locales respondiendo a la situación.
- Frame 7: PUNCH LINE WTF. El elemento más inesperado e imposible. El giro que hace que la gente comente y comparta. Animal/persona haciendo algo absurdo con el objeto de lujo.

Responde SIEMPRE en JSON puro, sin markdown, sin explicaciones fuera del JSON.`;

const USER_PROMPT = (perfume, brand, notes, price, mode, moods) => `
Genera un concepto de post para Instagram siguiendo la fórmula exacta de @kczco.

Perfume: ${perfume}
Marca: ${brand}
Notas principales: ${notes.join(', ')}
Precio: ${price}€
Modo: ${mode}
Moods/palabras de la comunidad Fragrantica: ${moods ? moods.join(', ') : 'no especificado'}

REQUISITOS:
- El elemento invasor DEBE nacer directamente de las notas olfativas del perfume (se materializa físicamente)
- La localización debe ser épica y específica (ciudad/lugar reconocible del mundo)
- El frame 7 (punch line WTF) debe ser el más inesperado e imposible de predecir desde el frame 1
- La protagonista HACE algo activamente — nunca es solo decorado
- La caption describe la ACCIÓN del avatar como si fuera lo más normal del mundo

Devuelve exactamente este JSON:
{
  "title": "2-3 palabras que capturan la idea",
  "concept_summary": "Qué pasa, qué vemos. 2-3 frases. Por qué funciona igual que kczco.",
  "element_invasor": "Qué invade la escena y por qué viene directamente de las notas del perfume",
  "localizacion": "Ciudad/lugar específico del mundo con su identidad propia",
  "accion_protagonista": "Qué hace ella con las manos en el frame 1 — verbo concreto",
  "punch_line_wtf": "Qué pasa en el frame 7 que nadie esperaba y que hará que la gente comente",
  "frames": [
    { "number": 1, "description": "Hook completo: ella (qué hace exactamente con las manos) + frasco (dónde está, cómo está) + localización (detalles físicos de la escena) + primer caos visible" },
    { "number": 2, "description": "Interior del frasco/objeto de lujo: cómo se ve por dentro o de cerca con el invasor haciéndole algo" },
    { "number": 3, "description": "Ella de frente sosteniendo/interactuando con el elemento invasor. Mirada directa a cámara. Indiferencia total." },
    { "number": 4, "description": "Close-up extremo del elemento invasor en contacto con el frasco o el objeto de lujo. Texturas." },
    { "number": 5, "description": "El frasco PERFECTO en primer plano, sin una mancha, en medio de la destrucción total del entorno." },
    { "number": 6, "description": "Reacción del entorno: personas locales, animales o elementos del lugar respondiendo al caos. Ella ausente o de espaldas." },
    { "number": 7, "description": "PUNCH LINE WTF: el elemento imposible. El giro final que hace que la gente comparta. Concreto, visual, absurdo pero fotografiable." }
  ],
  "caption_seed": "2-4 palabras deadpan en inglés, minúsculas, punto al final. Suena a excusa o declaración de amor absurda.",
  "caption_alternatives": ["opción 2", "opción 3"],
  "difficulty": "easy|medium|hard",
  "difficulty_reason": "Qué hace que sea difícil o fácil de producir con IA",
  "viral_mechanic": "Por qué este post concretamente haría que la gente lo comparta o comente",
  "scent_connection": "En una frase: por qué esta escena huele al perfume"
}`;

export async function generateConcept({ perfume, brand, notes, price, mode, moods = [] }) {
  if (!process.env.ANTHROPIC_API_KEY) {
    throw new Error('Falta ANTHROPIC_API_KEY en .env');
  }

  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

  console.log(`\n🧠 Generando concepto para ${perfume} de ${brand} — Modo ${mode}...\n`);

  const message = await client.messages.create({
    model: process.env.CLAUDE_MODEL || 'claude-sonnet-4-20250514',
    max_tokens: 2000,
    system: SYSTEM_PROMPT,
    messages: [
      { role: 'user', content: USER_PROMPT(perfume, brand, notes, price, mode, moods) }
    ]
  });

  const raw = message.content[0].text.trim();

  let concept;
  try {
    concept = JSON.parse(raw);
  } catch {
    // A veces el modelo añade ```json ... ```, intentar limpiar
    const cleaned = raw.replace(/^```json\n?/, '').replace(/\n?```$/, '');
    concept = JSON.parse(cleaned);
  }

  const posts = loadPosts();
  const id = nextId(posts);
  const now = new Date().toISOString();

  const post = {
    id,
    perfume,
    brand,
    mode,
    notes,
    price,
    ...concept,
    instagram_post_id: null,
    tiktok_post_id: null,
    status: 'concept',
    caption_chosen: null,
    images: [],
    video: null,
    created_at: now,
    published_at: null,
    metrics: {
      likes: 0,
      comments: 0,
      shares: 0,
      saves: 0,
      reach: 0,
      impressions: 0,
      engagement_rate: 0
    },
    notion_page_id: null
  };

  posts.push(post);
  savePosts(posts);

  // Actualizar contador en perfumes.json
  const perfumes = loadPerfumes();
  const idx = perfumes.findIndex(p => p.name === perfume && p.brand === brand);
  if (idx !== -1) {
    perfumes[idx].posts_generated = (perfumes[idx].posts_generated || 0) + 1;
    savePerfumes(perfumes);
  }

  // Imprimir resultado en consola
  console.log('═'.repeat(60));
  console.log(`✅ CONCEPTO #${id} GENERADO`);
  console.log('═'.repeat(60));
  console.log(`📌 Título:        ${concept.title}`);
  console.log(`📍 Modo:          ${mode}`);
  console.log(`🌍 Localización:  ${concept.localizacion}`);
  console.log(`💥 Invasor:       ${concept.element_invasor}`);
  console.log(`🙋 Ella hace:     ${concept.accion_protagonista}`);
  console.log(`💣 Punch line:    ${concept.punch_line_wtf}`);
  console.log(`🚀 Mecánica viral: ${concept.viral_mechanic}`);
  console.log(`👃 Olor:          ${concept.scent_connection}`);
  console.log(`🎬 Dificultad:    ${concept.difficulty?.toUpperCase()} — ${concept.difficulty_reason}`);
  console.log('─'.repeat(60));
  console.log(`💬 Caption:       "${concept.caption_seed}"`);
  if (concept.caption_alternatives?.length) {
    concept.caption_alternatives.forEach(c => console.log(`   alternativa:   "${c}"`));
  }
  console.log('─'.repeat(60));
  console.log('\n📋 FRAMES (7):\n');
  for (const frame of concept.frames) {
    console.log(`  [${frame.number}] ${frame.description}\n`);
  }
  console.log('═'.repeat(60));
  console.log(`💾 Guardado en data/posts.json con ID: ${id}`);
  console.log(`\n➡️  Siguiente paso: node run prompts --id=${id}`);

  return post;
}
