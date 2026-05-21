# VISAI — Informe Ejecutivo para Análisis Estratégico

**Documento:** Informe de Negocio para Asesoría Billion-Dollar AI Team  
**Fecha:** Mayo 2026  
**Protagonista:** Lucas Martínez Siciliano  
**Contexto:** Lanzamiento MVP con modelo barbero B2B2C  

---

## 1. QUÉ ES VISAI

**VISAI** es una plataforma de análisis facial por inteligencia artificial dirigida al sector barbería masculina española.

**Flujo de usuario:**
1. Cliente se hace 3 fotos (frontal + 2 perfiles 90°) desde móvil
2. IA analiza: forma facial (6 tipos) + tipo craneal (dolicocéfalo/mesocéfalo/braquicéfalo)
3. Genera informe digital personalizado en <2s con:
   - Cortes de cabello recomendados (12+ opciones de catálogo)
   - Instrucciones de styling específicas para su cabeza
   - Ilustraciones 3D por cada corte (frontal, perfil, dorsal)
4. Pago: €9,99 (add-ons de €4,99 cada)
5. Cliente recibe informe + galería de estilos posibles

**Diferenciador técnico:** Analiza la FORMA de la cabeza (tipo craneal), no solo la cara. Esto permite recomendaciones profundas que la barbería manual (probador virtual, IA genérica) no ofrece.

---

## 2. MERCADO OBJETIVO

**Segmento primario:** Barbería tradicional masculina en España (20.000+ salones)

**Razones:**
- Sector de alta confianza interpersonal
- El barbero es prescriptor clave (cliente sigue su recomendación)
- Barbería premium está en auge (precios: €15–25 por corte)
- Margen alto, clientes con poder adquisitivo
- Cliente va 1–2 veces/mes (frecuencia: 12–24 cortadas/año por cliente)

**Tamaño mercado:**
- 20.000 salones barbería España
- ~80–100 clientes activos/barbero/mes
- Penetración target año 1: 600 barberos = 48k–60k análisis mensuales

---

## 3. EL MODELO DE NEGOCIO (CORRECCIÓN CRÍTICA)

### ¿Cómo NO funciona?
❌ Barbero recluta a otros barberos  
❌ Sistema de referral entre peluqueros  
❌ Modelo MLM o piramidal

### ¿Cómo SÍ funciona?

**Actor 1: Barbero**
- Se registra en web de VISAI
- Recibe código personal único: `JUAN_MADRID_001`
- Muestra la app a cada cliente **antes del corte** (~30 segundos)
- Gana comisión por cada análisis

**Actor 2: Cliente**
- Cliente del barbero (ya existe relación)
- Analiza su cara con VISAI usando código del barbero
- Paga €9,99–€14,99 (precio con descuento si usa código)
- Recibe informe + gana barbero su comisión

**Volumen esperado:**
- Barbero promedio: 80–100 clientes/mes
- Análisis por cliente: 20–30% de clientes analizan (adopción conservadora)
- Análisis/barbero/mes: 16–30
- 600 barberos × 20 análisis promedio = **12.000 análisis/mes**
- Precio: €9,99 → VISAI ingreso neto ~€3/análisis
- Ingresos mes 6: ~€36k (conservador)

**Comisión barbero:** 20–25% del ingreso VISAI
- €0,60–€0,75 por análisis básico
- Sin techo, sin cuota mínima
- Pago automático vía Stripe Connect

### Por qué funciona este modelo

1. **Incentivo perfecto para el barbero:**
   - Tiempo: 30 segundos (mostrar app)
   - Coste: €0
   - Retorno: €2–3 por cliente (sin techo)
   - ROI infinito

2. **Beneficio al cliente:**
   - Informe científico de su cabeza
   - Fotos de resultado posible
   - Recomendaciones de styling
   - Precio justo (€10 es nada para un servicio personalizado)

3. **Beneficio al barbero (secundario):**
   - Cliente sale MÁS satisfecho (tiene referencia clara)
   - Reduce inseguridad "¿cuál me favorece?"
   - Barbero aparece como "experto moderno"
   - Clientes vuelven a mostrar a otros clientes

4. **Distribución orgánica:**
   - Un barbero trae sus 80–100 clientes
   - No es marketing de adquisición, es prescripción
   - CAC próximo a cero si el barbero confía en el producto

---

## 4. PRODUCTO TÉCNICO (ESTADO ACTUAL)

### Pipeline de Análisis
- ✅ Protocolo 3-fotos (frontal + 2×90° perfiles)
- ✅ MediaPipe FaceMesh para forma facial (6 tipos)
- ✅ OpenCV silhueta para análisis craneal (dolicocéfalo/mesocéfalo/braquicéfalo)
- ✅ LLM (Claude Anthropic) genera informe con catálogo 12+ cortes
- ✅ Generación de imágenes (Flux Pro via fal.ai) con referencias visuales
- ✅ Ilustraciones 3D por archetype + corte
- ✅ Pago integrado (Stripe, sin almacenamiento de tarjetas)

### UX
- Mobile-first (cliente se hace fotos en barbería)
- Resultado en <2 segundos
- Descargable + compartible
- Sin login necesario (código barbero = tracking anónimo)

### Privacidad & Legal
- ✅ RGPD compliant
- ✅ Consentimiento biométrico en 5 pasos
- ✅ Foto original se elimina inmediatamente (solo métricas numéricas se guardan 90 días)
- ✅ Política privacidad completa
- ✅ Términos: no es diagnóstico médico, es recomendación estética
- ⏳ SL a constituir (responsabilidad limitada por sanciones AEPD)
- ⏳ Contrato barbero (urgente, pendiente)

---

## 5. ECONOMÍA DEL MODELO

### Ingresos
| Producto | Precio | Margen VISAI | % mix esperado |
|---|---|---|---|
| Análisis básico | €9,99 | ~€3 | 60% |
| Add-on colorimetría | €4,99 | ~€2 | 15% |
| Add-on productos | €4,99 | ~€2 | 15% |
| Pack (análisis+2 add-ons) | €14,99 | ~€5 | 10% |

### Costes (Variables)
- **MediaPipe**: Gratis (local)
- **LLM** (Claude Anthropic): ~€0,30/análisis
- **Generación imágenes** (Flux via fal.ai): ~€0,50/análisis
- **Stripe**: 2,9% + €0,30
- **Hosting** (Railway/Vercel): ~€300/mes (amortizado)
- **Total variable**: ~€0,95/análisis

### Margen
- Ingreso promedio por análisis: €3
- Coste variable: €0,95
- Margen bruto: €2,05 (68%)
- Comisión barbero (25% del ingreso): €0,75
- **Margen neto VISAI**: €1,30 por análisis (43%)

### Proyección 12 meses (adquisición de barberos = 100/mes)
| Mes | Barberos | Análisis/mes | Ingresos | Margen |
|---|---|---|---|---|
| 1 | 100 | 2.000 | €6k | €2,6k |
| 3 | 300 | 6.000 | €18k | €7,8k |
| 6 | 600 | 12.000 | €36k | €15,6k |
| 12 | 1.200 | 24.000 | €72k | €31k |

**Nota:** Sin inversión en marketing (CAC ~€0). Asume adopción conservadora: 20 análisis/barbero/mes (vs 80–100 potenciales).

---

## 6. RETOS PRIORITARIOS PARA RESOLVER

### 🔴 URGENTE — Antes del piloto (mes 1)

1. **¿Cómo convencer a 100 barberos en 6 meses?**
   - Problema: Barbero necesita confiar en el producto + ver que sus clientes lo usan
   - Pregunta: ¿Cuál es la propuesta de valor que hace que un barbero QUIERA mostrar VISAI a cada cliente?
   - Factor crítico: Primeros 10–20 barberos son piloto gratis (para validar UX + generar testimonios)

2. **¿Cuál es la oferta irresistible para el barbero?**
   - Opciones en debate:
     - A) Comisión pura (€0,60–€0,75/análisis)
     - B) Comisión fija mensual (ej. €2.000/mes si hace 3.000+ análisis)
     - C) Paquete: comisión + featured listing + newsletter marketing
   - Pregunta: ¿Cuál convierte mejor? ¿A qué precio se justifica para el barbero?

3. **¿Cómo llego a los primeros 100 barberos sin presupuesto de marketing?**
   - Canales potenciales:
     - LinkedIn (influencers barbería, academias, cadenas)
     - Comunidades WhatsApp (asociaciones barberos)
     - Eventos barbería (ej. Barbershop Expo)
     - Referral entre barberos (sí cuenta, pero no es canal principal)
   - Pregunta: ¿Cuál es la secuencia de canales que da 100 barberos en 6 meses sin presupuesto?

4. **¿Cómo hago que el barbero ENTIENDA que VISAI mejora su negocio?**
   - Problema: Barbero no ve conexión "app de análisis facial" ← → "mi barbería"
   - Narrativa necesaria: VISAI no es "vender un extra", es "mejorar satisfacción del cliente y reducir devoluciones"
   - Pregunta: ¿Cuál es el story/pitch que CLICKEA en la mente del barbero en 60 segundos?

### 🟡 IMPORTANTE — Antes del mes 3

5. **Contrato barbero** (legal)
   - Definir: naturaleza relación, comisión, obligaciones, cláusula consentimiento foto referencia

6. **Dashboard barbero**
   - Trackear: conversiones, comisiones acumuladas, clientes únicos, ROI

7. **Landing de barbero optimizada**
   - Copy + diseño específico para esta audiencia
   - Testimonios de barberos piloto

---

## 7. LOS 3 ÁNGULOS DE ANÁLISIS QUE NECESITO

### Ángulo 1: HORMOZI (Oferta)
**Pregunta principal:** ¿Cuál es la oferta para el barbero que sea tan buena que diga que "sería estúpido no aceptar"?

**Qué necesito:**
- Estructura de comisión óptima (% vs fijo vs paquete)
- Value Equation: qué resuelvo realmente (no "gana dinero", sino qué problematica REAL del barbero resuelvo)
- Grand Slam Offer: si pudiera ofrecer UNA cosa que sea irresistible, ¿cuál es?

### Ángulo 2: GODIN (Posicionamiento)
**Pregunta principal:** ¿Cómo hago que un barbero se cuente a sí mismo una historia donde VISAI es natural para su negocio?

**Qué necesito:**
- Narrativa para el barbero (no para cliente final)
- Por qué un barbero moderno debería confiar en tecnología
- Comunidad/tribu (¿cómo hago que los barberos se sientan parte de un movimiento "barbería 2.0"?)

### Ángulo 3: BRUNSON (Funnel)
**Pregunta principal:** ¿Cuál es el journey exact que convierte un barbero en usuario activo en 30 días?

**Qué necesito:**
- Secuencia: cómo lo encuentro → lo convenzo → lo registro → hace su primer análisis → lo recomienda
- Frecuencia de interacción (email, Telegram, calls)
- Punto de inflexión: ¿cuándo sé que un barbero está "enganchado"?

---

## 8. CONTEXTO COMPETITIVO

### Competencia Directa
- **Retinax AI** (análisis facial genérico): No tiene protocolo de barbería, no tiene código barbero
- **Barberia.xyz** (directorio): No tiene análisis, solo marketplace
- **Audaces (software barbería)**: Software de citas, no análisis facial

### Ventaja VISAI
1. **Única con análisis cefálico real** (tipo craneal): diferenciador profundo
2. **Modelo barbero**: el barbero es vendedor + customer success
3. **Resultado inmediato** (<2s): vs webcam que tarda
4. **Catálogo 12+ cortes + matriz**: recomendaciones contextuales, no genéricas

### Riesgo Principal
- Barbero vé VISAI como "juguete" (no como herramienta de negocio) → baja adopción
- Solución: narrativa + testimonios + comisiones reales en primeros barberos

---

## 9. CONTEXTO DEL PROMOTOR

**Lucas Martínez Siciliano:**
- Técnico (desarrollo backend/IA)
- Emprendedor (busca SaaS + negocio escalable)
- Operando en solitario (necesita sistemas que funcionen sin personal)
- Márgenes altos, bajos costes fijos, distribución orgánica

**Limitación:** No tiene presupuesto de marketing CAC-heavy. Necesita distribución que funcione con prescripción + confianza.

---

## 10. ÉXITO DEFINIDO

**Métricas de éxito (6 meses):**
- 100+ barberos registrados ✅
- 20+ análisis promedio/barbero/mes ✅
- €36k+ ingresos mensuales ✅
- NPS barbero > 60 ✅
- Churn barbero < 10%/mes ✅

**Métricas de éxito (12 meses):**
- 600+ barberos ✅
- €72k+ ingresos mensuales ✅
- MVP v2: dashboard + referral + upsell productos ✅
- Presupuesto para 2–3 personas (customer success, marketing) ✅

---

## 11. PREGUNTAS ABIERTAS PARA LA ASESORIA

📌 **Para HORMOZI:**
1. ¿Cuál es el porcentaje de comisión que hace que un barbero diga "sí" sin dudarlo? (vs presión/manipulación)
2. ¿Qué obstaculo del barbero estoy dejando sin resolver?
3. ¿Necesito "bundlear" algo más con la comisión (ej. featured listing, training, branded materials)?

📌 **Para GODIN:**
1. ¿Cuál es la pequeña tribu de barberos que debería conquistar PRIMERO para que el movimiento se propague solo?
2. ¿Cómo hago que un barbero joven (25–35) entienda VISAI como "barbería moderna" vs "juguete tech"?
3. ¿Cuál es la historia que el barbero cuenta a sus colegas después de usar VISAI 2 semanas?

📌 **Para BRUNSON:**
1. ¿Cuál es el funnel exacto (5–7 pasos) que convierte un barbero prospecto en usuario activo?
2. ¿En qué momento del funnel hay máximo dropout? ¿Cómo lo cierro?
3. ¿Cuál es el "agit" (la razón por la que un barbero NECESITA esto YA) en el primer email/mensaje?

---

*Documento preparado para análisis estratégico. Toda la información técnica es actualizada y verificable directamente con el producto en marcha.*
