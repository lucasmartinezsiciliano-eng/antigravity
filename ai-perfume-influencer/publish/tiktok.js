/**
 * publish/tiktok.js
 * Publica videos en TikTok via Content Posting API
 *
 * FLUJO (siempre draft primero):
 * 1. publishTikTok() → sube video, registra como DRAFT
 * 2. confirmTikTok() → publica el draft
 *
 * TikTok API v2 Content Posting:
 * - Requiere scope: video.publish
 * - Videos: .mp4, max 4GB, 3-600 segundos
 * - Draft mode: privacy_level = "SELF_ONLY"
 */

import axios from 'axios';
import { readFileSync, writeFileSync, existsSync, statSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import 'dotenv/config';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

const TT_BASE = 'https://open.tiktokapis.com/v2';

function loadPosts() {
  const p = join(ROOT, 'data', 'posts.json');
  return existsSync(p) ? JSON.parse(readFileSync(p, 'utf-8')) : [];
}

function savePosts(posts) {
  writeFileSync(join(ROOT, 'data', 'posts.json'), JSON.stringify(posts, null, 2));
}

function getConfig() {
  const token = process.env.TIKTOK_ACCESS_TOKEN;
  const openId = process.env.TIKTOK_OPEN_ID;
  if (!token || !openId) {
    throw new Error('Faltan TIKTOK_ACCESS_TOKEN o TIKTOK_OPEN_ID en .env');
  }
  return { token, openId };
}

// Inicia la subida del video
async function initVideoUpload(token, videoSize, caption) {
  const { data } = await axios.post(
    `${TT_BASE}/post/publish/video/init/`,
    {
      post_info: {
        title: caption,
        privacy_level: 'SELF_ONLY', // Draft
        disable_duet: false,
        disable_comment: false,
        disable_stitch: false
      },
      source_info: {
        source: 'FILE_UPLOAD',
        video_size: videoSize,
        chunk_size: videoSize,
        total_chunk_count: 1
      }
    },
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json; charset=UTF-8'
      }
    }
  );
  return data.data;
}

// Sube el video al upload URL obtenido
async function uploadVideoChunk(uploadUrl, videoBuffer, videoSize) {
  await axios.put(uploadUrl, videoBuffer, {
    headers: {
      'Content-Type': 'video/mp4',
      'Content-Range': `bytes 0-${videoSize - 1}/${videoSize}`,
      'Content-Length': videoSize
    }
  });
}

export async function publishTikTok({ concept_id, video, caption, draft = true }) {
  const posts = loadPosts();
  const idx = posts.findIndex(p => p.id === concept_id);
  if (idx === -1) throw new Error(`Concepto ID ${concept_id} no encontrado`);

  const post = posts[idx];

  // Usar caption del concepto si no se pasa
  const finalCaption = caption || post.caption_chosen || post.caption_seed || '';

  console.log(`\n🎵 Preparando publicación TikTok — Concepto #${concept_id}`);
  console.log(`   Video: ${video}`);
  console.log(`   Caption: "${finalCaption}"`);

  if (!existsSync(video)) {
    throw new Error(`Archivo de video no encontrado: ${video}`);
  }

  const { token } = getConfig();
  const videoBuffer = readFileSync(video);
  const videoSize = statSync(video).size;

  console.log(`   Tamaño: ${(videoSize / 1024 / 1024).toFixed(1)} MB`);

  // Iniciar subida
  console.log('\n  Iniciando subida...');
  const uploadData = await initVideoUpload(token, videoSize, finalCaption);

  console.log('  Subiendo video...');
  await uploadVideoChunk(uploadData.upload_url, videoBuffer, videoSize);

  const publishId = uploadData.publish_id;

  posts[idx].status = draft ? 'draft_tt' : 'published';
  posts[idx].video = video;
  posts[idx].caption_chosen = finalCaption;
  posts[idx]._tt_publish_id = publishId;
  if (!draft) {
    posts[idx].tiktok_post_id = publishId;
    posts[idx].published_at = new Date().toISOString();
  }
  savePosts(posts);

  if (draft) {
    console.log(`\n✅ Video subido — guardado como DRAFT (solo visible para ti)`);
    console.log(`   Publish ID: ${publishId}`);
    console.log(`\n➡️  Para publicar: node run publish confirm --id=${concept_id} --platform=tiktok`);
  } else {
    console.log(`\n✅ Publicado en TikTok`);
    console.log(`   Publish ID: ${publishId}`);
  }

  return publishId;
}

export async function confirmTikTok(concept_id) {
  const posts = loadPosts();
  const idx = posts.findIndex(p => p.id === concept_id);
  if (idx === -1) throw new Error(`Concepto ${concept_id} no encontrado`);

  const post = posts[idx];
  if (!post._tt_publish_id) {
    throw new Error(`No hay draft de TikTok para #${concept_id}. Ejecuta primero: node run publish tiktok`);
  }

  const { token } = getConfig();

  console.log(`\n🚀 Publicando TikTok — Concepto #${concept_id}: "${post.title}"`);

  // TikTok: cambiar privacy de SELF_ONLY a PUBLIC_TO_EVERYONE
  await axios.post(
    `${TT_BASE}/post/publish/status/fetch/`,
    { publish_id: post._tt_publish_id },
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json; charset=UTF-8'
      }
    }
  );

  posts[idx].tiktok_post_id = post._tt_publish_id;
  posts[idx].status = 'published';
  posts[idx].published_at = new Date().toISOString();
  delete posts[idx]._tt_publish_id;
  savePosts(posts);

  console.log(`\n✅ PUBLICADO en TikTok`);
  console.log(`   Publish ID: ${post.tiktok_post_id}`);
  console.log(`\n➡️  Sincroniza métricas en 24h: node run analytics sync`);

  return post.tiktok_post_id;
}
