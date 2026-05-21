import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_ALERT_CHAT_ID
from database import get_unnotified, mark_notified

def notify_pending():
    rows = get_unnotified()
    for r in rows:
        if TELEGRAM_BOT_TOKEN and TELEGRAM_ALERT_CHAT_ID:
            text = f"🚨 Monitoring alert\nKanal: {r.channel_username}\nKeyword/gap: {r.matched_keyword}\nSoni: {r.repetition_count}\nSentiment: {r.sentiment}\nAI: {r.ai_classification}\nLink: {r.message_url}"
            try:
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={"chat_id": TELEGRAM_ALERT_CHAT_ID, "text": text[:3900], "disable_web_page_preview": True},
                    timeout=10
                )
            except Exception:
                pass
        mark_notified(r.id)
