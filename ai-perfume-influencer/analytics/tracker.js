/**
 * analytics/tracker.js
 * Sincroniza métricas desde Instagram Graph API y genera informes
 *
 * MÉTRICAS PONDERADAS (modelo 2026):
 * - Saves:       peso x3  (señal de contenido de referencia)
 * - Comments:    peso x2  (engagement cualitativo)
 * - Shares:      peso x2  (distribución orgánica)
 * - Likes:       peso x1  (base)
 * - Reach:       informativo
 * - Impressions: informativo
 *
 * Engagement real = (saves*3 + comments*2 + shares*2 + likes) / reach * 100
 */

import axios from 'axios';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
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

function weightedEngagement(metrics) {
  const { saves = 0, comments = 0, shares = 0, likes = 0, reach = 1 } = metrics;
  return ((saves * 3 + comments * 2 + shares * 2 + likes) / reach * 100).toFixed(2);
}

async function fetchIGMetrics(postId, token) {
  const fields = 'like_count,comments_count,saved,reach,impressions,shares';
  const { data } = await axios.get(`${IG_BASE}/${postId}`, {
    params: { fields, access_token: token }
  });
  return {
    likes: data.like_count || 0,
    comments: data.comments_count || 0,
    saves: data.saved || 0,
    shares: data.shares || 0,
    reach: data.reach || 0,
    impressions: data.impressions || 0
  };
}

export async function syncAnalytics() {
  const token = process.env.INSTAGRAM_ACCESS_TOKEN;
  if (!token) throw new Error('Falta INSTAGRAM_ACCESS_TOKEN en .env');

  const posts = loadPosts();
  const published = posts.filter(p => p.instagram_post_id && p.status === 'published');

  if (published.length === 0) {
    console.log('\n📊 No hay posts publicados para sincronizar métricas.');
    return;
  }

  console.log(`\n📊 Sincronizando métricas de ${published.length} posts...\n`);

  let updated = 0;
  for (const post of published) {
    try {
      const metrics = await fetchIGMetrics(post.instagram_post_id, token);
      metrics.engagement_rate = parseFloat(weightedEngagement(metrics));
      metrics.synced_at = new Date().toISOString();

      const idx = posts.findIndex(p => p.id === post.id);
      posts[idx].metrics = metrics;
      updated++;

      console.log(`  #${post.id} "${post.title}" — ❤️ ${metrics.likes} 💾 ${metrics.saves} 💬 ${metrics.comments} | ER: ${metrics.engagement_rate}%`);
    } catch (err) {
      console.warn(`  ⚠️ #${post.id}: ${err.message}`);
    }
  }

  savePosts(posts);
  console.log(`\n✅ ${updated} posts actualizados`);
}

export async function generateReport(period = 'week') {
  const posts = loadPosts();
  const published = posts.filter(p => p.status === 'published' && p.published_at);

  const now = new Date();
  const cutoff = new Date(now);
  if (period === 'week') cutoff.setDate(cutoff.getDate() - 7);
  else if (period === 'month') cutoff.setDate(cutoff.getDate() - 30);

  const inPeriod = published.filter(p => new Date(p.published_at) >= cutoff);

  console.log('\n' + '═'.repeat(60));
  console.log(`📊 INFORME — Último ${period === 'week' ? '7 días' : 'mes'}`);
  console.log('═'.repeat(60));
  console.log(`Posts publicados: ${inPeriod.length}`);

  if (inPeriod.length === 0) {
    console.log('No hay posts en este período.');
    return;
  }

  const totals = inPeriod.reduce((acc, p) => {
    const m = p.metrics || {};
    acc.likes += m.likes || 0;
    acc.saves += m.saves || 0;
    acc.comments += m.comments || 0;
    acc.shares += m.shares || 0;
    acc.reach += m.reach || 0;
    acc.impressions += m.impressions || 0;
    return acc;
  }, { likes: 0, saves: 0, comments: 0, shares: 0, reach: 0, impressions: 0 });

  const avgER = (inPeriod.reduce((s, p) => s + (p.metrics?.engagement_rate || 0), 0) / inPeriod.length).toFixed(2);

  console.log('\n📈 TOTALES:');
  console.log(`  ❤️  Likes:       ${totals.likes.toLocaleString()}`);
  console.log(`  💾 Saves:       ${totals.saves.toLocaleString()}  ← indicador principal`);
  console.log(`  💬 Comentarios: ${totals.comments.toLocaleString()}`);
  console.log(`  🔁 Shares:      ${totals.shares.toLocaleString()}`);
  console.log(`  👁️  Reach:       ${totals.reach.toLocaleString()}`);
  console.log(`  📢 Impresiones: ${totals.impressions.toLocaleString()}`);
  console.log(`\n  ⭐ Engagement ponderado medio: ${avgER}%`);

  // Top post
  const top = inPeriod.sort((a, b) => (b.metrics?.engagement_rate || 0) - (a.metrics?.engagement_rate || 0))[0];
  if (top) {
    console.log(`\n🏆 MEJOR POST:`);
    console.log(`  #${top.id} — "${top.title}" (${top.perfume} · ${top.brand})`);
    console.log(`  Modo ${top.mode} | ER: ${top.metrics?.engagement_rate}%`);
    console.log(`  💾 ${top.metrics?.saves || 0} saves | ❤️ ${top.metrics?.likes || 0} likes`);
  }

  // Análisis por modo
  const byMode = { A: [], B: [], C: [] };
  for (const p of inPeriod) {
    if (byMode[p.mode]) byMode[p.mode].push(p.metrics?.engagement_rate || 0);
  }

  console.log('\n📊 ENGAGEMENT POR MODO:');
  for (const [mode, rates] of Object.entries(byMode)) {
    if (rates.length > 0) {
      const avg = (rates.reduce((s, r) => s + r, 0) / rates.length).toFixed(2);
      console.log(`  Modo ${mode}: ${avg}% avg (${rates.length} posts)`);
    }
  }

  console.log('\n' + '═'.repeat(60));
}
