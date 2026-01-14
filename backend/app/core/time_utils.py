from datetime import datetime, date
import pytz

IST = pytz.timezone("Asia/Kolkata")

def get_current_time_ist() -> datetime:
    """Returns current aware datetime in IST."""
    return datetime.now(IST)

def get_today_date_ist() -> date:
    """Returns current date in IST."""
    return get_current_time_ist().date()
