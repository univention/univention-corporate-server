#!/usr/share/ucs-test/runner pytest-3 -s -l -v
## desc: "test ignore attributes feature"
## exposure: dangerous
## packages:
## - univention-ad-connector
## tags:
##  - skip_admember


from datetime import datetime
from subprocess import check_call

import pytest

from univention.testing.strings import random_username
from univention.testing.utils import adconnector_stopped

from adconnector import connector_setup2


@pytest.mark.parametrize('mode', ['sync'], ids=['sync mode'])
def test_ignore_attribute_performance_in_ad(udm, mode, lo):
    max_duration_in_seconds = .1
    settings = [
        'connector/ad/mapping/attributes/irrelevant=description,whenChanged,uSNChanged,msDS-RevealedDSAs',
        'connector/ad/poll/profiling=yes',
    ]
    with connector_setup2(mode, ucr_settings=settings) as ad:
        username = random_username(mixed_case=True)
        user_dn_ad = ad.create_user(username, password='Univention.99')
        # TODO: bad, we "clear" the log file
        check_call(['logrotate', '-f', '/etc/logrotate.d/univention-ad-connector'])
        assert not ad.get_logs_poll_from_con()
        ad.set_attributes(user_dn_ad, {'description': [b'desc']})
        # check "performance"
        logs = ad.get_logs_poll_from_con()
        assert len(logs) == 2
        assert 'Incoming' in logs[0]
        assert 'Processed' in logs[1]
        start = logs[0].split()[1]
        start = datetime.strptime(start, '%H:%M:%S.%f')
        end = logs[1].split()[1]
        end = datetime.strptime(end, '%H:%M:%S.%f')
        diff = end - start
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
        last_log = ad.get_logs_change()[-1]
        assert user_dn.casefold() in last_log
        with adconnector_stopped():
            ad.delete_attribute(user_dn_ad, 'otherMobile', wait_for_replication=False)
            ad.set_attributes(user_dn_ad, {'otherMobile': [b'test3', b'test2', b'test']}, wait_for_replication=False)
        ad.wait_for_sync()
        assert last_log == ad.get_logs_change()[-1]
