from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

def to_aware_utc(dt):
    if dt is None:
        return utc_now()

    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)

    return dt

