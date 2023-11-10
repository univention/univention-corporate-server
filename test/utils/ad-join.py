#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2015-2023 Univention GmbH
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

from __future__ import print_function

from argparse import ArgumentParser, Namespace
from shutil import copy
from subprocess import run
from sys import exit
from time import sleep
from types import SimpleNamespace
from typing import Any, Dict

import ldap
from ldap.dn import dn2str, escape_dn_chars, str2dn

from univention.config_registry import handler_set, ucr_factory
from univention.lib.umc import Client


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument('-H', '--host', default='localhost', help='host to connect to')
    parser.add_argument('-u', '--user', dest='username', help='username', metavar='UID', default='administrator')
    parser.add_argument('-p', '--password', default='univention', help='password')
    parser.add_argument('-D', '--domain_host', default=None, help='domain controller to connect to', required=True)
    parser.add_argument('-A', '--domain_admin', help='domain admin username', metavar='DOMAIN_UID', default='administrator')
    parser.add_argument('-P', '--domain_password', default='Univention@99', help='domain admin password')
    parser.add_argument('-S', '--sync_mode', action="store_true", help='join in synchronization mode (instead of read by default)')
    parser.add_argument('--prepare-new-instance', default=None, help='Instance name to create with prepare-new-instance')
    parser.add_argument('--kerberos-realm', default=None, help='Kerberos realm name to use with prepare-new-instance')

    options = parser.parse_args()

    return options


options = parse_args()
client = Client(options.host, options.username, options.password, language='en-US')


def get_ad_details(ip) -> SimpleNamespace:
    lo = ldap.initialize("ldap://%s" % ip)
    res = lo.search_s("", ldap.SCOPE_BASE, None, ["dnsHostName", "defaultNamingContext"])
    return SimpleNamespace(**{k: v[0].decode("UTF-8") for (k, v) in res[0][1].items()})


def join_sync_mode() -> None:
    """Join in bi-directional sync mode via UMC requests"""
    # check domain / get configuration:
    print('=== AD-JOIN STARTED ===')
    request_options = {
        "ad_server_address": options.domain_host,
        "username": options.domain_admin,
        "password": options.domain_password,
        "mode": "adconnector",
    }
    result = client.umc_command("adconnector/check_domain", request_options).result

    # configure / save options:
    print('=== AD-JOIN CONFIGURATION ===')
    try:
        kerberos_domain = result['Domain']
        ad_ldap_base = result['LDAP_Base']
        ad_dc_name = result['DC_DNS_Name']
    except KeyError as exc:
        print("\nAn Error while reading the AD Domain configuration: %r" % exc)
        exit(1)

    request_options = {
        'Host_IP': options.domain_host,
        'KerberosDomain': kerberos_domain,
        'LDAP_Base': ad_ldap_base,
        'LDAP_BindDN': "cn=" + escape_dn_chars(options.domain_admin) + ",cn=users," + ad_ldap_base,
        'LDAP_Host': ad_dc_name,
        'LDAP_Password': options.domain_password,
        'MappingSyncMode': "sync",
    }

    conf_result = client.umc_command("adconnector/adconnector/save", request_options).result
    if not conf_result['success']:
        print("\nThe AD Connector configuration was not saved successfully: %s" % conf_result)
        exit(1)

    # start AD connector:
    print('=== AD-JOIN STARTING CONNECTOR ===')
    start_result = client.umc_command("adconnector/service", {'action': "start"}).result
    if not start_result['success']:
        print("\nThe AD Connector was not started successfully: %s" % start_result)
        exit(1)

    print('=== AD-JOIN FINISHED ===')


def join_read_mode() -> None:
    """Join in read mode (as admember) via UMC requests"""
    send_data = {
        'ad_server_address': options.domain_host,
        'password': options.domain_password,
        'username': options.domain_admin,
    }

    result = client.umc_command("adconnector/admember/join", send_data).result

    if not result:
        print('ERROR: Failed to join ad domain as member!')
        exit(1)

    progress_id = result['id']
    progress_data = {'progress_id': progress_id}

    print('=== AD-JOIN STARTED ===')
    status: Dict[str, Any] = {'finished': False}
    while not status['finished']:
        # FIXME: this might loop forever?
        status = client.umc_command('adconnector/admember/progress', progress_data).result
        percentage = status['percentage']
        print(percentage)
        sleep(2)

    if not status['result']['success']:
        print(status['result']['error'])
        print('=== AD-JOIN FINISHED WITH ERROR ===')
        exit(1)

    print('=== AD-JOIN FINISHED ===')


def prepare_new_instance() -> None:
    """Setup bi-directional sync mode via prepare-new-instance"""
    print('=== AD-PREPARE-NEW-INSTANCE STARTED ===')
    ad_details = get_ad_details(options.domain_host)
    run(["/usr/share/univention-ad-connector/scripts/prepare-new-instance", "-a", "create", "-c", options.prepare_new_instance], check=True)
    run(["univention-directory-listener-ctrl", "resync", "ad-connector"], check=True)
    handler_set([
        "%s/ad/ldap/base=%s" % (options.prepare_new_instance, ad_details.defaultNamingContext),
        "%s/ad/ldap/binddn=cn=Administrator,cn=users,%s" % (options.prepare_new_instance, ad_details.defaultNamingContext),
        "%s/ad/ldap/bindpw=/etc/univention/connector/ad/bindpw" % (options.prepare_new_instance,),
        "%s/ad/ldap/host=%s" % (options.prepare_new_instance, ad_details.dnsHostName),
        "hosts/static/%s=%s" % (options.domain_host, ad_details.dnsHostName),
        "%s/ad/mapping/kerberosdomain=%s" % (options.prepare_new_instance, options.kerberos_realm),
        "%s/ad/ldap/ssl=false" % (options.prepare_new_instance,),
    ])
    copy("/etc/univention/connector/ad/bindpw", "/etc/univention/%s/ad/" % options.prepare_new_instance)
    run(["systemctl", "start", "univention-ad-%s" % options.prepare_new_instance], check=True)
    print('=== AD-PREPARE-NEW-INSTANCE FINISHED ===')


def join_ad() -> None:
    """Function for joining an AD domain, mimicking a join from umc"""
    if options.sync_mode:
        print('=== AD-JOIN SYNC MODE SELECTED ===')
        join_sync_mode()
    elif options.prepare_new_instance:
        # join in sync mode:
        print('=== AD-PREPARE-NEW-INSTANCE SYNC MODE SELECTED ===')
        prepare_new_instance()
    else:
        # join in read mode:
        print('=== AD-JOIN READ MODE SELECTED (admember) ===')
        join_read_mode()


def check_correct_passwords() -> None:
    """
    Check domain password saved for ucs-test and
    correct if needed
    """
    print('=== Checking / Correcting ucs-test passwords ===')

    with ucr_factory() as ucr:
        ucr_domain_pw = ucr['tests/domainadmin/pwd']
        if ucr_domain_pw != options.domain_password:
            ucr['tests/domainadmin/pwd'] = options.domain_password

    with open("/var/lib/ucs-test/pwdfile") as pwfile:
        pwfile_pw = pwfile.read().replace('\n', '')
    if pwfile_pw != options.domain_password:
        with open("/var/lib/ucs-test/pwdfile", "w") as pwfile:
            pwfile.write(options.domain_password)


def check_correct_domain_admin() -> None:
    """
    Check domain administrator saved for ucs-test and
    correct if needed
    """
    print('=== Checking / Correcting ucs-test domain administrator ===')

    with ucr_factory() as ucr:
        ucr_domain_admin = ucr['tests/domainadmin/account']
        if ucr_domain_admin:
            ucr_domain_admin_parts = str2dn(ucr_domain_admin)
            if ucr_domain_admin_parts[0][0][1] != options.domain_admin:
                ucr_domain_admin_parts[0][0] = ('uid', options.domain_admin, ucr_domain_admin_parts[0][0][2])
                ucr['tests/domainadmin/account'] = dn2str(ucr_domain_admin_parts)
        else:
            print("=== tests/domainadmin/account is not set, trying to create it ===")
            ucr['tests/domainadmin/account'] = 'uid=%s,cn=users,%s' % (escape_dn_chars(options.domain_admin), ucr['ldap/base'])


join_ad()

# don't do that, why?
# tests/domainadmin/account and tests/domainadmin/pwd is the UCS account, why settings this to the windows account?
# check_correct_passwords()
# check_correct_domain_admin()
