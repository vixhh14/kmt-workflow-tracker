import pytz
from datetime import datetime

# Global IST Timezone
IST = pytz.timezone('Asia/Kolkata')

def get_current_time_ist():
    """
    Get current time in IST as timezone-aware datetime.
    Use this for all timestamp creation.
    """
    return datetime.now(IST)

def get_current_date_ist():
    """Get current date in IST"""
    return get_current_time_ist().date()
