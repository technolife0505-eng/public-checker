import re
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def normalize_channel_link(link: str):
    link = link.strip()

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

def count_keyword(text: str, keyword: str):
    return (text or "").lower().count((keyword or "").lower().strip())

def fetch_public_posts(channel_link: str):
    username, clean_link, web_url = normalize_channel_link(channel_link)

    response = requests.get(web_url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    title_el = soup.select_one(".tgme_channel_info_header_title span")
    channel_title = title_el.get_text(" ", strip=True) if title_el else username

    posts = []
    post_blocks = soup.select(".tgme_widget_message")

    for block in post_blocks:
        data_post = block.get("data-post", "")
        message_id = data_post.split("/")[-1] if "/" in data_post else data_post

        text_el = block.select_one(".tgme_widget_message_text")
        text = text_el.get_text("\n", strip=True) if text_el else ""

        time_el = block.select_one("time")
        message_time = time_el.get("datetime") if time_el else ""

        if not text or not message_id:
            continue

        posts.append({
            "username": username,
            "channel_link": clean_link,
            "channel_title": channel_title,
            "message_id": message_id,
            "message_url": f"https://t.me/{username}/{message_id}",
            "text": text,
            "message_time": message_time
        })

    return posts

def scan_channel_for_keywords(channel_link: str, keywords):
    posts = fetch_public_posts(channel_link)
    results = []

    for post in posts:
        for kw in keywords:
            keyword = kw["keyword"] if isinstance(kw, dict) else kw["keyword"]
            count = count_keyword(post["text"], keyword)
            if count >= 2:
                results.append({
                    **post,
                    "matched_keyword": keyword,
                    "repetition_count": count
                })

    return results
