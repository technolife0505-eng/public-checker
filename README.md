# Telegram Public Checker v2

## Yangi imkoniyatlar

- Har 1 minut avtomatik scan
- “Real tekshirish” bosilganda oxirgi 2 kunlik postlarni tekshiradi
- Kalit so‘z yoki kalit gap 2 va undan ko‘p uchrasa bazaga yozadi
- Bitta xabarda bir nechta keyword/gap mos kelsa, har biri alohida saqlanadi
- PostgreSQL support
- Browser notification
- Telegram bot alert
- Grafiklar
- Keyword analytics
- Channel analytics
- AI classification
- Sentiment analysis
- CSV export

## Render Start Command

```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

## Render Build Command

```bash
pip install -r requirements.txt
```

## Render Environment Variables

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DB
AUTO_SCAN_ENABLED=true
SCAN_INTERVAL_SECONDS=60
REAL_SCAN_DAYS=2
TELEGRAM_BOT_TOKEN=
TELEGRAM_ALERT_CHAT_ID=
```

`DATABASE_URL` bo‘lmasa SQLite ishlaydi.
