const express = require('express');
const path = require('path');
const fs = require('fs');
const app = express();
const PORT = 3333;

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

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

// ─── LEGACY MOCK DATA (Mission Control Dashboard) ────────────────────────────
const mockData = {
  agents: [
    { id: 'jarvis', name: 'Jarvis', role: 'Director General', status: 'active', lastSeen: new Date().toISOString(), emoji: '🤖' },
    { id: 'rex', name: 'Rex', role: 'Broker', status: 'active', lastSeen: new Date().toISOString(), emoji: '🏠' },
    { id: 'nova', name: 'Nova', role: 'Marketing', status: 'active', lastSeen: new Date().toISOString(), emoji: '🎬' },
    { id: 'flow', name: 'Flow', role: 'n8n Técnico', status: 'idle', lastSeen: new Date(Date.now() - 3600000).toISOString(), emoji: '⚡' }
  ],
  leads: [
    { id: 'L001', nombre: 'Lead_001', estado: 'nuevo', origen: 'Instagram', zona: 'Tarragona', fecha: new Date(Date.now() - 86400000).toISOString(), score: 8 },
    { id: 'L002', nombre: 'Lead_002', estado: 'en_seguimiento', origen: 'Instagram', zona: 'Reus', fecha: new Date(Date.now() - 172800000).toISOString(), score: 6 },
    { id: 'L003', nombre: 'Lead_003', estado: 'reunion_agendada', origen: 'Boca a boca', zona: 'Baix Camp', fecha: new Date(Date.now() - 259200000).toISOString(), score: 9 },
    { id: 'L004', nombre: 'Lead_004', estado: 'en_seguimiento', origen: 'Instagram', zona: 'Tarragona', fecha: new Date(Date.now() - 432000000).toISOString(), score: 5 },
    { id: 'L005', nombre: 'Lead_005', estado: 'sin_respuesta', origen: 'Instagram', zona: 'Reus', fecha: new Date(Date.now() - 518400000).toISOString(), score: 3 },
    { id: 'L006', nombre: 'Lead_006', estado: 'cerrado_ganado', origen: 'Boca a boca', zona: 'Tarragona', fecha: new Date(Date.now() - 604800000).toISOString(), score: 10 }
  ],
  activity: [
    { time: new Date(Date.now() - 300000).toISOString(), agent: 'Jarvis', action: 'Briefing diario generado' },
    { time: new Date(Date.now() - 600000).toISOString(), agent: 'Rex', action: 'Lead_003 — reunión agendada para mañana' },
    { time: new Date(Date.now() - 1800000).toISOString(), agent: 'Nova', action: 'Calendario de contenido semana 2 listo' },
    { time: new Date(Date.now() - 3600000).toISOString(), agent: 'Flow', action: 'WF1 Instagram activado correctamente' },
    { time: new Date(Date.now() - 7200000).toISOString(), agent: 'Rex', action: 'Lead_001 nuevo — origen: comentario FIRMAX en reel' }
  ]
};

// ─── LEGACY ENDPOINTS (Mission Control) ──────────────────────────────────────
app.get('/api/agents', (req, res) => res.json(mockData.agents));
app.get('/api/leads', (req, res) => res.json(mockData.leads));
app.get('/api/activity', (req, res) => res.json(mockData.activity));

app.get('/api/stats', (req, res) => {
  const leads = mockData.leads;
  const sinRespuesta = leads.filter(l => {
    const dias = (Date.now() - new Date(l.fecha)) / 86400000;
    return l.estado === 'en_seguimiento' && dias > 3;
  });
  res.json({
    total: leads.length,
    nuevos: leads.filter(l => l.estado === 'nuevo').length,
    enSeguimiento: leads.filter(l => l.estado === 'en_seguimiento').length,
    reunionAgendada: leads.filter(l => l.estado === 'reunion_agendada').length,
    cerradosGanados: leads.filter(l => l.estado === 'cerrado_ganado').length,
    sinRespuesta: sinRespuesta.length,
    alertas: sinRespuesta.map(l => `${l.nombre} lleva más de 3 días sin respuesta`)
  });
});

app.get('/api/briefing', (req, res) => {
  res.json({
    fecha: new Date().toLocaleDateString('es-ES', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }),
    resumen: 'Pipeline activo. 2 leads en seguimiento, 1 reunión agendada para hoy. Nova tiene el calendario de la semana listo para aprobación. Flow reporta WF1 activo sin errores.',
    prioridades: [
      'Aprobar calendario de contenido semana 2 (Nova)',
      'Confirmar reunión con Lead_003 — Baix Camp',
      'Reactivar Lead_005 — 6 días sin respuesta'
    ]
  });
});

// ─── CRM ENDPOINTS ────────────────────────────────────────────────────────────

// GET all leads
app.get('/api/crm/leads', (req, res) => {
  res.json(loadCRM().leads);
});

// POST create new lead
app.post('/api/crm/leads', (req, res) => {
  const data = loadCRM();
  const now = new Date().toISOString();
  const lead = {
    id: 'L' + Date.now().toString().slice(-6),
    ...req.body,
    etapa: req.body.etapa || 'nuevo',
    fecha_entrada: now,
    fecha_etapa: now,
    notas: [],
    ultima_actividad: now
  };
  data.leads.unshift(lead);
  saveCRM(data);
  res.status(201).json(lead);
});

// PATCH update lead fields
app.patch('/api/crm/leads/:id', (req, res) => {
  const data = loadCRM();
  const i = data.leads.findIndex(l => l.id === req.params.id);
  if (i === -1) return res.status(404).json({ error: 'Lead no encontrado' });

  const updates = { ...req.body, ultima_actividad: new Date().toISOString() };
  if (updates.etapa && updates.etapa !== data.leads[i].etapa) {
    updates.fecha_etapa = new Date().toISOString();
  }
  data.leads[i] = { ...data.leads[i], ...updates };
  saveCRM(data);
  res.json(data.leads[i]);
});

// DELETE lead
app.delete('/api/crm/leads/:id', (req, res) => {
  const data = loadCRM();
  data.leads = data.leads.filter(l => l.id !== req.params.id);
  saveCRM(data);
  res.json({ ok: true });
});

// POST add note to lead
app.post('/api/crm/leads/:id/notes', (req, res) => {
  const data = loadCRM();
  const i = data.leads.findIndex(l => l.id === req.params.id);
  if (i === -1) return res.status(404).json({ error: 'Lead no encontrado' });

  const nota = {
    id: 'N' + Date.now(),
    fecha: new Date().toISOString(),
    ...req.body
  };
  if (!data.leads[i].notas) data.leads[i].notas = [];
  data.leads[i].notas.push(nota);
  data.leads[i].ultima_actividad = new Date().toISOString();
  saveCRM(data);
  res.status(201).json(nota);
});

// GET chat messages (with optional since= timestamp in ms)
app.get('/api/crm/chat', (req, res) => {
  const data = loadCRM();
  const since = req.query.since ? Number(req.query.since) : 0;
  const msgs = since
    ? data.chat.filter(m => new Date(m.fecha).getTime() > since)
    : data.chat.slice(-60);
  res.json(msgs);
});

// POST send chat message
app.post('/api/crm/chat', (req, res) => {
  const data = loadCRM();
  const msg = {
    id: 'M' + Date.now(),
    fecha: new Date().toISOString(),
    ...req.body
  };
  data.chat.push(msg);
  if (data.chat.length > 500) data.chat = data.chat.slice(-500);
  saveCRM(data);
  res.status(201).json(msg);
});

// GET CRM stats
app.get('/api/crm/stats', (req, res) => {
  const leads = loadCRM().leads;
  const now = Date.now();
  const stale = leads.filter(l => {
    if (['firmado', 'descartado'].includes(l.etapa)) return false;
    const dias = (now - new Date(l.ultima_actividad)) / 86400000;
    return dias > 3;
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

// ─── START ────────────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`🚀 Mission Control en http://localhost:${PORT}`);
  console.log(`📊 CRM Firmax en http://localhost:${PORT}/crm.html`);
});
