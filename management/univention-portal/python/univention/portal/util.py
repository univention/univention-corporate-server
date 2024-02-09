#!/usr/bin/python3
#
# Univention Portal
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2020-2024 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.
#

import os
from datetime import MAXYEAR, MINYEAR, datetime
from urllib.parse import urlsplit, urlunsplit

import boto3
import dateutil.parser

from univention.portal.log import get_logger


def _sanitize_and_parse_iso_datetime_str(iso_datetime: str, default: datetime):
    try:
        datetime_obj = dateutil.parser.isoparse(iso_datetime)
    except (ValueError, TypeError):
        datetime_obj = default
    return datetime_obj


def _extend_end_day_to_midnight_if_necessary(
    end_iso_datetime_str: str,
    range_end: datetime,
):
    """
    This is to handle cases, where only an end date is given, but no time.
    In this case isoparse would return a date with hours, mins, ... set to 0.
    This is unintuitive when comparing the current day, as datetime.now()
    returns later hours, mins, ... than 0 but it is still the same day.
    """
    new_range_end = range_end
    if (
        end_iso_datetime_str
        and len(end_iso_datetime_str) <= len("YYYY-MM-DD")
        and range_end != datetime(MAXYEAR, 12, 31)
    ):
        new_range_end = range_end.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
        )
    return new_range_end


def is_current_time_between(
    start_iso_datetime_str: str,
    end_iso_datetime_str: str,
) -> bool:
    """
    Return if the current system time (datetime.now()) lies within the given range.
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
    range_start = _sanitize_and_parse_iso_datetime_str(
        start_iso_datetime_str,
        datetime(MINYEAR, 1, 1),
    )
    range_end = _sanitize_and_parse_iso_datetime_str(
        end_iso_datetime_str,
        datetime(MAXYEAR, 12, 31),
    )
    range_end = _extend_end_day_to_midnight_if_necessary(
        end_iso_datetime_str,
        range_end,
    )
    if range_start <= range_end:
        return range_start <= now <= range_end
    else:
        get_logger("util").warning("given time boundaries not in chronological order")
        return True


def log_url_safe(url):
    """
    Hide the password in the URL if present.

    Intended to be used when logging URLs which may contain a password in it.
    """
    parts = urlsplit(url)
    if parts.password:
        netloc_without_auth = parts.netloc.split("@")[1]
        new_netloc = f"{parts.username}:***hidden***@{netloc_without_auth}"
        url = urlunsplit(
            (parts.scheme, new_netloc, parts.path, parts.query, parts.fragment),
        )
    return url


def get_portal_update_call(reason):
    call_args = ["/usr/sbin/univention-portal"]
    if os.environ.get("PORTAL_LISTENER_LOG_STREAM") == "true":
        call_args.append("--log-stream")
    call_args.extend(["update", "--reason", reason])
    return call_args


def get_object_storage_client(
    object_storage_endpoint,
    access_key_id,
    secret_access_key,
):
    """Create an object storage client"""
    return boto3.client(
        "s3",
        endpoint_url=object_storage_endpoint,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        config=boto3.session.Config(signature_version="s3v4"),
        verify=bool(object_storage_endpoint.startswith("https")),
    )
