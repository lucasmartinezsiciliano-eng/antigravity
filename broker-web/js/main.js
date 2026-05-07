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
// SCORING 3-BLOQUES (Endeudamiento 40% · Estabilidad 30% · Ahorros 30%)
// ============================================
function calcularScore(data) {
  // ── B1: Endeudamiento / DTI (0-100) ──────────────────────────────────────
  const precioMid = { 'menos-150': 100000, '150-250': 200000, '250-300': 275000, '300-500': 400000, '500-750': 625000, 'mas-750': 900000 };
  const ahorrosPct = { 'mas-30': 0.33, '20-30': 0.25, '10-20': 0.15, 'menos-10': 0.08 };
  const cuotasMap  = { 'cero': 0, 'menos-200': 100, '200-500': 350, 'mas-500': 600 };
  const ingresosMid = { 'menos-1500': 1200, '1500-2500': 2000, '2500-3500': 3000, '3500-5000': 4250, 'mas-5000': 6000 };

  const precio   = precioMid[data.precio_vivienda] || 200000;
  const pctAho   = ahorrosPct[data.ahorros_pct] || 0.15;
  const prestamo = precio * (1 - pctAho);
  const cuotaHipo = prestamo * 0.0042; // ~30yr 3.8%
  const otrasCuotas = cuotasMap[data.otras_cuotas] || 0;
  const ingresos = ingresosMid[data.ingresos] || 2000;
  const dti = (cuotaHipo + otrasCuotas) / ingresos;

  let b1 = dti < 0.28 ? 100 : dti < 0.33 ? 80 : dti < 0.38 ? 58 : dti < 0.43 ? 32 : 10;
  if (data.cotitular === 'si') b1 = Math.min(100, b1 + 12);

  // ── B2: Estabilidad laboral (0-100) ──────────────────────────────────────
  const tc = data.tipo_contrato || '';
  const estabilidadBase = { 'funcionario': 100, 'indefinido': 85, 'interino': 70, 'fijo_discontinuo': 65, 'autonomo_2plus': 60, 'temporal': 45, 'autonomo_nuevo': 25 };
  let b2 = estabilidadBase[tc] || 50;
  if (data.cambio_empleo === 'si') b2 = Math.max(0, b2 - 20);

  // ── B3: Ahorros / Patrimonio (0-100) ─────────────────────────────────────
  const ahorroPtsMap = { 'mas-30': 100, '20-30': 75, '10-20': 45, 'menos-10': 15 };
  let b3 = ahorroPtsMap[data.ahorros_pct] || 45;
  if (data.tiene_patrimonio === 'si') b3 = Math.min(100, b3 + 10);

  // ── Knockout ──────────────────────────────────────────────────────────────
  if (data.impagos === 'si') return { b1: 0, b2: 0, b3: 0, score: 0, clasificacion: 'D' };

  // ── Global (ponderado) ────────────────────────────────────────────────────
  const global = Math.round(b1 * 0.40 + b2 * 0.30 + b3 * 0.30);
  const clasificacion = global >= 75 ? 'A' : global >= 55 ? 'B' : global >= 35 ? 'C' : 'D';

  return { b1: Math.round(b1), b2: Math.round(b2), b3: Math.round(b3), score: global, clasificacion };
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
      // Honeypot: si el bot rellenó el campo oculto, descarta silenciosamente
      if (fd.get('website')) { btn.textContent = orig; btn.disabled = false; return; }
      const ok = await submitLead({
        nombre: fd.get('nombre'), telefono: fd.get('telefono'),
        servicio: fd.get('servicio') || 'General', email: fd.get('email') || '',
        _hp: '',
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
const STEP_NAMES = [
  'situacion_laboral', 'ingresos', 'otras_cuotas', 'precio_vivienda',
  'ahorros_pct', 'estado_vivienda', 'cotitular', 'senales_adicionales', 'contacto',
];

const STEP_TEXTS = [
  '⏱ 2 minutos y lo tienes',
  '🔥 Paso 2 — ingresos del hogar',
  '💰 Paso 3 — carga financiera actual',
  '🏦 Paso 4 — precio de la vivienda',
  '🏦 Paso 5 — ahorros disponibles',
  '🔍 Paso 6 — situación de búsqueda',
  '👫 Paso 7 — titulares de la hipoteca',
  '✨ Paso 8 — detalles finales',
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
    // Analytics
    if (idx === 1) window.brokerAnalytics?.sendEvent('quiz_start');
    else if (idx > 1) window.brokerAnalytics?.sendEvent('quiz_step', { step: idx, step_name: STEP_NAMES[idx] || '' });
  }

  // Click en opciones
  quiz.querySelectorAll('.quiz-opt').forEach(opt => {
    opt.addEventListener('click', () => {
      const step = opt.closest('.quiz-step');
      if (opt.dataset.multiselect === 'true') {
        // Multi-select: toggle individual option
        opt.classList.toggle('selected');
        if (opt.classList.contains('selected')) {
          answers[opt.dataset.key] = opt.dataset.value;
        } else {
          delete answers[opt.dataset.key];
        }
      } else {
        // Single-select: deselect all, select clicked
        step.querySelectorAll('.quiz-opt').forEach(o => o.classList.remove('selected'));
        opt.classList.add('selected');
        answers[opt.dataset.key] = opt.dataset.value;
      }
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
    const hp       = (quiz.querySelector('[name="q_hp"]') || {value: ''}).value;

    if (!nombre || !telefono) {
      showToast('Por favor rellena nombre y teléfono.', 'error');
      return;
    }

    const btn = quiz.querySelector('.quiz-submit');
    btn.textContent = 'Analizando...';
    btn.disabled = true;

    const { b1, b2, b3, score, clasificacion } = calcularScore(answers);

    const ok = await submitLead({
      nombre, telefono, email,
      _hp: hp,
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

    // Rellenar bloques de scoring
    function tagLabel(val) {
      if (val >= 75) return 'Excelente';
      if (val >= 55) return 'Bueno';
      if (val >= 35) return 'Mejorable';
      return 'Crítico';
    }
    [['b1', b1], ['b2', b2], ['b3', b3]].forEach(([key, val]) => {
      const scoreEl = quiz.querySelector(`#r-${key}-score`);
      const fillEl  = quiz.querySelector(`#r-${key}-fill`);
      const tagEl   = quiz.querySelector(`#r-${key}-tag`);
      if (scoreEl) scoreEl.textContent = val + '/100';
      if (fillEl)  fillEl.style.width  = val + '%';
      if (tagEl)   tagEl.textContent   = tagLabel(val);
    });

    window.brokerAnalytics?.sendEvent('quiz_complete', { clasificacion, score });
    if (!ok) showToast('Error al enviar. Te llamaremos igualmente.', 'error');
  }

  // Abandon tracking: detecta si el usuario sale a mitad del quiz
  window.addEventListener('beforeunload', () => {
    if (current > 0 && current < total - 1) {
      window.brokerAnalytics?.sendEvent('quiz_abandon', { step: current, step_name: STEP_NAMES[current] || '' });
    }
  });

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
