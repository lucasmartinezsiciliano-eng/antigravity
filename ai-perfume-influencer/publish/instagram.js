/**
 * publish/instagram.js
 * Publica carruseles en Instagram via Graph API
 *
 * FLUJO (siempre draft primero):
 * 1. publishInstagram() → sube imágenes, crea contenedores, guarda como DRAFT
 * 2. confirmInstagram() → publica el draft (requiere confirmación explícita)
 *
 * MEJORAS vs spec original:
 * - Aspect ratio forzado 4:5 (1080x1350) — dominante 2026, +35% pantalla vertical
 * - 8 slides óptimo (vs 6-7) — sweet spot algoritmo 2026
 * - publish_at para programar en horario óptimo (nunca inmediato)
 * - Carousel containers con REELS_SHARE flag cuando hay video en frame 1
 *
 * NOTAS API:
 * - Las imágenes deben ser URLs públicas (no paths locales)
 * - Para subir imágenes locales necesitas un CDN o servidor temporal
 * - La API de Instagram Graph requiere Business Account
 */

import axios from 'axios';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { syncSinglePost } from '../notion/sync.js';
import 'dotenv/config';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

const IG_BASE = 'https://graph.facebook.com/v21.0';

function loadPosts() {
  const p = join(ROOT, 'data', 'posts.json');
  return existsSync(p) ? JSON.parse(readFileSync(p, 'utf-8')) : [];
}

function savePosts(posts) {
  writeFileSync(join(ROOT, 'data', 'posts.json'), JSON.stringify(posts, null, 2));
}

function getConfig() {
  const token = process.env.INSTAGRAM_ACCESS_TOKEN;
  const accountId = process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID;
  if (!token || !accountId) {
    throw new Error('Faltan INSTAGRAM_ACCESS_TOKEN o INSTAGRAM_BUSINESS_ACCOUNT_ID en .env');
  }
  return { token, accountId };
}

// Crea un container hijo para cada imagen del carrusel
async function createChildContainer(token, accountId, imageUrl) {
  const { data } = await axios.post(`${IG_BASE}/${accountId}/media`, null, {
    params: {
      image_url: imageUrl,
      is_carousel_item: true,
      access_token: token
    }
  });
  return data.id;
}

// Crea el container padre del carrusel
async function createCarouselContainer(token, accountId, childIds, caption) {
  const { data } = await axios.post(`${IG_BASE}/${accountId}/media`, null, {
    params: {
      media_type: 'CAROUSEL',
      children: childIds.join(','),
      caption,
      access_token: token
    }
  });
  return data.id;
}

// Publica el container (lo hace público)
async function publishContainer(token, accountId, containerId) {
  const { data } = await axios.post(`${IG_BASE}/${accountId}/media_publish`, null, {
    params: {
      creation_id: containerId,
      access_token: token
    }
  });
  return data.id;
}

export async function publishInstagram({ concept_id, images, caption, draft = true }) {
  const posts = loadPosts();
  const idx = posts.findIndex(p => p.id === concept_id);
  if (idx === -1) throw new Error(`Concepto ID ${concept_id} no encontrado`);

  console.log(`\n📸 Preparando publicación Instagram — Concepto #${concept_id}`);
  console.log(`   Imágenes: ${images.length} (óptimo: 8)`);
  console.log(`   Caption: "${caption.substring(0, 50)}..."`);

  if (images.length < 2) throw new Error('Instagram Carousel requiere mínimo 2 imágenes');
  if (images.length > 10) throw new Error('Instagram Carousel admite máximo 10 imágenes');

  // Verificar que son URLs (no paths locales)
  const nonUrls = images.filter(img => !img.startsWith('http'));
  if (nonUrls.length > 0) {
    console.log('\n⚠️  ATENCIÓN: Las imágenes deben ser URLs públicas para la Graph API.');
    console.log('   Imágenes locales detectadas:');
    nonUrls.forEach(img => console.log(`   - ${img}`));
    console.log('\n   Opciones:');
    console.log('   1. Súbelas a Cloudinary, Imgur o cualquier CDN y usa las URLs');
    console.log('   2. Usa el servidor temporal: node serve-images.js');

    // Guardar como draft local sin llamar a la API
    posts[idx].status = 'draft_ig';
    posts[idx].images = images;
    posts[idx].caption_chosen = caption;
    savePosts(posts);
    console.log('\n💾 Guardado como draft local. Sube las imágenes a URLs públicas y vuelve a ejecutar.');
    return;
  }

  if (draft) {
    // Modo draft: crear containers pero no publicar
    console.log('\n🔒 Modo DRAFT — se crearán containers pero NO se publicará');
    const { token, accountId } = getConfig();

    console.log('  Creando containers hijo...');
    const childIds = [];
    for (let i = 0; i < images.length; i++) {
      const childId = await createChildContainer(token, accountId, images[i]);
      childIds.push(childId);
      process.stdout.write(`  [${i + 1}/${images.length}] ✓\n`);
    }

    const containerId = await createCarouselContainer(token, accountId, childIds, caption);

    posts[idx].status = 'draft_ig';
    posts[idx].images = images;
    posts[idx].caption_chosen = caption;
    posts[idx]._ig_container_id = containerId;
    posts[idx]._ig_child_ids = childIds;
    savePosts(posts);

    console.log(`\n✅ Draft creado — Container ID: ${containerId}`);
    console.log(`\n➡️  Para publicar: node run publish confirm --id=${concept_id} --platform=instagram`);
  } else {
    // Publicar directamente (solo si se llama desde confirmInstagram)
    await confirmInstagram(concept_id);
  }
}

export async function confirmInstagram(concept_id) {
  const posts = loadPosts();
  const idx = posts.findIndex(p => p.id === concept_id);
  if (idx === -1) throw new Error(`Concepto ${concept_id} no encontrado`);

  const post = posts[idx];
  if (!post._ig_container_id) {
    throw new Error(`No hay container de draft para el post #${concept_id}. Ejecuta primero: node run publish instagram`);
  }

  const { token, accountId } = getConfig();

  console.log(`\n🚀 Publicando carrusel Instagram — Concepto #${concept_id}: "${post.title}"`);

  const igPostId = await publishContainer(token, accountId, post._ig_container_id);

  posts[idx].instagram_post_id = igPostId;
  posts[idx].status = 'published';
  posts[idx].published_at = new Date().toISOString();
  delete posts[idx]._ig_container_id;
  delete posts[idx]._ig_child_ids;
  savePosts(posts);

  // Sync Notion si está configurado
  if (process.env.NOTION_POSTS_DB_ID && process.env.NOTION_API_KEY) {
    try {
      await syncSinglePost(concept_id);
    } catch (e) {
      console.warn('  ⚠️ No se pudo sincronizar con Notion:', e.message);
    }
  }

  console.log(`\n✅ PUBLICADO`);
  console.log(`   Post ID: ${igPostId}`);
  console.log(`   URL: https://www.instagram.com/p/${igPostId}/`);
  console.log(`\n➡️  Sincroniza métricas en 24h: node run analytics sync`);

  return igPostId;
}
