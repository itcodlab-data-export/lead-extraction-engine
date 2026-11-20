"""Lead scoring + 7-point QC."""
import config

TRACK_PTS = {"Executive": 10, "Marketing": 10, "Sales": 8, "Tech_IT": 8, "HR_Ops": 5}
STATUS_PTS = {"Valid_MX_Direct": 30, "Pattern_Matched_MX": 22, "Permutated_Unverified": 10}

def score(lead):
    s = STATUS_PTS.get(lead["Email_Status"], 0)
    s += 20 if lead["Exact_Evidence_Snippet"] else 0
    s += 15 if lead["Website_Audit_Fact"] else 0
    s += TRACK_PTS.get(lead["Department_Track"], 0)
    s += 5 if lead["Phone_Number"] else 0
    s += 5 if lead["LinkedIn_URL"] else 0
    s += 5 if lead["Industry_Tag"] not in ("", "Other") else 0
    s += 10 if lead["Outreach_Priority"] in (1, "1", 2, "2") else 0
    return min(100, s)

def qc(lead, dnc_hit=False):
    checks = [
        lead["Email_Status"] in ("Valid_MX_Direct", "Pattern_Matched_MX", "Permutated_Unverified"),
        bool(lead["Person_Fingerprint"]),
        bool(lead["Full_Name"]) and bool(lead["Company_Name"]),
        bool(lead["Industry_Tag"]),
        bool(lead["Exact_Evidence_Snippet"] or lead["Website_Audit_Fact"]),
        int(lead["Lead_Score"] or 0) >= config.MIN_LEAD_SCORE,
        not dnc_hit,
    ]
    return all(checks), [i + 1 for i, c in enumerate(checks) if not c]
