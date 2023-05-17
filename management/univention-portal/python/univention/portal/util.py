from datetime import datetime
import dateutil.parser


def _parse_date_str(iso_datetime: str):
    try:
        time = dateutil.parser.isoparse(iso_datetime)
    except (ValueError, TypeError):
        time = None
    return time


def in_range(iso_start_time: str, iso_end_time: str) -> bool:
    start = _parse_date_str(iso_start_time)
    end = _parse_date_str(iso_end_time)
    now = datetime.now()
    if start:
        if end:
            if start <= end:
                return start <= now <= end
            else:
                return start <= now  # to be discussed
        else:
            return start <= now
    elif end:
        return now <= end
    else:
        return True
