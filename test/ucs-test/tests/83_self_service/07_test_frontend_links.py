#!/usr/share/ucs-test/runner python3
## desc: Tests the Self Service Subpages
## tags: [apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-self-service

import importlib
import os
import sys
import time

from univention.testing import utils


test_lib = os.environ.get('UCS_TEST_LIB', 'univention.testing.apptest')
try:
    test_lib = importlib.import_module(test_lib)
except ImportError:
    print(f'Could not import {test_lib}. Maybe set $UCS_TEST_LIB')
    sys.exit(1)


LINK_HASHES = ['profile', 'createaccount', 'verifyaccount', 'passwordchange', 'passwordforgotten', 'protectaccount']


def get_visible_selfservice_links(chrome):
    elements = chrome.find_all('.portal-tile__root-element > a')
    return sorted({elem.get_attribute('href').rsplit('#', 1)[1] for elem in elements})


def assert_link_hashes(links, without):
    wanted_hashes = [link_hash for link_hash in LINK_HASHES if link_hash not in without]
    assert len(links) == len(wanted_hashes)
    for link_hash in wanted_hashes:
        assert f'/selfservice/{link_hash}' in links


def goto_selfservice(chrome, login=False):
    if login:
        chrome.get("/univention/login/?location=/univention/selfservice/")
        time.sleep(2)
        chrome.enter_input('username', 'Administrator')
        chrome.enter_input('password', 'univention')
        chrome.enter_return()
        time.sleep(10)
    else:
        chrome.get('/univention/selfservice/')
        time.sleep(2)


def test_all_links(chrome):
    goto_selfservice(chrome)
    links = get_visible_selfservice_links(chrome)
    assert_link_hashes(links, without=['verifyaccount', 'createaccount', 'passwordchange'])


def test_all_links_login(chrome):
    goto_selfservice(chrome, login=True)
    links = get_visible_selfservice_links(chrome)
    assert_link_hashes(links, without=['verifyaccount', 'createaccount', "passwordforgotten"])


def test_disabled_protectaccount(chrome, ucr):
    ucr.set({'umc/self-service/protect-account/backend/enabled': 'false'})
    utils.wait_for_replication()
    goto_selfservice(chrome)
    links = get_visible_selfservice_links(chrome)
    assert_link_hashes(links, without=['protectaccount', 'verifyaccount', 'createaccount', 'passwordchange'])


def test_disabled_passwordforgotten(chrome, ucr):
    ucr.set({'umc/self-service/passwordreset/backend/enabled': 'false'})
    utils.wait_for_replication()
    goto_selfservice(chrome)
    links = get_visible_selfservice_links(chrome)
    assert_link_hashes(links, without=['passwordforgotten', 'verifyaccount', 'createaccount', 'passwordchange'])


def test_disabled_passwordchange(chrome, ucr):
    ucr.set({'umc/self-service/passwordchange/frontend/enabled': 'false'})
    goto_selfservice(chrome)
    links = get_visible_selfservice_links(chrome)
    assert_link_hashes(links, without=['passwordchange', 'verifyaccount', 'createaccount'])


def test_disabled_profiledata(chrome, ucr):
    ucr.set({'umc/self-service/profiledata/enabled': 'false'})
    utils.wait_for_replication()
    goto_selfservice(chrome)
    links = get_visible_selfservice_links(chrome)
    assert_link_hashes(links, without=['profile', 'verifyaccount', 'createaccount', 'passwordchange'])


def test_disabled_accountregistration(chrome, ucr):
    ucr.set({'umc/self-service/account-registration/backend/enabled': 'true'})
    utils.wait_for_replication()
    goto_selfservice(chrome)
    links = get_visible_selfservice_links(chrome)
    assert_link_hashes(links, without=['verifyaccount', 'passwordchange'])


def test_disabled_accountverification(chrome, ucr):
    ucr.set({'umc/self-service/account-verification/backend/enabled': 'true'})
    utils.wait_for_replication()
    goto_selfservice(chrome)
    links = get_visible_selfservice_links(chrome)
    assert_link_hashes(links, without=['createaccount', 'passwordchange'])


def test_login_disabled_passwordchange(chrome, ucr):
    ucr.set({'umc/self-service/passwordchange/frontend/enabled': 'false'})
    goto_selfservice(chrome, login=True)
    links = get_visible_selfservice_links(chrome)
    assert_link_hashes(links, without=['verifyaccount', 'createaccount', 'passwordforgotten'])


if __name__ == '__main__':
    test_lib.run_test_file(__file__)
