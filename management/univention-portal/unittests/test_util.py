from datetime import datetime, timedelta

import pytest

from univention.portal.util import is_current_time_between


@pytest.mark.parametrize(
    "start,end,expected",
    [
        pytest.param(
                        (datetime.now() + timedelta(minutes=1)).isoformat(), None,
            False,
            id="before start",
        ),
        pytest.param(
            (datetime.now() + timedelta(minutes=1)).isoformat(), "invalid datetime string",
            False,
            id="before start, invalid end datetime string",
        ),
        pytest.param(
            (datetime.now() - timedelta(minutes=1)).isoformat(), None,
            True,
            id="after start, no end",
        ),
        pytest.param(
            (datetime.now() - timedelta(minutes=1)).isoformat(), (datetime.now() + timedelta(minutes=1)).isoformat(),
            True,
            id="in range",
        ),
        pytest.param(
            (datetime.now() + timedelta(minutes=1)).isoformat(), (datetime.now() + timedelta(minutes=2)).isoformat(),
            False,
            id="before range",
        ),
        pytest.param(
            (datetime.now() - timedelta(minutes=2)).isoformat(), (datetime.now() - timedelta(minutes=1)).isoformat(),
            False,
            id="after range",
        ),
        pytest.param(
            None, (datetime.now() - timedelta(minutes=1)).isoformat(),
            False,
            id="after end, no start",
        ),
        pytest.param(
            None, (datetime.now() + timedelta(minutes=1)).isoformat(),
            True,
            id="before end, no start",
        ),
        pytest.param(
            None, None,
            True,
            id="neither start nor end",
        ),
        pytest.param(
            datetime.now().date().isoformat(), (datetime.now() + timedelta(days=1)).date().isoformat(),
            True,
            id="only date",
        ),
        pytest.param(
            (datetime.now() + timedelta(days=1)).date().isoformat(), datetime.now().date().isoformat(),
            True,
            id="start after end",
        ),
        pytest.param(
            (datetime.now() - timedelta(days=1)).date().isoformat(), datetime.now().date().isoformat(),
            True,
            id="end is today",
        ),
        pytest.param(
            datetime.now().date().isoformat(), datetime.now().date().isoformat(),
            True,
            id="start is today, end is today",
        ),
    ],
)
def test_is_current_time_between(start, end, expected):
    assert is_current_time_between(start, end) == expected
