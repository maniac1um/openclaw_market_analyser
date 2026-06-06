from datetime import datetime, timezone


def parse_iso_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def format_cn_local_datetime(value: object) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, datetime):
        dt = value
    else:
        dt = parse_iso_dt(str(value).strip())
    if dt is None:
        return str(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone()
    return dt.strftime("%Y年%m月%d日%H：%M")
