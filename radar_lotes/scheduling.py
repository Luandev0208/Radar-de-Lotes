from datetime import datetime, timedelta


def search_is_overdue(last_search, now=None, hours=6):
    now = now or datetime.now()
    if not last_search:
        return True
    try:
        last = datetime.fromisoformat(last_search)
    except (TypeError, ValueError):
        return True
    return now - last >= timedelta(hours=hours)

