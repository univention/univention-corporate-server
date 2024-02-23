#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
# -*- coding: utf-8 -*-
## desc: test various functionality of the LDAP directory UMC Module
## packages:
##  - univention-management-console-module-udm
## roles-not:
##  - memberserver
##  - basesystem
## join: true
## exposure: dangerous

from playwright.sync_api import expect

from univention.lib.i18n import Translation
from univention.testing.browser.ldap_directory import LDAPDirectory
from univention.testing.browser.policies import Policies


_ = Translation('ucs-test-browser').translate


def create_registry_policy(udm, ucr, random_string) -> str:
    policy_name = random_string()
    policy_key = random_string()
    policy_value = random_string()
    return udm.create_object('policies/registry', position=f"cn=config-registry,cn=policies,{ucr.get('ldap/base')}", name=policy_name, registry=f'{policy_key} {policy_value}')


def test_add_remove_policies_multivalue(ldap_directory: LDAPDirectory, ucr, udm, random_string):
    container_name = random_string()
    position = f"cn=users,{ucr.get('ldap/base')}"

    policy_dns = [create_registry_policy(udm, ucr, random_string) for i in range(3)]

    udm.create_object('container/cn', position=position, name=container_name, userPath='1', policy_reference=policy_dns)

    ldap_directory.navigate()
    ldap_directory.expand_directory('users', exact=True)
    ldap_directory.edit_container(container_name)

    policies_tab = Policies(ldap_directory.tester)
    policies_tab.navigate()
    policies_tab.toggle_section('Policy: Univention Configuration Registry')

    expect(ldap_directory.page.get_by_role('button', name='New Entry')).to_be_visible()

    for policy_dn in policy_dns:
        hidden_input = policies_tab.page.locator(f"input[type=hidden][value='{policy_dn}']")
        expect(hidden_input, 'input does not have DN as value').to_have_attribute('value', policy_dn)

    new_policy_name = random_string()
    policies_tab.create_registry_policy(new_policy_name, random_string(), random_string())
    policy_dns.append(f"cn={new_policy_name},cn=config-registry,cn=policies,{ucr.get('ldap/base')}")
    for policy_dn in policy_dns:
        hidden_input = policies_tab.page.locator(f"input[type=hidden][value='{policy_dn}']")
        expect(hidden_input, 'input does not have DN as value, after creating new policy').to_have_attribute('value', policy_dn)
