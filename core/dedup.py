"""3-key person dedup + junk filters."""
import re, hashlib
from core import models

GENERIC_LOCAL = re.compile(r"^(noreply|no-reply|donotreply|abuse|postmaster|webmaster|admin|hr|jobs|careers|support|help|billing|privacy|legal|spam)$", re.I)
AGENCY_NAME = re.compile(r"\b(agency|seo|digital marketing|ad agency|media buying|growth studio|web design)\b", re.I)

def norm_email(e):
    e = (e or "").strip().lower()
    if "@" not in e: return ""
    local, dom = e.split("@", 1)
    if dom in ("gmail.com", "googlemail.com"):
        local = local.split("+")[0].replace(".", "")
    return f"{local}@{dom}"

def li_slug(u):
    m = re.search(r"linkedin\.com/in/([A-Za-z0-9_%-]+)", u or "")
    return m.group(1).lower() if m else ""

def fingerprint(name, domain):
    k = re.sub(r"[^a-z]", "", (name or "").lower()) + "|" + (domain or "")
    return hashlib.sha1(k.encode()).hexdigest()[:16]

class Dedup:
    def __init__(self, index_rows=None, dnc_rows=None):
        self.fp, self.em, self.li = set(), set(), set()
        self.dnc = set()
        for r in index_rows or []:
            if r.get("Person_Fingerprint"): self.fp.add(r["Person_Fingerprint"])
            if r.get("Normalized_Email"): self.em.add(r["Normalized_Email"])
            if r.get("LinkedIn_Slug"): self.li.add(r["LinkedIn_Slug"])
        for r in dnc_rows or []:
            if r.get("Value"): self.dnc.add(str(r["Value"]).lower())

    def reject_reason(self, lead):
        email, dom = norm_email(lead["Email"]), lead["Website_Domain"]
        if email and GENERIC_LOCAL.match(email.split("@")[0]): return "generic_inbox"
        if AGENCY_NAME.search(lead["Company_Name"]): return "competitor_agency"
        if email in self.dnc or dom in self.dnc: return "do_not_contact"
        if lead["Person_Fingerprint"] in self.fp: return "dup_fingerprint"
        if email and email in self.em: return "dup_email"
        s = li_slug(lead["LinkedIn_URL"])
        if s and s in self.li: return "dup_linkedin"
        return ""

    def add(self, lead):
        self.fp.add(lead["Person_Fingerprint"])
        e = norm_email(lead["Email"])
        if e: self.em.add(e)
        s = li_slug(lead["LinkedIn_URL"])
        if s: self.li.add(s)
