from datetime import datetime, timedelta

def format_time(value):
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}"
    elif isinstance(value, datetime):
        return value.strftime("%H:%M")
    elif isinstance(value, str):
        return value[:5]
    return ""