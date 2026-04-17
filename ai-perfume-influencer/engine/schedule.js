/**
 * engine/schedule.js
 * Sistema de rotación 11 días por perfume (#001, #002…)
 *
 * Cada perfume activo tiene 11 días de contenido:
 * - 4 posts WTF (estilo kczco): los del drop
 * - 4 posts olfativos: hacen sentir el olor
 * - 2 posts narrativos: opinión/momento/obsesión
 * - 1 post de cierre: ranking o comparación
 *
 * El calendario se genera automáticamente desde una fecha de inicio.
 */

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const SCHEDULE_FILE = join(ROOT, 'data', 'schedule.json');

// Días de la semana óptimos por tipo de contenido
const OPTIMAL_DAYS = {
  wtf_hook:      2, // martes — hook fuerte para arrancar semana
  wtf_animal:    3, // miércoles — mid-week viral boost
  olfactory_1:   1, // lunes — contemplativo post-weekend
  olfactory_2:   4, // jueves — aspiracional antes del fin de semana
  narrative_1:   1, // lunes — reflexivo
  narrative_2:   5, // viernes — introspección fin de semana
  wtf_intimate:  0, // domingo — momento íntimo
  olfactory_3:   2, // martes
  wtf_close:     5, // viernes — cierre épico
  narrative_3:   3, // miércoles
  olfactory_4:   4, // jueves
  close:         6, // sábado — cierre de ciclo
};

// Plantilla de los 11 días
const ELEVEN_DAY_TEMPLATE = [
  { day: 1,  type: 'wtf',       subtype: 'hook_geografico', pillar: 'kczco',    description: 'Post WTF #1 — Hook geográfico. Frame 1 debe parar el scroll.' },
  { day: 2,  type: 'olfactory', subtype: 'first_impression', pillar: 'olfativo', description: 'Post olfativo #1 — Primera impresión. Qué siente la nariz en segundo 0.' },
  { day: 3,  type: 'narrative', subtype: 'opinion',          pillar: 'mof',      description: 'Post narrativo #1 — Opinión directa sobre el perfume.' },
  { day: 4,  type: 'wtf',       subtype: 'animal',           pillar: 'kczco',    description: 'Post WTF #2 — Animal invasor. El más viral del ciclo.' },
  { day: 5,  type: 'olfactory', subtype: 'body',             pillar: 'olfativo', description: 'Post olfativo #2 — La experiencia completa en piel. Sinestesia máxima.' },
  { day: 6,  type: 'narrative', subtype: 'moment',           pillar: 'mof',      description: 'Post narrativo #2 — El momento concreto donde tiene sentido este perfume.' },
  { day: 7,  type: 'wtf',       subtype: 'declaracion',      pillar: 'kczco',    description: 'Post WTF #3 — Declaración íntima. Más emocional, mismo estilo visual.' },
  { day: 8,  type: 'olfactory', subtype: 'progression',      pillar: 'olfativo', description: 'Post olfativo #3 — Cómo evoluciona en piel durante el día. El dry-down.' },
  { day: 9,  type: 'narrative', subtype: 'obsession',        pillar: 'mof',      description: 'Post narrativo #3 — Obsesión irracional. Por qué lo llevas aunque no tenga sentido.' },
  { day: 10, type: 'wtf',       subtype: 'cierre_wtf',       pillar: 'kczco',    description: 'Post WTF #4 — Cierre épico. El más WTF de todos. Deja expectativa para el próximo.' },
  { day: 11, type: 'olfactory', subtype: 'close',            pillar: 'olfativo', description: 'Post olfativo #4 — Cierre sensorial. La memoria que deja. Por qué lo recordarás.' },
];

function addDays(date, days) {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

function formatDate(date) {
  return date.toISOString().split('T')[0];
}

export function generateSchedule({ perfume, brand, notes, price, startDate, cycleNumber }) {
  const start = startDate ? new Date(startDate) : new Date();
  const cycle = cycleNumber || 1;
  const id = `#${String(cycle).padStart(3, '0')}`;

  const posts = ELEVEN_DAY_TEMPLATE.map((template, i) => ({
    ...template,
    cycle_id:    id,
    perfume,
    brand,
    notes:       notes || [],
    price:       price || null,
    date:        formatDate(addDays(start, i)),
    status:      'pending',
    content_id:  null, // se rellena cuando se genera el concepto
  }));

  // Resumen
  console.log('\n' + '═'.repeat(60));
  console.log(`📅 CALENDARIO ${id} — ${perfume} · ${brand}`);
  console.log(`   Inicio: ${formatDate(start)}  →  Fin: ${formatDate(addDays(start, 10))}`);
  console.log('═'.repeat(60));

  const pillarCount = { kczco: 0, olfativo: 0, mof: 0 };
  posts.forEach(p => {
    pillarCount[p.pillar]++;
    const icon = p.pillar === 'kczco' ? '🎬' : p.pillar === 'olfativo' ? '👃' : '🖊️';
    console.log(`  ${icon} Día ${String(p.day).padStart(2)} · ${p.date} · ${p.subtype.padEnd(18)} ${p.description.slice(0, 50)}`);
  });

  console.log('\n📊 Distribución:');
  console.log(`   🎬 WTF visual (kczco):  ${pillarCount.kczco} posts`);
  console.log(`   👃 Olfativo:            ${pillarCount.olfativo} posts`);
  console.log(`   🖊️  Narrativo (MoF):    ${pillarCount.mof} posts`);

  // Guardar en schedule.json
  let schedule = [];
  if (existsSync(SCHEDULE_FILE)) {
    schedule = JSON.parse(readFileSync(SCHEDULE_FILE, 'utf-8'));
  }
  // Eliminar ciclo anterior si existe
  schedule = schedule.filter(p => p.cycle_id !== id);
  schedule.push(...posts);
  writeFileSync(SCHEDULE_FILE, JSON.stringify(schedule, null, 2));

  console.log(`\n💾 Guardado en data/schedule.json`);
  console.log('\n➡️  Comandos de este ciclo:');
  console.log(`   node run.js drop --perfume="${perfume}" --brand="${brand}"  → genera los 4 posts WTF`);
  console.log(`   node run.js narrative --format=olfactory --perfume="${perfume}" --brand="${brand}"  → posts olfativos`);
  console.log(`   node run.js narrative --format=opinion --perfume="${perfume}" --brand="${brand}"  → posts narrativos`);
  console.log('═'.repeat(60));

  return posts;
}

export function listSchedule() {
  if (!existsSync(SCHEDULE_FILE)) {
    console.log('No hay ciclos programados. Usa: node run.js schedule --perfume=X --brand=Y');
    return [];
  }
  const schedule = JSON.parse(readFileSync(SCHEDULE_FILE, 'utf-8'));
  const byCycle = {};
  schedule.forEach(p => {
    if (!byCycle[p.cycle_id]) byCycle[p.cycle_id] = [];
    byCycle[p.cycle_id].push(p);
  });

  console.log('\n📅 CICLOS ACTIVOS\n');
  Object.entries(byCycle).forEach(([id, posts]) => {
    const done = posts.filter(p => p.status === 'published').length;
    const pending = posts.filter(p => p.status === 'pending').length;
    console.log(`  ${id} — ${posts[0].perfume} · ${posts[0].brand}`);
    console.log(`       ${posts[0].date} → ${posts[posts.length - 1].date} | ✅ ${done} publicados | ⏳ ${pending} pendientes`);
    posts.filter(p => p.status === 'pending').slice(0, 3).forEach(p => {
      const icon = p.pillar === 'kczco' ? '🎬' : p.pillar === 'olfativo' ? '👃' : '🖊️';
      console.log(`       ${icon} ${p.date} — ${p.subtype}`);
    });
    console.log('');
  });

  return schedule;
}
