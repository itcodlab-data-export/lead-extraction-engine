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


# ---- Part 2 / Batch 1 (all offline: no network, no keys) ----
import time, config
from core import contacts, apiverify
from sources import ats, shopify_reviews, producthunt, batch1

PAGE = '''<html><head><script type="application/ld+json">{"@type":"Organization","contactPoint":{"email":"mailto:Ceo@Acme.com"}}</script></head>
<body><a href="mailto:hello@acme.com?subject=x">x</a> sales@acme.com, logo@acme.com.png, other@elsewhere.org
<a class="__cf_email__" data-cfemail="%s">[email protected]</a></body></html>''' % (
    "".join(["%02x" % 0x42] + ["%02x" % (ord(c) ^ 0x42) for c in "cfo@acme.com"]))

def test_contacts_deep_scrape(monkeypatch):
    em = contacts.extract_emails(PAGE)
    assert {"ceo@acme.com", "hello@acme.com", "sales@acme.com", "cfo@acme.com"} <= em and "logo@acme.com.png" not in em
    monkeypatch.setattr(contacts.net, "text", lambda url, **k: PAGE if url.endswith("/team") else "")
    assert "other@elsewhere.org" not in contacts.deep_emails("https://acme.com", "acme.com") and \
        "cfo@acme.com" in contacts.deep_emails("https://acme.com", "acme.com")
    assert {"/contact", "/contact-us", "/about", "/team", "/policies/contact-information", "/privacy-policy"} == set(contacts.PATHS)

def test_apiverify_skips_missing_keys_and_uses_cache(monkeypatch):
    for k in ("REOON_API_KEY", "VERIFALIA_USER", "VERIFALIA_PASS", "ZEROBOUNCE_API_KEY", "ABSTRACT_API_KEY", "HUNTER_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(apiverify.net, "get", lambda *a, **k: (_ for _ in ()).throw(AssertionError("called without key")))
    assert apiverify.waterfall("a@acme.com") == "unknown"
    monkeypatch.setenv("ZEROBOUNCE_API_KEY", "k"); monkeypatch.setenv("HUNTER_API_KEY", "k")
    seq = iter(["unknown", "catch_all"]); monkeypatch.setattr(apiverify, "zerobounce", lambda e, k: next(seq))
    monkeypatch.setattr(apiverify, "hunter", lambda e, k: next(seq))
    monkeypatch.setattr(apiverify, "PROVIDERS", [("zerobounce", apiverify.zerobounce, lambda: "k"), ("hunter", apiverify.hunter, lambda: "k")])
    cache = apiverify.DomainCache()
    assert apiverify.check("a@acme.com", "acme.com", cache) == "catch_all"       # waterfall fell through to Hunter
    assert apiverify.check("b@acme.com", "acme.com", cache) == "catch_all"       # served from Domain_Cache, no API call
    assert cache.new and cache.new[0][:2] == ["acme.com", "yes"]
    assert apiverify._map("accept_all") == "catch_all" and apiverify._map("Do-Not-Mail") == "invalid"

def test_ats_parsing():
    assert ats.company_of("https://boards.greenhouse.io/acme-corp/jobs/123") == "Acme Corp"
    assert ats.company_of("https://jobs.lever.co/zeta/abc") == "Zeta"
    assert ats.company_of("https://apply.workable.com/beta/j/XYZ/") == "Beta"
    assert ats.company_of("https://example.com/foo") == ""
    import base64; u = base64.urlsafe_b64encode(b"https://jobs.ashbyhq.com/gamma/1").decode().rstrip("=")
    assert ats.parse_results(f'<h2><a href="https://www.bing.com/ck/a?!&amp;u=a1{u}&amp;ntb=1">t</a></h2>') == ["https://jobs.ashbyhq.com/gamma/1"]

REV = '''<div data-merchant-review=""><div aria-label="1 out of 5 stars" role="img"></div><div class="tw-mb-xs">Meta pixel stopped tracking purchase events</div>
<div class="tw-text-heading-xs tw-x">Shop One</div><div>United States</div></div>
<div data-merchant-review=""><div aria-label="5 out of 5 stars"></div><div class="tw-mb-xs">pixel great</div><div class="tw-text-heading-xs">Shop Two</div><div>United States</div></div>
<div data-merchant-review=""><div aria-label="2 out of 5 stars"></div><div class="tw-mb-xs">capi sync broken</div><div class="tw-text-heading-xs">Shop Three</div><div>India</div></div>'''

def test_shopify_reviews_only_low_star_and_country(monkeypatch):
    assert [r["store"] for r in shopify_reviews.parse(REV, "facebook")] == ["Shop One", "Shop Three"]
    monkeypatch.setattr(shopify_reviews, "discover", lambda: ["facebook"])
    monkeypatch.setattr(shopify_reviews.net, "text", lambda *a, **k: REV)
    monkeypatch.setattr(shopify_reviews.time, "sleep", lambda s: None)
    for tc, want in (("US", {"Shop One"}), ("INDIA", {"Shop Three"}), ("BOTH", {"Shop One", "Shop Three"})):
        monkeypatch.setattr(config, "TARGET_COUNTRY", tc)
        assert {s["company"] for s in shopify_reviews.fetch()} == want

def test_producthunt_graceful_skip_and_country(monkeypatch):
    monkeypatch.delenv("PRODUCTHUNT_TOKEN", raising=False)
    assert producthunt.fetch() == []
    assert producthunt.country_of({"name": "X", "tagline": "Built in Bengaluru", "website": ""}) == "INDIA"
    assert producthunt.country_of({"name": "X", "tagline": "t", "website": "https://x.in/a"}) == "INDIA"
    assert producthunt.country_of({"name": "X", "tagline": "t", "website": "https://x.com"}) == "US"

def test_batch1_parallel_isolated_and_capped():
    def boom(deadline=None): raise RuntimeError("down")
    def slow(deadline=None): time.sleep(5); return [{"company": "never"}]
    def ok(deadline=None): return [{"company": "fine"}]
    t0 = time.time()
    out = batch1.fetch(budget=0.5, sources=(("a", boom), ("b", slow), ("c", ok)))
    assert out == [{"company": "fine"}] and time.time() - t0 < 2          # crash isolated, slow source cut at the cap
    t0 = time.time(); batch1.fetch(budget=5, sources=tuple((str(i), lambda deadline=None: time.sleep(0.4) or []) for i in range(3)))
    assert time.time() - t0 < 1.0                                          # ran in parallel (3 x 0.4s < 1s)
    assert config.BATCH1_BUDGET_SEC == 300

# ---- Batch 2/3 (offline) ----
from sources import dork, social_dorks, launches, marketplaces, competitor_reviews, youtube, batch2

def test_dork_helpers(monkeypatch):
    assert dork.site_in("check https://reddit.com/x and my store glowbar.co.in thanks") == "glowbar.co.in"
    assert dork.site_in("only reddit.com and shopify.com") == ""
    items = list(range(12)); assert len(set(dork.pick(items, 3))) == 3 and 0 <= dork.slot(8) < 8
    html = '<div class="result"><a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fa.com%2Fx">T</a><a class="result__snippet">snip glowbar.com</a></div>'
    monkeypatch.setattr(dork.net, "text", lambda *a, **k: html)
    assert dork.search("q") == [{"url": "https://a.com/x", "title": "T", "snippet": "snip glowbar.com"}]

def test_dork_sources_build_signals(monkeypatch):
    res = [{"url": "https://reddit.com/r/x", "title": "pixel broken", "snippet": "my store glowbar.com has no sales"},
           {"url": "https://reddit.com/r/y", "title": "no domain", "snippet": "nothing here"}]
    monkeypatch.setattr(dork, "search", lambda q: res); monkeypatch.setattr(dork.net, "jitter", lambda x: None)
    monkeypatch.setattr(config, "TARGET_COUNTRY", "US")
    for mod in (social_dorks, launches, marketplaces, competitor_reviews):
        out = mod.fetch()
        assert out and all(s["domain_hint"] == "glowbar.com" and s["country"] == "US" and s["people"] == [] for s in out), mod.__name__
        assert len({s["company"] for s in out}) == 1               # deduped by company

def test_youtube_skips_without_key_and_batch_registry(monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    assert youtube.fetch() == [] and len(batch2.SOURCES) == 5

def test_hiring_rotation_changes_with_slot(monkeypatch):
    seen = set()
    for h in range(0, 24, 3):
        monkeypatch.setattr(dork, "utc_now", lambda h=h: datetime.datetime(2026, 11, 25, h, 0, tzinfo=datetime.timezone.utc))
        seen.add(tuple(dork.pick(config.JOB_QUERIES, config.JOB_QUERIES_PER_RUN)))
    assert len(seen) >= 4
import datetime
