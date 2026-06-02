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


## v5.0.1 Offline AI fixed
Tuzatildi:
- Render deploy xatosi bartaraf etildi.
- scanner.py importlari to‘g‘rilandi.
- Tashqi AI API yo‘q.
- "си", "ai", "ии" kabi qisqa keywordlar faqat alohida so‘z sifatida qidiriladi.
- Pora olmagan / mukofotlangan xabarlar positive chiqadi.
- Eksternat/imtiҳон/e’lon xabarlari neutral chiqadi.


## v5.0.2 Title + Calendar JS fix
Tuzatildi:
- Browser tab title: "Media Monitoring Platform"
- Dashboard inline datepicker JS dagi Unexpected string xatosi
- Keraksiz duplicate calendar.js chaqiruvi olib tashlandi
- favicon.ico 404 logi yo‘qolishi uchun 204 route qo‘shildi


## v5.0.3 Uzbekistan time fix
Tuzatildi:
- Telegram/Render UTC vaqti O‘zbekiston vaqti UTC+5 ga o‘tkaziladi.
- message_time None bo‘lsa, avtomatik scan/created vaqt bilan to‘ldiriladi.
- Jadval va exportlarda vaqt bo‘sh chiqmaydi.
- Format: YYYY-MM-DD HH:MM:SS


## v5.0.4 Filters + strict keyword + time
Qo‘shildi/tuzatildi:
- "Hammasi" so‘zi "Barchasi" ga almashtirildi.
- Real tekshirishga Platformalar, Kanallar, Kalit so‘zlar checkbox filtrlari qo‘shildi.
- Har birida "Barchasi" varianti bor.
- Keyword matching qat’iy: mobil != avtomobil, ai == AI.
- Matn va keywordlar kichik harfga o‘tkazilib solishtiriladi.
- O‘zbekiston vaqti formatda ko‘rsatiladi, mikrosekundalar olib tashlandi.


## v5.0.5 Multi-select dropdown
Tuzatildi:
- Platforma/Kanal/Kalit so‘z filtrlari katta paneldan dropdown multi-select ko‘rinishiga o‘tkazildi.
- Barchasi checkboxi qoldi.
- Tanlanganlar soni ko‘rsatiladi.
- Scroll bar yashirildi.
- Dashboard balandligi ixcham bo‘ldi.


## v5.0.6 Dropdown + button size fix
Tuzatildi:
- Multi-select dropdown bosilganda ochiladi.
- Platformalar/Kanallar/Kalit so‘zlar va Oxirgi 1/7/30 kun/Tozalash tugmalari bir xil balandlikka keltirildi.
- Dropdown ichidagi scroll bar yashirildi.
- Dropdown panel card ichida kesilib qolmasligi uchun z-index/overflow tuzatildi.


## v5.0.7 Inline dropdown fix
Tuzatildi:
- Platformalar/Kanallar/Kalit so‘zlar va Oxirgi 1/7/30/Tozalash bitta qatorda.
- Barcha tugmalar balandligi bir xil.
- Dropdown bosilganda ro‘yxat ochiladi.
- Dropdown ichidagi scroll bar yashirildi.


## v5.0.8 Dropdown open fix
Tuzatildi:
- Dropdown ochilmasligi muammosi inline onclick orqali tuzatildi.
- Dropdown menyu card ichida kesilmasligi uchun z-index/overflow kuchaytirildi.


## v5.0.9 Dropdown JS fixed
- toggleMS is not defined xatosi tuzatildi.
- Dropdown JS /static/multiselect.js fayliga chiqarildi.
