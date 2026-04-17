/**
 * notion/sync.js
 * Sincroniza posts, perfumes y brands con Notion
 *
 * Bases de datos necesarias en Notion (IDs en .env):
 * - NOTION_POSTS_DB_ID     → pipeline de contenido
 * - NOTION_PERFUMES_DB_ID  → catálogo de perfumes
 * - NOTION_BRANDS_DB_ID    → CRM de marcas / outreach
 * - NOTION_ANALYTICS_DB_ID → métricas por post
 */

import { Client } from '@notionhq/client';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import 'dotenv/config';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

function loadJSON(name) {
  const p = join(ROOT, 'data', `${name}.json`);
  return existsSync(p) ? JSON.parse(readFileSync(p, 'utf-8')) : [];
}

function saveJSON(name, data) {
  writeFileSync(join(ROOT, 'data', `${name}.json`), JSON.stringify(data, null, 2));
}

function getNotion() {
  if (!process.env.NOTION_API_KEY) throw new Error('Falta NOTION_API_KEY en .env');
  return new Client({ auth: process.env.NOTION_API_KEY });
}

// ─── SYNC POSTS ──────────────────────────────────────────────────────────────

async function syncPost(notion, post) {
  const dbId = process.env.NOTION_POSTS_DB_ID;
  if (!dbId) throw new Error('Falta NOTION_POSTS_DB_ID en .env');

  const statusMap = {
    concept: 'Concepto',
    prompts_ready: 'Prompts listos',
    shooting: 'Producción',
    editing: 'Edición',
    ready: 'Listo para publicar',
    published: 'Publicado',
    draft_ig: 'Borrador IG',
    draft_tt: 'Borrador TikTok'
  };

  const properties = {
    'Título': { title: [{ text: { content: `#${post.id} — ${post.title || post.perfume}` } }] },
    'Perfume': { rich_text: [{ text: { content: `${post.perfume} · ${post.brand}` } }] },
    'Modo': { select: { name: `Modo ${post.mode}` } },
    'Estado': { select: { name: statusMap[post.status] || post.status } },
    'Dificultad': { select: { name: post.difficulty ? post.difficulty.charAt(0).toUpperCase() + post.difficulty.slice(1) : 'Medium' } },
    'Caption': { rich_text: [{ text: { content: post.caption_chosen || post.caption_seed || '' } }] },
    'Precio': { number: post.price || 0 },
    'Likes': { number: post.metrics?.likes || 0 },
    'Saves': { number: post.metrics?.saves || 0 },
    'Engagement': { number: post.metrics?.engagement_rate || 0 },
    'Fecha publicación': post.published_at
      ? { date: { start: post.published_at } }
      : { date: null },
    'Concepto': { rich_text: [{ text: { content: post.concept_summary || '' } }] },
    'Invasor': { rich_text: [{ text: { content: post.element_invasor || '' } }] }
  };

  if (post.notion_page_id) {
    // Actualizar página existente
    await notion.pages.update({
      page_id: post.notion_page_id,
      properties
    });
    return post.notion_page_id;
  } else {
    // Crear nueva página
    const page = await notion.pages.create({
      parent: { database_id: dbId },
      properties
    });
    return page.id;
  }
}

// ─── SYNC PERFUMES ────────────────────────────────────────────────────────────

async function syncPerfume(notion, perfume) {
  const dbId = process.env.NOTION_PERFUMES_DB_ID;
  if (!dbId) return; // Opcional

  const properties = {
    'Nombre': { title: [{ text: { content: perfume.name } }] },
    'Marca': { rich_text: [{ text: { content: perfume.brand } }] },
    'Notas top': { rich_text: [{ text: { content: perfume.notes?.top?.join(', ') || '' } }] },
    'Notas base': { rich_text: [{ text: { content: perfume.notes?.base?.join(', ') || '' } }] },
    'Precio': { number: perfume.price || 0 },
    'Posts generados': { number: perfume.posts_generated || 0 },
    'Posts publicados': { number: perfume.posts_published || 0 },
    'Fragrantica': { url: perfume.fragrantica_url || null }
  };

  if (perfume.notion_page_id) {
    await notion.pages.update({ page_id: perfume.notion_page_id, properties });
    return perfume.notion_page_id;
  } else {
    const page = await notion.pages.create({
      parent: { database_id: dbId },
      properties
    });
    return page.id;
  }
}

// ─── SYNC BRANDS ─────────────────────────────────────────────────────────────

async function syncBrand(notion, brand) {
  const dbId = process.env.NOTION_BRANDS_DB_ID;
  if (!dbId) return;

  const statusLabels = {
    pending: 'Pendiente',
    contacted: 'Contactado',
    responded: 'Respondió',
    deal: 'Deal activo',
    rejected: 'Rechazado'
  };

  const properties = {
    'Marca': { title: [{ text: { content: brand.name } }] },
    'Instagram': { rich_text: [{ text: { content: brand.instagram || '' } }] },
    'Precio aprox.': { rich_text: [{ text: { content: brand.price_range || '' } }] },
    'Seguidores IG': { number: brand.followers_ig || 0 },
    'Estado': { select: { name: statusLabels[brand.status] || brand.status } },
    'AI influencer': { checkbox: brand.has_ai_influencer || false },
    'Email': { email: brand.email || null },
    'Notas': { rich_text: [{ text: { content: brand.notes || '' } }] }
  };

  if (brand.notion_page_id) {
    await notion.pages.update({ page_id: brand.notion_page_id, properties });
    return brand.notion_page_id;
  } else {
    const page = await notion.pages.create({
      parent: { database_id: dbId },
      properties
    });
    return page.id;
  }
}

// ─── PUBLIC API ───────────────────────────────────────────────────────────────

export async function syncAll() {
  const notion = getNotion();
  let synced = 0;
  let errors = 0;

  console.log('\n🔄 Sincronizando con Notion...\n');

  // Posts
  if (process.env.NOTION_POSTS_DB_ID) {
    const posts = loadJSON('posts');
    console.log(`📝 Sincronizando ${posts.length} posts...`);
    for (const post of posts) {
      try {
        const pageId = await syncPost(notion, post);
        if (!post.notion_page_id) {
          post.notion_page_id = pageId;
        }
        synced++;
        process.stdout.write('.');
      } catch (err) {
        errors++;
        process.stdout.write('x');
        console.error(`\n  ⚠️ Post #${post.id}: ${err.message}`);
      }
    }
    saveJSON('posts', posts);
    console.log('');
  }

  // Perfumes
  if (process.env.NOTION_PERFUMES_DB_ID) {
    const perfumes = loadJSON('perfumes');
    console.log(`\n🍾 Sincronizando ${perfumes.length} perfumes...`);
    for (const p of perfumes) {
      try {
        const pageId = await syncPerfume(notion, p);
        if (pageId && !p.notion_page_id) p.notion_page_id = pageId;
        synced++;
        process.stdout.write('.');
      } catch (err) {
        errors++;
        process.stdout.write('x');
      }
    }
    saveJSON('perfumes', perfumes);
    console.log('');
  }

  // Brands
  if (process.env.NOTION_BRANDS_DB_ID) {
    const brands = loadJSON('brands');
    console.log(`\n🤝 Sincronizando ${brands.length} marcas...`);
    for (const b of brands) {
      try {
        const pageId = await syncBrand(notion, b);
        if (pageId && !b.notion_page_id) b.notion_page_id = pageId;
        synced++;
        process.stdout.write('.');
      } catch (err) {
        errors++;
        process.stdout.write('x');
      }
    }
    saveJSON('brands', brands);
    console.log('');
  }

  console.log(`\n✅ Sync completado: ${synced} items | ❌ Errores: ${errors}`);
}

export async function syncSinglePost(postId) {
  const notion = getNotion();
  const posts = loadJSON('posts');
  const idx = posts.findIndex(p => p.id === postId);
  if (idx === -1) throw new Error(`Post ${postId} no encontrado`);

  const pageId = await syncPost(notion, posts[idx]);
  if (!posts[idx].notion_page_id) posts[idx].notion_page_id = pageId;
  saveJSON('posts', posts);

  console.log(`✅ Post #${postId} sincronizado con Notion: ${pageId}`);
  return pageId;
}

export async function showStatus() {
  const posts = loadJSON('posts');
  const brands = loadJSON('brands');
  const perfumes = loadJSON('perfumes');

  const synced_posts = posts.filter(p => p.notion_page_id).length;
  const synced_brands = brands.filter(b => b.notion_page_id).length;
  const synced_perfumes = perfumes.filter(p => p.notion_page_id).length;

  console.log('\n📊 Estado de sincronización Notion:');
  console.log(`  Posts:     ${synced_posts}/${posts.length} sincronizados`);
  console.log(`  Perfumes:  ${synced_perfumes}/${perfumes.length} sincronizados`);
  console.log(`  Marcas:    ${synced_brands}/${brands.length} sincronizadas`);

  const pending = posts.filter(p => !p.notion_page_id);
  if (pending.length > 0) {
    console.log(`\n⏳ Posts pendientes de sync: ${pending.map(p => `#${p.id}`).join(', ')}`);
    console.log('  → Ejecuta: node run notion sync');
  }
}
