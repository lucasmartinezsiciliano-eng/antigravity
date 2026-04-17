#!/usr/bin/env node
/**
 * run.js — CLI principal del AI Perfume Influencer
 *
 * Uso:
 *   node run concept --perfume="Torino 21" --brand="Xerjoff" --notes="mint,citrus,mojito" --price=320 --mode=A
 *   node run prompts --id=001
 *   node run captions --id=001
 *   node run hooks --id=001
 *   node run diversify --count=10
 *   node run drop --perfume="Beaver" --brand="Zoologist" --notes="castoreum,birch,moss" --price=120 --month="Abril 2026"
 *   node run narrative --format=opinion --perfume="Torino 21" --brand="Xerjoff" --notes="mint,lemon"
 *   node run narrative --format=moment --perfume="Sloth" --brand="Zoologist" --notes="chocolate,benzoin"
 *   node run narrative --format=obsession --perfume="Black Afgano" --brand="Nasomatto" --notes="cannabis,oud"
 *   node run narrative --format=comparison --perfume="Creed Aventus" --brand="Creed" --perfume2="Kilian Black Phantom" --brand2="Kilian"
 *   node run narrative --format=ranking --perfumes="Sloth,Beaver,Hummingbird,Tyrannosaurus Rex" --criterio="perfumes para llevar si te pierdes en un bosque"
 *   node run publish instagram --id=001 --images="f1.jpg,f2.jpg,f3.jpg" --caption="too fresh."
 *   node run publish tiktok --id=001 --video="reel.mp4"
 *   node run publish confirm --id=001 --platform=instagram
 *   node run outreach find --limit=20
 *   node run outreach pitch --brand=brand_001
 *   node run analytics sync
 *   node run analytics report --period=week
 *   node run notion sync
 *   node run notion status
 */

import { program } from 'commander';
import 'dotenv/config';

program
  .name('run')
  .description('AI Perfume Influencer — CLI de automatización')
  .version('1.0.0');

// ─── CONCEPT ─────────────────────────────────────────────────────────────────
program
  .command('concept')
  .description('Genera un concepto completo de post a partir de un perfume')
  .requiredOption('--perfume <name>', 'Nombre del perfume')
  .requiredOption('--brand <name>', 'Casa/marca del perfume')
  .requiredOption('--notes <notes>', 'Notas separadas por coma (ej: mint,citrus,mojito)')
  .requiredOption('--price <price>', 'Precio en euros', parseFloat)
  .requiredOption('--mode <mode>', 'Modo de contenido: A (invasión), B (colisión), C (declaración)')
  .option('--moods <moods>', 'Palabras/moods de la comunidad sobre este perfume (separados por coma)')
  .action(async (opts) => {
    try {
      const { generateConcept } = await import('./engine/concept.js');
      const notes = opts.notes.split(',').map(n => n.trim());
      const moods = opts.moods ? opts.moods.split(',').map(m => m.trim()) : [];
      const mode = opts.mode.toUpperCase();

      if (!['A', 'B', 'C'].includes(mode)) {
        console.error('❌ Modo inválido. Usa A, B o C.');
        process.exit(1);
      }

      await generateConcept({
        perfume: opts.perfume,
        brand: opts.brand,
        notes,
        price: opts.price,
        mode,
        moods
      });
    } catch (err) {
      console.error(`❌ Error: ${err.message}`);
      process.exit(1);
    }
  });

// ─── PROMPTS ─────────────────────────────────────────────────────────────────
program
  .command('prompts')
  .description('Genera prompts Higgsfield + Kling para un concepto existente')
  .requiredOption('--id <id>', 'ID del concepto (ej: 001)')
  .action(async (opts) => {
    try {
      const { generatePrompts } = await import('./engine/prompts.js');
      await generatePrompts(opts.id);
    } catch (err) {
      console.error(`❌ Error: ${err.message}`);
      process.exit(1);
    }
  });

// ─── CAPTIONS ────────────────────────────────────────────────────────────────
program
  .command('captions')
  .description('Genera 5 variantes de caption deadpan para un concepto')
  .requiredOption('--id <id>', 'ID del concepto')
  .action(async (opts) => {
    try {
      const { generateCaptions } = await import('./engine/captions.js');
      await generateCaptions(opts.id);
    } catch (err) {
      console.error(`❌ Error: ${err.message}`);
      process.exit(1);
    }
  });

// ─── HOOKS ───────────────────────────────────────────────────────────────────
program
  .command('hooks')
  .description('Genera 5 variantes del frame 1 (hook) para A/B testear')
  .requiredOption('--id <id>', 'ID del concepto')
  .action(async (opts) => {
    try {
      const { generateHooks } = await import('./engine/hook.js');
      await generateHooks(opts.id);
    } catch (err) {
      console.error(`❌ Error: ${err.message}`);
      process.exit(1);
    }
  });

// ─── DROP ─────────────────────────────────────────────────────────────────────
program
  .command('drop')
  .description('Genera un drop mensual completo: 4 posts del mismo perfume')
  .requiredOption('--perfume <name>', 'Nombre del perfume')
  .requiredOption('--brand <name>', 'Marca')
  .requiredOption('--notes <notes>', 'Notas separadas por coma')
  .requiredOption('--price <price>', 'Precio en euros', parseFloat)
  .option('--month <month>', 'Mes del drop (ej: "Abril 2026")')
  .option('--moods <moods>', 'Moods de la comunidad Fragrantica')
  .action(async (opts) => {
    try {
      const { generateDrop } = await import('./engine/drops.js');
      const notes = opts.notes.split(',').map(n => n.trim());
      const moods = opts.moods ? opts.moods.split(',').map(m => m.trim()) : [];
      await generateDrop({ perfume: opts.perfume, brand: opts.brand, notes, price: opts.price, moods, month: opts.month });
    } catch (err) {
      console.error(`❌ Error: ${err.message}`);
      process.exit(1);
    }
  });

// ─── NARRATIVE ───────────────────────────────────────────────────────────────
program
  .command('narrative')
  .description('Genera contenido MoF: opiniones, momentos, obsesiones, comparaciones, rankings')
  .requiredOption('--format <format>', 'Formato: opinion | moment | obsession | comparison | ranking')
  .option('--perfume <name>', 'Nombre del perfume')
  .option('--brand <name>', 'Marca')
  .option('--notes <notes>', 'Notas separadas por coma')
  .option('--perfume2 <name>', 'Segundo perfume (para comparison)')
  .option('--brand2 <name>', 'Segunda marca (para comparison)')
  .option('--perfumes <list>', 'Lista de perfumes para ranking (separados por coma)')
  .option('--criterio <text>', 'Criterio del ranking')
  .action(async (opts) => {
    try {
      const { generateNarrative } = await import('./engine/narrative.js');
      const notes = opts.notes ? opts.notes.split(',').map(n => n.trim()) : [];
      await generateNarrative({
        format: opts.format,
        perfume: opts.perfume,
        brand: opts.brand,
        notes,
        perfume2: opts.perfume2,
        brand2: opts.brand2,
        perfumes_list: opts.perfumes,
        criterio: opts.criterio
      });
    } catch (err) {
      console.error(`❌ Error: ${err.message}`);
      process.exit(1);
    }
  });

// ─── DIVERSIFY ───────────────────────────────────────────────────────────────
program
  .command('diversify')
  .description('Genera nuevas ideas de posts evitando repetir lo ya hecho')
  .option('--count <n>', 'Número de ideas a generar', '10')
  .action(async (opts) => {
    try {
      const { generateDiversify } = await import('./engine/diversify.js');
      await generateDiversify(parseInt(opts.count, 10));
    } catch (err) {
      console.error(`❌ Error: ${err.message}`);
      process.exit(1);
    }
  });

// ─── PUBLISH ─────────────────────────────────────────────────────────────────
const publish = program
  .command('publish')
  .description('Publicar contenido en Instagram o TikTok');

publish
  .command('instagram')
  .description('Publicar carrusel en Instagram (draft por defecto)')
  .requiredOption('--id <id>', 'ID del concepto')
  .requiredOption('--images <paths>', 'Rutas de imágenes separadas por coma')
  .requiredOption('--caption <text>', 'Caption elegida')
  .option('--draft', 'Guardar como borrador sin publicar (por defecto: true)', true)
  .action(async (opts) => {
    try {
      const { publishInstagram } = await import('./publish/instagram.js');
      const images = opts.images.split(',').map(p => p.trim());
      await publishInstagram({
        concept_id: opts.id,
        images,
        caption: opts.caption,
        draft: opts.draft !== false
      });
    } catch (err) {
      console.error(`❌ Error: ${err.message}`);
      process.exit(1);
    }
  });

publish
  .command('tiktok')
  .description('Publicar video en TikTok (draft por defecto)')
  .requiredOption('--id <id>', 'ID del concepto')
  .requiredOption('--video <path>', 'Ruta del video .mp4')
  .option('--caption <text>', 'Caption (opcional, usa la del concepto si existe)')
  .option('--draft', 'Guardar como borrador sin publicar (por defecto: true)', true)
  .action(async (opts) => {
    try {
      const { publishTikTok } = await import('./publish/tiktok.js');
      await publishTikTok({
        concept_id: opts.id,
        video: opts.video,
        caption: opts.caption,
        draft: opts.draft !== false
      });
    } catch (err) {
      console.error(`❌ Error: ${err.message}`);
      process.exit(1);
    }
  });

publish
  .command('confirm')
  .description('Confirmar y publicar un post en borrador')
  .requiredOption('--id <id>', 'ID del concepto')
  .requiredOption('--platform <platform>', 'Plataforma: instagram | tiktok')
  .action(async (opts) => {
    try {
      if (opts.platform === 'instagram') {
        const { confirmInstagram } = await import('./publish/instagram.js');
        await confirmInstagram(opts.id);
      } else if (opts.platform === 'tiktok') {
        const { confirmTikTok } = await import('./publish/tiktok.js');
        await confirmTikTok(opts.id);
      } else {
        console.error('❌ Plataforma inválida. Usa instagram o tiktok.');
        process.exit(1);
      }
    } catch (err) {
      console.error(`❌ Error: ${err.message}`);
      process.exit(1);
    }
  });

// ─── OUTREACH ────────────────────────────────────────────────────────────────
const outreach = program
  .command('outreach')
  .description('Gestión de outreach a marcas de perfumes');

outreach
  .command('find')
  .description('Encuentra nuevas marcas candidatas')
  .option('--limit <n>', 'Número máximo de marcas a buscar', '20')
  .action(async (opts) => {
    try {
      const { findBrands } = await import('./outreach/finder.js');
      await findBrands(parseInt(opts.limit, 10));
    } catch (err) {
      console.error(`❌ Error: ${err.message}`);
      process.exit(1);
    }
  });

outreach
  .command('pitch')
  .description('Genera pitch personalizado para una marca')
  .requiredOption('--brand <id>', 'ID de la marca (ej: brand_001)')
  .action(async (opts) => {
    try {
      const { generatePitch } = await import('./outreach/pitch.js');
      await generatePitch(opts.brand);
    } catch (err) {
      console.error(`❌ Error: ${err.message}`);
      process.exit(1);
    }
  });

// ─── ANALYTICS ───────────────────────────────────────────────────────────────
const analytics = program
  .command('analytics')
  .description('Métricas y análisis de rendimiento');

analytics
  .command('sync')
  .description('Sincroniza métricas desde Instagram y TikTok APIs')
  .action(async () => {
    try {
      const { syncAnalytics } = await import('./analytics/tracker.js');
      await syncAnalytics();
    } catch (err) {
      console.error(`❌ Error: ${err.message}`);
      process.exit(1);
    }
  });

analytics
  .command('report')
  .description('Genera informe de rendimiento')
  .option('--period <period>', 'Período: week | month', 'week')
  .action(async (opts) => {
    try {
      const { generateReport } = await import('./analytics/tracker.js');
      await generateReport(opts.period);
    } catch (err) {
      console.error(`❌ Error: ${err.message}`);
      process.exit(1);
    }
  });

// ─── NOTION ──────────────────────────────────────────────────────────────────
const notion = program
  .command('notion')
  .description('Sincronización con Notion');

notion
  .command('sync')
  .description('Sincroniza todos los datos locales con Notion')
  .action(async () => {
    try {
      const { syncAll } = await import('./notion/sync.js');
      await syncAll();
    } catch (err) {
      console.error(`❌ Error: ${err.message}`);
      process.exit(1);
    }
  });

notion
  .command('status')
  .description('Muestra el estado de sincronización con Notion')
  .action(async () => {
    try {
      const { showStatus } = await import('./notion/sync.js');
      await showStatus();
    } catch (err) {
      console.error(`❌ Error: ${err.message}`);
      process.exit(1);
    }
  });

// ─── SCHEDULE ────────────────────────────────────────────────────────────────
program
  .command('schedule')
  .description('Genera o visualiza el calendario de 11 días para un perfume')
  .option('--perfume <name>', 'Nombre del perfume')
  .option('--brand <name>', 'Marca')
  .option('--notes <notes>', 'Notas separadas por coma')
  .option('--price <price>', 'Precio del perfume', parseFloat)
  .option('--start <date>', 'Fecha de inicio YYYY-MM-DD (por defecto: hoy)')
  .option('--cycle <n>', 'Número de ciclo (#001, #002…)', parseInt)
  .option('--list', 'Ver todos los ciclos activos')
  .action(async (opts) => {
    try {
      const { generateSchedule, listSchedule } = await import('./engine/schedule.js');
      if (opts.list) {
        listSchedule();
      } else {
        if (!opts.perfume || !opts.brand) throw new Error('schedule requiere --perfume y --brand (o usa --list)');
        const notes = opts.notes ? opts.notes.split(',').map(n => n.trim()) : [];
        generateSchedule({
          perfume: opts.perfume,
          brand: opts.brand,
          notes,
          price: opts.price,
          startDate: opts.start,
          cycleNumber: opts.cycle || 1
        });
      }
    } catch (err) {
      console.error(`❌ Error: ${err.message}`);
      process.exit(1);
    }
  });

program.parse(process.argv);
