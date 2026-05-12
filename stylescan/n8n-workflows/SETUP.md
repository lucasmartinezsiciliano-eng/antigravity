# VISAI — n8n Workflows Setup

## Workflows incluidos

| Archivo | Trigger | Qué hace |
|---------|---------|----------|
| `WF_VISAI_Marketing_CRM.json` | Webhook POST del backend | CRM + secuencia 4 emails (day 0, 2, 7, 30) |

---

## Credenciales necesarias

### 1. Resend (emails transaccionales)
- Regístrate en [resend.com](https://resend.com) — plan gratis: 3.000 emails/mes
- Dashboard → API Keys → **Create API Key**
- Verificar el dominio `visaiapp.com` en Resend (DNS TXT record)
- Guarda la key como `re_xxxxxxxxx`

### 2. Twenty CRM API Key
- Abre [twenty-production-8066.up.railway.app](https://twenty-production-8066.up.railway.app)
- Settings → API → **New API Key**
- Guarda el token generado

### 3. n8n URL del workflow
- El webhook path es `/webhook/visai-marketing`
- URL completa: `https://TU-N8N-DOMINIO/webhook/visai-marketing`

---

## Configuración Railway (backend VISAI)

Añade estas variables de entorno en el servicio `harmonious-gratitude` en Railway:

| Variable | Valor |
|----------|-------|
| `RESEND_API_KEY` | `re_xxxxxxxxx` |
| `RESEND_FROM_EMAIL` | `VISAI <noreply@visaiapp.com>` |
| `N8N_MARKETING_WEBHOOK_URL` | `https://TU-N8N-DOMINIO/webhook/visai-marketing` |

---

## Importar el workflow en n8n

1. Abre n8n → **Workflows** → **Import from file**
2. Selecciona `WF_VISAI_Marketing_CRM.json`
3. En los nodos HTTP Request, busca `{{RESEND_API_KEY}}` y `{{TWENTY_API_KEY}}` y reemplaza con los valores reales
4. Activa el workflow → copia la URL del webhook
5. Pon esa URL en Railway como `N8N_MARKETING_WEBHOOK_URL`

---

## Flujo completo

```
Usuario paga (Stripe) 
  → Backend: payments.py → _handle_checkout_completed
  → Email directo: "Pago confirmado — sube tus fotos" (Resend, sin n8n)
  → SI marketing_consent=True:
      → POST n8n webhook → WF_VISAI_Marketing_CRM
          → Twenty CRM: crea persona + nota
          → Email day 0: "Ya tienes tu look documentado"
          → Wait 48h
          → Email day 2: "Muéstraselo a tu barbero"
          → Wait 5 días
          → Comprueba si compró upsell
          → SI no → Email day 7: "Añade colorimetría €2,49"
          → Wait 23 días
          → Email day 30: "¿Cuándo fue tu último corte?"

Usuario sube fotos → Análisis completa
  → Email directo: "Tu análisis está listo" (Resend, sin n8n)
```

---

## Twenty CRM — qué se registra

Por cada cliente que da consentimiento de marketing:
- **Persona**: email como identificador principal
- **Nota**: analysis_id, fecha, resultado URL, importe pagado

Puedes ver los clientes en: [twenty-production-8066.up.railway.app](https://twenty-production-8066.up.railway.app)

---

## Próximos pasos opcionales

- [ ] Añadir Telegram alert en n8n cuando llega nuevo cliente
- [ ] Workflow separado para clientes sin consentimiento (CRM only, sin emails)
- [ ] Dashboard analytics en Twenty con pipeline de conversión
