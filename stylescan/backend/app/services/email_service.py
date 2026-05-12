"""
VISAI Email Service

Transactional (Resend REST via httpx):
  - send_payment_confirmed   → after Stripe webhook confirms payment
  - send_analysis_ready      → after face analysis completes (called from analysis.py bg task)

Marketing (n8n webhook — only when marketing_consent=True):
  - trigger_n8n_marketing_sequence → starts 4-email sequence in n8n
    n8n handles: welcome (day 0) → tip (day 2) → upsell (day 7) → re-engagement (day 30)
    n8n also creates/updates the customer in Twenty CRM.
"""

import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal sender — Resend REST API
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
        subject="Tu análisis VISAI está listo 🎯",
        html=_analysis_ready_html(analysis_id),
    )


# ---------------------------------------------------------------------------
# n8n marketing webhook — fires only when marketing_consent=True
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
                    "marketing_consent": True,
                },
                timeout=5.0,
            )
        logger.info("n8n marketing trigger → %d for %s", resp.status_code, email)
    except Exception as e:
        logger.error("n8n marketing webhook failed for %s: %s", email, e)


# ---------------------------------------------------------------------------
# HTML email builder — dark gold brand, table-based for Gmail/Outlook
# ---------------------------------------------------------------------------
def _base(
    *,
    badge: str,
    headline: str,
    body_html: str,
    cta_url: str,
    cta_label: str,
    unsubscribe_url: str = "",
    note_html: str = "",
) -> str:
    unsub = unsubscribe_url or f"{settings.FRONTEND_URL}/baja-email"
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>VISAI</title>
</head>
<body style="margin:0;padding:0;background:#0a0a0a;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#0a0a0a;min-height:100vh;">
  <tr><td align="center" style="padding:48px 20px 32px;">
    <table width="520" cellpadding="0" cellspacing="0" border="0" style="max-width:520px;width:100%;">

      <!-- LOGO -->
      <tr><td style="padding-bottom:36px;">
        <span style="font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;font-size:17px;font-weight:800;letter-spacing:7px;color:#f0f0f0;text-transform:uppercase;">VISAI</span>
      </td></tr>

      <!-- MAIN CARD -->
      <tr><td style="background:#111111;border:1px solid #1c1c1c;border-radius:14px;padding:36px 32px;">

        <!-- BADGE -->
        <table cellpadding="0" cellspacing="0" border="0" style="margin-bottom:24px;">
          <tr><td style="background:#160f00;border:1px solid rgba(201,168,76,0.3);border-radius:99px;padding:5px 14px;">
            <span style="font-family:-apple-system,Arial,sans-serif;font-size:10px;font-weight:700;letter-spacing:2px;color:#c9a84c;text-transform:uppercase;">{badge}</span>
          </td></tr>
        </table>

        <!-- HEADLINE -->
        <h1 style="font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;font-size:24px;font-weight:700;color:#f0f0f0;margin:0 0 14px;line-height:1.2;">{headline}</h1>

        <!-- BODY -->
        {body_html}

        <!-- CTA BUTTON -->
        <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-top:28px;">
          <tr><td>
            <a href="{cta_url}"
               style="display:block;background:#c9a84c;color:#080808;text-decoration:none;text-align:center;padding:17px 24px;border-radius:8px;font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;font-weight:700;font-size:15px;letter-spacing:-0.2px;">{cta_label} &rarr;</a>
          </td></tr>
        </table>

        {f'<p style="font-family:-apple-system,Arial,sans-serif;font-size:12px;color:#444;margin:20px 0 0;line-height:1.6;">{note_html}</p>' if note_html else ''}
      </td></tr>

      <!-- FOOTER -->
      <tr><td style="padding-top:28px;text-align:center;">
        <p style="font-family:-apple-system,Arial,sans-serif;font-size:11px;color:#3a3a3a;line-height:1.9;margin:0;">
          VISAI &nbsp;&middot;&nbsp;
          <a href="{settings.FRONTEND_URL}/privacidad" style="color:#4a4a4a;text-decoration:none;">Privacidad</a> &nbsp;&middot;&nbsp;
          <a href="{unsub}" style="color:#4a4a4a;text-decoration:none;">Darse de baja</a><br>
          Recibes este email porque realizaste un an&aacute;lisis VISAI.
        </p>
      </td></tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""


def _payment_confirmed_html(analysis_id: str) -> str:
    return _base(
        badge="PAGO CONFIRMADO",
        headline="Ya puedes subir tus fotos",
        body_html="""
<p style="font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;font-size:15px;color:#888;line-height:1.65;margin:0 0 10px;">
  El análisis tarda aproximadamente <strong style="color:#d0d0d0;">60 segundos</strong> y recibirás
  3 cortes personalizados con instrucciones exactas para tu barbero.
</p>
<p style="font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;font-size:15px;color:#888;line-height:1.65;margin:0;">
  Necesitarás 5 fotos bajo buena luz: frente, perfil izquierdo, perfil derecho y dos ángulos de 45°.
</p>""",
        cta_url=f"{settings.FRONTEND_URL}/capture/{analysis_id}",
        cta_label="Subir mis fotos",
        note_html=f"ID de an&aacute;lisis: <code style='font-family:monospace;color:#555;'>{analysis_id}</code>",
    )


def _analysis_ready_html(analysis_id: str) -> str:
    return _base(
        badge="ANÁLISIS LISTO",
        headline="Tus 3 cortes personalizados están listos",
        body_html="""
<p style="font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;font-size:15px;color:#888;line-height:1.65;margin:0 0 10px;">
  Hemos analizado tu morfolog&iacute;a facial con <strong style="color:#d0d0d0;">468 puntos de referencia</strong> y
  calculado los cortes que mejor equilibran tu forma de cara.
</p>
<p style="font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;font-size:15px;color:#888;line-height:1.65;margin:0;">
  Tu resultado incluye instrucciones exactas para la barber&iacute;a: n&uacute;mero de m&aacute;quina, tipo de degradado y
  t&eacute;cnica espec&iacute;fica.
</p>""",
        cta_url=f"{settings.FRONTEND_URL}/result/{analysis_id}",
        cta_label="Ver mi análisis",
        note_html="Tu informe estar&aacute; disponible durante <strong style='color:#666;'>90 d&iacute;as</strong>. Gu&aacute;rda el link.",
    )
