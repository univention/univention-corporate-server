#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Common Python Library
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2010-2022 Univention GmbH
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
from subprocess import Popen, PIPE


class PolicyResultFailed(Exception):

	def __init__(self, message, returncode):
		super(PolicyResultFailed, self).__init__(message)
		self.returncode = returncode


def policy_result(dn, binddn="", bindpw="", encoding='UTF-8', ldap_server=None):
	"""
	Return a tuple of hash-lists, mapping attributes to a list of values and
	mapping attributes to the matching Policy-DN.

	>>> (results, policies) = policy_result('dc=univention,dc=local')
	>>> policies['univentionDhcpDomainNameServers']
	'cn=default-settings,cn=dns,cn=dhcp,cn=policies,dc=univention,dc=local'
	results['univentionDhcpDomainNameServers']
	['192.168.0.111']
	"""
	results, policies = _policy_result(dn, binddn, bindpw, encoding, ldap_server)
	return (
		{_replace_ucr_key(key, encoding): value for key, value in results.items()},
		{_replace_ucr_key(key, encoding): value for key, value in policies.items()}
	)


def ucr_policy_result(dn, binddn="", bindpw="", encoding='UTF-8', ldap_server=None):
	"""
	Return a tuple of hash-lists, mapping attributes to a list of values and
	mapping attributes to the matching Policy-DN.
	"""
	results, policies = _policy_result(dn, binddn, bindpw, encoding, ldap_server)
	return (
		{_replace_ucr_key(key, encoding): value for key, value in results.items() if key.startswith('univentionRegistry;entry-hex-')},
		{_replace_ucr_key(key, encoding): value for key, value in policies.items() if key.startswith('univentionRegistry;entry-hex-')}
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

	command = ['univention-policy-result', '-D', binddn, '-y', bindpw, ]
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
