"""
Parental Consent Service

Handles sending authorization emails to parents of minors (12-17 years).
RGPD Art. 8: requires parental consent for biometric data of minors.

- send_parental_consent_email(parent_email, child_age, auth_token, expires_at)
  → Sends email with authorization link valid for 72 hours
"""

import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


async def _send_email(to: str, subject: str, html: str) -> None:
    """Internal Resend API wrapper."""
    if not settings.RESEND_API_KEY:
        logger.debug("RESEND_API_KEY not configured — skipping email to %s", to)
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
            logger.info("Parental consent email sent → %s", to)
    except Exception as e:
        logger.error("Parental consent email failed for %s: %s", to, e)


async def send_parental_consent_email(
    parent_email: str,
    child_age: int,
    authorization_token: str,
    expires_at_iso: str,
) -> None:
    """
    Send parental authorization email.
    Parent clicks link to authorize child's biometric analysis.
    Token valid for 72 hours.
    """
    auth_url = f"{settings.FRONTEND_URL}/parental-consent/authorize?token={authorization_token}"

    html = _parental_consent_html(
        child_age=child_age,
        authorization_url=auth_url,
        expires_at=expires_at_iso,
    )

    await _send_email(
        to=parent_email,
        subject="Autorización requerida para análisis facial | VISAI",
        html=html,
    )


def _parental_consent_html(
    child_age: int,
    authorization_url: str,
    expires_at: str,
) -> str:
    """
    HTML template for parental consent email.
    GDPR compliant: explains what biometric data is used for,
    how long it's retained, and gives parent clear authorization path.
    """
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>Autorización requerida — VISAI</title>
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
            <span style="font-family:-apple-system,Arial,sans-serif;font-size:10px;font-weight:700;letter-spacing:2px;color:#c9a84c;text-transform:uppercase;">AUTORIZACIÓN REQUERIDA</span>
          </td></tr>
        </table>

        <!-- HEADLINE -->
        <h1 style="font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;font-size:24px;font-weight:700;color:#f0f0f0;margin:0 0 14px;line-height:1.2;">Consentimiento para análisis facial</h1>

        <!-- BODY -->
        <p style="font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;font-size:15px;color:#888;line-height:1.65;margin:0 0 16px;">
          Hemos detectado que <strong style="color:#d0d0d0;">tu hijo/a (edad {child_age})</strong> ha iniciado un análisis facial con VISAI.
          Según la ley RGPD, requerimos tu autorización explícita para procesar datos biométricos de menores.
        </p>

        <p style="font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;font-size:15px;color:#888;line-height:1.65;margin:0 0 20px;">
          <strong style="color:#d0d0d0;">¿Qué es VISAI?</strong><br>
          Plataforma de análisis facial personalizado que recomienda cortes de cabello basados en la forma del rostro y la morfología craneal.
        </p>

        <p style="font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;font-size:14px;color:#666;line-height:1.6;margin:0 0 20px;">
          <strong style="color:#888;">Datos que se analizan:</strong><br>
          • Forma del rostro (ovalado, redondo, cuadrado, etc.)<br>
          • Tipo de cabeza (proporciones craneales)<br>
          • Simetría facial<br>
          <br>
          <strong style="color:#888;">Retención de datos:</strong><br>
          • Las fotos se eliminan inmediatamente después del análisis<br>
          • Los parámetros numéricos se guardan 90 días y luego se eliminan<br>
          • Nunca vendemos datos a terceros
        </p>

        <!-- IMPORTANT NOTICE -->
        <div style="background:#1c1c1c;border-left:4px solid #c9a84c;padding:16px 16px;margin:24px 0;border-radius:4px;">
          <p style="font-family:-apple-system,Arial,sans-serif;font-size:13px;color:#aaa;margin:0;line-height:1.6;">
            Este enlace de autorización expira en <strong style="color:#d0d0d0;">72 horas</strong>.
            Si no autorizas en este plazo, el análisis no se podrá completar.
          </p>
        </div>

        <!-- CTA BUTTON -->
        <table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin-top:28px;">
          <tr><td>
            <a href="{authorization_url}"
               style="display:block;background:#c9a84c;color:#080808;text-decoration:none;text-align:center;padding:17px 24px;border-radius:8px;font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;font-weight:700;font-size:15px;letter-spacing:-0.2px;">SÍ, Autorizar análisis &rarr;</a>
          </td></tr>
        </table>

        <!-- FOOTER NOTE -->
        <p style="font-family:-apple-system,Arial,sans-serif;font-size:12px;color:#555;margin:20px 0 0;line-height:1.6;">
          Si tu hijo/a no ha solicitado un análisis VISAI, puedes ignorar este email.
          No se realizará ningún análisis sin tu autorización explícita.
        </p>

      </td></tr>

      <!-- FOOTER -->
      <tr><td style="padding-top:28px;text-align:center;">
        <p style="font-family:-apple-system,Arial,sans-serif;font-size:11px;color:#3a3a3a;line-height:1.9;margin:0;">
          VISAI &nbsp;&middot;&nbsp;
          <a href="{settings.FRONTEND_URL}/privacidad" style="color:#4a4a4a;text-decoration:none;">Política de Privacidad (RGPD)</a> &nbsp;&middot;&nbsp;
          <a href="{settings.FRONTEND_URL}/terminos" style="color:#4a4a4a;text-decoration:none;">Términos de Uso</a><br>
          Dirección: VISAI SL | NIF: [TBD] | Email: legal@visaiapp.com
        </p>
      </td></tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""
