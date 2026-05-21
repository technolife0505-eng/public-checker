import csv, io
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler
from config import AUTO_SCAN_ENABLED, SCAN_INTERVAL_SECONDS, REAL_SCAN_DAYS
from database import init_db, add_channel, add_keyword, get_channels, get_keywords, save_result, get_results, get_stats, analytics_keyword, analytics_channel, analytics_daily
from scanner import normalize_channel_link, scan_channel_for_keywords
from notifications import notify_pending

app = FastAPI(title="Telegram Public Checker v2")
templates = Jinja2Templates(directory="templates")
scheduler = BackgroundScheduler()

def run_scan(days=2):
    channels = get_channels(active_only=True)
    keywords = get_keywords(active_only=True)
    matched = saved = 0
    for ch in channels:
        try:
            found = scan_channel_for_keywords(ch.link, keywords, days=days)
            matched += len(found)
            for item in found:
                if save_result(item):
                    saved += 1
        except Exception as e:
            print("Scan error:", ch.link, e)
    notify_pending()
    return {"matched": matched, "saved": saved}

@app.on_event("startup")
def startup():
    init_db()
    if AUTO_SCAN_ENABLED and not scheduler.running:
        scheduler.add_job(lambda: run_scan(REAL_SCAN_DAYS), "interval", seconds=SCAN_INTERVAL_SECONDS, id="auto_scan", replace_existing=True)
        scheduler.start()

@app.get("/", response_class=HTMLResponse)
def home(request: Request, q: str = "", keyword: str = "", channel: str = "", msg: str = ""):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "channels": get_channels(),
        "keywords": get_keywords(),
        "results": get_results(q=q or None, keyword=keyword or None, channel=channel or None),
        "stats": get_stats(),
        "keyword_chart": analytics_keyword(),
        "channel_chart": analytics_channel(),
        "daily_chart": analytics_daily(),
        "q": q, "keyword": keyword, "channel": channel, "msg": msg,
        "interval": SCAN_INTERVAL_SECONDS, "days": REAL_SCAN_DAYS
    })

@app.get("/api/live")
def live():
    return {
        "stats": get_stats(),
        "results": [
            {"id": r.id, "channel": r.channel_username, "keyword": r.matched_keyword, "count": r.repetition_count, "url": r.message_url, "text": r.message_text}
            for r in get_results(limit=50)
        ],
        "keyword_chart": analytics_keyword(),
        "channel_chart": analytics_channel(),
        "daily_chart": analytics_daily()
    }

@app.post("/channels")
def create_channel(link: str = Form(...)):
    try:
        username, clean_link, _ = normalize_channel_link(link)
        add_channel(clean_link, username)
        return RedirectResponse("/?msg=Kanal qo‘shildi", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/?msg=Xatolik: {str(e)}", status_code=303)

@app.post("/keywords")
def create_keyword(keyword: str = Form(...), category: str = Form("")):
    add_keyword(keyword, category or None)
    return RedirectResponse("/?msg=Kalit so‘z/gap qo‘shildi", status_code=303)

@app.post("/scan")
def scan_now():
    r = run_scan(days=REAL_SCAN_DAYS)
    return RedirectResponse(f"/?msg=Oxirgi {REAL_SCAN_DAYS} kunlik tekshiruv tugadi. Mos: {r['matched']}, yangi saqlandi: {r['saved']}", status_code=303)

@app.get("/export.csv")
def export_csv():
    rows = get_results(limit=10000)
    out = io.StringIO()
    wr = csv.writer(out)
    wr.writerow(["ID", "Kanal", "URL", "Keyword/gap", "Count", "Time", "AI class", "Sentiment", "Text"])
    for r in rows:
        wr.writerow([r.id, r.channel_username, r.message_url, r.matched_keyword, r.repetition_count, r.message_time, r.ai_classification, r.sentiment, r.message_text])
    out.seek(0)
    return StreamingResponse(iter([out.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=telegram_public_results_v2.csv"})
