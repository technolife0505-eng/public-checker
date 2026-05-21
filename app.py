import csv
import io
import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from database import init_db, add_channel, add_keyword, get_channels, get_keywords, save_result, get_results, stats
from scanner import normalize_channel_link, scan_channel_for_keywords

app = FastAPI(title="Telegram Public Realtime Checker")
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
def home(request: Request, q: str = "", keyword: str = "", msg: str = ""):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "channels": get_channels(),
        "keywords": get_keywords(),
        "results": get_results(q=q or None, keyword=keyword or None),
        "stats": stats(),
        "q": q,
        "keyword": keyword,
        "msg": msg
    })

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
    return RedirectResponse("/?msg=Kalit so‘z qo‘shildi", status_code=303)

@app.post("/scan")
def scan_now():
    channels = get_channels()
    keywords = get_keywords()
    total = 0

    for ch in channels:
        try:
            found = scan_channel_for_keywords(ch["link"], keywords)
            for item in found:
                save_result(
                    channel_link=item["channel_link"],
                    username=item["username"],
                    message_id=item["message_id"],
                    message_url=item["message_url"],
                    text=item["text"],
                    keyword=item["matched_keyword"],
                    count=item["repetition_count"],
                    message_time=item["message_time"]
                )
                total += 1
        except Exception as e:
            print("Scan error:", ch["link"], e)

    return RedirectResponse(f"/?msg=Real tekshiruv tugadi. Topilgan mos xabarlar: {total}", status_code=303)

@app.get("/export.csv")
def export_csv():
    rows = get_results()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Kanal", "Message URL", "Keyword", "Count", "Time", "Text"])

    for r in rows:
        writer.writerow([r["id"], r["channel_username"], r["message_url"], r["matched_keyword"], r["repetition_count"], r["message_time"], r["message_text"]])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=telegram_public_results.csv"}
    )

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
