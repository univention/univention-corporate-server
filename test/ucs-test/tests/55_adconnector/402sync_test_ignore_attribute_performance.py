#!/usr/share/ucs-test/runner pytest-3 -s -l -v
## desc: "test ignore attributes feature"
## exposure: dangerous
## packages:
## - univention-ad-connector
## tags:
##  - skip_admember


from univention.testing.utils import adconnector_stopped

from adconnector import connector_setup2


def test_order_does_not_matter_for_changed_attributes_check_in_ad(udm):
    with connector_setup2('sync') as ad:
        # create in UCS, we need a password in AD
        setup = ad.create_ou_structure_and_user(udm)
        ad.set_attributes(setup.user_dn_ad, {'otherMobile': ['test'.encode('UTF-8'), 'test2'.encode('UTF-8'), 'test3'.encode('UTF-8')]}, wait_for_replication=False)
        ad.wait_for_sync()
        last_log = ad.get_logs()[-1]
        assert setup.user_dn.casefold() in last_log
        with adconnector_stopped():
            ad.delete_attribute(setup.user_dn_ad, 'otherMobile', wait_for_replication=False)
            ad.set_attributes(setup.user_dn_ad, {'otherMobile': ['test3'.encode('UTF-8'), 'test2'.encode('UTF-8'), 'test'.encode('UTF-8')]}, wait_for_replication=False)
        ad.wait_for_sync()
        assert last_log == ad.get_logs()[-1]
