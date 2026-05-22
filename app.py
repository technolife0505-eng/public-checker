import csv, io
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler
from openpyxl import Workbook
from config import AUTO_SCAN_ENABLED, SCAN_INTERVAL_SECONDS, REAL_SCAN_DAYS
from database import *
from scanner import normalize_source_link, scan_source_for_keywords
from notifications import notify_pending

app=FastAPI(title="Media Monitoring Platform v3")
templates=Jinja2Templates(directory="templates")
scheduler=BackgroundScheduler()

def run_scan(scan_type="auto", date_from=None, date_to=None):
    sid=scan_start(scan_type); matched=saved=0
    try:
        for src in get_sources(active_only=True):
            found=scan_source_for_keywords(src, get_keywords(active_only=True), date_from, date_to)
            matched+=len(found)
            for item in found:
                if save_result(item): saved+=1
        notify_pending(); scan_finish(sid,matched,saved)
    except Exception as e:
        scan_finish(sid,matched,saved,"error",str(e))
    return {"matched":matched,"saved":saved}

@app.on_event("startup")
def startup():
    init_db()
    if AUTO_SCAN_ENABLED and not scheduler.running:
        scheduler.add_job(lambda: run_scan("auto"),"interval",seconds=SCAN_INTERVAL_SECONDS,id="auto_scan",replace_existing=True)
        scheduler.start()

@app.get("/", response_class=HTMLResponse)
def home(request:Request,q:str="",keyword:str="",source:str="",platform:str="",language:str="",sentiment:str="",msg:str=""):
    sources=get_sources(); keywords=get_keywords()
    return templates.TemplateResponse("index.html",{
        "request":request,"sources":sources,"keywords":keywords,
        "results":get_results(q or None, keyword or None, source or None, platform or None, language or None, sentiment or None),
        "stats":stats(),"keyword_chart":chart("matched_keyword"),"source_chart":chart("source_username"),"daily_chart":daily(),"language_chart":chart("source_language"),"platform_chart":chart("platform"),"ai_chart":chart("ai_classification"),"sentiment_chart":chart("sentiment"),
        "scan_history":scan_history(),"source_counts":{s.username:cnt_source(s.username) for s in sources},"keyword_counts":{k.keyword:cnt_keyword(k.keyword) for k in keywords},
        "q":q,"keyword":keyword,"source":source,"platform":platform,"language":language,"sentiment":sentiment,"msg":msg,"interval":SCAN_INTERVAL_SECONDS,"days":REAL_SCAN_DAYS
    })

@app.get("/api/live")
def live():
    return {"stats":stats()}

@app.post("/sources")
def create_source(platform:str=Form("telegram"), link:str=Form(...), language:str=Form("UZ"), category:str=Form("")):
    try:
        username,clean,_=normalize_source_link(platform,link)
        add_source(platform.lower(),clean,username,language.upper(),category or None)
        return RedirectResponse("/?msg=Source qo‘shildi",status_code=303)
    except Exception as e:
        return RedirectResponse(f"/?msg=Xatolik: {str(e)}",status_code=303)

@app.post("/keywords")
def create_keyword(keyword:str=Form(...), user_category:str=Form(""), priority:str=Form("MEDIUM")):
    add_keyword(keyword,user_category or None,priority.upper())
    return RedirectResponse("/?msg=Kalit so‘z/gap qo‘shildi",status_code=303)

@app.post("/scan")
def scan_now(date_from:str=Form(""), date_to:str=Form("")):
    r=run_scan("manual",date_from or None,date_to or None)
    period=f"{date_from} dan {date_to} gacha" if date_from and date_to else f"oxirgi {REAL_SCAN_DAYS} kun"
    return RedirectResponse(f"/?msg=Real tekshiruv tugadi: {period}. Mos: {r['matched']}, yangi saqlandi: {r['saved']}",status_code=303)

@app.post("/sources/{i}/pause")
def ps(i:int): set_source_status(i,False); return RedirectResponse("/?msg=Source pause qilindi",303)
@app.post("/sources/{i}/resume")
def rs(i:int): set_source_status(i,True); return RedirectResponse("/?msg=Source aktiv qilindi",303)
@app.post("/sources/{i}/delete")
def ds(i:int): del_source(i); return RedirectResponse("/?msg=Source o‘chirildi",303)
@app.post("/keywords/{i}/pause")
def pk(i:int): set_keyword_status(i,False); return RedirectResponse("/?msg=Keyword pause qilindi",303)
@app.post("/keywords/{i}/resume")
def rk(i:int): set_keyword_status(i,True); return RedirectResponse("/?msg=Keyword aktiv qilindi",303)
@app.post("/keywords/{i}/delete")
def dk(i:int): del_keyword(i); return RedirectResponse("/?msg=Keyword o‘chirildi",303)

@app.get("/export.csv")
def export_csv():
    rows=get_results(limit=10000); out=io.StringIO()
    wr=csv.writer(out,delimiter=";",quotechar='"',quoting=csv.QUOTE_ALL,lineterminator="\n")
    wr.writerow(["ID","Platform","Source","Language","URL","Keyword/gap","User category","Count","Time","AI class","Sentiment","Risk","Text"])
    for r in rows: wr.writerow([r.id,r.platform,r.source_username,r.source_language,r.message_url,r.matched_keyword,r.user_category,r.repetition_count,r.message_time,r.ai_classification,r.sentiment,r.risk_level,r.message_text])
    return StreamingResponse(iter(["\ufeff"+out.getvalue()]),media_type="text/csv; charset=utf-8",headers={"Content-Disposition":"attachment; filename=media_monitoring_results.csv"})

@app.get("/export.xlsx")
def export_xlsx():
    rows=get_results(limit=10000); wb=Workbook(); ws=wb.active; ws.title="Results"
    ws.append(["ID","Platform","Source","Language","URL","Keyword/gap","User category","Count","Time","AI class","Sentiment","Risk","Text"])
    for r in rows: ws.append([r.id,r.platform,r.source_username,r.source_language,r.message_url,r.matched_keyword,r.user_category,r.repetition_count,str(r.message_time or ""),r.ai_classification,r.sentiment,r.risk_level,r.message_text])
    out=io.BytesIO(); wb.save(out); out.seek(0)
    return StreamingResponse(out,media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",headers={"Content-Disposition":"attachment; filename=media_monitoring_results.xlsx"})
