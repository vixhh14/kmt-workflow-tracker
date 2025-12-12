from datetime import datetime, timezone

def utc_now():
    """Get current UTC time as timezone-aware datetime"""
    return datetime.now(timezone.utc)

def make_aware(dt):
    """Convert naive datetime to UTC timezone-aware datetime"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

def safe_datetime_diff(end_dt, start_dt):
    """
    Safely calculate difference between two datetimes in seconds.
    Handles timezone-aware and naive datetimes.
    Returns 0 if either is None.
    """
    if end_dt is None or start_dt is None:
        return 0
    
    # Make both aware if needed
    end_aware = make_aware(end_dt)
    start_aware = make_aware(start_dt)
    
    diff = (end_aware - start_aware).total_seconds()
    return int(max(0, diff))
