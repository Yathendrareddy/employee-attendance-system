from datetime import datetime
from zoneinfo import ZoneInfo

STORE_TZ = ZoneInfo("America/Chicago")

def store_now() -> datetime:
    """Current wall-clock time at the store, as a naive datetime (matches naive DateTime columns)."""
    return datetime.now(STORE_TZ).replace(tzinfo=None)

def store_today():
    return store_now().date()
