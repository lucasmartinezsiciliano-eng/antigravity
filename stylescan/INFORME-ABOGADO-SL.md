# INFORME PARA ASESOR JURÍDICO
## Constitución de Sociedad Limitada — Proyecto VISAI

**Fecha:** Mayo 2026  
**Promotor:** Lucas Martínez Siciliano  
**Contacto:** lucas.martinez.siciliano@gmail.com  
**Web:** visaiapp.com

---

## 1. QUÉ ES VISAI

VISAI es una aplicación móvil web de análisis facial por inteligencia artificial dirigida al sector de la barbería masculina en España. El usuario se hace entre 3 y 5 fotos del rostro desde su móvil, la IA analiza su morfología craneal y proporciones faciales, y genera un informe digital personalizado con recomendaciones de corte de cabello adaptadas a su tipo de cabeza.

El servicio se entrega de forma inmediata, íntegramente online, previo pago con tarjeta.

**Estado actual:** producto en fase final de desarrollo, con arquitectura técnica completa, términos legales redactados y flujo de pago integrado. Pendiente de lanzamiento comercial.

---

## 2. MODELO DE NEGOCIO

### Ingresos directos (B2C)

| Producto | Precio orientativo (IVA inc.) |
|---|---|
| Análisis facial básico | ~9,99 € |
| Add-on colorimetría | ~4,99 € |
| Add-on guía de productos | ~4,99 € |
| Pack completo | ~14,99 € |
| Análisis de temporada | ~2,99 € |

### Canal de distribución (B2B2C — Barberías colaboradoras)

Las barberías se registran como socias y reciben un **código de barbería** personal. Cuando un cliente compra a través del código de su barbero, la barbería recibe una comisión (porcentaje a definir) y el cliente accede a un precio especial. Este canal es el principal motor de adquisición de usuarios previsto.

**Relación jurídica con barberías:** actualmente no formalizada. Necesita contrato. Ver sección 6.

### Proyección

El negocio está diseñado para operar con costes variables bajos (pago por uso de APIs de IA) y márgenes altos por análisis. No requiere plantilla inicial. El promotor opera en solitario en fase de lanzamiento.

---

## 3. TECNOLOGÍA Y FLUJO DE DATOS (resumen ejecutivo)

Es fundamental que el abogado comprenda cómo fluyen los datos para valorar el marco de responsabilidad:

```
USUARIO
  │
  ├─ Sube 3-5 fotos del rostro desde el móvil
  │
  ▼
SERVIDOR BACKEND (Railway — infraestructura cloud, jurisdicción UE)
  │
  ├─ MediaPipe (Google) — análisis facial LOCAL en servidor
  │   Extrae métricas numéricas (proporciones, distancias)
  │   LA IMAGEN ORIGINAL NO SE ALMACENA
  │
  ├─ fal.ai (EE.UU.) — generación de imagen virtual try-on
  │   Recibe la foto del usuario para procesar
  │
  ├─ Anthropic / OpenRouter (EE.UU.) — generación del informe de texto
  │   Recibe las métricas (NO la foto)
  │
  └─ Stripe (EE.UU.) — cobro
      VISAI nunca ve datos de tarjeta
```

**Dato crítico:** la foto original del usuario se elimina del servidor inmediatamente después del análisis. Solo se conservan las métricas numéricas derivadas durante 90 días. Los registros de consentimiento se conservan 5 años (obligación legal LOPDGDD).

---

## 4. MARCO LEGAL YA IMPLEMENTADO

El promotor ha trabajado con rigor en la capa legal antes del lanzamiento. Lo que ya existe:

### 4.1 Protección de datos (RGPD)

- **Flujo de consentimiento biométrico en 5 pasos** antes de que el usuario pueda subir fotos, con:
  - Consentimiento al tratamiento de datos biométricos (categoría especial Art. 9.2.a RGPD)
  - Consentimiento al tratamiento de datos de categoría especial (Art. 9.2.a)
  - Consentimiento a la retención de 90 días
  - Consentimiento a la eliminación inmediata de la foto
  - Verificación de mayoría de edad (declaración del usuario)
- **Hash del texto de consentimiento mostrado** almacenado en base de datos para acreditar qué texto exacto leyó y aceptó cada usuario
- **Política de privacidad** completa con bases jurídicas diferenciadas (Art. 6.1.a, 6.1.b, 6.1.c, 6.1.f y Art. 9.2.a RGPD)
- **Derecho de supresión (Art. 17)** implementado técnicamente: endpoint `/analysis/{id}` DELETE que borra todos los datos del análisis
- **Derecho de baja de marketing** implementado: endpoint `/analysis/{id}/unsubscribe`
- **Plazos de conservación** diferenciados por tipo de dato y documentados

### 4.2 Condiciones de servicio

- Carácter orientativo del análisis explicitamente declarado (no diagnóstico médico)
- Limitación de responsabilidad al importe abonado
- Restricción de uso a mayores de 18 años
- Prohibición de subida de imágenes de terceros
- Propiedad intelectual del informe generado atribuida a VISAI con licencia de uso personal al cliente
- Ley española aplicable / fuero del consumidor

### 4.3 Pagos

- Integración con **Stripe** (PCI-DSS compliant). VISAI no almacena datos de tarjeta.
- Política de reembolso existente (página `/reembolso` en la aplicación)
- IVA incluido en precios mostrados al consumidor

### 4.4 Transferencias internacionales

Tres encargados del tratamiento en EE.UU. identificados en la política de privacidad:
- **Stripe** — SCCs Comisión Europea vigentes
- **OpenRouter** — SCCs vigentes
- **fal.ai** — SCCs declaradas (pendiente verificar DPA firmado)

---

## 5. ESTRUCTURA SOCIETARIA A CONSTITUIR

### Forma jurídica recomendada: **Sociedad Limitada (SL)**

**Motivación principal:** VISAI trata datos biométricos (categoría especial RGPD). Una sanción de la AEPD puede alcanzar el 4% del volumen de negocio global o 20.000.000 €. Operar como autónomo expone el patrimonio personal del promotor de forma ilimitada. La SL limita la responsabilidad al capital social.

**Motivación secundaria:** El modelo con barberías implica contratos B2B con socios comerciales. Una SL da mayor imagen de seriedad y facilita la firma de acuerdos.

### Datos para la constitución

| Campo | Información disponible |
|---|---|
| Socio único | Lucas Martínez Siciliano |
| Administrador único | Lucas Martínez Siciliano |
| Objeto social | Desarrollo y comercialización de software de análisis facial por IA; servicios digitales al sector de la estética y peluquería; consultoría tecnológica |
| Domicilio social | **[Confirmar con promotor]** |
| Capital social | 3.000 € mínimo legal (pendiente decisión del promotor) |
| Denominación propuesta | VISAI Technologies SL / VISAI Studio SL / [a definir] |

**Nota:** la denominación "VISAI" y el dominio `visaiapp.com` ya están en uso operativo. Conviene verificar disponibilidad en el Registro Mercantil Central antes de la constitución.

---

## 6. CUESTIONES PRIORITARIAS PARA REVISAR

### 6.1 Contrato con barberías colaboradoras (URGENTE antes del lanzamiento)

El modelo de barberías es el canal principal de distribución. Actualmente no existe ningún contrato. Necesita regularse:

- **Naturaleza de la relación:** agente comercial, contrato de distribución, afiliación o colaboración mercantil. Importante definir para evitar que se reclasifique como relación laboral.
- **Comisión:** porcentaje, momento de devengo (¿al pago del cliente? ¿al finalizar el análisis?), forma de liquidación.
- **Obligaciones del barbero:** no usar el código de forma fraudulenta, no ceder el código a terceros.
- **Cláusula crítica — fotos de clientes:** si en el futuro las barberías aportan fotografías de sus trabajos para el sistema de referencia de VISAI, el contrato debe incluir una **cláusula de garantía de consentimiento**: el barbero certifica que dispone del consentimiento expreso de cada persona fotografiada para (a) uso comercial, (b) uso en sistemas de IA, (c) exposición a terceros usuarios de la plataforma. VISAI queda indemnizada ante cualquier reclamación derivada de un consentimiento inexistente o insuficiente.

### 6.2 Desistimiento y política de reembolso

La LGDCU otorga 14 días de desistimiento en contratos digitales. Existe excepción cuando el servicio digital se ha prestado íntegramente con consentimiento expreso del consumidor (Art. 103.m LGDCU). VISAI entrega el informe de forma inmediata al finalizar el análisis, lo que encajaría en esa excepción.

**Acción necesaria:** añadir en el checkout una casilla específica donde el usuario consiente expresamente que el servicio se ejecutará de forma inmediata y que por tanto renuncia al derecho de desistimiento. Actualmente no existe esta casilla.

### 6.3 Verificación de edad

Los términos exigen mayoría de 18 años, pero la verificación es una mera declaración del usuario. El tratamiento de datos biométricos de menores sin verificación efectiva puede generar responsabilidad. Consultar si en el contexto actual es suficiente la declaración responsable o si se requiere algún mecanismo adicional.

### 6.4 Responsable del tratamiento en la política de privacidad

La política de privacidad actual tiene los campos de responsable del tratamiento en blanco (`[COMPLETAR]`): denominación, NIF y domicilio. Estos campos se rellenan con los datos de la SL en el momento de la constitución. No se puede publicar el producto comercialmente con esos campos vacíos.

### 6.5 Evaluación de Impacto (DPIA)

El RGPD (Art. 35) exige realizar una Evaluación de Impacto relativa a la Protección de Datos (DPIA) cuando el tratamiento puede entrañar un alto riesgo, en particular cuando se tratan datos biométricos a gran escala. Consultar si a la escala inicial de VISAI es ya obligatorio o si aplica algún umbral mínimo.

---

## 7. LO QUE NO NECESITA REVISIÓN INMEDIATA

Para no consumir tiempo innecesario en la reunión:

- **La arquitectura de consentimiento biométrico** está bien construida técnicamente y jurídicamente.
- **Los plazos de retención** están correctamente diferenciados y documentados.
- **La limitación de responsabilidad** en TOS es estándar y adecuada.
- **La integración de pagos** con Stripe es correcta desde el punto de vista del consumidor.
- **El carácter no médico** del servicio está suficientemente aclarado.

---

## 8. ORDEN DE PRIORIDADES PROPUESTO

| # | Acción | Cuándo |
|---|---|---|
| 1 | Elegir denominación social y verificar disponibilidad en RMC | Inmediato |
| 2 | Constituir la SL (escritura + Registro Mercantil) | Antes del lanzamiento |
| 3 | Completar campos responsable del tratamiento en política de privacidad | Al tener NIF/SL |
| 4 | Añadir casilla desistimiento en pantalla de checkout | Antes del lanzamiento |
| 5 | Redactar contrato tipo para barberías colaboradoras | Antes de firmar primeros acuerdos |
| 6 | Verificar DPA firmado con fal.ai | Antes del lanzamiento |
| 7 | Valorar necesidad de DPIA | Cuando se alcance volumen significativo |

---

*Documento preparado por el promotor para facilitar la reunión con el asesor jurídico. Toda la información técnica puede ser ampliada o contrastada directamente con el sistema en funcionamiento.*
