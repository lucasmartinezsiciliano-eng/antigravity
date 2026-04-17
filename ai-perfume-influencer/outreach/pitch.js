/**
 * outreach/pitch.js
 * Genera pitch personalizado por email para una marca
 *
 * El pitch es corto, directo y nunca suena a agencia.
 * Objetivo: conseguir que el PR de la marca quiera saber más,
 * no convencerles en el primer email.
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

function loadPosts() {
  const p = join(ROOT, 'data', 'posts.json');
  return existsSync(p) ? JSON.parse(readFileSync(p, 'utf-8')) : [];
}

const SYSTEM_PROMPT = `Escribes emails de outreach para un AI influencer de perfumes de nicho en Instagram.

El tono del influencer:
- Seria, directa, sin florituras
- Nunca suena a agencia o marketing
- Habla de su trabajo como "contenido" no como "servicio"
- No menciona métricas falsas ni exagera

REGLAS DEL EMAIL:
1. Asunto: <8 palabras, sin signos de exclamación
2. Cuerpo: máximo 5 frases. Ni una más.
3. Primera frase: referencia específica a UNA fragancia de la marca (no genérico)
4. Segunda frase: qué es el AI influencer y por qué es diferente (una oración)
5. Tercera frase: qué podría hacer con sus fragancias (muy concreto, no vago)
6. Cuarta frase (opcional): número pequeño de seguidores + engagement alto o algo diferencial
7. Última frase: CTA simple — ¿les interesa ver el perfil?
8. Firma: solo nombre + Instagram handle + link

NUNCA mencionar: "colaboración pagada", "rate card", "estadísticas", "viral", "influencer marketing"

Responde en JSON puro sin markdown.`;

export async function generatePitch(brandId) {
  if (!process.env.ANTHROPIC_API_KEY) {
    throw new Error('Falta ANTHROPIC_API_KEY en .env');
  }

  const brands = loadBrands();
  const brand = brands.find(b => b.id === brandId);
  if (!brand) throw new Error(`Marca ${brandId} no encontrada en brands.json`);

  const posts = loadPosts();
  const published = posts.filter(p => p.status === 'published');
  const postCount = published.length;

  const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

  console.log(`\n✉️  Generando pitch para ${brand.name}...\n`);

  const message = await client.messages.create({
    model: process.env.CLAUDE_MODEL || 'claude-sonnet-4-20250514',
    max_tokens: 1000,
    system: SYSTEM_PROMPT,
    messages: [{
      role: 'user',
      content: `Genera el pitch email para esta marca:

Marca: ${brand.name}
Instagram: ${brand.instagram}
País: ${brand.country || 'desconocido'}
Fragancias conocidas: ${brand.notable_fragrances?.join(', ') || 'investigar'}
Notas visuales de sus fragancias: ${brand.visual_notes?.join(', ') || ''}
Ángulo de contacto sugerido: ${brand.contact_angle || ''}
Por qué son perfectos: ${brand.why_perfect || ''}

Sobre el AI influencer:
- Handle Instagram: @${process.env.IG_HANDLE || 'kczco'}
- Cuenta de AI — el avatar es generado con IA pero el contenido es editorial oscuro y lujoso
- Posts publicados hasta ahora: ${postCount}
- Estilo: perfumes de nicho + invasiones físicas de sus notas + deadpan humor

Devuelve:
{
  "brand_id": "${brandId}",
  "subject": "asunto del email",
  "body": "cuerpo completo del email listo para enviar — incluir firma",
  "body_es": "versión en español por si el contacto es de habla hispana",
  "email_to": "${brand.email || 'press@' + brand.name.toLowerCase().replace(/\s+/g, '') + '.com'}",
  "follow_up_note": "cuándo y cómo hacer follow-up si no responden"
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

  // Guardar pitch en la marca
  const idx = brands.findIndex(b => b.id === brandId);
  brands[idx].pitch_subject = result.subject;
  brands[idx].pitch_body = result.body;
  brands[idx].pitch_generated_at = new Date().toISOString();
  saveBrands(brands);

  console.log('═'.repeat(60));
  console.log(`✉️  PITCH — ${brand.name}`);
  console.log('═'.repeat(60));
  console.log(`\n📧 PARA: ${result.email_to}`);
  console.log(`📌 ASUNTO: ${result.subject}`);
  console.log('\n─── CUERPO (EN) ─────────────────────────────────────────');
  console.log(result.body);
  console.log('\n─── CUERPO (ES) ─────────────────────────────────────────');
  console.log(result.body_es);
  console.log('\n─── FOLLOW-UP ──────────────────────────────────────────');
  console.log(result.follow_up_note);
  console.log('═'.repeat(60));
  console.log('\n💾 Pitch guardado en brands.json');

  return result;
}
