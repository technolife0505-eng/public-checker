import re, requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from ai_rules import classify_text, sentiment_text, risk_level

HEADERS={'User-Agent':'Mozilla/5.0'}


def keyword_matches(text, keyword):
    text_l = (text or '').lower()
    kw = (keyword or '').lower().strip()
    if not kw:
        return 0
    if len(kw) <= 3:
        letters = r"A-Za-zА-Яа-яЁёЎўҚқҒғҲҳІі"
        pattern = r"(?<![" + letters + r"])" + re.escape(kw) + r"(?![" + letters + r"])"
        return len(re.findall(pattern, text_l, flags=re.IGNORECASE))
    return text_l.count(kw)

def normalize_source_link(platform,link):
    platform=(platform or 'telegram').lower().strip(); link=(link or '').strip()
    if platform!='telegram':
        username=link.rstrip('/').split('/')[-1] or link
        return username,link,link
    if link.startswith('@'): username=link[1:]
    elif 't.me/' in link: username=link.split('t.me/',1)[1].strip('/')
    else: username=link.strip('/')
    if username.startswith('+') or 'joinchat' in username: raise ValueError('Private invite link ishlamaydi.')
    username=username.split('/')[0]
    if not re.match(r'^[A-Za-z0-9_]{4,}$',username): raise ValueError('Telegram username noto‘g‘ri.')
    return username,f'https://t.me/{username}',f'https://t.me/s/{username}'

def parse_dt(v):
    if not v: return None
    try: return datetime.fromisoformat(v.replace('Z','+00:00'))
    except Exception: return None
def count_kw(text,keyword):
    text=(text or '').lower(); keyword=(keyword or '').lower().strip()
    return text.count(keyword) if keyword else 0
def fetch_page(username,before=None):
    url=f'https://t.me/s/{username}'
    if before: url+=f'?before={before}'
    r=requests.get(url,headers=HEADERS,timeout=20); r.raise_for_status(); return r.text
def parse_posts(html,username,clean_link):
    soup=BeautifulSoup(html,'html.parser')
    title_el=soup.select_one('.tgme_channel_info_header_title span')
    title=title_el.get_text(' ',strip=True) if title_el else username
    posts=[]
    for block in soup.select('.tgme_widget_message'):
        data=block.get('data-post',''); mid=data.split('/')[-1] if '/' in data else data
        text_el=block.select_one('.tgme_widget_message_text'); text=text_el.get_text('\n',strip=True) if text_el else ''
        time_el=block.select_one('time'); dt=parse_dt(time_el.get('datetime') if time_el else '')
        if text and mid: posts.append({'platform':'telegram','username':username,'source_link':clean_link,'source_title':title,'message_id':str(mid),'message_url':f'https://t.me/{username}/{mid}','text':text,'message_time':dt})
    return posts
def fetch_telegram_between(link,date_from=None,date_to=None,max_pages=80):
    username,clean,_=normalize_source_link('telegram',link)
    start=datetime.fromisoformat(str(date_from)).replace(tzinfo=timezone.utc) if date_from else datetime.now(timezone.utc)-timedelta(days=2)
    end=datetime.fromisoformat(str(date_to)).replace(hour=23,minute=59,second=59,microsecond=999999,tzinfo=timezone.utc) if date_to else datetime.now(timezone.utc)
    out=[]; seen=set(); before=None
    for _ in range(max_pages):
        posts=parse_posts(fetch_page(username,before),username,clean)
        if not posts: break
        for p in posts:
            if p['message_id'] in seen: continue
            seen.add(p['message_id']); mt=p.get('message_time')
            if not mt or (start<=mt<=end): out.append(p)
        dated=[p for p in posts if p.get('message_time')]
        if dated and min(p['message_time'] for p in dated)<start: break
        nums=[int(p['message_id']) for p in posts if str(p['message_id']).isdigit()]
        if not nums: break
        before=min(nums)
        if before<=1: break
    return out
def scan_source_for_keywords(source,keywords,date_from=None,date_to=None):
    if (source.platform or 'telegram').lower()!='telegram': return []
    posts=fetch_telegram_between(source.link,date_from,date_to); results=[]
    for p in posts:
        for kw in keywords:
            cnt=count_kw(p['text'],kw.keyword)
            if cnt>=1:
                sent=sentiment_text(p['text'])
                ai_classification, sentiment, risk_level = classify_text(text, getattr(kw, 'user_category', None))
                results.append({**p,'source_language':source.language,'matched_keyword':kw.keyword,'user_category':kw.user_category,'repetition_count':cnt,'ai_classification': ai_classification,'sentiment': sentiment,'risk_level': risk_level,sent)})
    return results
