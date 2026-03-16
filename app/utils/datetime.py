from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from flask import current_app


def app_timezone():
    return ZoneInfo(current_app.config.get("APP_TIMEZONE", "America/Santiago"))


def utc_now():
    return datetime.now(timezone.utc)


def local_now():
    return utc_now().astimezone(app_timezone())


def to_local(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(app_timezone())


def format_local_datetime(dt, fmt="%d/%m/%Y %H:%M"):
    local_dt = to_local(dt)
    if local_dt is None:
        return ""
    return local_dt.strftime(fmt)


def local_date_range_utc(target_date):
    start_local = datetime.combine(target_date, time.min, tzinfo=app_timezone())
    end_local = start_local + timedelta(days=1)
    start_utc = start_local.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = end_local.astimezone(timezone.utc).replace(tzinfo=None)
    return start_utc, end_utc


def local_date_to_utc_start(target_date):
    return local_date_range_utc(target_date)[0]
