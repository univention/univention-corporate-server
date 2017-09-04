#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2017 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

import ldap
import socket

import univention.uldap
import univention.lib.s4 as s4
import univention.config_registry
from univention.management.console.modules.diagnostic import Warning

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check well known SIDs')
description = _('All SIDs exist and names are consistent.')


NON_EXISTENT_SIDS = set(('Power Users', 'Creator Group Server',
	'Creator Owner Server', 'Local', 'Console Logon', 'All Services',
	'Creator Authority', 'Local Authority', 'NT Authority',
	'Non-unique Authority', 'Cloneable Domain Controllers'))


class CheckError(Exception):
	def __init__(self, sid, expected_name):
		self.sid = sid
		self.expected_name = expected_name


class SIDNotFound(CheckError):
	def __str__(self):
		msg = _('No user or group with SID {sid} found, expected {expected!r}.')
		return msg.format(sid=self.sid, expected=self.expected_name)


class NameMismatch(CheckError):
	def __init__(self, sid, expected_name, actual_name):
		super(NameMismatch, self).__init__(sid, expected_name)
		self.actual_name = actual_name

	def __str__(self):
		msg = _('User or group with SID {sid} has name {actual!r}, but should be {expected!r}.')
		return msg.format(sid=self.sid, actual=self.actual_name, expected=self.expected_name)


class LDAPConnection(object):
	def __init__(self):
		self._connection = univention.uldap.getMachineConnection()
		self._ucr = univention.config_registry.ConfigRegistry()
		self._ucr.load()

	def _map_group_name(self, name):
		if name is None:
			return name
		return self._ucr.get('connector/s4/mapping/group/table/{}'.format(name)) or name

	def search(self, expression, attr=[]):
		for (dn, attr) in self._connection.search(expression, attr=attr):
			if dn is not None:
				yield (dn, attr)

	def get_domain_sid(self):
		for (dn, attr) in self.search('(objectClass=sambaDomain)', attr=['sambaSID']):
			for sid in attr.get('sambaSID'):
				return sid
		raise KeyError('domain sid not found')

	def get_by_sid(self, sid):
		expression = ldap.filter.filter_format('(sambaSID=%s)', (sid,))
		for (dn, attr) in self.search(expression, attr=['cn', 'uid']):
			for uid in attr.get('uid', []):
				return uid
			for cn in attr.get('cn', []):
				return self._map_group_name(cn)
		raise KeyError(sid)


def all_sids_and_names(domain_sid):
	for (sid, name) in s4.well_known_sids.iteritems():
		if name not in NON_EXISTENT_SIDS:
			yield (sid, name)

	for (rid, name) in s4.well_known_domain_rids.iteritems():
		if name not in NON_EXISTENT_SIDS:
			yield ('{}-{}'.format(domain_sid, rid), name)


def check_existence_and_consistency():
	ldap_connection = LDAPConnection()
	domain_sid = ldap_connection.get_domain_sid()
	for (sid, expected_name) in all_sids_and_names(domain_sid):
		try:
			actual_name = ldap_connection.get_by_sid(sid)
		except KeyError as error:
			yield SIDNotFound(error.message, expected_name)
		else:
			if actual_name.lower() != expected_name.lower():
				yield NameMismatch(sid, expected_name, actual_name)


def is_service_active(service):
	lo = univention.uldap.getMachineConnection()
	raw_filter = '(&(univentionService=%s)(cn=%s))'
	filter_expr = ldap.filter.filter_format(raw_filter, (service, socket.gethostname()))
	for (dn, _attr) in lo.search(filter_expr, attr=['cn']):
		if dn is not None:
			return True
	return False


def run(_umc_instance):
	if not is_service_active('S4 Connector'):
		return

	check_errors = list(check_existence_and_consistency())
	if check_errors:
		raise Warning(description='\n'.join(str(x) for x in check_errors))


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
