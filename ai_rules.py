def classify_text(text):
    t=(text or '').lower()
    if any(x in t for x in ['об-ҳаво','ёмғир','жала','сел','момақалдироқ','шамол','қор','дўл','гидромет','фвв','fvv','сув тошқини']): return 'FVV / Ob-havo'
    if any(x in t for x in ['йўл','yo‘l','дорога','транспорт','авто','машина','тирбанд','tirband','йпх','ypx','авария']): return 'Transport / Yo‘l'
    if any(x in t for x in ['газ','свет','электр','коммунал','сув','suv','вода','иссиқлик']): return 'Kommunal'
    if any(x in t for x in ['эко','ekolog','чиқинди','стикер','stiker','экология','атмосфера']): return 'Ekologiya'
    if any(x in t for x in ['жиноят','firib','ўғир','милитсия','militsiya','суд','прокуратура']): return 'Huquq / Xavfsizlik'
    if any(x in t for x in ['президент','вазир','ҳоким','сенат','парламент','қарор','фармон']): return 'Siyosat / Davlat'
    if any(x in t for x in ['кредит','банк','инфляция','нарх','солиқ','иқтисод','экспорт']): return 'Iqtisod'
    if any(x in t for x in ['шифохона','касал','соғлиқ','вирус','грипп','covid','дори']): return 'Sog‘liq'
    return 'Boshqa'

def sentiment_text(text):
    t=(text or '').lower()
    if any(w in t for w in ['сел','сув тошқини','портлаш','ёнғин','кучли жала','хавф','фавқулодда','эвакуация','авария','ҳалок','огоҳлантириш']): return 'risk'
    neg=sum(1 for w in ['муаммо','xato','ёмон','yomon','норози','shikoyat','жарима','қийнал','qiyin','танқид','buzildi','ёпилди'] if w in t)
    pos=sum(1 for w in ['яхши','zo‘r','зўр','рахмат','minnatdor','ijobiy','очилди','yaxshilandi','muvaffaqiyat','табрик'] if w in t)
    if neg>pos: return 'negative'
    if pos>neg: return 'positive'
    return 'neutral'

def risk_level(text, sentiment):
    t=(text or '').lower()
    if any(w in t for w in ['портлаш','сув тошқини','ёнғин','ҳалок','эвакуация','кучли жала','сел']): return 'high'
    if sentiment=='risk' or any(w in t for w in ['хавф','огоҳлантириш','авария','қутқарув','ёмғир','момағалдироқ','шамол']): return 'medium'
    if sentiment=='negative': return 'low'
    return 'none'
