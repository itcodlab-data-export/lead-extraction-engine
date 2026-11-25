"""All tunables in one place (zero-token config)."""
import os

def _load_api_keys():
    """Optional single secret API_KEYS ('NAME=value' per line) -> env; real env vars win."""
    for line in os.getenv("API_KEYS", "").splitlines():
        k, _, v = line.partition("=")
        if k.strip() and v.strip():
            os.environ.setdefault(k.strip(), v.strip())
_load_api_keys()

TARGET_COUNTRY = os.getenv("TARGET_COUNTRY", "BOTH").upper()  # US | INDIA | BOTH
SHEET_ID = os.getenv("SHEET_ID", "1xmng34DW_b-TqH5nG8bktCDo0f-yFoMdKWccGjohRy4")
# SEC requires a contact in the User-Agent; set SEC_CONTACT as a GitHub Secret/env var.
SEC_USER_AGENT = "ITCODLAB-Extraction " + os.getenv("SEC_CONTACT", "contact-not-set")
BROWSER_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"

MAX_COMPANIES_PER_RUN = 60
MAX_CONTACTS_PER_COMPANY = 8
MAX_PER_DEPARTMENT = 2
MAX_DORK_QUERIES = 20
DORK_JITTER = (4, 8)
MIN_LEAD_SCORE = 65
SHEET_CHUNK = 500
CELL_MAX_CHARS = 1500
ROTATION_ALERT_ROWS = 15000
HTTP_TIMEOUT = 8

# --- Shared-server SMTP (must stay <= core/safety_guard.py ceilings, else the run is blocked) ---
SMTP_HOURLY_CAP = 15            # total checks / UTC hour
SMTP_MX_HOURLY_CAP = 5          # per Google / Microsoft MX / UTC hour
SMTP_DAILY_CAP = 60             # operational cap / UTC day (~15 per run x 4 runs)
SMTP_JITTER = (30, 60)          # seconds between checks
SMTP_MIN_SCORE = 75             # only top P1 decision-makers
SMTP_MAX_PRIORITY = 1
SMTP_WARMUP_START = os.getenv("SMTP_WARMUP_START", "")  # UTC YYYY-MM-DD; empty = auto (first SMTP day)
SMTP_STATE_FILE = os.getenv("SMTP_STATE_FILE", ".smtp_state.json")
SMTP_RUN_CAP = 8                # per run: 8 runs/day x 8 = spread, daily cap 60 still clamps
SMTP_FLUSH_EVERY = 5            # write counter to State tab every N checks
SHARED_VERIFIER_URL = os.getenv("SHARED_VERIFIER_URL", "")
BATCH1_BUDGET_SEC = 300         # combined time cap for the 3 Batch-1 sources
BATCH1_MAX_SIGNALS = 60

JOB_QUERIES = ["Meta Ads manager", "Performance Marketing", "Shopify developer", "Facebook Ads specialist", "paid social manager",
               "ecommerce manager", "growth marketing manager", "digital marketing manager", "CRO specialist", "D2C marketing",
               "media buyer", "Shopify store manager"]
JOB_QUERIES_PER_RUN = 3   # rotates every 3-hour slot so each run sees new jobs
JOB_CITIES = {"US": ["New York, NY", "Los Angeles, CA", "Austin, TX", "Chicago, IL", "Miami, FL", "Seattle, WA", "Boston, MA", "Denver, CO"],
              "INDIA": ["Mumbai", "Delhi", "Bangalore", "Pune", "Hyderabad", "Chennai", "Ahmedabad", "Nagpur"]}
JOB_LOCATIONS = {"US": "United States", "INDIA": "India"}

def countries():
    return ["US", "INDIA"] if TARGET_COUNTRY == "BOTH" else [TARGET_COUNTRY]
