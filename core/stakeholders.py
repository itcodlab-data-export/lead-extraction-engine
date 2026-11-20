"""Multi-stakeholder role extractor: native-first (team/about pages), capped dorks as fallback."""
import re, config
from bs4 import BeautifulSoup
from core import net, logger
log = logger.get()

TRACKS = [
    ("Executive", r"\b(ceo|chief executive|founder|co-?founder|cfo|coo|owner|managing director|president)\b"),
    ("Marketing", r"\b(cmo|chief marketing|head of (growth|marketing)|growth|performance marketing|marketing (manager|head|director)|brand manager)\b"),
    ("Sales", r"\b(vp.{0,3}sales|sales (manager|head|director)|cro|chief revenue|business development)\b"),
    ("Tech_IT", r"\b(cto|chief technology|it manager|shopify (lead|developer)|head of (engineering|technology)|engineering manager)\b"),
    ("HR_Ops", r"\b(head of (hr|people|operations)|hr manager|operations manager|talent acquisition (lead|head))\b"),
]
JUNIOR = re.compile(r"\b(intern|trainee|junior|assistant|associate|executive assistant|apprentice)\b", re.I)
NAME = re.compile(r"^[A-Z][a-z]+(?:[ '-][A-Z][a-z]+){1,2}$")
PATHS = ["/team", "/about", "/about-us", "/leadership", "/pages/about-us", "/pages/team", "/company"]
LINKEDIN = re.compile(r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/in/[A-Za-z0-9_%-]+")

TITLEWORDS = re.compile(r"\b(chief|officer|director|manager|president|founder|owner|chairman|executive|head|developer|vp|lead|ceo|cfo|cto|cmo|coo|partner|team|board|about|contact|our|the)\b", re.I)

def track_of(role):
    if not role or JUNIOR.search(role):
        return ""
    for t, rx in TRACKS:
        if re.search(rx, role, re.I):
            return t
    return ""

def _scrape_page(html):
    soup = BeautifulSoup(html, "html.parser")
    found = []
    for el in soup.find_all(["h2", "h3", "h4", "strong", "p", "span", "div"]):
        txt = el.get_text(" ", strip=True)
        if not NAME.match(txt) or TITLEWORDS.search(txt):
            continue
        sib = el.find_next(["p", "span", "div", "h5", "h6"])
        role = sib.get_text(" ", strip=True) if sib else ""
        if len(role) > 70 or NAME.match(role):
            continue
        tr = track_of(role)
        if tr:
            li = ""
            par = el.find_parent()
            if par:
                m = LINKEDIN.search(str(par))
                li = m.group(0) if m else ""
            found.append({"name": txt, "role": role, "track": tr, "linkedin": li})
    return found

def extract(root, extra_people=None):
    people = list(extra_people or [])
    for p in PATHS:
        html = net.text(root + p)
        if html:
            people += _scrape_page(html)
    return _cap(people)

def _cap(people):
    seen, per_dept, out = set(), {}, []
    order = {t: i for i, (t, _) in enumerate(TRACKS)}
    for p in sorted(people, key=lambda x: order.get(x["track"], 9)):
        k = p["name"].lower()
        if k in seen or per_dept.get(p["track"], 0) >= config.MAX_PER_DEPARTMENT:
            continue
        seen.add(k); per_dept[p["track"]] = per_dept.get(p["track"], 0) + 1
        out.append(p)
        if len(out) >= config.MAX_CONTACTS_PER_COMPANY:
            break
    for i, p in enumerate(out, 1):
        p["priority"] = i
    return out

def size_tier(n_people, html=""):
    if n_people >= 6 or re.search(r"\b(500|1000)\+? employees", html or "", re.I): return "Mid_Large"
    if n_people >= 3: return "Small"
    return "Micro"
