from datetime import datetime, MINYEAR, MAXYEAR
import dateutil.parser

from univention.portal.log import get_logger


def _sanitize_and_parse_iso_datetime_str(iso_datetime: str, default: datetime):
    try:
        datetime_obj = dateutil.parser.isoparse(iso_datetime)
    except (ValueError, TypeError):
        datetime_obj = default
    return datetime_obj


def is_current_time_between(start_iso_datetime_str: str, end_iso_datetime_str: str) -> bool:
    """Return if the current system time (datetime.now()) lies within the given range.
    In case, start is later than end, ignore both.

    start_iso_datetime_str : str
        the first point in time that is in range
    end_iso_datetime_str : str
        the last point in time that is in range

    return: bool
        is datetime.now() between start_iso_datetime_str and end_iso_datetime_str,
        including boundaries
    """
    now = datetime.now()
    range_start = _sanitize_and_parse_iso_datetime_str(start_iso_datetime_str, datetime(MINYEAR, 1, 1))
    range_end = _sanitize_and_parse_iso_datetime_str(end_iso_datetime_str, datetime(MAXYEAR, 1, 1))

    if range_start <= range_end:
        return range_start <= now <= range_end
    else:
        get_logger("util").warning("given time boundaries not in chronological order")
        return True
