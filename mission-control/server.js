const express = require('express');
const path = require('path');
const fs = require('fs');
const app = express();
const PORT = process.env.PORT || 9999;

app.use(express.json({ limit: '1mb' }));
app.use(express.static(path.join(__dirname, 'public')));

// ─── CORS — analytics desde brokerhipotecario.es ──────────────────────────────
app.use((req, res, next) => {
  const origin = req.headers.origin || '';
  if (origin.includes('brokerhipotecario.es') || origin.includes('localhost')) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Access-Control-Allow-Methods', 'GET,POST,PATCH,DELETE,OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  }
  if (req.method === 'OPTIONS') return res.sendStatus(200);
  next();
});

// ─── CRM DATA PERSISTENCE ─────────────────────────────────────────────────────
const CRM_FILE = process.env.CRM_DATA_DIR
  ? path.join(process.env.CRM_DATA_DIR, 'crm-data.json')
  : path.join(__dirname, 'crm-data.json');

function loadCRM() {
  try { return JSON.parse(fs.readFileSync(CRM_FILE, 'utf8')); }
  catch { return { leads: [], chat: [] }; }
}
function saveCRM(data) {
  fs.writeFileSync(CRM_FILE, JSON.stringify(data, null, 2));
}

// ─── ANALYTICS IN-MEMORY ─────────────────────────────────────────────────────
// Se resetea al reiniciar el contenedor — solo para visualización live
const analyticsStore = {
  events: [],    // { ts, event, url, session_id, referrer, utm_source, data }
  sessions: {}   // session_id → { ts, page, referrer, first_seen }
};

function pruneEvents() {
  const cutoff = Date.now() - 86400000; // 24h
  analyticsStore.events = analyticsStore.events.filter(e => e.ts > cutoff);
}

function startOfToday() {
  const d = new Date();
  return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
}

// ─── ANALYTICS ENDPOINTS ──────────────────────────────────────────────────────

// POST /api/analytics/event — recibe eventos desde brokerhipotecario.es
app.post('/api/analytics/event', (req, res) => {
  const { event, url, referrer, session_id, timestamp, utm_source, data } = req.body;
  if (!event) return res.status(400).json({ error: 'event required' });

  const ts = timestamp ? new Date(timestamp).getTime() : Date.now();
  const entry = { ts, event, url: url || '/', session_id: session_id || null,
                  referrer: referrer || '', utm_source: utm_source || '', data: data || {} };

  analyticsStore.events.push(entry);
  if (analyticsStore.events.length > 2000) analyticsStore.events = analyticsStore.events.slice(-2000);

  // Actualizar sesión activa
  if (session_id) {
    if (!analyticsStore.sessions[session_id]) {
      analyticsStore.sessions[session_id] = { first_seen: ts, referrer: referrer || '' };
    }
    analyticsStore.sessions[session_id].ts = ts;
    analyticsStore.sessions[session_id].page = url || '/';
  }

  // Limpiar sesiones viejas (>30min sin heartbeat)
  const sessionCutoff = Date.now() - 1800000;
  Object.keys(analyticsStore.sessions).forEach(id => {
    if (analyticsStore.sessions[id].ts < sessionCutoff) delete analyticsStore.sessions[id];
  });

  res.json({ ok: true });
});

// GET /api/analytics/live — visitantes activos ahora (últimos 90s)
app.get('/api/analytics/live', (req, res) => {
  const cutoff = Date.now() - 90000;
  const visitors = Object.entries(analyticsStore.sessions)
    .filter(([, s]) => s.ts > cutoff)
    .map(([id, s]) => ({
      id: id.slice(0, 8),
      page: s.page || '/',
      since: s.first_seen,
      last_seen: s.ts,
      referrer: s.referrer
    }))
    .sort((a, b) => b.last_seen - a.last_seen);

  res.json({ count: visitors.length, visitors });
});

// GET /api/analytics/today — estadísticas del día (buckets por hora)
app.get('/api/analytics/today', (req, res) => {
  pruneEvents();
  const start = startOfToday();
  const todayEvents = analyticsStore.events.filter(e => e.ts >= start);

  const hours = Array.from({ length: 24 }, (_, h) => ({ hour: h, views: 0, interactions: 0, leads: 0 }));
  const pages = {};
  let quizStarts = 0, quizCompletes = 0, quizAbandons = 0;

  todayEvents.forEach(e => {
    const h = new Date(e.ts).getHours();
    if (e.event === 'page_view')       { hours[h].views++; pages[e.url] = (pages[e.url] || 0) + 1; }
    else if (e.event === 'lead_submit') hours[h].leads++;
    else                                hours[h].interactions++;
    if (e.event === 'quiz_start')    quizStarts++;
    if (e.event === 'quiz_complete') quizCompletes++;
    if (e.event === 'quiz_abandon')  quizAbandons++;
  });

  const topPages = Object.entries(pages).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([p, n]) => ({ page: p, views: n }));

  res.json({
    hours,
    totals: {
      views:        hours.reduce((s, h) => s + h.views, 0),
      interactions: hours.reduce((s, h) => s + h.interactions, 0),
      leads:        hours.reduce((s, h) => s + h.leads, 0)
    },
    quiz: { starts: quizStarts, completes: quizCompletes, abandons: quizAbandons },
    topPages
  });
});

// GET /api/analytics/feed — últimos N eventos (live stream)
app.get('/api/analytics/feed', (req, res) => {
  pruneEvents();
  const since = req.query.since ? Number(req.query.since) : 0;
  const limit = Math.min(Number(req.query.limit) || 30, 100);
  const events = analyticsStore.events
    .filter(e => e.ts > since && e.event !== 'heartbeat')
    .slice(-limit);
  res.json(events);
});

// ─── CRM ENDPOINTS ────────────────────────────────────────────────────────────

app.get('/api/crm/leads', (req, res) => res.json(loadCRM().leads));

app.post('/api/crm/leads', (req, res) => {
  const data = loadCRM();
  const now = new Date().toISOString();
  const lead = { id: 'L' + Date.now().toString().slice(-6), ...req.body,
    etapa: req.body.etapa || 'nuevo', fecha_entrada: now, fecha_etapa: now,
    notas: [], ultima_actividad: now };
  data.leads.unshift(lead);
  saveCRM(data);

  // Registrar captación en analytics
  analyticsStore.events.push({ ts: Date.now(), event: 'lead_captado', url: req.body.pagina || '/',
    session_id: null, referrer: '', utm_source: req.body.origen || '', data: {
      clasificacion: lead.clasificacion, score: lead.score, nombre: lead.nombre
    }});

  res.status(201).json(lead);
});

app.patch('/api/crm/leads/:id', (req, res) => {
  const data = loadCRM();
  const i = data.leads.findIndex(l => l.id === req.params.id);
  if (i === -1) return res.status(404).json({ error: 'Lead no encontrado' });
  const updates = { ...req.body, ultima_actividad: new Date().toISOString() };
  if (updates.etapa && updates.etapa !== data.leads[i].etapa) updates.fecha_etapa = new Date().toISOString();
  data.leads[i] = { ...data.leads[i], ...updates };
  saveCRM(data);
  res.json(data.leads[i]);
});

app.delete('/api/crm/leads/:id', (req, res) => {
  const data = loadCRM();
  data.leads = data.leads.filter(l => l.id !== req.params.id);
  saveCRM(data);
  res.json({ ok: true });
});

app.post('/api/crm/leads/:id/notes', (req, res) => {
  const data = loadCRM();
  const i = data.leads.findIndex(l => l.id === req.params.id);
  if (i === -1) return res.status(404).json({ error: 'Lead no encontrado' });
  const nota = { id: 'N' + Date.now(), fecha: new Date().toISOString(), ...req.body };
  if (!data.leads[i].notas) data.leads[i].notas = [];
  data.leads[i].notas.push(nota);
  data.leads[i].ultima_actividad = new Date().toISOString();
  saveCRM(data);
  res.status(201).json(nota);
});

app.get('/api/crm/chat', (req, res) => {
  const data = loadCRM();
  const since = req.query.since ? Number(req.query.since) : 0;
  const msgs = since ? data.chat.filter(m => new Date(m.fecha).getTime() > since) : data.chat.slice(-60);
  res.json(msgs);
});

app.post('/api/crm/chat', (req, res) => {
  const data = loadCRM();
  const msg = { id: 'M' + Date.now(), fecha: new Date().toISOString(), ...req.body };
  data.chat.push(msg);
  if (data.chat.length > 500) data.chat = data.chat.slice(-500);
  saveCRM(data);
  res.status(201).json(msg);
});

app.get('/api/crm/stats', (req, res) => {
  const leads = loadCRM().leads;
  const now = Date.now();
  const stale = leads.filter(l => {
    if (['firmado', 'descartado'].includes(l.etapa)) return false;
    return (now - new Date(l.ultima_actividad)) / 86400000 > 3;
  });
  res.json({
    total: leads.length,
    nuevo: leads.filter(l => l.etapa === 'nuevo').length,
    contactado: leads.filter(l => l.etapa === 'contactado').length,
    documentacion: leads.filter(l => l.etapa === 'documentacion').length,
    en_banco: leads.filter(l => l.etapa === 'en_banco').length,
    firmado: leads.filter(l => l.etapa === 'firmado').length,
    descartado: leads.filter(l => l.etapa === 'descartado').length,
    claseA: leads.filter(l => l.clasificacion === 'A' && !['firmado','descartado'].includes(l.etapa)).length,
    sinAsignar: leads.filter(l => !l.asignado_a && !['firmado','descartado'].includes(l.etapa)).length,
    sinActividad: stale.map(l => ({ id: l.id, nombre: l.nombre, dias: Math.floor((now - new Date(l.ultima_actividad)) / 86400000) }))
  });
});

// ─── CENTRUM AGENTS MONITOR ──────────────────────────────────────────────────
const OPENCLAW_URL    = process.env.OPENCLAW_URL    || 'https://openclaw.lukimporta.es';
const OPENCLAW_TOKEN  = process.env.OPENCLAW_TOKEN  || 'centrum2026gw';
const PORTAINER_URL   = process.env.PORTAINER_URL   || 'https://portainer.lukimporta.es';
const PORTAINER_USER  = process.env.PORTAINER_USER  || 'lucasmartinez';
const PORTAINER_PASS  = process.env.PORTAINER_PASS  || '';   // set via env

// In-memory activity feed (resets on server restart)
const agentActivity = [];   // { ts, from, to, task, result, error, msg }
const MAX_ACTIVITY  = 500;

// Cached Portainer JWT (refreshed on 401)
let portainerJwt = '';
let portainerExpiry = 0;
let ocContainerId = '';
let logBuffer = [];         // raw log lines fetched from container
let logLastTs = 0;

async function getPortainerJwt() {
  if (portainerJwt && Date.now() < portainerExpiry) return portainerJwt;
  if (!PORTAINER_PASS) return null;
  try {
    const r = await fetch(`${PORTAINER_URL}/api/auth`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: PORTAINER_USER, password: PORTAINER_PASS }),
      signal: AbortSignal.timeout(10000)
    });
    if (!r.ok) return null;
    const d = await r.json();
    portainerJwt = d.jwt || '';
    portainerExpiry = Date.now() + 3 * 60 * 1000;  // 3 min
    return portainerJwt;
  } catch { return null; }
}

async function resolveOcContainer(jwt) {
  if (ocContainerId) return ocContainerId;
  try {
    const r = await fetch(`${PORTAINER_URL}/api/endpoints/1/docker/containers/json`, {
      headers: { Authorization: `Bearer ${jwt}` },
      signal: AbortSignal.timeout(10000)
    });
    if (!r.ok) return null;
    const containers = await r.json();
    const oc = containers.find(c => (c.Image||'').includes('openclaw'));
    if (oc) { ocContainerId = oc.Id; return oc.Id; }
  } catch {}
  return null;
}

async function fetchContainerLogs(jwt, containerId) {
  const since = Math.floor(logLastTs / 1000) || Math.floor(Date.now()/1000) - 300;
  try {
    const r = await fetch(
      `${PORTAINER_URL}/api/endpoints/1/docker/containers/${containerId}/logs?stdout=1&stderr=1&since=${since}&tail=100`,
      { headers: { Authorization: `Bearer ${jwt}` }, signal: AbortSignal.timeout(15000) }
    );
    if (!r.ok) return [];
    const buf = Buffer.from(await r.arrayBuffer());
    // Docker multiplexed stream — strip 8-byte header per chunk
    const lines = [];
    let i = 0;
    while (i + 8 <= buf.length) {
      const size = buf.readUInt32BE(i + 4);
      i += 8;
      if (size > 0 && i + size <= buf.length) {
        const chunk = buf.slice(i, i + size).toString('utf8');
        chunk.split('\n').forEach(l => { if (l.trim()) lines.push(l.trimEnd()); });
        i += size;
      } else { i += size || 1; }
    }
    return lines;
  } catch { return []; }
}

// Periodic log fetcher (runs in background)
async function pollLogs() {
  try {
    const jwt = await getPortainerJwt();
    if (!jwt) return;
    const cid = await resolveOcContainer(jwt);
    if (!cid) return;
    const lines = await fetchContainerLogs(jwt, cid);
    if (lines.length) {
      logBuffer.push(...lines);
      if (logBuffer.length > 2000) logBuffer = logBuffer.slice(-2000);
      logLastTs = Date.now();
    }
  } catch {}
}

// Run every 10 seconds
setInterval(pollLogs, 10000);
setTimeout(pollLogs, 2000);  // first run soon after start

// POST /api/agents/activity — agentes reportan aquí (webhook)
// Body: { from, to, task, result, error, msg }
app.post('/api/agents/activity', (req, res) => {
  const { from, to, task, result, error, msg } = req.body || {};
  const entry = { ts: Date.now(), from, to, task, result, error, msg };
  agentActivity.push(entry);
  if (agentActivity.length > MAX_ACTIVITY) agentActivity.splice(0, agentActivity.length - MAX_ACTIVITY);
  res.json({ ok: true });
});

// GET /api/agents/activity?since=TS — feed de actividad
app.get('/api/agents/activity', (req, res) => {
  const since = Number(req.query.since) || 0;
  res.json(agentActivity.filter(e => e.ts > since));
});

// GET /api/agents/logs?since=TS — últimas líneas de log del contenedor
app.get('/api/agents/logs', async (req, res) => {
  const since = Number(req.query.since) || 0;
  // Return buffered lines newer than since
  const lines = since
    ? logBuffer.slice(-100)  // always return last 100 when polling
    : logBuffer.slice(-200);
  res.json({ lines, ts: Date.now(), online: logLastTs > Date.now() - 60000 });
});

// GET /api/agents/status — estado del contenedor OpenClaw
app.get('/api/agents/status', async (req, res) => {
  try {
    const r = await fetch(`${OPENCLAW_URL}/health`, {
      signal: AbortSignal.timeout(5000)
    });
    const online = r.ok;
    res.json({ online, container: ocContainerId ? ocContainerId.slice(0, 12) : null });
  } catch {
    res.json({ online: false, container: ocContainerId ? ocContainerId.slice(0, 12) : null });
  }
});

// ─── START ────────────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`Mission Control en http://localhost:${PORT}`);
});
