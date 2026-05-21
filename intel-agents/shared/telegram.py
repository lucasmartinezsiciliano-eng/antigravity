"""
Telegram helper para los agentes Intel.
"""
import os
import requests

LUCAS_CHAT_ID = "5631114912"


def send(text: str, chat_id: str = LUCAS_CHAT_ID, parse_mode: str = "Markdown") -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print(f"[Telegram] Sin token — mensaje no enviado:\n{text}")
        return False
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[Telegram] Error: {e}")
        return False


def error_alert(agent: str, message: str) -> None:
    send(f"❌ *[Intel/{agent}]* Error en ejecución diaria:\n`{message}`")
