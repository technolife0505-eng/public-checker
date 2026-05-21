import re, requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

HEADERS = {"User-Agent": "Mozilla/5.0"}

def normalize_channel_link(link: str):
    link = (link or "").strip()
    if link.startswith("@"):
        username = link[1:]
    elif "t.me/" in link:
        username = link.split("t.me/", 1)[1].strip("/")
    else:
        username = link.strip("/")
    if username.startswith("+") or "joinchat" in username:
        raise ValueError("Private invite link ishlamaydi. Faqat public kanal username kerak.")
    username = username.split("/")[0]
    if not re.match(r"^[A-Za-z0-9_]{4,}$", username):
        raise ValueError("Telegram kanal username noto‘g‘ri.")
    return username, f"https://t.me/{username}", f"https://t.me/s/{username}"

def parse_dt(v):
    if not v:
        return None
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
    except Exception:
        return None

def count_kw(text, keyword):
    text = (text or "").lower()
    keyword = (keyword or "").lower().strip()
    if not keyword:
        return 0
    return text.count(keyword)

def classify(text):
    t = (text or "").lower()
    if any(x in t for x in ["йўл","yo‘l","дорога","транспорт","авто","машина","tirband"]): return "Transport / Yo‘l"
    if any(x in t for x in ["эко","ekolog","chiqindi","стикер","stiker","экология"]): return "Ekologiya"
    if any(x in t for x in ["газ","свет","электр","коммунал","сув","suv","вода"]): return "Kommunal"
    if any(x in t for x in ["жиноят","firib","ўғир","милитсия","militsiya","суд"]): return "Huquq / Xavfsizlik"
    if any(x in t for x in ["мактаб","bog‘cha","таълим","университет","o‘qish"]): return "Ta’lim"
    return "Boshqa"

def sentiment(text):
    t = (text or "").lower()
    neg_words = ["муаммо","xato","ёмон","yomon","норози","shikoyat","жарима","қийнал","qiyin","хавф","ёпилди","авария","tanqid"]
    pos_words = ["яхши","zo‘r","зўр","рахмат","minnatdor","ijobiy","очилди","yaxshilandi","muvaffaqiyat"]
    neg = sum(1 for w in neg_words if w in t)
    pos = sum(1 for w in pos_words if w in t)
    if neg > pos: return "negative"
    if pos > neg: return "positive"
    return "neutral"

def fetch_page(username, before=None):
    url = f"https://t.me/s/{username}"
    if before:
        url += f"?before={before}"
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text

def parse_posts(html, username, clean_link):
    soup = BeautifulSoup(html, "html.parser")
    title_el = soup.select_one(".tgme_channel_info_header_title span")
    title = title_el.get_text(" ", strip=True) if title_el else username
    posts = []
    for block in soup.select(".tgme_widget_message"):
        data_post = block.get("data-post", "")
        mid = data_post.split("/")[-1] if "/" in data_post else data_post
        text_el = block.select_one(".tgme_widget_message_text")
        text = text_el.get_text("\n", strip=True) if text_el else ""
        time_el = block.select_one("time")
        dt = parse_dt(time_el.get("datetime") if time_el else "")
        if text and mid:
            posts.append({
                "username": username, "channel_link": clean_link, "channel_title": title,
                "message_id": str(mid), "message_url": f"https://t.me/{username}/{mid}",
                "text": text, "message_time": dt
            })
    return posts

def fetch_posts_last_days(channel_link, days=2, max_pages=35):
    username, clean_link, _ = normalize_channel_link(channel_link)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    all_posts, seen, before = [], set(), None
    for _ in range(max_pages):
        posts = parse_posts(fetch_page(username, before), username, clean_link)
        if not posts:
            break
        for p in posts:
            if p["message_id"] not in seen:
                seen.add(p["message_id"])
                if not p["message_time"] or p["message_time"] >= cutoff:
                    all_posts.append(p)
        dated = [p for p in posts if p["message_time"]]
        if dated and min(p["message_time"] for p in dated) < cutoff:
            break
        nums = [int(p["message_id"]) for p in posts if str(p["message_id"]).isdigit()]
        if not nums: break
        before = min(nums)
        if before <= 1: break
    return all_posts

def scan_channel_for_keywords(channel_link, keywords, days=2):
    posts = fetch_posts_last_days(channel_link, days=days)
    out = []
    for p in posts:
        for kw in keywords:
            keyword = kw.keyword
            cnt = count_kw(p["text"], keyword)
            if cnt >= 2:
                out.append({
                    **p,
                    "matched_keyword": keyword,
                    "keyword_category": kw.category,
                    "repetition_count": cnt,
                    "ai_classification": classify(p["text"]),
                    "sentiment": sentiment(p["text"]),
                })
    return out
