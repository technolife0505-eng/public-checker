import re
import hashlib
from types import SimpleNamespace
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, UniqueConstraint, func
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL

engine=create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal=sessionmaker(bind=engine)
Base=declarative_base()

UZ_OFFSET_HOURS = 5

def normalize_time_uz(dt):
    """Return Uzbekistan time without microseconds. Telegram/Render usually gives UTC."""
    if dt is None:
        dt = datetime.utcnow()
    try:
        # if datetime already has timezone, convert by simple offset after making naive UTC
        dt = dt.replace(tzinfo=None)
    except Exception:
        dt = datetime.utcnow()
    return (dt + timedelta(hours=UZ_OFFSET_HOURS)).replace(microsecond=0)

def display_time(dt):
    if dt is None:
        return ""
    try:
        return dt.replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(dt).split(".")[0]

def normalize_keyword_text(value):
    text = (value or "").lower().strip()
    text = text.replace("ё", "е")
    text = text.replace("ў", "у")
    text = text.replace("қ", "к")
    text = text.replace("ғ", "г")
    text = text.replace("ҳ", "х")
    text = text.replace("ʼ", "'").replace("‘", "'").replace("’", "'")
    text = re.sub(r"\s+", " ", text)
    return text

def strict_keyword_count(text, keyword):
    """Whole-word / whole-phrase case-insensitive match.
    mobil != avtomobil, ai == AI, raqamli hukumat == Raqamli Hukumat.
    """
    text_n = normalize_keyword_text(text)
    kw = normalize_keyword_text(keyword)
    if not kw:
        return 0
    letters = r"A-Za-zА-Яа-яЁёЎўҚқҒғҲҳІі0-9"
    pattern = r"(?<![" + letters + r"])" + re.escape(kw) + r"(?![" + letters + r"])"
    return len(re.findall(pattern, text_n, flags=re.IGNORECASE))


UZ_OFFSET_HOURS = 5

def to_uz_time(dt):
    if dt is None:
        return datetime.utcnow() + timedelta(hours=UZ_OFFSET_HOURS)
    try:
        # Telegram/Render times are usually UTC. Store/display as Uzbekistan time.
        return dt + timedelta(hours=UZ_OFFSET_HOURS)
    except Exception:
        return datetime.utcnow() + timedelta(hours=UZ_OFFSET_HOURS)

def fmt_time(dt):
    return display_time(dt)

class Source(Base):
    __tablename__='sources'
    id=Column(Integer,primary_key=True)
    platform=Column(String(50),default='telegram',index=True)
    link=Column(String(700),unique=True,nullable=False,index=True)
    username=Column(String(255),nullable=False,index=True)
    title=Column(String(255))
    language=Column(String(20),default='UZ',index=True)
    category=Column(String(120),index=True)
    is_active=Column(Boolean,default=True,index=True)
    created_at=Column(DateTime,default=datetime.utcnow)

class Keyword(Base):
    __tablename__='keywords'
    id=Column(Integer,primary_key=True)
    keyword=Column(String(500),unique=True,nullable=False,index=True)
    user_category=Column(String(120),index=True)
    priority=Column(String(20),default='MEDIUM',index=True)
    is_active=Column(Boolean,default=True,index=True)
    created_at=Column(DateTime,default=datetime.utcnow)

class Result(Base):
    __tablename__='results'
    id=Column(Integer,primary_key=True)
    platform=Column(String(50),default='telegram',index=True)
    source_link=Column(String(700),nullable=False,index=True)
    source_username=Column(String(255),nullable=False,index=True)
    source_title=Column(String(255))
    source_language=Column(String(20),index=True)
    message_id=Column(String(100),nullable=False,index=True)
    message_url=Column(String(900))
    message_text=Column(Text,nullable=False)
    matched_keyword=Column(String(500),nullable=False,index=True)
    user_category=Column(String(120),index=True)
    repetition_count=Column(Integer,nullable=False,index=True)
    message_time=Column(DateTime,index=True)
    ai_classification=Column(String(120),index=True)
    sentiment=Column(String(50),index=True)
    risk_level=Column(String(50),index=True)
    created_at=Column(DateTime,default=datetime.utcnow,index=True)
    __table_args__=(UniqueConstraint('platform','source_username','message_id','matched_keyword',name='uq_result'),)

class ScanHistory(Base):
    __tablename__='scan_history'
    id=Column(Integer,primary_key=True)
    scan_type=Column(String(50),default='auto')
    started_at=Column(DateTime,default=datetime.utcnow)
    finished_at=Column(DateTime)
    matched_count=Column(Integer,default=0)
    saved_count=Column(Integer,default=0)
    status=Column(String(50),default='running')
    note=Column(Text)

def init_db(): Base.metadata.create_all(bind=engine)
def db(): return SessionLocal()

def add_source(platform,link,username,language='UZ',category=None,title=None):
    s=db()
    try:
        item=s.query(Source).filter(Source.link==link).first()
        if not item: s.add(Source(platform=platform,link=link,username=username,language=language,category=category,title=title or username))
        else: item.platform=platform; item.language=language; item.category=category
        s.commit()
    finally: s.close()

def add_keyword(keyword,user_category=None,priority='MEDIUM'):
    s=db()
    try:
        val=keyword.lower().strip()
        item=s.query(Keyword).filter(Keyword.keyword==val).first()
        if not item: s.add(Keyword(keyword=val,user_category=user_category,priority=priority))
        else: item.user_category=user_category; item.priority=priority
        s.commit()
    finally: s.close()

def get_sources(active_only=False):
    s=db()
    try:
        q=s.query(Source)
        if active_only: q=q.filter(Source.is_active==True)
        return q.order_by(Source.id.desc()).all()
    finally: s.close()

def get_keywords(active_only=False):
    s=db()
    try:
        q=s.query(Keyword)
        if active_only: q=q.filter(Keyword.is_active==True)
        return q.order_by(Keyword.id.desc()).all()
    finally: s.close()


def duplicate_norm_text(text):
    """Normalize text for duplicate grouping across different channels."""
    t = normalize_keyword_text(text or "")
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"t\.me/\S+", " ", t)
    t = re.sub(r"@\w+", " ", t)
    t = re.sub(r"#\w+", " ", t)
    t = re.sub(r"\b(reklama|реклама|batafsil|подробнее|kanal|канал)\b", " ", t)
    t = re.sub(r"[^\w\sА-Яа-яЁёЎўҚқҒғҲҳІі'-]+", " ", t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:700]

def duplicate_key(result):
    base = duplicate_norm_text(getattr(result, "message_text", ""))
    return hashlib.sha1(base.encode("utf-8", errors="ignore")).hexdigest() if base else str(getattr(result, "id", ""))

def group_duplicate_results(rows):
    """Return display rows. DB still keeps every result, but UI gets one row per duplicate group."""
    groups = {}
    order = []
    for r in rows:
        key = duplicate_key(r)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(r)

    display = []
    for key in order:
        items = groups[key]
        items.sort(key=lambda x: (x.message_time or x.created_at or datetime.utcnow()))
        primary = items[0]

        sources = []
        seen_sources = set()
        for item in items:
            src_key = (item.platform, item.source_username)
            if src_key in seen_sources:
                continue
            seen_sources.add(src_key)
            sources.append({
                "source": item.source_username,
                "url": item.message_url,
                "time": display_time(item.message_time or item.created_at),
                "platform": item.platform,
                "is_primary": item.id == primary.id
            })

        row = SimpleNamespace(**primary.__dict__)
        row.source_variants = sources
        row.duplicate_count = len(sources)
        row.repetition_count = len(sources)
        row.source_username = primary.source_username
        row.message_url = primary.message_url
        row.message_time = primary.message_time
        display.append(row)

    display.sort(key=lambda x: (x.message_time or x.created_at or datetime.utcnow()), reverse=True)
    return display

def save_result(item):
    s=db()
    try:
        ex=s.query(Result).filter(Result.platform==item['platform'],Result.source_username==item['username'],Result.message_id==item['message_id'],Result.matched_keyword==item['matched_keyword']).first()
        if ex: return False
        s.add(Result(platform=item['platform'],source_link=item['source_link'],source_username=item['username'],source_title=item.get('source_title'),source_language=item.get('source_language'),message_id=item['message_id'],message_url=item['message_url'],message_text=item['text'],matched_keyword=item['matched_keyword'],user_category=item.get('user_category'),repetition_count=item['repetition_count'],message_time=normalize_time_uz(item.get('message_time')),ai_classification=item.get('ai_classification'),sentiment=item.get('sentiment'),risk_level=item.get('risk_level')))
        s.commit(); return True
    finally: s.close()

def get_results(q=None,keyword=None,source=None,platform=None,language=None,sentiment=None,limit=500):
    s=db()
    try:
        query=s.query(Result)
        if q: query=query.filter(Result.message_text.ilike(f'%{q}%'))
        if keyword: query=query.filter(Result.matched_keyword==keyword)
        if source: query=query.filter(Result.source_username==source)
        if platform: query=query.filter(Result.platform==platform)
        if language: query=query.filter(Result.source_language==language)
        if sentiment: query=query.filter(Result.sentiment==sentiment)
        rows=query.order_by(Result.created_at.desc()).limit(limit).all()
        for r in rows:
            if r.message_time is None:
                r.message_time = normalize_time_uz(r.created_at)
        return group_duplicate_results(rows)
    finally: s.close()


def get_results_raw(q=None,keyword=None,source=None,platform=None,language=None,sentiment=None,limit=10000):
    s=db()
    try:
        query=s.query(Result)
        if q: query=query.filter(Result.message_text.ilike(f'%{q}%'))
        if keyword: query=query.filter(Result.matched_keyword==keyword)
        if source: query=query.filter(Result.source_username==source)
        if platform: query=query.filter(Result.platform==platform)
        if language: query=query.filter(Result.source_language==language)
        if sentiment: query=query.filter(Result.sentiment==sentiment)
        rows=query.order_by(Result.created_at.desc()).limit(limit).all()
        for r in rows:
            if r.message_time is None:
                r.message_time = normalize_time_uz(r.created_at)
        return rows
    finally:
        s.close()

def cnt_source(username):
    s=db()
    try: return s.query(Result).filter(Result.source_username==username).count()
    finally: s.close()
def cnt_keyword(keyword):
    s=db()
    try: return s.query(Result).filter(Result.matched_keyword==keyword).count()
    finally: s.close()
def stats():
    s=db()
    try:
        return {'total_results':s.query(Result).count(),'today_results':s.query(Result).filter(func.date(Result.created_at)==func.current_date()).count(),'total_sources':s.query(Source).count(),'active_sources':s.query(Source).filter(Source.is_active==True).count(),'total_keywords':s.query(Keyword).count(),'risk_results':s.query(Result).filter(Result.sentiment.in_(['negative','risk'])).count()}
    finally: s.close()
def chart(field):
    s=db()
    try:
        col=getattr(Result,field); rows=s.query(col,func.count(Result.id)).group_by(col).order_by(func.count(Result.id).desc()).limit(10).all()
        return [{'name':r[0] or 'N/A','count':r[1]} for r in rows]
    finally: s.close()
def daily():
    s=db()
    try:
        rows=s.query(func.date(Result.created_at),func.count(Result.id)).group_by(func.date(Result.created_at)).order_by(func.date(Result.created_at)).limit(30).all()
        return [{'date':str(r[0]),'count':r[1]} for r in rows]
    finally: s.close()
def scan_start(t):
    s=db()
    try:
        row=ScanHistory(scan_type=t); s.add(row); s.commit(); return row.id
    finally: s.close()
def scan_finish(i,matched,saved,status='done',note=None):
    s=db()
    try:
        row=s.query(ScanHistory).filter(ScanHistory.id==i).first()
        if row: row.finished_at=datetime.utcnow(); row.matched_count=matched; row.saved_count=saved; row.status=status; row.note=note; s.commit()
    finally: s.close()
def scan_history():
    s=db()
    try: return s.query(ScanHistory).order_by(ScanHistory.started_at.desc()).limit(50).all()
    finally: s.close()
def set_source_status(i,active):
    s=db()
    try:
        row=s.query(Source).filter(Source.id==i).first()
        if row: row.is_active=active; s.commit()
    finally: s.close()
def del_source(i):
    s=db()
    try:
        row=s.query(Source).filter(Source.id==i).first()
        if row: s.delete(row); s.commit()
    finally: s.close()
def set_keyword_status(i,active):
    s=db()
    try:
        row=s.query(Keyword).filter(Keyword.id==i).first()
        if row: row.is_active=active; s.commit()
    finally: s.close()
def del_keyword(i):
    s=db()
    try:
        row=s.query(Keyword).filter(Keyword.id==i).first()
        if row: s.delete(row); s.commit()
    finally: s.close()


def get_source_by_id(i):
    s=db()
    try:
        return s.query(Source).filter(Source.id==i).first()
    finally:
        s.close()

def get_keyword_by_id(i):
    s=db()
    try:
        return s.query(Keyword).filter(Keyword.id==i).first()
    finally:
        s.close()

def source_exists(platform, link, username):
    s=db()
    try:
        return s.query(Source).filter(
            ((Source.platform==platform) & (Source.link==link)) |
            ((Source.platform==platform) & (Source.username==username))
        ).first() is not None
    finally:
        s.close()

def keyword_exists(keyword):
    s=db()
    try:
        val=(keyword or '').lower().strip()
        return s.query(Keyword).filter(Keyword.keyword==val).first() is not None
    finally:
        s.close()

def update_source(i, platform, link, username, language='UZ', category=None):
    s=db()
    try:
        row=s.query(Source).filter(Source.id==i).first()
        if row:
            row.platform=platform
            row.link=link
            row.username=username
            row.language=language
            row.category=category
            s.commit()
    finally:
        s.close()

def update_keyword(i, keyword, user_category=None, priority='MEDIUM'):
    s=db()
    try:
        row=s.query(Keyword).filter(Keyword.id==i).first()
        if row:
            row.keyword=(keyword or '').lower().strip()
            row.user_category=user_category
            row.priority=priority
            s.commit()
    finally:
        s.close()


def clear_results_only():
    s=db()
    try:
        s.query(Result).delete()
        s.query(ScanHistory).delete()
        s.commit()
    finally:
        s.close()

def clear_sources_only():
    s=db()
    try:
        s.query(Result).delete()
        s.query(ScanHistory).delete()
        s.query(Source).delete()
        s.commit()
    finally:
        s.close()

def clear_keywords_only():
    s=db()
    try:
        s.query(Result).delete()
        s.query(ScanHistory).delete()
        s.query(Keyword).delete()
        s.commit()
    finally:
        s.close()

def factory_reset_all():
    s=db()
    try:
        s.query(Result).delete()
        s.query(ScanHistory).delete()
        s.query(Keyword).delete()
        s.query(Source).delete()
        s.commit()
    finally:
        s.close()
