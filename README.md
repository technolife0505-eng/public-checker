# Media Monitoring Platform v4.6 — Bulk Import

Qo‘shildi:
- Sources: bir nechta linkni birdan qo‘shish
- Keywords: bir nechta keyword/gapni birdan qo‘shish
- Sources TXT/CSV import
- Keywords TXT/CSV import
- Bazada oldin mavjud bo‘lsa avtomatik o‘tkazib yuboradi
- Import ichida takror bo‘lsa avtomatik o‘tkazib yuboradi
- Edit / Pause / Resume / Delete
- Calendar fix saqlangan

Render:
Build Command: pip install -r requirements.txt
Start Command: uvicorn app:app --host 0.0.0.0 --port $PORT


## v4.7 ping health-check
Qo‘shildi:
- GET /ping → 200 OK
- HEAD /ping → 200 OK
- GET /health → 200 OK
- HEAD /health → 200 OK
- Root / ham HEAD/GET uchun 200 OK qaytaradi
- Startup logda DATABASE_KIND=postgresql yoki sqlite chiqadi

UptimeRobot uchun URL:
https://telegram-public-checker.onrender.com/ping


## v4.8 dashboard recent scroll
Qo‘shildi:
- Dashboard oxirgi 100 ta topilgan xabarni ko‘rsatadi
- “Oxirgi topilgan xabarlar” jadvali ichida vertikal skrol ishlaydi
- Uzoq matnlar o‘qilishi uchun kengroq joy berildi
- “Barcha natijalarni ko‘rish” tugmasi qo‘shildi


## v4.9 Database Management
- Settings sahifasi
- Delete Results Only
- Delete Sources Only
- Delete Keywords Only
- Factory Reset Everything
