# Media Monitoring Platform v3

Bu versiyada:
- Channels o‘rniga Sources qo‘shildi.
- Platform tanlash: Telegram, Facebook, Instagram, YouTube, X/Twitter, TikTok, News/RSS, VK, OK, Reddit.
- Hozir real scan faqat Telegram public channel uchun ishlaydi.
- Kelajakda boshqa platformalar shu Sources arxitekturasi orqali ulanadi.
- Source language: UZ/RU/EN.
- Keyword/gap, User category, Priority.
- User category va AI class alohida.
- FVV/Ob-havo AI classification yaxshilandi.
- Sentiment: positive, neutral, negative, risk.
- Sana oralig‘i orqali real scan: boshlanish va tugash sanalari inclusive.
- Auto scan har 1 minut.
- Yangi natija topilsa browser notification + sahifa refresh.
- CSV Excel-friendly va XLSX export.

Render:
Build Command:
pip install -r requirements.txt

Start Command:
uvicorn app:app --host 0.0.0.0 --port $PORT
