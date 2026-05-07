"""
VISAI Email Service

Transactional (Resend REST — no extra dependency, uses httpx already in requirements):
  - send_payment_confirmed   → after Stripe webhook payment
  - send_analysis_ready      → after face analysis completes
  - send_photos_reminder     → 24h after payment if photos not uploaded (scheduled via n8n)

Marketing (n8n webhook — fire and forget):
  - trigger_n8n_marketing_sequence → starts 4-email sequence in n8n
    Only called when analysis.marketing_consent = True

n8n workflow design:
  Trigger: POST /webhook/visai-marketing
  Body: { email, analysis_id, created_at, result_url }
  Flow:
    → Send welcome email (Resend node)
    → Wait 48h
    → Send "Muéstrale a tu barbero" email
    → Wait 5 days (day 7 total)
    → HTTP GET /api/v1/analysis/{analysis_id}
    → IF includes_colorimetry=false AND includes_products_guide=false
       → Send upsell email
    → Wait 23 days (day 30 total)
    → Send re-engagement email
"""

import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal sender — Resend REST API (httpx, already in requirements)
# ---------------------------------------------------------------------------
async def _send(to: str, subject: str, html: str) -> None:
    if not settings.RESEND_API_KEY:
        logger.debug("RESEND_API_KEY not configured — skipping email to %s | %s", to, subject)
        return
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": settings.RESEND_FROM_EMAIL,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                },
                timeout=10.0,
            )
        if resp.status_code not in (200, 201):
            logger.error("Resend error %d for %s: %s", resp.status_code, to, resp.text[:200])
        else:
            logger.info("Email sent → %s | %s", to, subject)
    except Exception as e:
        logger.error("Email send failed for %s: %s", to, e)


# ---------------------------------------------------------------------------
# Transactional emails
# ---------------------------------------------------------------------------
async def send_payment_confirmed(to_email: str, analysis_id: str) -> None:
    await _send(
        to=to_email,
        subject="Pago confirmado — sube tus fotos | VISAI",
        html=_payment_confirmed_html(analysis_id),
    )


async def send_analysis_ready(to_email: str, analysis_id: str) -> None:
    await _send(
        to=to_email,
        subject="Tu análisis VISAI está listo",
        html=_analysis_ready_html(analysis_id),
    )


# ---------------------------------------------------------------------------
# n8n marketing webhook
# ---------------------------------------------------------------------------
async def trigger_n8n_marketing_sequence(
    email: str,
    analysis_id: str,
    created_at_iso: str,
) -> None:
    if not settings.N8N_MARKETING_WEBHOOK_URL:
        logger.debug("N8N_MARKETING_WEBHOOK_URL not set — skipping marketing trigger for %s", email)
        return
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                settings.N8N_MARKETING_WEBHOOK_URL,
                json={
                    "email": email,
                    "analysis_id": analysis_id,
                    "created_at": created_at_iso,
                    "result_url": f"{settings.FRONTEND_URL}/result/{analysis_id}",
                    "capture_url": f"{settings.FRONTEND_URL}/capture/{analysis_id}",
                    "unsubscribe_url": f"{settings.FRONTEND_URL}/baja-email?id={analysis_id}",
                },
                timeout=5.0,
            )
        logger.info("n8n marketing trigger → %d for %s", resp.status_code, email)
    except Exception as e:
        logger.error("n8n marketing webhook failed for %s: %s", email, e)


# ---------------------------------------------------------------------------
# HTML email templates — minimal dark design matching VISAI brand
# ---------------------------------------------------------------------------
def _wrap(body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    body  {{ margin:0; padding:0; background:#080808; color:#e8e8e8;
             font-family:-apple-system,'Segoe UI',sans-serif; font-size:15px; }}
    .wrap {{ max-width:520px; margin:40px auto; padding:0 24px; }}
    .logo {{ font-size:20px; font-weight:800; letter-spacing:5px; color:#e8e8e8; margin-bottom:28px; }}
    .card {{ background:#101010; border:1px solid #1e1e1e; border-radius:16px; padding:28px; margin-bottom:12px; }}
    h2   {{ font-size:20px; font-weight:700; margin:0 0 10px; line-height:1.2; }}
    p    {{ color:#888; line-height:1.65; margin:0 0 14px; }}
    .btn {{ display:block; background:#e8e8e8; color:#080808; text-decoration:none; text-align:center;
            padding:16px 24px; border-radius:999px; font-weight:700; font-size:15px; margin:20px 0 0; }}
    .foot {{ text-align:center; font-size:11px; color:#333; margin-top:28px; line-height:1.9; }}
    .foot a {{ color:#444; text-decoration:none; }}
  </style>
</head>
<body>
<div class="wrap">
  <div class="logo">VISAI</div>
  {body}
  <div class="foot">
    VISAI &nbsp;·&nbsp;
    <a href="{settings.FRONTEND_URL}/privacidad">Privacidad</a> &nbsp;·&nbsp;
    <a href="{settings.FRONTEND_URL}/baja-email">Darse de baja</a><br>
    Recibiste este email porque realizaste un análisis o diste consentimiento de marketing.
  </div>
</div>
</body>
</html>"""


def _payment_confirmed_html(analysis_id: str) -> str:
    return _wrap(f"""
<div class="card">
  <h2>Pago confirmado ✓</h2>
  <p>Ya puedes subir tus fotos. El análisis tarda <strong style="color:#e8e8e8">aproximadamente 60 segundos</strong>
     y recibirás 3 cortes personalizados para tu forma de cara.</p>
  <a href="{settings.FRONTEND_URL}/capture/{analysis_id}" class="btn">Subir fotos ahora →</a>
</div>
<div class="card">
  <p style="font-size:13px;margin:0">ID de análisis: <code style="color:#444">{analysis_id}</code><br>
  Guárdalo por si necesitas acceder a tu resultado más tarde.</p>
</div>""")


def _analysis_ready_html(analysis_id: str) -> str:
    return _wrap(f"""
<div class="card">
  <h2>Tu análisis está listo</h2>
  <p>Hemos analizado tu morfología facial. Ya tienes disponibles tus <strong style="color:#e8e8e8">3 cortes personalizados</strong>
     con instrucciones exactas para pedir en tu barbería.</p>
  <a href="{settings.FRONTEND_URL}/result/{analysis_id}" class="btn">Ver mi análisis →</a>
</div>
<div class="card">
  <p style="font-size:13px;margin:0">Tu informe estará disponible durante
  <strong style="color:#e8e8e8">90 días</strong>.
  Guarda el link para tenerlo siempre a mano.</p>
</div>""")
