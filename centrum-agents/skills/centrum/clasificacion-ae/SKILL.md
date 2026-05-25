---
name: centrum-clasificacion-ae
description: Criterios A/B/C/D/E para clasificar leads entrantes de Centrum. Se activa en lead-classifier, lead-scorer, form-analyzer, lead-router. Decide el flujo del caso. Velocidad es crítica — Mariano necesita saber en segundos.
version: 1
---

# Clasificación A-E de leads — criterios Centrum

> Cada lead entrante (formulario web, DM, llamada inbound) se clasifica en una de 5 categorías. La categoría **determina el flujo** y la urgencia. Validado por Mariano.

---

## A — URGENTE

**Definición:** subasta activa, demanda judicial en curso, o carta notarial recibida.

**Señales:**
- Menciona subasta con fecha próxima (<60 días)
- Tiene número de procedimiento judicial
- Recibió cédula judicial de notificación
- Carta notarial de banco o juzgado en mano

**Score típico:** 8-10

**Acción inmediata:**
- Notificación a Mariano vía Telegram **en menos de 30 segundos**
- Llamar HOY (idealmente en la primera hora)
- Prioridad máxima sobre cualquier otro caso

**Flujo:** `centrum` → `intake-director` urgente → `call-prep` express → llamada Mariano hoy

---

## B — NORMAL

**Definición:** sin demanda judicial todavía. Impago en curso pero ventana de acción disponible.

**Señales:**
- 1-12 meses sin pagar la cuota
- Banco ha llamado / enviado burofax pero **no** ha iniciado procedimiento
- Cliente angustiado pero la urgencia legal aún no es inmediata

**Score típico:** 5-7

**Acción inmediata:**
- Notificación a Mariano normal (no urgente)
- Llamar en las **próximas 24 horas**

**Flujo:** `centrum` → `intake-director` → `call-prep` → agendar llamada

---

## C — NO CUALIFICADO

**Definición:** sin hipoteca, fuera de zona geográfica, caso sin viabilidad clara, o información insuficiente.

**Señales:**
- No tiene hipoteca (es alquiler, vivienda heredada sin gravamen, etc.)
- Fuera de Cataluña sin caso fuerte
- Inquilino con problema con el propietario (no es el cliente de Centrum)
- Spam o broma evidente
- Información tan incompleta que no se puede valorar

**Score típico:** 1-3

**Acción inmediata:**
- Respuesta amable + derivar a otro recurso si aplica (PAH, oficinas municipales)
- **Nunca hacer sentir mal al lead** — pueden conocer a alguien que sí encaje
- Cierre con tono cálido

**Flujo:** `auto-responder` envía mensaje cordial, caso archivado

---

## D — DERIVAR ABOGADO

**Definición:** fase judicial muy avanzada que requiere defensa legal urgente, más allá de lo que Centrum gestiona en primera instancia desde el broker.

**Señales:**
- Procedimiento en fase final (lanzamiento próximo / subasta celebrada)
- Necesidad de oposición formal con plazos vencidos o por vencer en días
- Casos con concursalidad activa (segunda oportunidad ya iniciada)
- Demanda con respuesta vencida o por vencer en 48h

**Score típico:** variable — **la urgencia judicial manda sobre el score**

**Acción inmediata:**
- Mariano revisa **personalmente** y decide si pasa al abogado de confianza
- Notificación urgente a Mariano con resumen del estado procesal

**Flujo:** `centrum` → notificación urgente Mariano → Mariano decide → abogado de confianza

---

## E — ENTREGA DE POSESIÓN

**Definición:** cliente quiere **entregar voluntariamente** el inmueble a cambio de un pago único. No quiere litigar ni quedarse. Caso para broker + inversor.

**Señales:**
- Cliente dice claramente "quiero entregar la casa"
- Cliente quiere irse del piso (mudarse, vender, dejar de pelear)
- Cliente pregunta directamente por dación, entrega, venta rápida
- Cliente acepta perder la propiedad si recibe algo a cambio

**Score típico:** 4-7 (viable pero sin urgencia de defensa)

**Acción inmediata:**
- Activar flujo específico de **estrategia 2** (entrega a inversor)
- `sale-evaluator` analiza directamente tras análisis básico
- Coordinar con red de inversores

**Flujo:** `centrum` → `analysis-director` (versión light) → `sale-evaluator` directo → propuesta inversor

---

## Regla de oro: en duda, subir urgencia

Si la información es ambigua entre **A y B**, asigno **A** y lo indico.
Si la información es ambigua entre **B y C**, asigno **B** y lo indico.
Nunca clasifico un lead A como B por falta de datos.

La velocidad sobre la perfección: Mariano puede recalibrar en 2 minutos, pero un caso A clasificado mal como B puede llegar tarde a la subasta.

---

## NO confundir nunca

| Confusión típica | Cómo evitarla |
|------------------|----------------|
| **E con C** | E tiene solución real (entrega + pago único). C es genuinamente no cualificado. Si el cliente quiere entregar → es E, nunca C |
| **A con D** | A es urgente para Centrum (subasta/demanda — gestionable). D es urgencia que **sólo abogado** puede resolver en horas |
| **B con A** | A tiene urgencia legal con plazo (subasta, demanda con plazo activo). B tiene urgencia emocional pero margen de días/semanas |

---

## Output estándar del clasificador

```json
{
  "lead_id": "<id>",
  "categoria": "A/B/C/D/E",
  "razon": "<1 frase>",
  "accion_inmediata": "<qué hacer ahora>",
  "flujo_siguiente": "<bloque o sub-rol al que va>",
  "confianza": "ALTA/MEDIA/BAJA",
  "datos_faltantes": ["<si confianza no es alta, qué falta>"]
}
```

Si la categoría es **A** → adicionalmente: notificación Telegram a Mariano en <30s con el JSON resumido.
