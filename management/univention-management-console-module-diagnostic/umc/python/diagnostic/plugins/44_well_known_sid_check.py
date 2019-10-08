#!/usr/bin/python2.7
# coding: utf-8
#
# Univention Management Console module:
#  System Diagnosis UMC module
#
# Copyright 2017-2019 Univention GmbH
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

import ldap

import univention.uldap
import univention.lib.s4 as s4
import univention.lib.misc
import univention.config_registry
from univention.management.console.modules.diagnostic import Warning, MODULE
from univention.management.console.modules.diagnostic import util
from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Check well known SIDs')
description = _('All SIDs exist and names are consistent.')
run_descr = ['Checks if all well known SIDs exist and if their names are consistent']


NON_EXISTENT_SIDS = set((
	'Power Users', 'Creator Group Server',
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


class SIDMismatch(CheckError):
	def __init__(self, sid, actual_sid, expected_name):
		super(SIDMismatch, self).__init__(sid, expected_name)
		self.actual_sid = actual_sid

	def __str__(self):
		msg = _('User or group with name {name!r} has sid {actual_sid}, but should be {sid}.')
		return msg.format(name=self.expected_name, actual_sid=self.actual_sid, sid=self.sid)


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
				return cn
		raise KeyError(sid)

	def get_by_name(self, name):
		expression = ldap.filter.filter_format('(|(cn=%s)(uid=%s))', (name, name))
		for (dn, attr) in self.search(expression, attr=['sambaSID']):
			for sid in attr.get('sambaSID', []):
				return sid
		raise KeyError(name)


def all_sids_and_names(domain_sid):
	for (sid, name) in s4.well_known_sids.items():
		if name not in NON_EXISTENT_SIDS:
			yield (sid, name)

	for (rid, name) in s4.well_known_domain_rids.items():
		if name not in NON_EXISTENT_SIDS:
			yield ('{}-{}'.format(domain_sid, rid), name)


def custom_name(name, ucr=None):
	mapped_user = univention.lib.misc.custom_username(name, ucr)
	if mapped_user != name:
		return mapped_user
	mapped_group = univention.lib.misc.custom_groupname(name, ucr)
	if mapped_group != name:
		return mapped_group
	return name


def check_existence_and_consistency():
	ldap_connection = LDAPConnection()
	domain_sid = ldap_connection.get_domain_sid()
	ucr = univention.config_registry.ConfigRegistry()
	ucr.load()
	for (sid, expected_name) in all_sids_and_names(domain_sid):
		mapped_name = custom_name(expected_name, ucr)
		try:
			# The user/group retrieved by SID should have the name as specified
			# in the well-known-sid-mapping (or mapped as per
			# `custom_{user,group}name()`)
			actual_name = ldap_connection.get_by_sid(sid)
		except KeyError as error:
			# If nothing is found, we search for an user/group with the
			# (mapped) name and check if there is a SID mismatch.
			yield SIDNotFound(error.message, mapped_name)
			try:
				actual_sid = ldap_connection.get_by_name(mapped_name)
			except KeyError as error:
				pass
			else:
				# We don't need an explicit `sid != actual_sid` here, as no
				# object with `sid` exists and we therefore have a mismatch in
				# every case.
				yield SIDMismatch(sid, actual_sid, mapped_name)
		else:
			if actual_name.lower() != mapped_name.lower():
				yield NameMismatch(sid, mapped_name, actual_name)


def run(_umc_instance):
	if not util.is_service_active('S4 Connector'):
		return

	check_errors = list(check_existence_and_consistency())
	if check_errors:
		MODULE.error('\n'.join(str(x) for x in check_errors))
		raise Warning(description='\n'.join(str(x) for x in check_errors))


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
