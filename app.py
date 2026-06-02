import csv, io
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
from openpyxl import Workbook
from config import AUTO_SCAN_ENABLED, SCAN_INTERVAL_SECONDS, REAL_SCAN_DAYS
from database import *
from scanner import normalize_source_link, scan_source_for_keywords
from notifications import notify_pending

app=FastAPI(title='Media Monitoring Platform v4')
templates=Jinja2Templates(directory='templates')
app.mount('/static', StaticFiles(directory='static'), name='static')
scheduler=BackgroundScheduler()

def run_scan(scan_type='auto',date_from=None,date_to=None):
    sid=scan_start(scan_type); matched=saved=0
    try:
        for src in get_sources(active_only=True):
            found=scan_source_for_keywords(src,get_keywords(active_only=True),date_from,date_to)
            matched+=len(found)
            for item in found:
                if save_result(item): saved+=1
        notify_pending(); scan_finish(sid,matched,saved)
    except Exception as e:
        scan_finish(sid,matched,saved,'error',str(e))
    return {'matched':matched,'saved':saved}

@app.on_event('startup')
def startup():
    from config import DATABASE_URL
    print('DATABASE_KIND=' + ('postgresql' if str(DATABASE_URL).startswith('postgres') else 'sqlite'))
    init_db()
    if AUTO_SCAN_ENABLED and not scheduler.running:
        scheduler.add_job(lambda: run_scan('auto'),'interval',seconds=SCAN_INTERVAL_SECONDS,id='auto_scan',replace_existing=True)
        scheduler.start()

def ctx(request,active,msg=''):
    return {'request':request,'active_page':active,'stats':stats(),'interval':SCAN_INTERVAL_SECONDS,'days':REAL_SCAN_DAYS,'msg':msg}

@app.api_route('/', methods=['GET','HEAD'])
def root(): return Response(content='ok', media_type='text/plain', status_code=200)

@app.api_route('/ping', methods=['GET','HEAD'])
def ping():
    return Response(content='ok', media_type='text/plain', status_code=200)

@app.api_route('/health', methods=['GET','HEAD'])
def health():
    return Response(content='ok', media_type='text/plain', status_code=200)


@app.get('/favicon.ico')
def favicon():
    return Response(status_code=204)

@app.get('/dashboard',response_class=HTMLResponse)
def dashboard(request:Request,msg:str=''):
    c=ctx(request,'dashboard',msg)
    c.update({'sources_list':get_sources(),'keywords_list':get_keywords(),'platforms':['Telegram','Facebook','Instagram','YouTube','X / Twitter','TikTok','News / RSS']}); c.update({'results':get_results(limit=100),'keyword_chart':chart('matched_keyword'),'source_chart':chart('source_username'),'daily_chart':daily()})
    return templates.TemplateResponse('dashboard.html',c)
@app.get('/sources',response_class=HTMLResponse)
def sources_page(request:Request,msg:str='',edit_id:int=0):
    sources=get_sources()
    edit_source=get_source_by_id(edit_id) if edit_id else None
    c=ctx(request,'sources',msg)
    c.update({'sources':sources,'edit_source':edit_source,'source_counts':{s.username:cnt_source(s.username) for s in sources}})
    return templates.TemplateResponse('sources.html',c)
@app.get('/autoscan',response_class=HTMLResponse)
def autoscan_page(request:Request,msg:str=''):
    c=ctx(request,'autoscan',msg); c.update({'scan_history':scan_history()})
    return templates.TemplateResponse('autoscan.html',c)
@app.get('/keywords',response_class=HTMLResponse)
def keywords_page(request:Request,msg:str='',edit_id:int=0):
    keywords=get_keywords()
    edit_keyword=get_keyword_by_id(edit_id) if edit_id else None
    c=ctx(request,'keywords',msg)
    c.update({'keywords':keywords,'edit_keyword':edit_keyword,'keyword_counts':{k.keyword:cnt_keyword(k.keyword) for k in keywords}})
    return templates.TemplateResponse('keywords.html',c)
@app.get('/analytics',response_class=HTMLResponse)
def analytics_page(request:Request,msg:str=''):
    c=ctx(request,'analytics',msg); c.update({'keyword_chart':chart('matched_keyword'),'source_chart':chart('source_username'),'daily_chart':daily(),'language_chart':chart('source_language'),'platform_chart':chart('platform'),'ai_chart':chart('ai_classification')})
    return templates.TemplateResponse('analytics.html',c)
@app.get('/results',response_class=HTMLResponse)
def results_page(request:Request,q:str='',keyword:str='',source:str='',platform:str='',language:str='',sentiment:str='',msg:str=''):
    c=ctx(request,'results',msg); c.update({'sources':get_sources(),'keywords':get_keywords(),'results':get_results(q or None,keyword or None,source or None,platform or None,language or None,sentiment or None),'q':q,'keyword':keyword,'source':source,'platform':platform,'language':language,'sentiment':sentiment})
    return templates.TemplateResponse('results.html',c)

@app.get('/settings', response_class=HTMLResponse)
def settings_page(request:Request,msg:str=''):
    c=ctx(request,'settings',msg)
    return templates.TemplateResponse('settings.html',c)

@app.get('/api/live')
def live(): return {'stats':stats()}

def split_bulk_text(text):
    if not text:
        return []
    out=[]
    for part in str(text).replace(',', '\n').replace(';', '\n').splitlines():
        val=part.strip()
        if val:
            out.append(val)
    return out

def bulk_add_sources(platform, links_text, language, category):
    total=added=skipped=errors=0
    seen=set()
    for raw in split_bulk_text(links_text):
        total+=1
        try:
            username,clean,_=normalize_source_link(platform,raw)
            key=(platform.lower(),clean.lower().rstrip('/'),username.lower())
            if key in seen:
                skipped+=1
                continue
            seen.add(key)
            if source_exists(platform.lower(),clean,username):
                skipped+=1
                continue
            add_source(platform.lower(),clean,username,language.upper(),category or None)
            added+=1
        except Exception:
            errors+=1
    return total,added,skipped,errors

def bulk_add_keywords(keywords_text, user_category, priority):
    total=added=skipped=errors=0
    seen=set()
    for raw in split_bulk_text(keywords_text):
        total+=1
        val=raw.lower().strip()
        if not val:
            errors+=1
            continue
        if val in seen:
            skipped+=1
            continue
        seen.add(val)
        if keyword_exists(val):
            skipped+=1
            continue
        add_keyword(val,user_category or None,priority.upper())
        added+=1
    return total,added,skipped,errors

@app.post('/sources')
def create_source(platform:str=Form('telegram'),links:str=Form(...),language:str=Form('UZ'),category:str=Form('')):
    total,added,skipped,errors=bulk_add_sources(platform,links,language,category)
    return RedirectResponse(f'/sources?msg=Sources: jami {total}, yangi {added}, mavjud/takror {skipped}, xato {errors}',303)

@app.post('/sources/import')
async def import_sources(platform:str=Form('telegram'),language:str=Form('UZ'),category:str=Form(''),file:UploadFile=File(...)):
    content=(await file.read()).decode('utf-8',errors='ignore')
    total,added,skipped,errors=bulk_add_sources(platform,content,language,category)
    return RedirectResponse(f'/sources?msg=TXT import: jami {total}, yangi {added}, mavjud/takror {skipped}, xato {errors}',303)

@app.post('/sources/{i}/update')
def update_source_route(i:int, platform:str=Form('telegram'), link:str=Form(...), language:str=Form('UZ'), category:str=Form('')):
    try:
        username,clean,_=normalize_source_link(platform,link)
        update_source(i,platform.lower(),clean,username,language.upper(),category or None)
        return RedirectResponse('/sources?msg=Source yangilandi',303)
    except Exception as e:
        return RedirectResponse(f'/sources?msg=Xatolik: {str(e)}',303)

@app.post('/keywords')
def create_keyword(keywords:str=Form(...),user_category:str=Form(''),priority:str=Form('MEDIUM')):
    total,added,skipped,errors=bulk_add_keywords(keywords,user_category,priority)
    return RedirectResponse(f'/keywords?msg=Keywords: jami {total}, yangi {added}, mavjud/takror {skipped}, xato {errors}',303)

@app.post('/keywords/import')
async def import_keywords(user_category:str=Form(''),priority:str=Form('MEDIUM'),file:UploadFile=File(...)):
    content=(await file.read()).decode('utf-8',errors='ignore')
    total,added,skipped,errors=bulk_add_keywords(content,user_category,priority)
    return RedirectResponse(f'/keywords?msg=TXT import: jami {total}, yangi {added}, mavjud/takror {skipped}, xato {errors}',303)

@app.post('/keywords/{i}/update')
def update_keyword_route(i:int, keyword:str=Form(...), user_category:str=Form(''), priority:str=Form('MEDIUM')):
    update_keyword(i,keyword,user_category or None,priority.upper())
    return RedirectResponse('/keywords?msg=Keyword yangilandi',303)


@app.post('/admin/clear-results')
def admin_clear_results(confirm:str=Form('')):
    if confirm != 'DELETE RESULTS':
        return RedirectResponse('/settings?msg=Tasdiqlash noto‘g‘ri. DELETE RESULTS deb yozing.',303)
    clear_results_only()
    return RedirectResponse('/settings?msg=Natijalar tozalandi',303)

@app.post('/admin/clear-sources')
def admin_clear_sources(confirm:str=Form('')):
    if confirm != 'DELETE SOURCES':
        return RedirectResponse('/settings?msg=Tasdiqlash noto‘g‘ri. DELETE SOURCES deb yozing.',303)
    clear_sources_only()
    return RedirectResponse('/settings?msg=Sources tozalandi',303)

@app.post('/admin/clear-keywords')
def admin_clear_keywords(confirm:str=Form('')):
    if confirm != 'DELETE KEYWORDS':
        return RedirectResponse('/settings?msg=Tasdiqlash noto‘g‘ri. DELETE KEYWORDS deb yozing.',303)
    clear_keywords_only()
    return RedirectResponse('/settings?msg=Keywords tozalandi',303)

@app.post('/admin/factory-reset')
def admin_factory_reset(confirm:str=Form('')):
    if confirm != 'DELETE ALL':
        return RedirectResponse('/settings?msg=Tasdiqlash noto‘g‘ri. DELETE ALL deb yozing.',303)
    factory_reset_all()
    return RedirectResponse('/dashboard?msg=Baza 0 dan tozalandi',303)

@app.post('/scan')
def scan_now(date_from:str=Form(''),date_to:str=Form('')):
    r=run_scan('manual',date_from or None,date_to or None); period=f'{date_from} dan {date_to} gacha' if date_from and date_to else f'oxirgi {REAL_SCAN_DAYS} kun'
    return RedirectResponse(f'/autoscan?msg=Real tekshiruv tugadi: {period}. Mos: {r["matched"]}, yangi saqlandi: {r["saved"]}',303)
@app.post('/sources/{i}/pause')
def ps(i:int): set_source_status(i,False); return RedirectResponse('/sources?msg=Source pause qilindi',303)
@app.post('/sources/{i}/resume')
def rs(i:int): set_source_status(i,True); return RedirectResponse('/sources?msg=Source aktiv qilindi',303)
@app.post('/sources/{i}/delete')
def ds(i:int): del_source(i); return RedirectResponse('/sources?msg=Source o‘chirildi',303)
@app.post('/keywords/{i}/pause')
def pk(i:int): set_keyword_status(i,False); return RedirectResponse('/keywords?msg=Keyword pause qilindi',303)
@app.post('/keywords/{i}/resume')
def rk(i:int): set_keyword_status(i,True); return RedirectResponse('/keywords?msg=Keyword aktiv qilindi',303)
@app.post('/keywords/{i}/delete')
def dk(i:int): del_keyword(i); return RedirectResponse('/keywords?msg=Keyword o‘chirildi',303)
@app.get('/export.csv')
def export_csv():
    rows=get_results(limit=10000); out=io.StringIO(); wr=csv.writer(out,delimiter=';',quotechar='"',quoting=csv.QUOTE_ALL,lineterminator='\n')
    wr.writerow(['ID','Platform','Source','Language','URL','Keyword/gap','User category','Count','Time','AI class','Sentiment','Risk','Text'])
    for r in rows: wr.writerow([r.id,r.platform,r.source_username,r.source_language,r.message_url,r.matched_keyword,r.user_category,r.repetition_count,r.message_time,r.ai_classification,r.sentiment,r.risk_level,r.message_text])
    return StreamingResponse(iter(['\ufeff'+out.getvalue()]),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename=media_monitoring_results.csv'})
@app.get('/export.xlsx')
def export_xlsx():
    rows=get_results(limit=10000); wb=Workbook(); ws=wb.active; ws.title='Results'; ws.append(['ID','Platform','Source','Language','URL','Keyword/gap','User category','Count','Time','AI class','Sentiment','Risk','Text'])
    for r in rows: ws.append([r.id,r.platform,r.source_username,r.source_language,r.message_url,r.matched_keyword,r.user_category,r.repetition_count,str(r.message_time or ''),r.ai_classification,r.sentiment,r.risk_level,r.message_text])
    out=io.BytesIO(); wb.save(out); out.seek(0)
    return StreamingResponse(out,media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={'Content-Disposition':'attachment; filename=media_monitoring_results.xlsx'})
