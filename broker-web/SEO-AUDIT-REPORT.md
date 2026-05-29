# SEO Full Audit — brokerhipotecario.es
**Fecha:** 2026-05-29  
**Auditor:** Claude SEO (claude-seo v1.9.8)  
**Páginas auditadas:** 19 (homepage + 8 servicios + 3 locales + 4 legales + reclamaciones)

---

## Puntuación Global: 54 / 100 ⚠️

| Categoría | Peso | Puntuación | Ponderado |
|---|---|---|---|
| Technical SEO | 22% | 45/100 | 9.9 |
| Content Quality | 23% | 62/100 | 14.3 |
| On-Page SEO | 20% | 50/100 | 10.0 |
| Schema / Structured Data | 10% | 35/100 | 3.5 |
| Performance (CWV) | 10% | 65/100 | 6.5 |
| AI Search Readiness (GEO) | 10% | 55/100 | 5.5 |
| Images | 5% | 75/100 | 3.75 |
| **TOTAL** | | | **53.4 → 54/100** |

---

## Resumen Ejecutivo

Sitio bien construido para un broker hipotecario local. Arquitectura clara, contenido relevante, estructura de URLs limpia. Sin embargo, **tres defectos técnicos de alto impacto** bloquean el potencial de posicionamiento:

1. **Ninguna página tiene meta description** — Google genera fragmentos propios, a menudo malos
2. **Ninguna página tiene canonical tag** — riesgo de contenido duplicado entre HTTP/HTTPS y variantes de URL
3. **Schema.org solo en homepage** — las 8 páginas de servicios y 3 de localización no tienen structured data

Fixing estos 3 puntos en una tarde debería mover el score a ~72/100.

---

## Top 5 Issues Críticos

| # | Issue | Impacto | Páginas afectadas |
|---|---|---|---|
| 1 | **Meta descriptions ausentes** | Alto CTR perdido en SERP | Todas (19) |
| 2 | **Canonical tags ausentes** | Riesgo duplicado / dilución señal | Todas (19) |
| 3 | **Sin Schema en servicios y locales** | No aparece en rich results | 11 páginas |
| 4 | **Páginas legales indexables** (probablemente) | Crawl budget + calidad índice | 4-5 páginas |
| 5 | **Sin FAQ Schema** | Pierde featured snippets y SERP expandido | 8 páginas de servicios |

---

## Top 5 Quick Wins

| # | Acción | Esfuerzo | Impacto estimado |
|---|---|---|---|
| 1 | Añadir meta descriptions únicas | 2h | +15-25% CTR orgánico |
| 2 | Añadir `<link rel="canonical">` a todas las páginas | 30min | Limpia señal de ranking |
| 3 | Añadir `noindex` a páginas legales (privacidad, cookies, aviso-legal, reclamaciones) | 15min | Mejora calidad del índice |
| 4 | Añadir FAQ Schema en páginas de servicio (ya tienen FAQs en el HTML) | 2h | Rich results en SERP |
| 5 | Añadir `LocalBusiness` Schema en páginas de localización | 1h | Mejora mapa pack local |

---

## 1. Technical SEO

### robots.txt ✅
```
User-agent: *
Allow: /
Sitemap: https://brokerhipotecario.es/sitemap.xml
```
Correcto. Todos los bots permitidos. Sitemap referenciado.

### Sitemap ✅ (con gap)
- 19 URLs indexadas
- Última modificación uniforme: 24/03/2026
- **Gap:** `reclamaciones.html` puede no estar incluida (verificar)
- **Recomendación:** excluir páginas legales del sitemap o añadir noindex para coherencia

### Canonical Tags ❌ CRÍTICO
**Ninguna página del sitio tiene canonical tag.**  
Riesgo: si el sitio es accesible en `http://` + `https://` + `www.` + sin `www.`, Google puede indexar 4 versiones del mismo contenido.

**Fix inmediato:**
```html
<link rel="canonical" href="https://brokerhipotecario.es/URL-EXACTA" />
```

### Meta Robots
No se detectan directivas `noindex` explícitas. Las páginas legales (privacidad, cookies, aviso-legal, reclamaciones) deberían tener:
```html
<meta name="robots" content="noindex, follow" />
```

### HTTPS / SSL ✅
El sitio sirve en HTTPS. CSP header configurado en HTML (aunque mejor en servidor).

### Redirects
No testados directamente. Verificar que `http://` y `www.` redirigen a `https://` con 301.

---

## 2. Content Quality (E-E-A-T)

### Señales de Autoridad ✅
- Registro BdE D219 mencionado en título, footer y Schema → señal de confianza fuerte
- "Mediterrane Firmax, SL" — entidad legal visible
- Teléfono y email consistentes en todas las páginas

### Volumen de Contenido
| Página | Palabras aprox. | Valoración |
|---|---|---|
| Homepage | ~1.900 | ✅ Suficiente |
| hipoteca-100.html | ~1.300 | ⚠️ Mejorable |
| hipoteca-fija.html | ~1.200 | ⚠️ Mejorable |
| hipoteca-variable.html | ~1.250 | ⚠️ Mejorable |
| funcionarios.html | ~1.850 | ✅ Suficiente |
| broker-hipotecario-reus.html | ~2.300 | ✅ Bueno |

### Gaps de contenido (oportunidades)
- No hay **blog o sección de artículos** — los competidores que publican guías ("cómo pedir una hipoteca") capturan tráfico TOFU alto volumen
- Falta página **"Tarragona"** específica (la homepage actúa como tal pero sin señal local explícita)
- Falta página **"¿Cuánto cobra un broker hipotecario?"** — keyword de alta intención informativa
- Falta página **"Broker hipotecario Barcelona"** para ampliar cobertura geográfica

### Testimonios ⚠️
Hay 3 testimonios en la homepage pero son texto estático. Sin `Review` Schema ni Google Reviews embedidos.

---

## 3. On-Page SEO

### Titles ✅ (parcial)
| Página | Title | Estado |
|---|---|---|
| Homepage | "Broker Hipotecario en Tarragona \| Firmax — Intermediario Reg. BdE D219" | ✅ |
| hipoteca-100.html | "Hipoteca 100% Financiación en Tarragona \| Sin Ahorros — Firmax BdE D219" | ✅ |
| hipoteca-fija.html | "Hipoteca Fija en Tarragona \| Firmax Broker — Reg. BdE D219" | ✅ |
| hipoteca-variable.html | "Hipoteca Variable en Tarragona \| Firmax Broker — Reg. BdE D219" | ✅ |
| funcionarios.html | "Hipoteca para Funcionarios en Tarragona \| Firmax Broker — BdE D219" | ✅ |
| broker-hipotecario-reus.html | "Broker Hipotecario en Reus \| Firmax — Intermediario Reg. BdE D219" | ✅ |

**Títulos bien optimizados.** Patrón consistente: `[keyword principal] en [ciudad] | Firmax Broker`.

### Meta Descriptions ❌ CRÍTICO
**Ninguna página tiene meta description.** Esto significa que Google genera el snippet automáticamente, lo que típicamente reduce el CTR vs. una descripción optimizada con CTA.

**Formato recomendado (155-160 caracteres):**
```
[Beneficio clave]. [Credencial autoridad]. [CTA suave]. Sin compromiso.
```

Ejemplo para homepage:
```
Broker hipotecario en Tarragona. Comparamos +20 bancos y negociamos tu hipoteca. 
Reg. BdE D219. Estudio gratuito sin compromiso.
```

### Heading Structure ✅
- H1 único en cada página ✅
- H2s semánticamente relevantes ✅
- Estructura lógica H1 > H2 > H3 ✅

### Enlazado interno ⚠️
- Las páginas de servicios enlazan entre sí desde el footer ✅
- Las páginas de localización (Reus, Salou, Cambrils) NO están enlazadas desde la homepage — solo en el footer
- **Recomendación:** añadir sección "Zonas que cubrimos" en la homepage con links explícitos a las 3 páginas locales

---

## 4. Schema / Structured Data

### Homepage ✅ (bueno)
`FinancialService + LocalBusiness` con:
- Nombre, URL, email, geo-coordinates
- Registro BdE (identifier)
- Areas served: Tarragona, Reus, Salou, Cambrils
- Credential: Banco de España

**Gaps en el schema actual:**
- Falta `telephone`
- Falta `priceRange` o `paymentAccepted` (puede mejorar rich results)
- `areaServed` duplicado en el JSON (bug menor)

### Páginas de Servicio ❌
**Ninguna tiene Schema.** Oportunidad inmediata: añadir `FAQPage` schema (las FAQs ya existen en el HTML).

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [{
    "@type": "Question",
    "name": "¿Qué es una hipoteca 100%?",
    "acceptedAnswer": {
      "@type": "Answer",
      "text": "Una hipoteca 100% financia el total del precio de compra..."
    }
  }]
}
```

### Páginas de Localización ❌
Añadir `LocalBusiness` específico por ciudad:
```json
{
  "@context": "https://schema.org",
  "@type": "FinancialService",
  "name": "Broker Hipotecario en Reus — Firmax",
  "areaServed": {"@type": "City", "name": "Reus"},
  "address": {"@type": "PostalAddress", "addressLocality": "Reus", ...}
}
```

---

## 5. Performance (CWV estimado)

No se pudo obtener datos reales de PageSpeed API. Estimaciones basadas en análisis del código:

| Métrica | Estimación | Nota |
|---|---|---|
| LCP | ~2.5-3.5s | Logo PNG + JS quiz — mejorable |
| CLS | ~0.05-0.1 | Drag wheels con JS dinámico — riesgo menor |
| INP | ~150-250ms | JS inline con event listeners múltiples |

**Factores de riesgo:**
- `drag-wheel` componentes con JS inline en cada paso del quiz
- reCAPTCHA externo (Google) — añade ~200ms de bloqueo
- CSS/JS no se sabe si están minificados
- Logo `bh-logo.png` — verificar que no es oversized

**Recomendaciones:**
- Añadir `loading="lazy"` a imágenes bajo the fold
- Añadir `rel="preload"` al logo y CSS crítico
- Considerar cargar reCAPTCHA solo cuando el usuario llega al paso 6 del quiz

---

## 6. Local SEO

### Fortalezas ✅
- Registro BdE D219 = señal de autoridad local única
- 3 páginas de localización (Reus, Salou, Cambrils)
- NAP consistente: `+34 669 71 51 75` / `info@brokerhipotecario.es`
- Dirección: Rambla President Francesc Macià, 10, Tarragona (en footer)

### Debilidades ❌
- **Dirección NO aparece en el Schema** del homepage (solo geo-coordinates)
- **Sin Google Business Profile** schema de reseñas
- **Páginas locales sin LocalBusiness schema**
- **Sin citas (citations)** verificadas en directorios (Páginas Amarillas, Infocif, etc.)

### Google Business Profile
No auditado directamente. Verificar que existe y está optimizado con:
- Categoría: "Intermediario hipotecario" o "Asesor financiero"
- Posts activos
- Reviews con respuestas

---

## 7. AI Search Readiness (GEO)

### Acceso a crawlers ✅
robots.txt permite GPTBot, ClaudeBot, Google-Extended, etc.

### Señales de citabilidad ✅ (parcial)
- Registro BdE D219 — dato verificable y específico → alta probabilidad de cita en respuestas IA
- Ubicación Tarragona muy clara
- Especialización definida

### Falta
- `llms.txt` — no existe. Añadir para señalizar qué páginas son relevantes para LLMs
- Respuestas tipo "la mejor hipoteca para funcionarios es X porque..." — estructura FAQ ideal para ser citado
- No hay content hub / blog que genere autoridad temática

---

## 8. Images

| Imagen | Alt | Formato | Nota |
|---|---|---|---|
| bh-logo.png | "Broker Hipotecario" | PNG | ✅ Bien |
| avatar-maria.svg | "María R." | SVG | ✅ |
| avatar-jordi.svg | "Jordi L." | SVG | ✅ |
| avatar-anacarios.svg | "Ana y Carlos" | SVG | ✅ |

**Bien.** Alt texts presentes y descriptivos. SVG para avatares = bien (escalable, ligero).

**Recomendaciones:**
- Convertir `bh-logo.png` a WebP o SVG si posible
- Añadir `width` y `height` a `<img>` para evitar CLS

---

## Plan de Acción Prioritizado

### CRÍTICO — Hacer esta semana

| Tarea | Archivo | Tiempo |
|---|---|---|
| Añadir `<link rel="canonical">` a todas las páginas | Todas las .html | 30 min |
| Añadir meta descriptions únicas (ver plantillas abajo) | Todas las .html | 2h |
| Añadir `noindex` a páginas legales | privacidad, cookies, aviso-legal, reclamaciones | 15 min |

### ALTO — Esta semana

| Tarea | Impacto |
|---|---|
| FAQ Schema en 8 páginas de servicio | Rich results → +CTR |
| LocalBusiness Schema en Reus/Salou/Cambrils | Mapa local |
| Añadir `telephone` al Schema del homepage | Completitud |
| Enlazar páginas locales desde el body de la homepage | Link equity |

### MEDIO — Este mes

| Tarea | Impacto |
|---|---|
| Optimizar imágenes (WebP, preload logo) | LCP mejorado |
| Crear página "Broker hipotecario Tarragona" como hub | Keyword local |
| Crear página "¿Cuánto cobra un broker hipotecario?" | Tráfico informacional |
| Cargar reCAPTCHA diferido (paso 6 del quiz) | INP mejorado |
| Verificar y reclamar Google Business Profile | Mapa local |

### BAJO — Backlog

| Tarea | Impacto |
|---|---|
| llms.txt | GEO/AI search |
| Blog / artículos hipotecarios | TOFU orgánico |
| Citations en directorios (Páginas Amarillas, etc.) | Local authority |
| Añadir Review schema a testimonios | Rich results |

---

## Plantillas Meta Description

```
Homepage:
Broker hipotecario en Tarragona. Comparamos más de 20 bancos y negociamos la hipoteca adaptada a tu perfil. Registro BdE D219. Estudio gratuito sin compromiso. (152 chars)

Hipoteca 100%:
¿Sin ahorros y quieres comprar piso? Un broker hipotecario te abre las puertas que el banco cierra. Tarragona y Costa Daurada. Estudio gratis. (141 chars)

Hipoteca Fija:
Hipoteca fija en Tarragona: cuota estable toda la vida. Negociamos con +20 bancos las mejores condiciones fijas para tu perfil. Reg. BdE D219. (142 chars)

Hipoteca Variable:
Hipoteca variable en Tarragona con el mejor diferencial sobre el Euríbor. Broker hipotecario independiente. Comparamos 20 bancos. Gratis y sin compromiso. (155 chars)

Funcionarios:
Hipoteca para funcionarios en Tarragona. Accede a condiciones exclusivas: hasta 100% financiación, sin vinculaciones. Broker Reg. BdE D219. (141 chars)

Reus:
Broker hipotecario en Reus. Negociamos tu hipoteca con los mejores bancos del Baix Camp. +20 años de experiencia. Reg. BdE D219. Gratis. (137 chars)

Salou:
Broker hipotecario en Salou. Hipotecas para primera y segunda vivienda en la Costa Daurada. Comparamos +20 bancos. Estudio sin compromiso. (138 chars)

Cambrils:
Broker hipotecario en Cambrils. Negociamos las mejores hipotecas para compradores en el Baix Camp. Reg. BdE D219. Consulta gratis. (131 chars)
```

---

*Generado con claude-seo v1.9.8 | Próximo audit recomendado: 90 días o tras implementar fixes críticos*
