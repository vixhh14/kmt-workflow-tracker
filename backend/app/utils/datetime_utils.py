from datetime import datetime, timezone
import pytz

IST = pytz.timezone("Asia/Kolkata")

def utc_now():
    """Returns current aware datetime in IST for project consistency."""
    return datetime.now(IST)

def make_aware(dt):
    """Convert naive datetime to IST timezone-aware datetime"""
    if dt is None:
        return None
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except:
            return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=IST)
    return dt.astimezone(IST)

def safe_datetime_diff(end_dt, start_dt):
    """
    Safely calculate difference between two datetimes in seconds.
    Handles ISO strings, timezone-aware and naive datetimes.
    """
    if end_dt is None or start_dt is None:
        return 0
    
    # Make both aware
    end_aware = make_aware(end_dt)
    start_aware = make_aware(start_dt)
    
    if not end_aware or not start_aware:
        return 0
    
    diff = (end_aware - start_aware).total_seconds()
    return int(max(0, diff))
