"""1-line daily summary via Telegram (optional)."""
import os
from core import net, logger
log = logger.get()

def send(msg):
    log.info(msg)
    tok, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if tok and chat:
        net.get(f"https://api.telegram.org/bot{tok}/sendMessage", params={"chat_id": chat, "text": msg})
