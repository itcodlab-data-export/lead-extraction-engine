import sys; sys.path.insert(0, ".")
from core import dedup, verifier, qc, stakeholders, models, logger, auditor

def test_all():
    assert dedup.norm_email("J.Doe+x@gmail.com") == "jdoe@gmail.com"
    assert verifier.fix("a@gmial.com") == "a@gmail.com"
    assert not verifier.layer1("info@acme.com") and verifier.layer1("jane.doe@acme.com")
    assert verifier.permutations("Jane", "Doe", "acme.com")["flast"] == "jdoe@acme.com"
    assert stakeholders.track_of("Head of Growth") == "Marketing"
    assert stakeholders.track_of("Marketing Intern") == ""
    assert auditor.canonical("https://www.shop.acme.co.in/x") == "acme.co.in"
    d = dedup.Dedup()
    l = models.blank(); l.update(Email="noreply@acme.com", Company_Name="Acme", Website_Domain="acme.com", Person_Fingerprint="x")
    assert d.reject_reason(l) == "generic_inbox"
    l.update(Email="a@acme.com", Company_Name="Acme SEO Agency"); assert d.reject_reason(l) == "competitor_agency"
    l = models.blank(); l.update(Email_Status="Valid_MX_Direct", Exact_Evidence_Snippet="x", Website_Audit_Fact="y",
        Department_Track="Marketing", Phone_Number="1", LinkedIn_URL="u", Industry_Tag="Ecommerce_D2C", Outreach_Priority=1,
        Full_Name="A B", Company_Name="C", Person_Fingerprint="f")
    l["Lead_Score"] = qc.score(l); assert l["Lead_Score"] >= 65 and qc.qc(l)[0]
    lg = logger.get(); import io, logging
    print("OK")
test_all()
