import re

POSITIVE_PATTERNS = [
    r"мукофот", r"тақдирлан", r"рағбатлантир", r"порадан бош торт", r"порани олмаган",
    r"пора олмаган", r"қонун доирасида иш тут", r"ютуқ", r"муваффақият", r"ишга туширилди",
    r"очилди", r"яратилди", r"яхшиланди", r"награда", r"награжден", r"отказался от взятки",
    r"не взял взятку", r"успех", r"достижение", r"запущен", r"открыт"
]
NEGATIVE_PATTERNS = [
    r"авария", r"ҳалокат", r"халокат", r"ўлим", r"вафот", r"жабрлан", r"жароҳат",
    r"ёнғин", r"портлаш", r"сел", r"кучли шамол", r"жиноят", r"қотил", r"ўғирлик",
    r"фирибгар", r"қамал", r"қўлга олин", r"ушланди", r"мусодара", r"ноқонуний",
    r"тақиқланган", r"коррупция", r"пора олди", r"пора талаб", r"пора билан ушлан",
    r"гиёҳванд", r"наркотик", r"муаммо", r"носозлик", r"катастроф", r"смерт", r"пожар",
    r"взрыв", r"преступ", r"мошенник", r"краж", r"задержан", r"изъят", r"незакон", r"ошибка", r"сбой"
]
ALERT_PATTERNS = [
    r"диққат", r"огоҳлантир", r"тезкор", r"фавқулодда", r"хавф", r"эвакуация",
    r"йўл ёпил", r"ҳаракат чеклан", r"сел кел", r"кучли жала", r"внимание",
    r"срочно", r"чрезвычай", r"опасност", r"перекрыт", r"ограничен"
]
ANNOUNCEMENT_PATTERNS = [
    r"имтиҳон", r"имтихон", r"экстернат", r"эълон", r"жадвал", r"санаси",
    r"юбориб қўйинг", r"гуруҳларга юбор", r"канал", r"обуна", r"реклама",
    r"экзамен", r"объявлен", r"расписание", r"дата", r"подпишитесь"
]
LAW_SECURITY_PATTERNS = [r"йпх", r"ииб", r"милиция", r"суд", r"жиноят", r"пора", r"қоидабузар", r"жарима", r"тергов", r"прокуратура", r"дхх", r"дпс", r"штраф", r"взятк"]
TRANSPORT_PATTERNS = [r"йўл", r"йул", r"автобус", r"автомобиль", r"машина", r"транспорт", r"тирбанд", r"ҳаракат", r"дорога", r"пробка", r"движение"]
EDU_PATTERNS = [r"мактаб", r"ўқувчи", r"укувчи", r"синф", r"имтиҳон", r"имтихон", r"экстернат", r"таълим", r"университет", r"школ", r"ученик", r"класс", r"экзамен"]
WEATHER_FVV_PATTERNS = [r"об-ҳаво", r"об хаво", r"ёмғир", r"емғир", r"жала", r"момақалдироқ", r"сел", r"шамол", r"қор", r"ҳарорат", r"фвв", r"мчс", r"погода", r"дожд", r"ливень", r"гроза", r"ветер"]
POLITICS_PATTERNS = [r"президент", r"вазир", r"ҳоким", r"ҳукумат", r"парламент", r"сенат", r"давлат", r"сиёсат", r"министр", r"правительств"]

def _contains_any(text, patterns):
    t = (text or "").lower()
    return any(re.search(p, t, flags=re.IGNORECASE) for p in patterns)

def classify_text(text, user_category=None):
    t = (text or "").lower()
    if user_category:
        ai_class = user_category
    elif _contains_any(t, WEATHER_FVV_PATTERNS):
        ai_class = "Ob-havo / FVV"
    elif _contains_any(t, EDU_PATTERNS):
        ai_class = "Ta'lim"
    elif _contains_any(t, LAW_SECURITY_PATTERNS):
        ai_class = "Huquq / Xavfsizlik"
    elif _contains_any(t, TRANSPORT_PATTERNS):
        ai_class = "Transport / Yo‘l"
    elif _contains_any(t, POLITICS_PATTERNS):
        ai_class = "Siyosat / Davlat"
    else:
        ai_class = "Boshqa"

    pos = _contains_any(t, POSITIVE_PATTERNS)
    neg = _contains_any(t, NEGATIVE_PATTERNS)
    alert = _contains_any(t, ALERT_PATTERNS)
    ann = _contains_any(t, ANNOUNCEMENT_PATTERNS)

    if re.search(r"(порадан бош торт|порани олмаган|пора олмаган|отказался от взятки|не взял взятку)", t):
        return ai_class, "positive", "low"
    if ann and not neg:
        return ai_class, "neutral", "low"
    if alert and neg:
        return ai_class, "negative", "high"
    if alert and not neg:
        return ai_class, "neutral", "medium"
    if pos and not neg:
        return ai_class, "positive", "low"
    if neg and pos:
        severe = _contains_any(t, [r"ўлим", r"вафот", r"портлаш", r"ёнғин", r"ҳалокат", r"жабрлан", r"наркотик", r"қўлга олин", r"ушланди"])
        return ai_class, ("negative" if severe else "neutral"), ("high" if severe else "medium")
    if neg:
        return ai_class, "negative", "medium"
    return ai_class, "neutral", "low"
