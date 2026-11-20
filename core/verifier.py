"""4-layer free verifier + @ permutator."""
import re, hashlib
import dns.resolver
from core import net

SYNTAX = re.compile(r"^[a-z0-9._%+-]+@[a-z0-9-]+(\.[a-z0-9-]+)+$")
TYPOS = {"gmial.com": "gmail.com", "gmai.com": "gmail.com", "yaho.com": "yahoo.com", "hotmial.com": "hotmail.com"}
DISPOSABLE = {"mailinator.com", "10minutemail.com", "guerrillamail.com", "tempmail.com", "yopmail.com"}
ROLE = re.compile(r"^(info|contact|sales|team|hello|office|mail|enquiries|enquiry|marketing)$")
_cache = {}

def fix(email):
    email = (email or "").strip().lower()
    if "@" in email:
        l, d = email.split("@", 1); email = f"{l}@{TYPOS.get(d, d)}"
    return email

def layer1(email):
    if not SYNTAX.match(email): return False
    l, d = email.split("@")
    return d not in DISPOSABLE and not ROLE.match(l)

def dns_info(domain):
    if domain in _cache: return _cache[domain]
    res = {"mx": False, "spf": False, "dmarc": False}
    try: res["mx"] = bool(dns.resolver.resolve(domain, "MX", lifetime=5))
    except Exception: pass
    for key, name in (("spf", domain), ("dmarc", "_dmarc." + domain)):
        try:
            txt = " ".join(str(r) for r in dns.resolver.resolve(name, "TXT", lifetime=5)).lower()
            res[key] = ("v=spf1" in txt) if key == "spf" else ("v=dmarc1" in txt)
        except Exception: pass
    _cache[domain] = res
    return res

def gravatar(email):
    h = hashlib.md5(email.encode()).hexdigest()
    r = net.get(f"https://www.gravatar.com/avatar/{h}?d=404", timeout=6)
    return r is not None and r.status_code == 200

def verify(email, source, pattern_confirmed=False):
    """Returns (status, route). route: hot | smtp | drop"""
    email = fix(email)
    if not layer1(email): return "Invalid", "drop"
    d = email.split("@")[1]
    info = dns_info(d)
    if not info["mx"]: return "Invalid", "drop"
    if source == "Scraped_Direct": return "Valid_MX_Direct", "hot"
    if source == "Domain_Pattern_Match" and pattern_confirmed: return "Pattern_Matched_MX", "hot"
    if gravatar(email): return "Valid_MX_Direct", "hot"
    return "Permutated_Unverified", "smtp"

def permutations(first, last, domain):
    f, l = re.sub(r"[^a-z]", "", first.lower()), re.sub(r"[^a-z]", "", last.lower())
    if not f or not l: return []
    return {"first.last": f"{f}.{l}@{domain}", "first": f"{f}@{domain}", "flast": f"{f[0]}{l}@{domain}",
            "firstlast": f"{f}{l}@{domain}", "first_l": f"{f}{l[0]}@{domain}"}

def detect_pattern(scraped_emails, people, domain):
    """If a scraped email matches a known person's name pattern, return that pattern key."""
    for e in scraped_emails:
        local = e.split("@")[0]
        for p in people:
            parts = p["name"].split()
            if len(parts) < 2: continue
            for key, cand in (permutations(parts[0], parts[-1], domain) or {}).items():
                if cand.split("@")[0] == local: return key
    return ""
