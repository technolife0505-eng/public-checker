from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, UniqueConstraint, func
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True)
    platform = Column(String(50), default="telegram", index=True)
    link = Column(String(700), unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=False, index=True)
    title = Column(String(255))
    language = Column(String(20), default="UZ", index=True)
    category = Column(String(120), index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Keyword(Base):
    __tablename__ = "keywords"
    id = Column(Integer, primary_key=True)
    keyword = Column(String(500), unique=True, nullable=False, index=True)
    user_category = Column(String(120), index=True)
    priority = Column(String(20), default="MEDIUM", index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True)
    platform = Column(String(50), default="telegram", index=True)
    source_link = Column(String(700), nullable=False, index=True)
    source_username = Column(String(255), nullable=False, index=True)
    source_title = Column(String(255))
    source_language = Column(String(20), index=True)
    message_id = Column(String(100), nullable=False, index=True)
    message_url = Column(String(900))
    message_text = Column(Text, nullable=False)
    matched_keyword = Column(String(500), nullable=False, index=True)
    user_category = Column(String(120), index=True)
    repetition_count = Column(Integer, nullable=False, index=True)
    message_time = Column(DateTime, index=True)
    ai_classification = Column(String(120), index=True)
    sentiment = Column(String(50), index=True)
    risk_level = Column(String(50), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (UniqueConstraint("platform","source_username","message_id","matched_keyword", name="uq_result"),)

class ScanHistory(Base):
    __tablename__ = "scan_history"
    id = Column(Integer, primary_key=True)
    scan_type = Column(String(50), default="auto")
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    matched_count = Column(Integer, default=0)
    saved_count = Column(Integer, default=0)
    status = Column(String(50), default="running")
    note = Column(Text)

def init_db():
    Base.metadata.create_all(bind=engine)

def db():
    return SessionLocal()

def add_source(platform, link, username, language="UZ", category=None, title=None):
    s=db()
    try:
        item=s.query(Source).filter(Source.link==link).first()
        if not item:
            s.add(Source(platform=platform, link=link, username=username, language=language, category=category, title=title or username))
        else:
            item.platform=platform; item.language=language; item.category=category
        s.commit()
    finally:
        s.close()

def add_keyword(keyword, user_category=None, priority="MEDIUM"):
    s=db()
    try:
        val=keyword.lower().strip()
        item=s.query(Keyword).filter(Keyword.keyword==val).first()
        if not item:
            s.add(Keyword(keyword=val, user_category=user_category, priority=priority))
        else:
            item.user_category=user_category; item.priority=priority
        s.commit()
    finally:
        s.close()

def get_sources(active_only=False):
    s=db()
    try:
        q=s.query(Source)
        if active_only: q=q.filter(Source.is_active==True)
        return q.order_by(Source.id.desc()).all()
    finally:
        s.close()

def get_keywords(active_only=False):
    s=db()
    try:
        q=s.query(Keyword)
        if active_only: q=q.filter(Keyword.is_active==True)
        return q.order_by(Keyword.id.desc()).all()
    finally:
        s.close()

def save_result(item):
    s=db()
    try:
        ex=s.query(Result).filter(Result.platform==item["platform"], Result.source_username==item["username"], Result.message_id==item["message_id"], Result.matched_keyword==item["matched_keyword"]).first()
        if ex: return False
        s.add(Result(platform=item["platform"], source_link=item["source_link"], source_username=item["username"], source_title=item.get("source_title"), source_language=item.get("source_language"), message_id=item["message_id"], message_url=item["message_url"], message_text=item["text"], matched_keyword=item["matched_keyword"], user_category=item.get("user_category"), repetition_count=item["repetition_count"], message_time=item.get("message_time"), ai_classification=item.get("ai_classification"), sentiment=item.get("sentiment"), risk_level=item.get("risk_level")))
        s.commit(); return True
    finally:
        s.close()

def get_results(q=None, keyword=None, source=None, platform=None, language=None, sentiment=None, limit=500):
    s=db()
    try:
        query=s.query(Result)
        if q: query=query.filter(Result.message_text.ilike(f"%{q}%"))
        if keyword: query=query.filter(Result.matched_keyword==keyword)
        if source: query=query.filter(Result.source_username==source)
        if platform: query=query.filter(Result.platform==platform)
        if language: query=query.filter(Result.source_language==language)
        if sentiment: query=query.filter(Result.sentiment==sentiment)
        return query.order_by(Result.created_at.desc()).limit(limit).all()
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
        return {"total_results":s.query(Result).count(),"today_results":s.query(Result).filter(func.date(Result.created_at)==func.current_date()).count(),"total_sources":s.query(Source).count(),"active_sources":s.query(Source).filter(Source.is_active==True).count(),"total_keywords":s.query(Keyword).count(),"risk_results":s.query(Result).filter(Result.sentiment.in_(["negative","risk"])).count()}
    finally: s.close()

def chart(field):
    s=db()
    try:
        col=getattr(Result, field)
        rows=s.query(col, func.count(Result.id)).group_by(col).order_by(func.count(Result.id).desc()).limit(10).all()
        return [{"name":r[0] or "N/A","count":r[1]} for r in rows]
    finally: s.close()

def daily():
    s=db()
    try:
        rows=s.query(func.date(Result.created_at), func.count(Result.id)).group_by(func.date(Result.created_at)).order_by(func.date(Result.created_at)).limit(30).all()
        return [{"date":str(r[0]),"count":r[1]} for r in rows]
    finally: s.close()

def scan_start(t):
    s=db()
    try:
        row=ScanHistory(scan_type=t); s.add(row); s.commit(); return row.id
    finally: s.close()

def scan_finish(i, matched, saved, status="done", note=None):
    s=db()
    try:
        row=s.query(ScanHistory).filter(ScanHistory.id==i).first()
        if row:
            row.finished_at=datetime.utcnow(); row.matched_count=matched; row.saved_count=saved; row.status=status; row.note=note; s.commit()
    finally: s.close()

def scan_history():
    s=db()
    try: return s.query(ScanHistory).order_by(ScanHistory.started_at.desc()).limit(20).all()
    finally: s.close()

def set_source_status(i, active):
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

def set_keyword_status(i, active):
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
