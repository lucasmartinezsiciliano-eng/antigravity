/* =============================================
   BROKER HIPOTECARIO — Main JS v2
   ============================================= */

const N8N_WEBHOOK_URL = 'https://n8n.lukimporta.es/webhook/broker-lead';

// ============================================
// TOAST
// ============================================
function showToast(msg, type = 'success') {
  let t = document.querySelector('.toast');
  if (!t) { t = document.createElement('div'); t.className = 'toast'; document.body.appendChild(t); }
  t.textContent = msg;
  t.className = `toast ${type}`;
  requestAnimationFrame(() => t.classList.add('show'));
  setTimeout(() => t.classList.remove('show'), 4500);
}

// ============================================
// SCORING A/B/C/D (replicado del WF3)
// ============================================
function calcularScore(data) {
  let score = 0;

  // Tipo contrato
  if (data.tipo_contrato === 'indefinido') score += 15;
  else if (data.tipo_contrato === 'funcionario') score += 15;
  else if (data.tipo_contrato === 'autonomo') score += 5;
  else if (data.tipo_contrato === 'temporal') score += 3;

  // Antigüedad
  const ant = parseFloat(data.antiguedad) || 0;
  if (ant >= 5) score += 15;
  else if (ant >= 2) score += 10;

  // Ahorros / LTV
  const ahorrosMap = { '0-5': 0, '5-10': 3, '10-20': 6, 'mas-20': 10 };
  score += ahorrosMap[data.ahorros] || 0;
  if (data.ahorros === 'mas-20') score += 7; // premium

  // Estado búsqueda / urgencia
  if (data.estado === 'reserva') score += 30;
  else if (data.estado === 'identificada') score += 5;
  else score -= 10;

  if (data.urgencia === 'menos-1') score += 15;
  else if (data.urgencia === '1-3') score += 0;
  else score -= 5;

  // Señales premium
  if (data.tipo_contrato === 'funcionario') score += 10;
  if (data.cotitular === 'si') score += 5;
  if (data.primera_vivienda === 'si') score += 10;

  // Banderas rojas
  if (data.impagos === 'si') score -= 40;
  if (data.cambio_empleo === 'si') score -= 20;

  const s = Math.max(0, Math.min(100, score));
  let clasificacion;
  if (s >= 80) clasificacion = 'A';
  else if (s >= 60) clasificacion = 'B';
  else if (s >= 40) clasificacion = 'C';
  else clasificacion = 'D';

  return { score: s, clasificacion };
}

// ============================================
// ENVÍO A N8N
// ============================================
async function submitLead(payload) {
  try {
    const res = await fetch(N8N_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...payload, timestamp: new Date().toISOString(), page: window.location.pathname }),
    });
    return res.ok;
  } catch {
    return false;
  }
}

// Formulario simple (hero)
function initSimpleForms() {
  document.querySelectorAll('[data-lead-form]').forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = form.querySelector('[type="submit"]');
      const orig = btn.textContent;
      btn.textContent = 'Enviando...';
      btn.disabled = true;
      const fd = new FormData(form);
      const ok = await submitLead({
        nombre: fd.get('nombre'), telefono: fd.get('telefono'),
        servicio: fd.get('servicio') || 'General', email: fd.get('email') || '',
        source: form.dataset.leadForm,
      });
      showToast(ok ? '✅ Recibido. Te contactamos pronto.' : '❌ Error. Llámanos directamente.', ok ? 'success' : 'error');
      if (ok) form.reset();
      btn.textContent = orig;
      btn.disabled = false;
    });
  });
}

// ============================================
// QUIZ WIZARD
// ============================================
const STEP_TEXTS = [
  '⏱ 45 segundos y lo tienes',
  '🔥 Ya llevas la mitad — 30 segundos más',
  '💪 Tres preguntas menos, casi estás',
  '🎯 Solo un par de pasos más',
  '✨ Última pregunta antes de tu análisis',
  '📬 Solo necesitamos saber a quién enviárselo',
];

function initQuiz() {
  const quiz = document.getElementById('quiz');
  if (!quiz) return;

  const steps = quiz.querySelectorAll('.quiz-step');
  const fill  = quiz.querySelector('.quiz-progress-fill');
  const ptext = quiz.querySelector('.quiz-progress-text');
  const total = steps.length;
  let current = 0;
  let answers = {};

  function goTo(idx) {
    steps[current].classList.remove('active');
    current = idx;
    steps[current].classList.add('active');
    const pct = Math.round((current / (total - 1)) * 100);
    fill.style.width = pct + '%';
    ptext.textContent = STEP_TEXTS[current] || '¡Ya casi!';
    quiz.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  // Click en opciones
  quiz.querySelectorAll('.quiz-opt').forEach(opt => {
    opt.addEventListener('click', () => {
      const step = opt.closest('.quiz-step');
      step.querySelectorAll('.quiz-opt').forEach(o => o.classList.remove('selected'));
      opt.classList.add('selected');
      answers[opt.dataset.key] = opt.dataset.value;
    });
  });

  // Botón siguiente
  quiz.querySelectorAll('.quiz-next').forEach(btn => {
    btn.addEventListener('click', () => {
      if (current < total - 2) {
        goTo(current + 1);
      } else {
        submitQuiz();
      }
    });
  });

  // Botón atrás
  quiz.querySelectorAll('.quiz-back').forEach(btn => {
    btn.addEventListener('click', () => {
      if (current > 0) goTo(current - 1);
    });
  });

  async function submitQuiz() {
    const nombre   = quiz.querySelector('[name="q_nombre"]').value.trim();
    const telefono = quiz.querySelector('[name="q_telefono"]').value.trim();
    const email    = quiz.querySelector('[name="q_email"]').value.trim();

    if (!nombre || !telefono) {
      showToast('Por favor rellena nombre y teléfono.', 'error');
      return;
    }

    const btn = quiz.querySelector('.quiz-submit');
    btn.textContent = 'Analizando...';
    btn.disabled = true;

    const { score, clasificacion } = calcularScore(answers);

    const ok = await submitLead({
      nombre, telefono, email,
      source: 'quiz',
      clasificacion,
      score,
      respuestas: answers,
    });

    // Mostrar resultado
    steps[current].classList.remove('active');
    const resultStep = quiz.querySelector('.quiz-result-step');
    resultStep.classList.add('active');
    fill.style.width = '100%';
    ptext.textContent = '✅ ¡Análisis completado!';

    // Mostrar mensaje según clasificación
    resultStep.querySelectorAll('.result-msg').forEach(el => el.style.display = 'none');
    const msgEl = resultStep.querySelector(`[data-result="${clasificacion}"]`);
    if (msgEl) msgEl.style.display = 'block';

    if (!ok) showToast('Error al enviar. Te llamaremos igualmente.', 'error');
  }

  // Init
  goTo(0);
}

// ============================================
// HEADER
// ============================================
function initHeader() {
  const header = document.querySelector('header');
  if (!header) return;
  window.addEventListener('scroll', () => {
    header.style.background = window.scrollY > 20
      ? 'rgba(13,30,36,0.98)'
      : 'rgba(13,30,36,0.95)';
  }, { passive: true });
}

// ============================================
// MOBILE MENU
// ============================================
function initMobileMenu() {
  const btn = document.querySelector('.hamburger');
  const nav = document.querySelector('nav');
  if (!btn || !nav) return;
  btn.addEventListener('click', () => {
    const open = nav.classList.toggle('mobile-open');
    nav.style.cssText = open
      ? 'display:flex;flex-direction:column;position:fixed;top:72px;left:0;right:0;background:#0D1E24;padding:16px 24px 24px;border-bottom:1px solid rgba(255,255,255,0.06);z-index:99;gap:4px;'
      : '';
  });
}

// ============================================
// SCROLL REVEAL
// ============================================
function initReveal() {
  const els = document.querySelectorAll('[data-reveal]');
  if (!els.length) return;
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); } });
  }, { threshold: 0.1 });
  els.forEach(el => obs.observe(el));
}

// ============================================
// COOKIE BANNER
// ============================================
function initCookieBanner() {
  if (localStorage.getItem('cookie_consent')) return;

  // Detecta si estamos en /servicios/ para usar rutas relativas correctas
  const inServicios = window.location.pathname.includes('/servicios/');
  const base = inServicios ? '../' : '';

  const banner = document.createElement('div');
  banner.className = 'cookie-banner';
  banner.innerHTML = `
    <p>Usamos cookies propias para el funcionamiento del sitio y, si acepta, cookies analíticas para mejorar nuestro servicio. Sus datos se tratan conforme al <a href="${base}privacidad.html">RGPD</a>. Más info en nuestra <a href="${base}cookies.html">política de cookies</a>.</p>
    <div class="cookie-banner-actions">
      <button class="cookie-btn-reject">Solo esenciales</button>
      <button class="cookie-btn-accept">Aceptar todas</button>
    </div>
  `;
  document.body.appendChild(banner);
  requestAnimationFrame(() => banner.classList.add('visible'));

  banner.querySelector('.cookie-btn-accept').addEventListener('click', () => {
    localStorage.setItem('cookie_consent', 'all');
    banner.classList.remove('visible');
    setTimeout(() => banner.remove(), 400);
  });
  banner.querySelector('.cookie-btn-reject').addEventListener('click', () => {
    localStorage.setItem('cookie_consent', 'essential');
    banner.classList.remove('visible');
    setTimeout(() => banner.remove(), 400);
  });
}

// ============================================
// INIT
// ============================================
document.addEventListener('DOMContentLoaded', () => {
  initSimpleForms();
  initQuiz();
  initHeader();
  initMobileMenu();
  initReveal();
  initCookieBanner();
});
