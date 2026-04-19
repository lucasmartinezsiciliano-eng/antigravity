/* =============================================
   BROKER HIPOTECARIO — Analytics v2
   Eventos → n8n webhook + Mission Control CRM
   Solo activo si el usuario acepta cookies analíticas
   ============================================= */

const ANALYTICS_URL = 'https://n8n.lukimporta.es/webhook/broker-analytics';
const MC_URL        = 'https://crm.lukimporta.es/api/analytics/event';

// Session ID persistente por pestaña (se genera una vez por sesión de navegación)
function getSessionId() {
  let sid = sessionStorage.getItem('broker_session');
  if (!sid) {
    sid = 'S' + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
    sessionStorage.setItem('broker_session', sid);
  }
  return sid;
}

// Envía un evento al webhook solo si hay consentimiento analítico
function sendEvent(event, data = {}) {
  if (localStorage.getItem('cookie_consent') !== 'all') return;

  const params = new URLSearchParams(window.location.search);
  const session_id = getSessionId();
  const payload = {
    event,
    url: window.location.pathname,
    referrer: document.referrer || '',
    timestamp: new Date().toISOString(),
    session_id,
    utm_source:   params.get('utm_source')   || '',
    utm_medium:   params.get('utm_medium')   || '',
    utm_campaign: params.get('utm_campaign') || '',
    data,
  };

  // sendBeacon para quiz_abandon: no bloquea el cierre del tab
  if (event === 'quiz_abandon' && navigator.sendBeacon) {
    navigator.sendBeacon(
      ANALYTICS_URL,
      new Blob([JSON.stringify(payload)], { type: 'application/json' })
    );
    navigator.sendBeacon(
      MC_URL,
      new Blob([JSON.stringify(payload)], { type: 'application/json' })
    );
    return;
  }

  fetch(ANALYTICS_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    keepalive: true,
  }).catch(() => {});

  fetch(MC_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    keepalive: true,
  }).catch(() => {}); // silencioso — nunca afecta al usuario
}

// ── Page view ────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  sendEvent('page_view', { title: document.title });
});

// ── Heartbeat cada 30s — mantiene sesión activa en Mission Control ────────────
setInterval(() => {
  if (localStorage.getItem('cookie_consent') === 'all') {
    const session_id = getSessionId();
    const payload = {
      event: 'heartbeat',
      url: window.location.pathname,
      session_id,
      timestamp: new Date().toISOString(),
    };
    fetch(MC_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      keepalive: true,
    }).catch(() => {});
  }
}, 30000);

// ── API pública para tracking desde main.js ──────────────────────────────────
window.brokerAnalytics = { sendEvent };
