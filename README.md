# Telegram Public Realtime Checker

Bu versiya Telegram API, telefon login kodi va api_hashsiz ishlaydi. Faqat public Telegram kanal linklarini tekshiradi.

## Ishlaydigan linklar

```text
https://t.me/kunuzofficial
https://t.me/daryo
https://t.me/gazetauz_ozb
```

## Ishlamaydigan linklar

```text
https://t.me/+privateInvite
private group
yopiq kanal
```

## Ishga tushirish

```bash
pip install -r requirements.txt
python app.py
```

Keyin brauzerda:

```text
http://127.0.0.1:8000
```

## Qanday ishlaydi?

1. Public kanal linkini qo‘shasiz.
2. Kalit so‘z qo‘shasiz.
3. “Real tekshirishni boshlash” tugmasini bosasiz.
4. Agar public post ichida keyword 2 yoki undan ko‘p marta kelsa, SQLite bazaga yoziladi.
5. Natija web jadvalda ko‘rinadi.
