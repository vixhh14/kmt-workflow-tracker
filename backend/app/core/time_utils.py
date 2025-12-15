from datetime import datetime, date
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

def get_current_time_ist() -> datetime:
    return datetime.now(IST)

def get_today_date_ist() -> date:
    return get_current_time_ist().date()
