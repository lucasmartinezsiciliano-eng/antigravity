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
// SCORING — ITP POR PROVINCIA
// ============================================
const ITP_BASE = {
  almeria:{ccaa:'Andalucía',itp:7},cadiz:{ccaa:'Andalucía',itp:7},cordoba:{ccaa:'Andalucía',itp:7},granada:{ccaa:'Andalucía',itp:7},huelva:{ccaa:'Andalucía',itp:7},jaen:{ccaa:'Andalucía',itp:7},malaga:{ccaa:'Andalucía',itp:7},sevilla:{ccaa:'Andalucía',itp:7},
  huesca:{ccaa:'Aragón',itp:8},teruel:{ccaa:'Aragón',itp:8},zaragoza:{ccaa:'Aragón',itp:8},
  asturias:{ccaa:'Asturias',itp:8},baleares:{ccaa:'Illes Balears',itp:11},
  laspalmas:{ccaa:'Canarias',itp:6.5},tenerife:{ccaa:'Canarias',itp:6.5},
  cantabria:{ccaa:'Cantabria',itp:10},
  albacete:{ccaa:'Castilla-La Mancha',itp:9},ciudadreal:{ccaa:'Castilla-La Mancha',itp:9},cuenca:{ccaa:'Castilla-La Mancha',itp:9},guadalajara:{ccaa:'Castilla-La Mancha',itp:9},toledo:{ccaa:'Castilla-La Mancha',itp:9},
  avila:{ccaa:'Castilla y León',itp:8},burgos:{ccaa:'Castilla y León',itp:8},leon:{ccaa:'Castilla y León',itp:8},palencia:{ccaa:'Castilla y León',itp:8},salamanca:{ccaa:'Castilla y León',itp:8},segovia:{ccaa:'Castilla y León',itp:8},soria:{ccaa:'Castilla y León',itp:8},valladolid:{ccaa:'Castilla y León',itp:8},zamora:{ccaa:'Castilla y León',itp:8},
  barcelona:{ccaa:'Cataluña',itp:10,itp_joven:5,edad_joven:35},girona:{ccaa:'Cataluña',itp:10,itp_joven:5,edad_joven:35},lleida:{ccaa:'Cataluña',itp:10,itp_joven:5,edad_joven:35},tarragona:{ccaa:'Cataluña',itp:10,itp_joven:5,edad_joven:35},
  alicante:{ccaa:'C. Valenciana',itp:10},castellon:{ccaa:'C. Valenciana',itp:10},valencia:{ccaa:'C. Valenciana',itp:10},
  badajoz:{ccaa:'Extremadura',itp:11},caceres:{ccaa:'Extremadura',itp:11},
  acoruña:{ccaa:'Galicia',itp:10},lugo:{ccaa:'Galicia',itp:10},ourense:{ccaa:'Galicia',itp:10},pontevedra:{ccaa:'Galicia',itp:10},
  larioja:{ccaa:'La Rioja',itp:7},madrid:{ccaa:'Madrid',itp:6},murcia:{ccaa:'Murcia',itp:8},navarra:{ccaa:'Navarra',itp:6},
  alava:{ccaa:'País Vasco',itp:7},gipuzkoa:{ccaa:'País Vasco',itp:7},bizkaia:{ccaa:'País Vasco',itp:7},
};

const CS_LABORAL = { funcionario:100, indefinido:90, fijo_disc:70, func_interino:65, autonomo_cons:60, temporal:40, autonomo_rec:30, otro:20 };

function calcEdad(v) {
  if (!v || !v.trim()) return null;
  const p = v.split('-'); if (p.length < 2) return null;
  const y = parseInt(p[0], 10), m = parseInt(p[1], 10);
  if (isNaN(y) || isNaN(m)) return null;
  const h = new Date(); let e = h.getFullYear() - y;
  if (h.getMonth() + 1 < m) e--; return e;
}

function getITPEfectivo(prov, tipo, edad1, edad2, nSol) {
  const d = ITP_BASE[prov];
  if (!d) return { itp: 8, ccaa: '', reducido: false };
  const e1 = edad1 !== null ? edad1 : 99, e2 = edad2 !== null ? edad2 : 99;
  if (d.itp_joven && tipo === 'habitual') {
    if (nSol === 2 && edad1 !== null && edad2 !== null) {
      const t1 = e1 < d.edad_joven ? d.itp_joven : d.itp;
      const t2 = e2 < d.edad_joven ? d.itp_joven : d.itp;
      return { itp: (t1 + t2) / 2, ccaa: d.ccaa, reducido: t1 < d.itp || t2 < d.itp };
    }
    if (e1 < d.edad_joven) return { itp: d.itp_joven, ccaa: d.ccaa, reducido: true };
  }
  return { itp: d.itp, ccaa: d.ccaa, reducido: false };
}

function scoreDTI(dti) {
  if (dti < 25) return { score: 100, label: 'Muy holgado' };
  if (dti < 35) return { score: 75,  label: 'Holgado' };
  if (dti <= 45) return { score: 40, label: 'Ajustado' };
  return { score: 10, label: 'Muy ajustado' };
}

function tagColor(s) {
  if (s >= 75) return { label: 'Alto',    bg: '#EAF3DE', color: '#27500A' };
  if (s >= 50) return { label: 'Medio',   bg: '#FAEEDA', color: '#633806' };
  if (s >= 25) return { label: 'Bajo',    bg: '#FAECE7', color: '#712B13' };
  return         { label: 'Muy bajo', bg: '#FCEBEB', color: '#791F1F' };
}

function scoreColor(s) {
  if (s >= 75) return '#639922';
  if (s >= 50) return '#EF9F27';
  if (s >= 25) return '#D85A30';
  return '#E24B4A';
}

function calcScenario(precio, ahorros, ltv, itpEf, cuotasTotales, ingresosTotalesComp, scoreLaboral, tipo, pat1, pat2, edad1, edad2, nSol) {
  const hipoteca = precio * (ltv / 100);
  const gastosITP = precio * (itpEf.itp / 100);
  const gNotaria = Math.max(2500, precio * 0.018);
  const totalNecesario = precio * (1 - ltv / 100) + gastosITP + gNotaria;
  const r = 0.027 / 12;
  const edadMayor = nSol === 2 ? Math.max(edad1 || 35, edad2 || 35) : (edad1 || 35);
  const plazo = Math.min(30, Math.max(5, 80 - edadMayor));
  const n = plazo * 12;
  const cuotaHip = hipoteca * (r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1);
  const dti = ingresosTotalesComp > 0 ? ((cuotaHip + cuotasTotales) / ingresosTotalesComp) * 100 : 100;
  const dtiResult = scoreDTI(dti);
  let scoreEndeu = dtiResult.score;
  if (ltv > 80) scoreEndeu = Math.max(0, scoreEndeu - 20);
  if (tipo === 'inversion') scoreEndeu = Math.max(0, scoreEndeu - 15);
  if (tipo === 'segunda') scoreEndeu = Math.max(0, scoreEndeu - 5);
  if (pat1 === 'si' || pat2 === 'si') scoreEndeu = Math.min(100, scoreEndeu + 5);
  if (plazo < 30) scoreEndeu = Math.max(0, scoreEndeu - 10);
  if (plazo < 20) scoreEndeu = Math.max(0, scoreEndeu - 10);
  const pctAhorros = precio > 0 ? (ahorros / precio) * 100 : 0;
  let scoreAhorros = 0;
  if (ahorros >= precio * 0.40)      scoreAhorros = 100;
  else if (ahorros >= precio * 0.35) scoreAhorros = 90;
  else if (ahorros >= totalNecesario && pctAhorros >= 30) scoreAhorros = 80;
  else if (ahorros >= totalNecesario) scoreAhorros = 65;
  else if (ahorros >= precio * 0.25) scoreAhorros = 45;
  else if (ahorros >= precio * 0.20) scoreAhorros = 30;
  else if (ahorros >= precio * 0.15) scoreAhorros = 15;
  else                               scoreAhorros = 5;
  const global = Math.round(scoreEndeu * 0.4 + scoreLaboral * 0.3 + scoreAhorros * 0.3);
  const suficiente = ahorros >= totalNecesario;
  return { hipoteca, gastosITP, gNotaria, totalNecesario, cuotaHip, dti, dtiResult, scoreEndeu, scoreLaboral, scoreAhorros, global, plazo, pctAhorros, suficiente };
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
// Índices de pasos en el DOM (0-5 data, 6 resultado)
// 0: urgencia | 1: n_sol | 2: S1 datos | 3: S2 datos (condicional) | 4: operación | 5: contacto | 6: resultado
const STEP_TEXTS = [
  '⏱ 2 minutos y tenemos tu análisis',
  '👥 ¿Quién solicitará la hipoteca?',
  '💼 Datos del titular principal',
  '💼 Datos del segundo titular',
  '🏠 Datos de la vivienda',
  '📬 ¿A quién enviamos el análisis?',
];

function initQuiz() {
  const quiz = document.getElementById('quiz');
  if (!quiz) return;

  const steps = quiz.querySelectorAll('.quiz-step');
  const fill  = quiz.querySelector('.quiz-progress-fill');
  const ptext = quiz.querySelector('.quiz-progress-text');
  let current = 0;
  let answers = {};

  // Secuencia de pasos según nSol (excluye resultado)
  function getSeq() {
    return answers.n_sol === '2' ? [0, 1, 2, 3, 4, 5] : [0, 1, 2, 4, 5];
  }

  function goTo(idx) {
    steps[current].classList.remove('active');
    current = idx;
    steps[current].classList.add('active');
    const seq = getSeq();
    const pos = seq.indexOf(idx);
    const pct = pos >= 0 ? Math.round((pos / (seq.length - 1)) * 100) : 0;
    fill.style.width = pct + '%';
    ptext.textContent = STEP_TEXTS[idx] || '¡Ya casi!';
    quiz.scrollIntoView({ behavior: 'smooth', block: 'center' });
    if (idx === 1) window.brokerAnalytics?.sendEvent('quiz_start');
  }

  // Click en opciones radio (quiz-opt)
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
      const seq = getSeq();
      const pos = seq.indexOf(current);
      if (pos < seq.length - 1) {
        goTo(seq[pos + 1]);
      } else {
        submitQuiz();
      }
    });
  });

  // Botón atrás
  quiz.querySelectorAll('.quiz-back').forEach(btn => {
    btn.addEventListener('click', () => {
      const seq = getSeq();
      const pos = seq.indexOf(current);
      if (pos > 0) goTo(seq[pos - 1]);
    });
  });

  function qval(name) {
    const el = quiz.querySelector(`[name="${name}"]`);
    return el ? el.value : '';
  }
  function qnum(name) { return parseFloat(qval(name)) || 0; }

  function fmt(v) { return '€' + Math.round(v).toLocaleString('es-ES'); }

  function renderScenario(px, s, sc, itpEf) {
    const tag = tagColor(s.global);
    const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    const setW  = (id, pct) => { const el = document.getElementById(id); if (el) el.style.width = pct + '%'; };

    setEl(`r${px}-global`, s.global);
    const tagEl = document.getElementById(`r${px}-tag`);
    if (tagEl) { tagEl.textContent = tag.label; tagEl.style.background = tag.bg; tagEl.style.color = tag.color; }
    const scoreEl = document.getElementById(`r${px}-global`);
    if (scoreEl) scoreEl.style.color = scoreColor(s.global);

    // 3 bloques
    [['b1', s.scoreEndeu], ['b2', s.scoreLaboral], ['b3', s.scoreAhorros]].forEach(([k, v]) => {
      setEl(`r${px}-${k}-score`, v);
      setW(`r${px}-${k}-fill`, v);
    });

    // Datos clave
    const kvsEl = document.getElementById(`r${px}-kvs`);
    if (kvsEl) {
      kvsEl.innerHTML = [
        { l: 'Hipoteca solicitada', v: fmt(s.hipoteca), s: 'LTV: ' + (px === 'A' ? '80' : '90') + '%' },
        { l: 'Cuota mensual est.', v: fmt(s.cuotaHip), s: s.plazo + ' años al 2,70%' },
        { l: 'DTI endeudamiento', v: sc.ingresosTotalesComp > 0 ? s.dti.toFixed(1) + '%' : '—', s: s.dtiResult.label },
        { l: 'Total necesario', v: fmt(s.totalNecesario), s: 'Entrada + ITP + notaría' },
        { l: 'Ahorros disponibles', v: fmt(sc.ahorros), s: s.suficiente ? '✓ Suficientes' : '⚠ Déficit ' + fmt(s.totalNecesario - sc.ahorros) },
        { l: 'ITP estimado', v: fmt(s.gastosITP), s: itpEf.itp + '% — ' + itpEf.ccaa },
      ].map(c => `<div class="result-kv-item"><div class="result-kv-label">${c.l}</div><div class="result-kv-val">${c.v}</div><div class="result-kv-sub">${c.s}</div></div>`).join('');
    }

    // Alertas
    const alertsEl = document.getElementById(`r${px}-alerts`);
    if (alertsEl) {
      const recs = [];
      if (sc.t1) recs.push({ cls: 'rec-alert', txt: 'Titular 1 temporal: ingresos no computables.' });
      if (sc.t2) recs.push({ cls: 'rec-alert', txt: 'Titular 2 temporal: 0 pts bloque laboral.' });
      if (sc.ingresosTotalesComp === 0) recs.push({ cls: 'rec-alert', txt: 'Sin ingresos computables: operación no viable.' });
      if (s.dti >= 45 && sc.ingresosTotalesComp > 0) recs.push({ cls: 'rec-alert', txt: 'DTI muy alto (' + s.dti.toFixed(1) + '%). Riesgo de denegación.' });
      else if (s.dti >= 35 && sc.ingresosTotalesComp > 0) recs.push({ cls: 'rec-info', txt: 'DTI ajustado (' + s.dti.toFixed(1) + '%). Estudiar cargas.' });
      if (px === 'B') recs.push({ cls: 'rec-info', txt: 'LTV 90%: solo entidades con productos específicos (jóvenes, aval ICO, etc.).' });
      if (!s.suficiente) recs.push({ cls: 'rec-alert', txt: 'Ahorros insuficientes para cubrir entrada + gastos.' });
      if (s.plazo < 30) recs.push({ cls: 'rec-warn', txt: 'Plazo reducido a ' + s.plazo + ' años (límite 80 años en última cuota).' });
      if (s.scoreLaboral < 50) recs.push({ cls: 'rec-warn', txt: 'Perfil laboral débil. Aportar IRPF y vida laboral.' });
      if (s.global >= 75) recs.push({ cls: 'rec-ok', txt: 'Perfil sólido. Viable en la mayoría de entidades.' });
      else if (s.global >= 50) recs.push({ cls: 'rec-info', txt: 'Viable con matices. Mejorar puntos débiles.' });
      else recs.push({ cls: 'rec-alert', txt: 'Perfil de riesgo. Conviene mejorar antes de solicitar.' });
      alertsEl.innerHTML = recs.map(r => `<p class="result-alert-item ${r.cls}">${r.txt}</p>`).join('');
    }
  }

  async function submitQuiz() {
    const nombre   = qval('q_nombre').trim();
    const telefono = qval('q_telefono').trim();
    const email    = qval('q_email').trim();
    const hp       = qval('q_hp');

    if (!nombre || !telefono) {
      showToast('Por favor rellena nombre y teléfono.', 'error');
      return;
    }

    const btn = quiz.querySelector('.quiz-submit');
    btn.textContent = 'Analizando...';
    btn.disabled = true;

    // Recoger todos los datos
    const nSol      = parseInt(answers.n_sol || '1', 10);
    const contrato1 = qval('q_contrato1') || 'indefinido';
    const contrato2 = qval('q_contrato2') || 'indefinido';
    const ingresos1Raw = qnum('q_ingresos1');
    const ingresos2Raw = nSol === 2 ? qnum('q_ingresos2') : 0;
    const cuotas1   = qnum('q_cuotas1');
    const cuotas2   = nSol === 2 ? qnum('q_cuotas2') : 0;
    const pat1      = qval('q_patrimonio1') || 'no';
    const pat2      = qval('q_patrimonio2') || 'no';
    const nac1      = qval('q_nacimiento1');
    const nac2      = qval('q_nacimiento2');
    const precio    = qnum('q_precio');
    const ahorros   = qnum('q_ahorros');
    const provincia = qval('q_provincia') || 'tarragona';
    const tipo      = qval('q_tipo_compra') || 'habitual';
    const urgencia  = answers.urgencia || 'mirando';

    const edad1 = calcEdad(nac1), edad2 = calcEdad(nac2);
    const t1 = contrato1 === 'temporal';
    const t2 = nSol === 2 && contrato2 === 'temporal';
    const ingresos1Comp = t1 ? 0 : ingresos1Raw;
    const ingresos2Comp = t2 ? 0 : ingresos2Raw;
    const ingresosTotalesComp = ingresos1Comp + ingresos2Comp;
    const cuotasTotales = cuotas1 + cuotas2;

    const scoreLaboral = nSol === 1
      ? (t1 ? 0 : (CS_LABORAL[contrato1] || 50))
      : (t1 ? 0 : Math.round((CS_LABORAL[contrato1] || 50) * 0.5)) + (t2 ? 0 : Math.round((CS_LABORAL[contrato2] || 50) * 0.5));

    const itpEf = getITPEfectivo(provincia, tipo, edad1, edad2, nSol);
    const sc = { ahorros, ingresosTotalesComp, t1, t2 };

    const sA = calcScenario(precio, ahorros, 80, itpEf, cuotasTotales, ingresosTotalesComp, scoreLaboral, tipo, pat1, pat2, edad1, edad2, nSol);
    const sB = calcScenario(precio, ahorros, 90, itpEf, cuotasTotales, ingresosTotalesComp, scoreLaboral, tipo, pat1, pat2, edad1, edad2, nSol);

    const globalMejor = Math.max(sA.global, sB.global);
    const clasificacion = globalMejor >= 75 ? 'A' : globalMejor >= 50 ? 'B' : globalMejor >= 25 ? 'C' : 'D';

    const ok = await submitLead({
      nombre, telefono, email, _hp: hp, source: 'quiz',
      urgencia, clasificacion,
      score_80: sA.global, score_90: sB.global,
      n_titulares: nSol,
      contrato1, ingresos1: ingresos1Raw, cuotas1,
      contrato2: nSol === 2 ? contrato2 : null, ingresos2: ingresos2Raw, cuotas2,
      precio, ahorros, provincia, tipo_compra: tipo,
    });

    // Mostrar resultado
    steps[current].classList.remove('active');
    const resultStep = quiz.querySelector('.quiz-result-step');
    resultStep.classList.add('active');
    fill.style.width = '100%';
    ptext.textContent = '✅ ¡Análisis completado!';

    // Mensaje clasificación
    const LEAD_MSG = {
      A: { icon: '🚀', titulo: 'Tu perfil es excelente', desc: 'Tienes todo lo que los bancos quieren ver. Es muy probable que consigamos condiciones muy por encima de la media para ti.' },
      B: { icon: '💪', titulo: 'Buen perfil, buenas opciones', desc: 'Tu situación es sólida. Hay varias entidades que estarían encantadas de trabajar contigo.' },
      C: { icon: '💡', titulo: 'Hay margen para mejorar', desc: 'Tu perfil tiene potencial. Con la estrategia correcta, las cosas mejoran rápido.' },
      D: { icon: '🤝', titulo: 'Tu caso necesita estrategia', desc: 'Hay cosas que trabajar, pero eso no significa que no haya opciones. Muchos clientes llegaron en tu misma situación y hoy tienen su hipoteca firmada.' },
    };
    const msg = LEAD_MSG[clasificacion];
    const iconEl = document.getElementById('r-icon');
    const titEl  = document.getElementById('r-titulo');
    const descEl = document.getElementById('r-desc');
    if (iconEl) iconEl.textContent = msg.icon;
    if (titEl)  titEl.textContent  = msg.titulo;
    if (descEl) descEl.textContent = msg.desc;

    setTimeout(() => {
      renderScenario('A', sA, sc, itpEf);
      renderScenario('B', sB, sc, itpEf);
    }, 100);

    window.brokerAnalytics?.sendEvent('quiz_complete', { clasificacion, score_80: sA.global, score_90: sB.global });
    if (!ok) showToast('Error al enviar. Te llamaremos igualmente.', 'error');
  }

  window.addEventListener('beforeunload', () => {
    if (current > 0 && current < 5) {
      window.brokerAnalytics?.sendEvent('quiz_abandon', { step: current });
    }
  });

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
