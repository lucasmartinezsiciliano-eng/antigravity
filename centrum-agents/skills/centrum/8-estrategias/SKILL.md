---
name: centrum-8-estrategias
description: Las 8 estrategias de salida de Centrum para casos de deuda hipotecaria. Se activa en todo razonamiento sobre solución, recomendación, matching, evaluación legal o comunicación al cliente. Filosofía Mariano "siempre hay una salida".
version: 1
---

# Las 8 estrategias de Centrum

> **Filosofía Mariano:** "Varias veces las soluciones que el cliente creía imposibles resultaron viables."
>
> Las 8 se **evalúan siempre**. Ninguna se descarta sin razón explícita documentada.

---

## 1. Quedarse el máximo tiempo en la vivienda

**Esencia:** estirar plazos legalmente disponibles (oposiciones, recursos, paralizaciones por cláusulas, requisitos formales del banco). El cliente sigue en su casa mientras se gana tiempo.

**Cuándo aplica:** familia con hijos, sin alternativa habitacional inmediata, voluntad de luchar.

**Próximo paso típico:** revisar fase procesal exacta, identificar paralizaciones disponibles, coordinar con abogado de confianza.

## 2. Entregar posesión a inversor + pago único + derecho de explotación X años

**Esencia:** inversor compra el inmueble (o asume la deuda con quita), paga al cliente un pago único, y mantiene al cliente como inquilino X años a precio accesible. Resuelve banco y da liquidez al cliente.

**Cuándo aplica:** deuda > valor, cliente acepta soltar la propiedad pero quiere quedarse o irse con dinero.

**Próximo paso típico:** valoración del inmueble, contacto con red de inversores de Centrum, simular escenario.

## 3. Negociar quita + vender el piso con remanente para el cliente

**Esencia:** banco acepta condonar parte de la deuda, el cliente vende el piso y se queda con el remanente. Sale sin deuda y con dinero.

**Cuándo aplica:** deuda < valor de mercado, banco con margen para negociar (banco originario, no siempre fondo buitre).

**Próximo paso típico:** valoración real, análisis perfil banco, preparar oferta de quita.

## 4. Negociar quita + familiar obtiene hipoteca nueva para comprar el piso

**Esencia:** banco acepta quita, un familiar del cliente (hijo/a, hermano/a, padre) consigue una hipoteca nueva y compra el piso. El cliente sigue viviendo, el familiar es propietario.

**Cuándo aplica:** familiar con solvencia y disponibilidad, voluntad familiar de ayudar.

**Próximo paso típico:** verificar perfil financiero del familiar, simular hipoteca nueva, evaluar viabilidad real.

## 5. Denunciar cláusulas abusivas + quedarse mientras dura el proceso

**Esencia:** detectar cláusula abusiva (suelo, IRPH, vencimiento anticipado, gastos), denunciar, suspender procedimiento ejecutivo. Gana tiempo y, si la cláusula prospera, recalcula la deuda a la baja.

**Cuándo aplica:** hipoteca anterior a 2013 (alta probabilidad de cláusulas), cualquier hipoteca donde se detecte vencimiento anticipado mal aplicado.

**Próximo paso típico:** auditoría de cláusulas, dictamen del abogado de confianza, decisión sobre denuncia.

## 6. Defender al cliente contestando la demanda

**Esencia:** el cliente está en fase judicial, se contesta la demanda con defensa activa: requisitos formales, cláusulas, vicios procesales, oposición a la ejecución. Puede paralizar o ralentizar mucho el procedimiento.

**Cuándo aplica:** demanda ya interpuesta, cliente quiere defenderse.

**Próximo paso típico:** abogado de confianza estudia expediente y diseña defensa.

## 7. Contrato de alquiler inscrito en Registro con opción a compra + subarrendar

**Esencia:** se firma alquiler en escritura pública e inscribe en Registro, con opción a compra y derecho a subarrendar habitaciones. El banco ya no puede subastar libre, el cliente puede generar ingresos extra.

**Cuándo aplica:** voluntad del cliente de quedarse, configuración del inmueble para subarrendar (habitaciones), banco lento en ejecución.

**Próximo paso típico:** notaría, registro, redacción contrato.

## 8. Ganar tiempo máximo para ahorrar sin pagar cuota ni alquiler

**Esencia:** la red de seguridad. Aunque el caso parece perdido, se estiran 2-10 años en la vivienda sin pagar cuota ni alquiler. Lo que el cliente ahorra en ese período le permite recomprar en subasta (si interesa), comprar otro piso, o reconstruir su vida.

**Cuándo aplica:** **siempre como suelo de garantía.** Aunque otras soluciones no prosperen, este escenario base existe.

**Próximo paso típico:** calcular tiempo realista de procedimiento, modelar ahorro acumulado del cliente.

---

## Lógica de decisión principal (validada por Mariano)

| Condición | Estrategias prioritarias |
|-----------|--------------------------|
| Deuda < valor inmueble | **3** (venta con remanente) |
| Deuda > valor inmueble | **2 → 4 → 5 → 1 → 8** |
| Banco negociador | **3** y **4** muy viables |
| Fondo buitre | **2** suele ser más rápido y limpio |
| Cláusulas abusivas detectadas | **5** como palanca de negociación, aunque no se litigue |
| Familiar disponible y solvente | **4** explorar activamente |
| Hijos pequeños / arraigo escolar | **1** + **7** prioritarias |
| Cliente quiere irse y olvidarse | **E** (entrega posesión) — categoría especial |

## Estructura del matching (output estándar)

```
MATCHING DE SOLUCIONES — CTR-<id>
────────────────────────────────────
SOLUCIONES VIABLES (ordenadas por viabilidad real):
1. <solución> | Viabilidad: ALTA/MEDIA/BAJA
   Razón: <basada en datos del análisis>
   Próximo paso: <acción concreta>

2. <solución> | …

3. <si aplica>

SOLUCIONES DESCARTADAS:
<solución> — Razón: <por qué no aplica con estos datos>
────────────────────────────────────
```

## Reglas absolutas al usar esta skill

- Evalúo **las 8 siempre**, ninguna se omite del razonamiento aunque al final se descarte
- Cada descarte lleva razón explícita
- El ranking es por **viabilidad real**, no por lo que parece más fácil
- La estrategia 8 es el **suelo de garantía** — ningún caso sale sin al menos esto
- Las palabras "no se puede" o "no hay solución" no existen en mi vocabulario; existen "viabilidad baja" y "requiere más datos"
