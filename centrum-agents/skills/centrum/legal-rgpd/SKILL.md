---
name: centrum-legal-rgpd
description: Cuándo y cómo se obtiene el consentimiento legal del cliente en el embudo de Centrum (RGPD/LOPDGDD/AI Act). Se activa en captación, llamada IA, solicitud de documentos y cualquier cesión a terceros. Define las 2 capas de consentimiento y qué bloquea cada una. Responsable: Mediterránea Firmax SL.
version: 1
---

# Legal y RGPD — consentimiento en el embudo de Centrum

> **Responsable del tratamiento:** Mediterránea Firmax SL (NIF B26553248).
> **Esta skill NO sustituye al abogado.** Ningún documento legal se genera para firma sin OK de Mariano (guardrails). Las plantillas las valida el abogado de confianza.

---

## Las 2 capas de consentimiento (regla central)

### CAPA 1 — Consentimiento ligero (informativo)
- **Cuándo:** primer contacto (formulario web, DM, inicio de la call IA).
- **Qué:** información art. 13 RGPD + permiso de contacto + consentimiento de grabación.
- **Cómo:** checkbox + enlace a política de privacidad (web/DM) · consentimiento verbal grabado (call IA).
- **Permite:** *recoger* datos y *hablar* con el cliente.
- **Base legal:** medidas precontractuales (art. 6.1.b) + consentimiento (art. 6.1.a).

### CAPA 2 — Firma formal (vinculante)
- **Cuándo:** al **abrir expediente**, tras la consulta gratuita con Mariano y **ANTES** de pedir documentación sensible o ceder datos a terceros.
- **Qué:** hoja de encargo + consentimiento RGPD completo + autorización de cesión a colaboradores (abogado/inmobiliaria/inversores) + ratificación de grabación.
- **Cómo:** firma electrónica con validez eIDAS (Signaturit), con sello de tiempo y pista de auditoría.
- **Permite:** *tratar a fondo* el caso y *ceder* a terceros.

> **Regla de oro:** con CAPA 1 se puede recoger el dato; **sin CAPA 2 firmada NO se piden documentos sensibles ni accede ningún tercero.**

---

## Qué bloquea cada cosa (para razonar en el flujo)

| Acción | Requiere | Quién lo verifica |
|---|---|---|
| Captar lead / primer mensaje | Capa 1a (checkbox + política) | form-analyzer / dm-qualifier |
| Grabar la call IA | Capa 1b (consentimiento verbal) | Ana (`call-vendedor`) |
| Consulta gratuita con Mariano | Capa 1 | — |
| Pedir documentos sensibles (escrituras, nóminas...) | **Capa 2 firmada** | `rgpd-guardian` (bloquea si falta) |
| Que el abogado/inmobiliaria/inversor vea el caso | **Capa 2 firmada** + encargo art. 28 | `rgpd-guardian` |
| Enviar email/WhatsApp al cliente | consentimiento de canal + footer RGPD | `rgpd-guardian` |

---

## Reglas absolutas al usar esta skill

- **Nunca** pedir documentación sensible ni ceder datos a un tercero sin la Capa 2 firmada.
- **Nunca** generar el documento legal para firma sin OK de Mariano.
- **Nunca** prometer al cliente sobre sus derechos como certeza legal — eso es del abogado.
- Ana y el dm-qualifier **informan** del tratamiento y **piden** consentimiento, pero **no asesoran** jurídicamente: derivan a Mariano/abogado.
- Footer RGPD obligatorio en toda comunicación al cliente.
- Ante duda sobre si una acción cumple → **no se actúa, se escala** (guardrails: silencio ante la duda).

## Flags abiertos (verificar con abogado, no asumir resueltos)

- AI Act art. 50: declarar que Ana es IA (por defecto activo).
- Grabación: base legal + conservación.
- Cesión a terceros: por categorías o nominados + contratos de encargo (art. 28).
- DPIA (art. 35): probablemente obligatoria (perfilado + IA + colectivo vulnerable).
- Transferencias internacionales (Twilio/Google EE.UU.): SCC / Data Privacy Framework.

> Detalle completo y mapa del embudo: vault `Broker/Centrum/Legal y RGPD — Cuándo firma el cliente.md`.
