/* =============================================
   BROKER HIPOTECARIO — Analytics v1
   Eventos → n8n webhook → Google Sheets
   Solo activo si el usuario acepta cookies analíticas
   ============================================= */

const ANALYTICS_URL = 'https://n8n.lukimporta.es/webhook/broker-analytics';

// Envía un evento al webhook solo si hay consentimiento analítico
function sendEvent(event, data = {}) {
  if (localStorage.getItem('cookie_consent') !== 'all') return;

  const params = new URLSearchParams(window.location.search);
  const payload = {
    event,
    url: window.location.pathname,
    referrer: document.referrer || '',
    timestamp: new Date().toISOString(),
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
    return;
  }

  fetch(ANALYTICS_URL, {
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

// ── API pública para tracking desde main.js ──────────────────────────────────
window.brokerAnalytics = { sendEvent };
