/**
 * Centrum de la Vivienda — Webhook Server
 * Recibe el lead del formulario web y dispara la llamada IA via Retell
 *
 * Deploy: OpenClaw PC (Ubuntu local, mismo servidor que los agentes Centrum)
 * Puerto: 3099
 * Expuesto via Cloudflare Tunnel → URL pública estable
 * Comando: node webhook-server.js
 */

const http = require('http');

const CONFIG = {
  PORT: 3099,
  RETELL_API_KEY: 'key_bd7400c5e034e3e89c3edd4e911a',
  RETELL_AGENT_ID: 'agent_d4a57a7f771c4f5520f2f58914',
  // Número Twilio desde donde llama la IA (rellenar cuando esté conectado)
  FROM_PHONE_NUMBER: process.env.CENTRUM_FROM_NUMBER || '+34XXXXXXXXX',
  // Telegram para notificar a Lucas
  TELEGRAM_TOKEN: '8683889993:AAEe9Va_TCaReMWkg3T4vfBjY6fH2aQSWCs',
  TELEGRAM_CHAT_ID: process.env.TELEGRAM_CHAT_ID || '',
};

/* ── HELPERS ── */

async function fetchJSON(url, options = {}) {
  const https = require('https');
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const reqOptions = {
      hostname: urlObj.hostname,
      path: urlObj.pathname + urlObj.search,
      method: options.method || 'GET',
      headers: options.headers || {},
    };
    const req = https.request(reqOptions, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(data) }); }
        catch { resolve({ status: res.statusCode, body: data }); }
      });
    });
    req.on('error', reject);
    if (options.body) req.write(options.body);
    req.end();
  });
}

async function triggerRetellCall(lead) {
  const phoneClean = lead.telefono.replace(/\s/g, '').replace(/^0034/, '+34').replace(/^34/, '+34');
  const toPhone = phoneClean.startsWith('+') ? phoneClean : '+34' + phoneClean;

  const payload = {
    from_number: CONFIG.FROM_PHONE_NUMBER,
    to_number: toPhone,
    agent_id: CONFIG.RETELL_AGENT_ID,
    retell_llm_dynamic_variables: {
      first_name: lead.nombre.split(' ')[0],
      full_name: lead.nombre,
      email: lead.email,
      // Pasar respuestas del quiz como contexto
      situacion: lead.respuestas?.[0]?.a || '',
      objetivo: lead.respuestas?.[1]?.a || '',
      deuda_valor: lead.respuestas?.[2]?.a || '',
      economia: lead.respuestas?.[3]?.a || '',
    },
    metadata: {
      email: lead.email,
      timestamp: lead.timestamp,
      source: 'web-quiz',
    },
  };

  return fetchJSON('https://api.retellai.com/create-phone-call', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${CONFIG.RETELL_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
}

async function notifyTelegram(lead, callResult) {
  if (!CONFIG.TELEGRAM_CHAT_ID) return;

  const status = callResult.status === 201 ? '✅ Llamada iniciada' : '⚠️ Error al llamar';
  const situacion = lead.respuestas?.[0]?.a || 'No especificado';
  const objetivo = lead.respuestas?.[1]?.a || 'No especificado';

  const msg = `🏠 *NUEVO LEAD — Centrum*\n\n` +
    `👤 *Nombre:* ${lead.nombre}\n` +
    `📞 *Teléfono:* ${lead.telefono}\n` +
    `📧 *Email:* ${lead.email}\n\n` +
    `📋 *Situación:* ${situacion}\n` +
    `🎯 *Objetivo:* ${objetivo}\n\n` +
    `${status}\n` +
    `_${new Date().toLocaleString('es-ES')}_`;

  const url = `https://api.telegram.org/bot${CONFIG.TELEGRAM_TOKEN}/sendMessage`;
  await fetchJSON(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: CONFIG.TELEGRAM_CHAT_ID,
      text: msg,
      parse_mode: 'Markdown',
    }),
  }).catch(e => console.error('Telegram error:', e.message));
}

/* ── SERVER ── */

const server = http.createServer(async (req, res) => {
  // CORS — permite peticiones desde cualquier origen (la web)
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204); res.end(); return;
  }

  if (req.method === 'POST' && req.url === '/centrum-lead') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', async () => {
      try {
        const lead = JSON.parse(body);
        console.log(`[${new Date().toISOString()}] Lead recibido: ${lead.nombre} — ${lead.telefono}`);

        // Disparar llamada Retell
        const callResult = await triggerRetellCall(lead);
        console.log(`Retell response: ${callResult.status}`, callResult.body);

        // Notificar Telegram
        await notifyTelegram(lead, callResult);

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, call_id: callResult.body?.call_id }));

      } catch (err) {
        console.error('Error:', err.message);
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: err.message }));
      }
    });
    return;
  }

  // Health check
  if (req.method === 'GET' && req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', agent: CONFIG.RETELL_AGENT_ID }));
    return;
  }

  res.writeHead(404); res.end();
});

server.listen(CONFIG.PORT, () => {
  console.log(`Centrum webhook server escuchando en puerto ${CONFIG.PORT}`);
  console.log(`Agent ID: ${CONFIG.RETELL_AGENT_ID}`);
  console.log(`Health: http://localhost:${CONFIG.PORT}/health`);
});
