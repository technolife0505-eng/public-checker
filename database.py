from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, UniqueConstraint, func
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Channel(Base):
    __tablename__ = "channels"
    id = Column(Integer, primary_key=True)
    link = Column(String(500), unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=False, index=True)
    title = Column(String(255))
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Keyword(Base):
    __tablename__ = "keywords"
    id = Column(Integer, primary_key=True)
    keyword = Column(String(500), unique=True, nullable=False, index=True)
    category = Column(String(100))
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Result(Base):
    __tablename__ = "results"
    id = Column(Integer, primary_key=True)
    channel_link = Column(String(500), nullable=False, index=True)
    channel_username = Column(String(255), nullable=False, index=True)
    channel_title = Column(String(255))
    message_id = Column(String(100), nullable=False, index=True)
    message_url = Column(String(700))
    message_text = Column(Text, nullable=False)
    matched_keyword = Column(String(500), nullable=False, index=True)
    keyword_category = Column(String(100), index=True)
    repetition_count = Column(Integer, nullable=False, index=True)
    message_time = Column(DateTime, index=True)
    ai_classification = Column(String(100), index=True)
    sentiment = Column(String(50), index=True)
    is_notified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (UniqueConstraint("channel_username", "message_id", "matched_keyword", name="uq_result_message_keyword"),)

def init_db():
    Base.metadata.create_all(bind=engine)

def db():
    return SessionLocal()

def add_channel(link, username, title=None):
    s = db()
    try:
        if not s.query(Channel).filter(Channel.link == link).first():
            s.add(Channel(link=link, username=username, title=title or username))
            s.commit()
    finally:
        s.close()

def add_keyword(keyword, category=None):
    s = db()
    try:
        value = keyword.lower().strip()
        if not s.query(Keyword).filter(Keyword.keyword == value).first():
            s.add(Keyword(keyword=value, category=category))
            s.commit()
    finally:
        s.close()

def get_channels(active_only=False):
    s = db()
    try:
        q = s.query(Channel)
        if active_only:
            q = q.filter(Channel.is_active == True)
        return q.order_by(Channel.id.desc()).all()
    finally:
        s.close()

def get_keywords(active_only=False):
    s = db()
    try:
        q = s.query(Keyword)
        if active_only:
            q = q.filter(Keyword.is_active == True)
        return q.order_by(Keyword.id.desc()).all()
    finally:
        s.close()

def save_result(item):
    s = db()
    try:
        exists = s.query(Result).filter(
            Result.channel_username == item["username"],
            Result.message_id == item["message_id"],
            Result.matched_keyword == item["matched_keyword"]
        ).first()
        if exists:
            return False
        s.add(Result(
            channel_link=item["channel_link"],
            channel_username=item["username"],
            channel_title=item.get("channel_title"),
            message_id=item["message_id"],
            message_url=item["message_url"],
            message_text=item["text"],
            matched_keyword=item["matched_keyword"],
            keyword_category=item.get("keyword_category"),
            repetition_count=item["repetition_count"],
            message_time=item.get("message_time"),
            ai_classification=item.get("ai_classification"),
            sentiment=item.get("sentiment"),
        ))
        s.commit()
        return True
    finally:
        s.close()

def get_results(q=None, keyword=None, channel=None, limit=500):
    s = db()
    try:
        query = s.query(Result)
        if q:
            query = query.filter(Result.message_text.ilike(f"%{q}%"))
        if keyword:
            query = query.filter(Result.matched_keyword == keyword)
        if channel:
            query = query.filter(Result.channel_username == channel)
        return query.order_by(Result.created_at.desc()).limit(limit).all()
    finally:
        s.close()

def get_stats():
    s = db()
    try:
        return {
            "total_results": s.query(Result).count(),
            "today_results": s.query(Result).filter(func.date(Result.created_at) == func.current_date()).count(),
            "total_channels": s.query(Channel).count(),
            "total_keywords": s.query(Keyword).count()
        }
    finally:
        s.close()

def analytics_keyword():
    s = db()
    try:
        rows = s.query(Result.matched_keyword, func.count(Result.id)).group_by(Result.matched_keyword).order_by(func.count(Result.id).desc()).limit(10).all()
        return [{"name": r[0], "count": r[1]} for r in rows]
    finally:
        s.close()

def analytics_channel():
    s = db()
    try:
        rows = s.query(Result.channel_username, func.count(Result.id)).group_by(Result.channel_username).order_by(func.count(Result.id).desc()).limit(10).all()
        return [{"name": r[0], "count": r[1]} for r in rows]
    finally:
        s.close()

def analytics_daily():
    s = db()
    try:
        rows = s.query(func.date(Result.created_at), func.count(Result.id)).group_by(func.date(Result.created_at)).order_by(func.date(Result.created_at)).limit(30).all()
        return [{"date": str(r[0]), "count": r[1]} for r in rows]
    finally:
        s.close()

def get_unnotified(limit=50):
    s = db()
    try:
        return s.query(Result).filter(Result.is_notified == False).order_by(Result.created_at.desc()).limit(limit).all()
    finally:
        s.close()

def mark_notified(result_id):
    s = db()
    try:
        row = s.query(Result).filter(Result.id == result_id).first()
        if row:
            row.is_notified = True
            s.commit()
    finally:
        s.close()
