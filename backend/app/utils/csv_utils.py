import csv
import io
from datetime import datetime, date, timedelta
from typing import List, Any
from app.core.time_utils import IST

def format_duration_hms(seconds: int) -> str:
    """Formats seconds into HH:MM:SS"""
    if not seconds:
        return "00:00:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def clean_csv_value(value: Any) -> str:
    """ENSURES no nested JSON or odd characters. Handles lists using semicolon."""
    if value is None:
        return ""
    if isinstance(value, list) or isinstance(value, set):
        return ";".join(str(v) for v in value)
    return str(value)

def generate_csv_stream(headers: List[str], rows: List[List[Any]]) -> io.StringIO:
    """Generates a CSV string stream."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        cleaned_row = [clean_csv_value(v) for v in row]
        writer.writerow(cleaned_row)
    output.seek(0)
    return output
