#!/usr/share/ucs-test/runner pytest-3 -s -l -v
## desc: "Test that a container rename won't delete the subobjects"
## exposure: dangerous
## packages:
## - univention-ad-connector
## bugs:
##  - 52230


import subprocess
import time

import pytest

import univention.config_registry
import univention.testing.strings as tstrings
from univention.testing.utils import wait_for_replication_and_postrun

from adconnector import connector_running_on_this_host, connector_setup


configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()


def service_listener(action):
    cmd = ["systemctl", action, "univention-directory-listener.service"]
    subprocess.call(cmd)


def modify_user_in_s4(ucr, username):
    ad_ldap_host = ucr.get('connector/ad/ldap/host')
    ad_ldap_binddn = ucr.get('connector/ad/ldap/binddn')
    ad_ldap_username = ad_ldap_binddn.split(",")[0].split("=")[1]
    ad_ldap_bindpw_file = ucr.get('connector/ad/ldap/bindpw')
    with open(ad_ldap_bindpw_file) as fd:
        ad_ldap_bindpw = fd.read().rstrip()

    cmd = ["samba-tool", "user", "disable", "--URL=ldap://%s" % ad_ldap_host, "-U%s%%%s" % (ad_ldap_username, ad_ldap_bindpw), username]
    print(cmd)
    subprocess.call(cmd)


@pytest.mark.skipif(not connector_running_on_this_host(), reason="Univention S4 Connector not configured.")
def test_initial_S4_pwd_is_synced(udm, ucr):
    with connector_setup("sync"):
        testusername = tstrings.random_name()
        container_name1 = tstrings.random_name()
        container_name2 = tstrings.random_name()
        container1_dn = udm.create_object("container/cn", name=container_name1)
        testuser_dn = udm.create_object("users/user", username=testusername, lastname=testusername, password="univention", position=container1_dn, wait_for=True)
        try:
            service_listener("stop")
            testcontainer_dn = udm.modify_object("container/cn", dn=container1_dn, name=container_name2, wait_for_replication=False)
            time.sleep(20)
            modify_user_in_s4(ucr, testusername)
            time.sleep(20)
        finally:
            service_listener("start")
        wait_for_replication_and_postrun()
        testuser_dn = "uid=%s,%s" % (testusername, testcontainer_dn)
        udm.verify_udm_object("users/user", testuser_dn, {'username': testusername})
