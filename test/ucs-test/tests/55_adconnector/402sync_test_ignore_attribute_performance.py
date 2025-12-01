#!/usr/share/ucs-test/runner pytest-3 -s -l -v
## desc: "test ignore attributes feature"
## exposure: dangerous
## packages:
## - univention-ad-connector
## tags:
##  - skip_admember


from datetime import datetime

import pytest

from univention.testing.strings import random_username
from univention.testing.utils import adconnector_stopped

from adconnector import connector_setup2


@pytest.mark.parametrize('mode', ['sync'], ids=['sync mode'])
def test_ignore_attribute_performance_in_ad(udm, mode, lo):
    max_duration_in_seconds = .01
    log_timstamp = '%Y-%m-%dT%H:%M:%S.%f%z'
    settings = [
        'connector/ad/mapping/attributes/irrelevant=description,whenChanged,uSNChanged,msDS-RevealedDSAs',
        'connector/ad/poll/profiling=yes',
    ]
    with connector_setup2(mode, ucr_settings=settings) as ad:
        username = random_username(mixed_case=True)
        user_dn_ad = ad.create_user(username, password='Univention.99')
        ad.set_attributes(user_dn_ad, {'description': [b'desc']})
        ad.wait_for_sync()
        # check "performance"
        logs = ad.get_logs_poll_from_con()
        assert any('Incoming' in line for line in logs)
        assert any(f'Processed non-change of {user_dn_ad}'.lower() in line.lower() for line in logs)
        for line in logs:
            if 'incoming' in line.lower():
                incoming_line = line
            if f'Processed non-change of {user_dn_ad}'.lower() in line.lower():
                processed_line = line
                break
        start = incoming_line.split()[0]
        start = datetime.strptime(start, log_timstamp)
        end = processed_line.split()[0]
        end = datetime.strptime(end, log_timstamp)
        diff = end - start
        print(f'Took {diff.microseconds} microseconds')
        assert diff.microseconds < (max_duration_in_seconds * 1000000)
        # check description is not synced
        user_dn = ad.ucs_dn(user_dn_ad)
        ad.get(user_dn_ad)
        assert ad.get(user_dn_ad)['description'][0].decode('UTF-8') == 'desc'
        assert not lo.get(user_dn).get('description')


@pytest.mark.parametrize('mode', ['sync'], ids=['sync mode'])
def test_order_does_not_matter_for_changed_attributes_check_in_ad(mode):
    with connector_setup2(mode) as ad:
        username = random_username(mixed_case=True)
        user_dn_ad = ad.create_user(username, password='Univention.99', wait_for_replication=False)
        ad.set_attributes(user_dn_ad, {'otherMobile': [b'test', b'test2', b'test3']}, wait_for_replication=False)
        ad.wait_for_sync()
        user_dn = ad.ucs_dn(user_dn_ad)
        last_change = ad.get_logs_change()[-1]
        assert user_dn.casefold() in last_change
        with adconnector_stopped():
            ad.delete_attribute(user_dn_ad, 'otherMobile', wait_for_replication=False)
            ad.set_attributes(user_dn_ad, {'otherMobile': [b'test3', b'test2', b'test']}, wait_for_replication=False)
        ad.wait_for_sync()
        assert last_change == ad.get_logs_change()[-1]
