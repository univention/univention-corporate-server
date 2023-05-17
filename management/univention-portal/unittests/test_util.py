from univention.portal.util import in_range
from datetime import datetime
from datetime import timedelta
import pytest


@pytest.mark.parametrize(
    "start_time,end_time,expected",
    [
        pytest.param(
            (datetime.now() + timedelta(minutes=1)).isoformat(), None,  # start_time, end_time
            False,  # expected result
            id="before start"
        ),
        pytest.param(
            (datetime.now() + timedelta(minutes=1)).isoformat(), "invalid time string",
            False,
            id="before start, invalid end time string"
        ),
        pytest.param(
            (datetime.now() - timedelta(minutes=1)).isoformat(), None,
            True,
            id="after start, no end"
        ),
        pytest.param(
            (datetime.now() - timedelta(minutes=1)).isoformat(), (datetime.now() + timedelta(minutes=1)).isoformat(),
            True,
            id="in range"
        ),
        pytest.param(
            (datetime.now() + timedelta(minutes=1)).isoformat(), (datetime.now() + timedelta(minutes=2)).isoformat(),
            False,
            id="before range"
        ),
        pytest.param(
            (datetime.now() - timedelta(minutes=2)).isoformat(), (datetime.now() - timedelta(minutes=1)).isoformat(),
            False,
            id="after range"
        ),
        pytest.param(
            None, (datetime.now() - timedelta(minutes=1)).isoformat(),
            False,
            id="after end, no start"
        ),
        pytest.param(
            None, (datetime.now() + timedelta(minutes=1)).isoformat(),
            True,
            id="before end, no start"
        ),
        pytest.param(
            None, None,
            True,
            id="neither start nor end"
        ),
        pytest.param(
            datetime.now().date().isoformat(), (datetime.now() + timedelta(days=1)).date().isoformat(),
            True,
            id="only date"
        ),
    ]
)
def test_time_in_range(start_time, end_time, expected):
    assert in_range(start_time, end_time) == expected
