/**
 * Broker Lead Proxy — Cloudflare Worker
 *
 * Capas de seguridad:
 *  1. Origin check — solo acepta peticiones de brokerhipotecario.es
 *  2. Honeypot      — descarta bots que rellenan campos ocultos
 *  3. Validación    — campos requeridos + formato teléfono ES
 *  4. Rate limiting — máx 10 envíos/hora por IP (via Cache API)
 *  5. Token secreto — añade X-Broker-Token antes de reenviar a n8n
 *  6. Headers HTTP  — CSP, HSTS, X-Frame-Options en cada respuesta
 *
 * Secrets (configurar con: wrangler secret put <NAME>)
 *   N8N_URL        → URL del webhook de n8n
 *   BROKER_SECRET  → Token compartido que n8n debe verificar
 */

const ALLOWED_ORIGINS = [
  'https://brokerhipotecario.es',
  'https://www.brokerhipotecario.es',
  'https://lucasmartinezsiciliano-eng.github.io', // GitHub Pages durante transición
]

const CORS_HEADERS = (origin) => ({
  'Access-Control-Allow-Origin': origin,
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Access-Control-Max-Age': '86400',
})

const SECURITY_HEADERS = {
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  'Content-Security-Policy': "default-src 'none'",
}

function respond(body, status, origin, extra = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'Content-Type': 'application/json',
      ...(origin ? CORS_HEADERS(origin) : {}),
      ...SECURITY_HEADERS,
      ...extra,
    },
  })
}

// Rate limiting: máx 10 envíos por IP por hora
// Usa Cache API (per-PoP, suficiente para este volumen)
async function checkRateLimit(ip) {
  const cache = caches.default
  const cacheKey = new Request(`https://broker-rl.internal/${encodeURIComponent(ip)}`)

  const cached = await cache.match(cacheKey)
  const now = Date.now()

  if (cached) {
    const data = await cached.json()
    const windowMs = 3600 * 1000 // 1 hora
    if (now - data.ts < windowMs && data.count >= 10) {
      return { allowed: false }
    }
    const newCount = now - data.ts < windowMs ? data.count + 1 : 1
    await cache.put(
      cacheKey,
      new Response(JSON.stringify({ count: newCount, ts: data.ts || now }), {
        headers: { 'Cache-Control': 'max-age=3600', 'Content-Type': 'application/json' },
      })
    )
    return { allowed: true }
  }

  await cache.put(
    cacheKey,
    new Response(JSON.stringify({ count: 1, ts: now }), {
      headers: { 'Cache-Control': 'max-age=3600', 'Content-Type': 'application/json' },
    })
  )
  return { allowed: true }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url)
    const origin = request.headers.get('Origin') || ''

    // Health check (sin auth)
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json', ...SECURITY_HEADERS },
      })
    }

    // Solo acepta /lead
    if (url.pathname !== '/lead') {
      return new Response('Not Found', { status: 404 })
    }

    // CORS preflight
    if (request.method === 'OPTIONS') {
      if (!ALLOWED_ORIGINS.includes(origin)) {
        return new Response('Forbidden', { status: 403 })
      }
      return new Response(null, { status: 204, headers: CORS_HEADERS(origin) })
    }

    // Solo POST
    if (request.method !== 'POST') {
      return respond({ ok: false, error: 'Method not allowed' }, 405, null)
    }

    // Origin check
    if (!ALLOWED_ORIGINS.includes(origin)) {
      return respond({ ok: false, error: 'Forbidden' }, 403, null)
    }

    // Rate limiting
    const ip = request.headers.get('CF-Connecting-IP') || 'unknown'
    const { allowed } = await checkRateLimit(ip)
    if (!allowed) {
      return respond({ ok: false, error: 'Too many requests' }, 429, origin)
    }

    // Parse body
    let body
    try {
      body = await request.json()
    } catch {
      return respond({ ok: false, error: 'Invalid request' }, 400, origin)
    }

    // Honeypot: si el bot rellenó el campo oculto, rechaza silenciosamente
    // (devuelve 200 para no dar pistas al bot)
    if (body._hp) {
      return respond({ ok: true }, 200, origin)
    }

    // Validación de campos requeridos
    const nombre = String(body.nombre || '').trim()
    const telefono = String(body.telefono || '').replace(/\s/g, '')

    if (!nombre || nombre.length < 2 || nombre.length > 100) {
      return respond({ ok: false, error: 'Nombre inválido' }, 400, origin)
    }

    // Teléfono móvil español: empieza por 6, 7, 8 o 9, 9 dígitos
    if (!/^[6-9]\d{8}$/.test(telefono)) {
      return respond({ ok: false, error: 'Teléfono inválido' }, 400, origin)
    }

    // Reenviar a n8n con token de autenticación
    let n8nOk = false
    try {
      const n8nResp = await fetch(env.N8N_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Broker-Token': env.BROKER_SECRET,
        },
        body: JSON.stringify({
          ...body,
          _hp: undefined,         // nunca reenviar el honeypot
          timestamp: new Date().toISOString(),
          ip,
          cf_country: request.cf?.country || null,
          cf_city: request.cf?.city || null,
        }),
      })
      n8nOk = n8nResp.ok
    } catch (err) {
      console.error('Error al contactar n8n:', err.message)
    }

    return respond({ ok: n8nOk }, 200, origin)
  },
}
