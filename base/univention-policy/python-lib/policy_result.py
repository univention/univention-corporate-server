#!/usr/bin/python3
#
# Univention Common Python Library
#
# SPDX-FileCopyrightText: 2010-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import codecs
from subprocess import PIPE, Popen


class PolicyResultFailed(Exception):

    def __init__(self, message, returncode):
        super().__init__(message)
        self.returncode = returncode


def policy_result(dn, binddn="", bindpw="", encoding='UTF-8', ldap_server=None):
    """
    Return a tuple of hash-lists, mapping attributes to a list of values and
    mapping attributes to the matching Policy-DN.

    >>> (results, policies) = policy_result('dc=univention,dc=example')
    >>> policies['univentionDhcpDomainNameServers']
    'cn=default-settings,cn=dns,cn=dhcp,cn=policies,dc=univention,dc=example'
    results['univentionDhcpDomainNameServers']
    ['192.168.0.111']
    """
    results, policies = _policy_result(dn, binddn, bindpw, encoding, ldap_server)
    return (
        {_replace_ucr_key(key, encoding): value for key, value in results.items()},
        {_replace_ucr_key(key, encoding): value for key, value in policies.items()},
    )


def ucr_policy_result(dn, binddn="", bindpw="", encoding='UTF-8', ldap_server=None):
    """
    Return a tuple of hash-lists, mapping attributes to a list of values and
    mapping attributes to the matching Policy-DN.
    """
    results, policies = _policy_result(dn, binddn, bindpw, encoding, ldap_server)
    return (
        {_replace_ucr_key(key, encoding): value for key, value in results.items() if key.startswith('univentionRegistry;entry-hex-')},
        {_replace_ucr_key(key, encoding): value for key, value in policies.items() if key.startswith('univentionRegistry;entry-hex-')},
    )


def _replace_ucr_key(current_attribute, encoding):
    if current_attribute.startswith('univentionRegistry;entry-hex-'):
        current_attribute = codecs.decode(current_attribute.replace('univentionRegistry;entry-hex-', ''), 'hex').decode(encoding)
    return current_attribute


def _policy_result(dn, binddn="", bindpw="", encoding='UTF-8', ldap_server=None):
    if not binddn:
        import univention.config_registry
        cr = univention.config_registry.ConfigRegistry()
        cr.load()
        binddn = cr.get("ldap/hostdn")
        bindpw = "/etc/machine.secret"

    command = ['univention-policy-result', '-D', binddn, '-y', bindpw]
    if ldap_server:
        command.extend(["-h", ldap_server])
    command.append(dn)
    p = Popen(command, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        raise PolicyResultFailed("Error getting univention-policy-result for '%(dn)s': %(error)s" % {'dn': dn, 'error': stderr.decode('utf-8', 'replace')}, returncode=p.returncode)

    results = {}  # Attribute -> [Values...]
    policies = {}  # Attribute -> Policy-DN
    current_attribute = None
    policy = None

    for line in stdout.decode(encoding, 'replace').splitlines():
        if line.startswith('Attribute: '):
            current_attribute = line[len('Attribute: '):]
            policies[current_attribute] = policy
            current_values = results.setdefault(current_attribute, [])
        elif line.startswith('Value: '):
            value = line[len('Value: '):]
            current_values.append(value)
        elif line.startswith('Policy: '):
            policy = line[len('Policy: '):]
        elif line.startswith('DN: '):
            pass  # DN of the object
        elif line.startswith('POLICY '):
            pass  # DN of the object ?
        else:
            pass  # empty line
    return (results, policies)
