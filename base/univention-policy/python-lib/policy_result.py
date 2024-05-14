#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Common Python Library
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2010-2024 Univention GmbH
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

import codecs
from subprocess import PIPE, Popen


class PolicyResultFailed(Exception):

    def __init__(self, message, returncode):
        # type: (str, int) -> None
        super(PolicyResultFailed, self).__init__(message)
        self.returncode = returncode


def policy_result(dn, binddn="", bindpw="", encoding='UTF-8', ldap_server=None):
    # type: (str, str, str, str, str | None) -> tuple[dict[str, list[str]], dict[str, str]]
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
    # type: (str, str, str, str, str | None) -> tuple[dict[str, list[str]], dict[str, str]]
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
    # type: (str, str) -> str
    if current_attribute.startswith('univentionRegistry;entry-hex-'):
        current_attribute = codecs.decode(current_attribute.replace('univentionRegistry;entry-hex-', ''), 'hex').decode(encoding)
    return current_attribute


def _policy_result(dn, binddn="", bindpw="", encoding='UTF-8', ldap_server=None):
    # type: (str, str, str, str, str | None) -> tuple[dict[str, list[str]], dict[str, str]]
    results = {}  # type: dict[str, list[str]] # Attribute -> [Values...]
    policies = {}  # type: dict[str, str] # Attribute -> Policy-DN

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
    assert p.stdout is not None
    for chunk in p.stdout:
        line = chunk.decode(encoding, 'replace').rstrip()
        key, _sep, val = line.partition(' ')
        if key == 'DN:':
            pass  # DN of the object
        elif key == 'POLICY':
            pass  # DN of the object ?
        elif key == 'Policy:':
            policy = val
        elif key == 'Attribute:':
            policies[val] = policy
            current_values = results.setdefault(val, [])
        elif key == 'Value:':
            current_values.append(val)
        else:
            pass  # empty line

    if p.wait() != 0:
        assert p.stderr is not None
        raise PolicyResultFailed("Error getting univention-policy-result for '%(dn)s': %(error)s" % {'dn': dn, 'error': p.stderr.read().decode('utf-8', 'replace')}, returncode=p.returncode)

    return (results, policies)
