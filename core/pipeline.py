"""Company signal -> list of finished leads."""
import time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from core import auditor, stakeholders, verifier, dedup, qc, models, logger, contacts, apiverify, smtp_gate
log = logger.get()

def build_leads(signals, dd, gate=None, cache=None):
    seen, companies = set(), []
    for s in signals:
        k = s["company"].lower()
        if k not in seen:
            seen.add(k); companies.append(s)
    out, stats = [], {"companies": len(companies), "audited": 0, "people": 0, "rejected": 0}
    lock, deadline = threading.Lock(), time.time() + 12 * 60
    cache = cache if cache is not None else apiverify.DomainCache()
    def work(s):
        if time.time() > deadline: return []
        try: return _one(s, dd, stats, lock, gate, cache, deadline)
        except Exception as e:
            log.warning("company failed (%s)", type(e).__name__); return []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for f in as_completed([ex.submit(work, s) for s in companies]):
            out += f.result()
    return out, stats

def _one(s, dd, stats, lock, gate, cache, deadline):
    a = auditor.audit(s["company"], s.get("domain_hint", ""))
    if not a: return []
    with lock: stats["audited"] += 1
    a["emails"] = sorted(set(a["emails"]) | set(contacts.deep_emails(a["root"], a["domain"], a["html"])))[:12]
    people = stakeholders.extract(a["root"], s.get("people"))
    with lock: stats["people"] += len(people)
    pat = verifier.detect_pattern(a["emails"], people, a["domain"])
    if pat: cache.put(a["domain"], pattern=pat)
    else: pat = cache.get(a["domain"]).get("Pattern", "")
    tier = stakeholders.size_tier(len(people), a["html"])
    extra = " | ".join(f"{k}: {v}" for k, v in {**a["socials"], "Site": a["meta"]}.items())
    leads = []
    for p in people:
        parts = p["name"].split()
        l = models.blank()
        l.update({"Industry_Tag": a["industry"], "Full_Name": p["name"], "Role_Title": p["role"],
                  "Department_Track": p["track"], "Company_Size_Tier": tier,
                  "Outreach_Priority": p["priority"], "Company_Name": s["company"],
                  "Website_Domain": a["domain"], "Phone_Number": ", ".join(a["phones"]),
                  "LinkedIn_URL": p.get("linkedin", ""), "Location_Country": s["country"],
                  "Other_Extra_Info": extra, "Source_Platform": s["source_platform"],
                  "Signal_Category": s["signal"], "Exact_Evidence_Snippet": s["evidence"],
                  "Website_Audit_Fact": "; ".join(a["audit_facts"]), "Source_URL": s["source_url"]})
        l["Person_Fingerprint"] = dedup.fingerprint(p["name"], a["domain"])
        email, src = _email(parts, a, pat)
        if not email: continue
        l["Email"], l["Email_Source"] = email, src
        l["Email_Status"], route = verifier.verify(email, src, bool(pat))
        l["Lead_ID"] = l["Person_Fingerprint"]
        if route == "smtp":
            res = apiverify.check(email, a["domain"], cache)
            if res == "valid": l["Email_Status"], route = "API_Verified", "hot"
            elif res == "invalid": route = "drop"
        if route == "drop": stats["rejected"] += 1; continue
        l["Lead_Score"] = qc.score(l)
        if l["Email_Status"] == "Permutated_Unverified":   # last resort: shared server, top P1 only
            if apiverify.smtp_last_resort(l, gate, smtp_gate.mx_provider(a["domain"]), deadline) == "valid":
                l["Email_Status"] = "SMTP_Verified"; l["Lead_Score"] = qc.score(l)
        ok, _ = qc.qc(l)
        l["QC_Passed_And_Status"] = "YES / Ready_To_Export" if ok else "NO"
        with lock:
            if dd.reject_reason(l): stats["rejected"] += 1; continue
            dd.add(l); leads.append(l)
    return leads

def _email(parts, a, pat):
    if len(parts) < 2: return "", ""
    f, last = parts[0].lower(), parts[-1].lower()
    for e in a["emails"]:
        if e.split("@")[0] in (f, last, f"{f}.{last}", f"{f[0]}{last}", f"{f}{last}"):
            return e, "Scraped_Direct"
    perms = verifier.permutations(parts[0], parts[-1], a["domain"])
    if not perms: return "", ""
    if pat and pat in perms: return perms[pat], "Domain_Pattern_Match"
    return perms["first.last"], "Permutated_Pattern"
