"""Zero-PII logger: emails/phones are masked before anything is printed."""
import re, sys, logging

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"\+?\d[\d\s().-]{8,}\d")

class _Mask(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        msg = _EMAIL.sub("<email>", msg)
        msg = _PHONE.sub("<phone>", msg)
        record.msg, record.args = msg, ()
        return True

def get(name="extract"):
    lg = logging.getLogger(name)
    if not lg.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        h.addFilter(_Mask())
        lg.addHandler(h)
        lg.setLevel(logging.INFO)
    return lg
