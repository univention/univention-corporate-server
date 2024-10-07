#!/usr/share/ucs-test/runner python3
## desc: Tests the service specific password creation for radius
## tags: [apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-self-service
##   - univention-radius

import importlib
import os
import subprocess
import sys
import time

import passlib.hash
import pytest
from selenium.webdriver.common.by import By

import univention.admin.uldap
from univention.config_registry import handler_set as hs
from univention.testing import utils
from univention.testing.ucr import UCSTestConfigRegistry


test_lib = os.environ.get('UCS_TEST_LIB', 'univention.testing.apptest')
try:
    test_lib = importlib.import_module(test_lib)
except ImportError:
    print(f'Could not import {test_lib}. Maybe set $UCS_TEST_LIB')
    sys.exit(1)


@pytest.fixture(scope="module", autouse=True)
def activate_self_registration():
    with UCSTestConfigRegistry() as ucr:
        hs(['umc/self-service/service-specific-passwords/backend/enabled=true'])
        hs(['radius/use-service-specific-password=true'])
        yield ucr


def radius_auth(username, password):
    subprocess.check_call([
        'radtest',
        '-t',
        'mschap',
        username,
        password,
        '127.0.0.1:18120',
        '0',
        'testing123',
    ])


def get_new_ssp(chrome, user):
    chrome.get('/')
    chrome.get('/univention/portal/#/selfservice/servicespecificpasswords')
    chrome.enter_input('username', user.properties['username'])
    chrome.enter_input('password', 'univention')
    chrome.enter_return()
    time.sleep(10)
    print(chrome.driver.page_source)
    chrome.driver.find_elements(By.CSS_SELECTOR, ".button--primary")[0].click()
    time.sleep(10)
    elem = chrome.driver.find_elements(By.CSS_SELECTOR, ".service-specific-passwords__hint")[0]
    return elem.text.splitlines()[1]


def test_service_specific_password(chrome, ucr, users):
    lo = univention.admin.uldap.access(host=ucr.get('ldap/master'), port=ucr.get('ldap/server/port'), base=ucr.get('ldap/base'), binddn=ucr.get('tests/domainadmin/account'), bindpw=ucr.get('tests/domainadmin/pwd'), start_tls=2, follow_referral=True)
    subprocess.call(['service', 'univention-management-console-server', 'restart'])  # needs to be restarted to be current wrt umc/self-service/service-specific-passwords/backend/enabled=true
    time.sleep(10)
    with chrome.capture('test_service_specific_password'):
        user = users('service-specific-password', {'networkAccess': True})
        password = get_new_ssp(chrome, user)
        utils.wait_for_replication()
        user2 = lo.get(user.dn)
        ldap_nt = user2.get('univentionRadiusPassword', ['???'])[0]
        nt = passlib.hash.nthash.hash(password).upper().encode('ascii')
        assert ldap_nt == nt
        with pytest.raises(subprocess.CalledProcessError):
            radius_auth(user.properties['username'], 'univention')
        radius_auth(user.properties['username'], password)

        # get another ssp and verify that the old password does not work any more
        new_password = get_new_ssp(chrome, user)
        utils.wait_for_replication()
        user2 = lo.get(user.dn)
        ldap_nt = user2.get('univentionRadiusPassword', ['???'])[0]
        nt = passlib.hash.nthash.hash(new_password).upper().encode('ascii')
        assert ldap_nt == nt
        with pytest.raises(subprocess.CalledProcessError):
            radius_auth(user.properties['username'], password)
        radius_auth(user.properties['username'], new_password)


if __name__ == '__main__':
    test_lib.run_test_file(__file__)
