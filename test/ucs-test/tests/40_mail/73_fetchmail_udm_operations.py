#!/usr/share/ucs-test/runner pytest-3 -s -vvv
## desc: Fetchmail, perform udm operations and check the contents of the /etc/fetchmailrc file.
## tags: [apptest, fetchmail]
## exposure: dangerous
## packages:
##  - univention-fetchmail

from __future__ import annotations

import re
import time
from functools import reduce
from typing import Iterable, List

import ldap
import pytest

import univention.debug as ud
import univention.testing.strings as uts
import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test

from essential.mail import random_email


@pytest.fixture()
def udm():
    with udm_test.UCSTestUDM() as udm:
        yield udm


@pytest.fixture()
def ucr():
    with ucr_test.UCSTestConfigRegistry() as ucr:
        yield ucr


@pytest.fixture()
def user_addr():
    return random_email()


@pytest.fixture()
def fqdn():
    with ucr_test.UCSTestConfigRegistry() as ucr:
        return '%(hostname)s.%(domainname)s' % ucr


FETCHMAILRC_FILE = '/etc/fetchmailrc'
UID_REGEX = re.compile("#UID='(.+)'[ \t]*$")


def _split_file(fetch_list, new_line):
    if new_line.startswith('set') or new_line.startswith('#'):
        fetch_list.append(new_line)
    elif fetch_list:
        if UID_REGEX.search(fetch_list[-1]) or fetch_list[-1].startswith('set'):
            fetch_list.append(new_line)
        else:
            fetch_list[-1] += (new_line)
    return fetch_list


def load_rc(ofile: str) -> List[str] | None:
    """open an textfile with setuid(0) for root-action"""
    rc = None
    try:
        with open(ofile) as fd:
            rc = reduce(_split_file, fd, [])
    except EnvironmentError as exc:
        ud.debug(ud.LISTENER, ud.ERROR, 'Failed to open "%s": %s' % (ofile, exc))
    return rc


def objfind(dlist: Iterable[str], uid: str) -> List[str]:
    return [line for line in dlist if re.search("#UID='%s'[ \t]*$" % re.escape(uid), line)]


def parse_fetchmailrc(config_content):
    parsed_config = {}
    poll_pattern = re.compile(r'poll\s+\'([^\s]+)\'')
    user_pattern = re.compile(r'user\s+\'([^\']+)\'\s+there\s+with\s+password\s+\'([^\']+)\'\s+is\s+\'?([^\']+)\'?\s+here')
    uid_pattern = re.compile('#UID=\'(.+)\'[ \t]*$')

    poll_match = poll_pattern.search(config_content)
    user_match = user_pattern.search(config_content)
    uid_match = uid_pattern.search(config_content)

    if poll_match:
        parsed_config['mail_server'] = poll_match.group(1)
    if user_match:
        parsed_config['username'] = user_match.group(1)
        parsed_config['password'] = user_match.group(2)
        parsed_config['mail'] = user_match.group(3)
    if uid_match:
        parsed_config['uid'] = uid_match.group(1)
    return parsed_config


def check_entry(config, mailserver, remote_username, password, mail_addr, uid):
    return {
        'mail_server': mailserver,
        'username': remote_username,
        'password': password,
        'mail': mail_addr,
        'uid': uid
    } == parse_fetchmailrc(config)


def test_create_single_drop_configuration(udm, ucr, fqdn, user_addr):
    remote_username = uts.random_string()
    password = uts.random_string()
    user_dn, _user_name = udm.create_user(
        set={
            'mailHomeServer': fqdn,
            'mailPrimaryAddress': user_addr,
            'FetchMailSingle': f'"{fqdn}" "IMAP" "{remote_username}" "{password}" 1 1'
        })

    time.sleep(3)
    fetchmail = load_rc(FETCHMAILRC_FILE)
    uid = ldap.explode_rdn(user_dn, notypes=True)[0]
    res = objfind(fetchmail, uid)
    assert len(res) == 1
    assert check_entry(res[0], fqdn, remote_username, password, user_addr, uid)


def test_create_multi_drop_configuration(udm, ucr, fqdn, user_addr):
    remote_username = uts.random_string()
    password = uts.random_string()
    user_dn, _user_name = udm.create_user(
        set={
            'mailHomeServer': fqdn,
            'mailPrimaryAddress': user_addr,
            'FetchMailMulti': f'"{fqdn}" "IMAP" "{remote_username}" "{password}" "" "" "Envelope-To" 1 1'
        })

    time.sleep(3)
    fetchmail = load_rc(FETCHMAILRC_FILE)
    uid = ldap.explode_rdn(user_dn, notypes=True)[0]
    res = objfind(fetchmail, uid)
    assert len(res) == 1
    assert check_entry(res[0], fqdn, remote_username, password, '*', uid)


def test_single_drop_configuration_removal(udm, ucr, fqdn, user_addr):
    remote_username = uts.random_string()
    password = uts.random_string()
    user_dn, _user_name = udm.create_user(
        set={
            'mailHomeServer': fqdn,
            'mailPrimaryAddress': user_addr,
        }, append={
            'FetchMailSingle': [f'"{fqdn}" "IMAP" "{remote_username}" "{password}" 1 1',
                                f'"{fqdn}" "IMAP" "{remote_username + "1" }" "{password}" 1 1',
                                f'"{fqdn}" "IMAP" "{remote_username + "2" }" "{password}" 1 1']
        })

    time.sleep(3)
    fetchmail = load_rc(FETCHMAILRC_FILE)
    uid = ldap.explode_rdn(user_dn, notypes=True)[0]
    res = objfind(fetchmail, uid)
    assert len(res) == 3

    # Remove only one configuration
    udm.modify_object('users/user', dn=user_dn, remove={
        'FetchMailSingle': [f'"{fqdn}" "IMAP" "{remote_username + "1"}" "{password}" 1 1']
    })

    time.sleep(3)
    fetchmail = load_rc(FETCHMAILRC_FILE)
    res = objfind(fetchmail, uid)
    assert len(res) == 2
    assert any(map(lambda x: not check_entry(x, fqdn, remote_username + "1", password, user_addr, uid), res))

    # Remove remaining configurations (Bug #56426)
    udm.modify_object('users/user', dn=user_dn, remove={
        'FetchMailSingle': [f'"{fqdn}" "IMAP" "{remote_username}" "{password}" 1 1',
                            f'"{fqdn}" "IMAP" "{remote_username + "2" }" "{password}" 1 1']
    })

    time.sleep(3)
    fetchmail = load_rc(FETCHMAILRC_FILE)
    res = objfind(fetchmail, uid)
    assert len(res) == 0


def test_multi_drop_configuration_removal(udm, ucr, fqdn, user_addr):
    remote_username = uts.random_string()
    password = uts.random_string()
    user_dn, _user_name = udm.create_user(
        set={
            'mailHomeServer': fqdn,
            'mailPrimaryAddress': user_addr,
        }, append={
            'FetchMailMulti': [f'"{fqdn}" "IMAP" "{remote_username}" "{password}" "" "" "Envelope-To" 1 1',
                               f'"{fqdn}" "IMAP" "{remote_username + "1"}" "{password}" "" "" "Envelope-To" 1 1',
                               f'"{fqdn}" "IMAP" "{remote_username + "2"}" "{password}" "" "" "Envelope-To" 1 1']
        })

    time.sleep(3)
    fetchmail = load_rc(FETCHMAILRC_FILE)
    uid = ldap.explode_rdn(user_dn, notypes=True)[0]
    res = objfind(fetchmail, uid)
    assert len(res) == 3

    # Remove only one configuration
    udm.modify_object('users/user', dn=user_dn, remove={
        'FetchMailMulti': [f'"{fqdn}" "IMAP" "{remote_username + "1"}" "{password}" "" "" "Envelope-To" 1 1']
    })

    time.sleep(3)
    fetchmail = load_rc(FETCHMAILRC_FILE)
    res = objfind(fetchmail, uid)
    assert len(res) == 2
    assert any(map(lambda x: not check_entry(x, fqdn, remote_username + "1", password, user_addr, uid), res))

    # Remove remaining configurations (Bug #56426)
    udm.modify_object('users/user', dn=user_dn, remove={
        'FetchMailMulti': [f'"{fqdn}" "IMAP" "{remote_username}" "{password}" "" "" "Envelope-To" 1 1',
                           f'"{fqdn}" "IMAP" "{remote_username + "2"}" "{password}" "" "" "Envelope-To" 1 1']
    })

    time.sleep(3)
    fetchmail = load_rc(FETCHMAILRC_FILE)
    res = objfind(fetchmail, uid)
    assert len(res) == 0


def test_non_fetchmail_user_does_not_show_in_fetchmailrc(udm, ucr, fqdn, user_addr):
    user_dn, _user_name = udm.create_user(
        set={
            'mailHomeServer': fqdn,
            'mailPrimaryAddress': user_addr,
        })

    time.sleep(3)
    fetchmail = load_rc(FETCHMAILRC_FILE)
    uid = ldap.explode_rdn(user_dn, notypes=True)[0]
    res = objfind(fetchmail, uid)
    assert len(res) == 0


def test_remove_mailPrimaryAddress(udm, ucr, fqdn, user_addr):
    remote_username = uts.random_string()
    password = uts.random_string()
    user_dn, _user_name = udm.create_user(
        set={
            'mailHomeServer': fqdn,
            'mailPrimaryAddress': user_addr,
        }, append={
            'FetchMailSingle': [f'"{fqdn}" "IMAP" "{remote_username}" "{password}" 1 1',
                                f'"{fqdn}" "IMAP" "{remote_username + "1" }" "{password}" 1 1',
                                f'"{fqdn}" "IMAP" "{remote_username + "2" }" "{password}" 1 1']
        })

    time.sleep(3)
    fetchmail = load_rc(FETCHMAILRC_FILE)
    uid = ldap.explode_rdn(user_dn, notypes=True)[0]
    res = objfind(fetchmail, uid)
    assert len(res) == 3

    udm.modify_object('users/user', dn=user_dn, isOxUser="Not", remove={
        'mailPrimaryAddress': [user_addr]
    })

    time.sleep(3)
    fetchmail = load_rc(FETCHMAILRC_FILE)
    res = objfind(fetchmail, uid)
    assert len(res) == 0


def test_create_user_without_mailPrimaryAddress(udm, ucr, fqdn, user_addr):
    remote_username = uts.random_string()
    password = uts.random_string()
    user_dn, _user_name = udm.create_user(
        set={
            'mailHomeServer': fqdn,
        }, append={
            'FetchMailSingle': [f'"{fqdn}" "IMAP" "{remote_username}" "{password}" 1 1',
                                f'"{fqdn}" "IMAP" "{remote_username + "1" }" "{password}" 1 1',
                                f'"{fqdn}" "IMAP" "{remote_username + "2" }" "{password}" 1 1']
        })

    time.sleep(3)
    fetchmail = load_rc(FETCHMAILRC_FILE)
    uid = ldap.explode_rdn(user_dn, notypes=True)[0]
    res = objfind(fetchmail, uid)
    assert len(res) == 0


def test_modify_mailPrimaryAddress(udm, ucr, fqdn, user_addr):
    remote_username = uts.random_string()
    password = uts.random_string()
    user_dn, _user_name = udm.create_user(
        set={
            'mailHomeServer': fqdn,
            'mailPrimaryAddress': user_addr,
        }, append={
            'FetchMailSingle': [f'"{fqdn}" "IMAP" "{remote_username}" "{password}" 1 1',
                                f'"{fqdn}" "IMAP" "{remote_username + "1" }" "{password}" 1 1',
                                f'"{fqdn}" "IMAP" "{remote_username + "2" }" "{password}" 1 1']
        })

    time.sleep(3)
    fetchmail = load_rc(FETCHMAILRC_FILE)
    uid = ldap.explode_rdn(user_dn, notypes=True)[0]
    res = objfind(fetchmail, uid)
    assert len(res) == 3

    new_mail = random_email()
    udm.modify_object('users/user', dn=user_dn, mailPrimaryAddress=new_mail)

    time.sleep(3)
    fetchmail = load_rc(FETCHMAILRC_FILE)
    res = objfind(fetchmail, uid)
    assert len(res) == 3
    assert all(map(lambda x: check_entry(x[0], fqdn, x[1], password, new_mail, uid), zip(sorted(res), sorted([remote_username, remote_username + "1", remote_username + "2"]))))


def test_modify_uid(udm, ucr, fqdn, user_addr):
    remote_username = uts.random_string()
    password = uts.random_string()
    user_dn, _user_name = udm.create_user(
        set={
            'mailHomeServer': fqdn,
            'mailPrimaryAddress': user_addr,
        }, append={
            'FetchMailSingle': [f'"{fqdn}" "IMAP" "{remote_username}" "{password}" 1 1',
                                f'"{fqdn}" "IMAP" "{remote_username + "1" }" "{password}" 1 1',
                                f'"{fqdn}" "IMAP" "{remote_username + "2" }" "{password}" 1 1']
        })

    time.sleep(3)
    fetchmail = load_rc(FETCHMAILRC_FILE)
    uid = ldap.explode_rdn(user_dn, notypes=True)[0]
    res = objfind(fetchmail, uid)
    assert len(res) == 3

    new_uid = uts.random_username()
    udm.modify_object('users/user', dn=user_dn, username=new_uid)

    time.sleep(3)
    fetchmail = load_rc(FETCHMAILRC_FILE)
    res = objfind(fetchmail, new_uid)
    assert len(res) == 3


def test_remove_user(udm, ucr, fqdn, user_addr):
    remote_username = uts.random_string()
    password = uts.random_string()
    user_dn, _user_name = udm.create_user(
        set={
            'mailHomeServer': fqdn,
            'mailPrimaryAddress': user_addr,
        }, append={
            'FetchMailSingle': [f'"{fqdn}" "IMAP" "{remote_username}" "{password}" 1 1',
                                f'"{fqdn}" "IMAP" "{remote_username + "1" }" "{password}" 1 1',
                                f'"{fqdn}" "IMAP" "{remote_username + "2" }" "{password}" 1 1']
        })

    time.sleep(3)
    fetchmail = load_rc(FETCHMAILRC_FILE)
    uid = ldap.explode_rdn(user_dn, notypes=True)[0]
    res = objfind(fetchmail, uid)
    assert len(res) == 3

    udm.remove_object("users/user", dn=user_dn)

    time.sleep(3)
    fetchmail = load_rc(FETCHMAILRC_FILE)
    res = objfind(fetchmail, uid)
    assert len(res) == 0


def test_modify_configuration(udm, ucr, fqdn, user_addr):
    remote_username = uts.random_string()
    password = uts.random_string()
    user_dn, _user_name = udm.create_user(
        set={
            'mailHomeServer': fqdn,
            'mailPrimaryAddress': user_addr,
        }, append={
            'FetchMailSingle': [f'"{fqdn}" "IMAP" "{remote_username}" "{password}" 1 1',
                                f'"{fqdn}" "IMAP" "{remote_username + "1"}" "{password}" 1 1',
                                f'"{fqdn}" "IMAP" "{remote_username + "2"}" "{password}" 1 1'],
            'FetchMailMulti': [f'"{fqdn}" "IMAP" "{remote_username + "3"}" "{password}" "" "" "Envelope-To" 1 1']
        })

    time.sleep(3)
    fetchmail = load_rc(FETCHMAILRC_FILE)
    uid = ldap.explode_rdn(user_dn, notypes=True)[0]
    res = objfind(fetchmail, uid)
    assert len(res) == 4

    udm.modify_object(
        'users/user',
        dn=user_dn,
        FetchMailSingle=[f'"{fqdn}" "IMAP" "{remote_username}" "{password}" 1 1',
                         f'"{fqdn}" "IMAP" "{remote_username + "5"}" "{password}" 1 1',
                         f'"{fqdn}" "IMAP" "{remote_username + "2"}" "{password}" 1 1'],
        remove={
            'FetchMailSingle': [f'"{fqdn}" "IMAP" "{remote_username + "1"}" "{password}" 1 1']
        })

    time.sleep(3)
    fetchmail = load_rc(FETCHMAILRC_FILE)
    res = objfind(fetchmail, uid)
    assert len(res) == 4
    assert any(map(lambda x: check_entry(x, fqdn, remote_username + "5", password, user_addr, uid), res))
