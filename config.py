"""All tunables in one place (zero-token config)."""
import os

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

JOB_QUERIES = ["Meta Ads manager", "Performance Marketing", "Shopify developer"]
JOB_LOCATIONS = {"US": "United States", "INDIA": "India"}

def countries():
    return ["US", "INDIA"] if TARGET_COUNTRY == "BOTH" else [TARGET_COUNTRY]
