"""Company signal -> list of finished leads."""
import datetime
from core import auditor, stakeholders, verifier, dedup, qc, models, logger
log = logger.get()

def build_leads(signals, dd):
    seen, companies = set(), []
    for s in signals:
        k = s["company"].lower()
        if k not in seen:
            seen.add(k); companies.append(s)
    out, stats = [], {"companies": len(companies), "audited": 0, "people": 0, "rejected": 0}
    for s in companies:
        try:
            out += _one(s, dd, stats)
        except Exception as e:
            log.warning("company failed (%s)", type(e).__name__)
    return out, stats

def _one(s, dd, stats):
    a = auditor.audit(s["company"], s.get("domain_hint", ""))
    if not a: return []
    stats["audited"] += 1
    people = stakeholders.extract(a["root"], s.get("people"))
    stats["people"] += len(people)
    pat = verifier.detect_pattern(a["emails"], people, a["domain"])
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
        if route == "drop": stats["rejected"] += 1; continue
        reason = dd.reject_reason(l)
        if reason: stats["rejected"] += 1; continue
        l["Lead_Score"] = qc.score(l)
        ok, _ = qc.qc(l)
        l["QC_Passed_And_Status"] = "YES / Ready_To_Export" if ok else "NO"
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
