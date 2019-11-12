#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  Mapping functions for proxyAddresses
#
# Copyright 2016-2019 Univention GmbH
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

import univention.debug2 as ud


def valid_mailaddress(val):
	# invalid is: <transport>:<address> iff <transport>.lower() != smtp
	if not val:
		return
	idx = val.find(':')
	if idx == -1:
		return val
	else:
		if val.lower().startswith('smtp:'):
			return val


def equal(values1, values2):
	''' This is called in these two ways:
		1. in sync_from_ucs: values1 are mapped ucs and values2 are        con
		2. in __set_values:  values1 are        ucs and values2 are mapped con
	'''
	_d = ud.function('proxyAddesses.equal')  # noqa: F841
	ud.debug(ud.LDAP, ud.ALL, "proxyAddesses: values1: %s" % (values1,))
	ud.debug(ud.LDAP, ud.ALL, "proxyAddesses: values2: %s" % (values2,))
	values_normalized = []
	for values in (values1, values2):
		if not isinstance(values, (list, tuple)):
			values = [values]
		values_normalized.append(
			filter(lambda v: v, map(valid_mailaddress, values))
		)
	if set(values_normalized[0]) == set(values_normalized[1]):
		return True
	else:
		return False


def to_proxyAddresses(s4connector, key, object):
	_d = ud.function('proxyAddesses.ucs_to_ad_mapping')  # noqa: F841
	new_con_values = []
	ucs_values = object['attributes'].get('mailPrimaryAddress', [])
	mailPrimaryAddress = ucs_values[0] if ucs_values else None
	if mailPrimaryAddress:
		new_con_value = 'SMTP:' + mailPrimaryAddress
		new_con_values.append(new_con_value)
	for v in object['attributes'].get('mailAlternativeAddress', []):
		if v == mailPrimaryAddress:
			continue
		new_con_value = 'smtp:' + v
		new_con_values.append(new_con_value)
	return new_con_values


def to_mailPrimaryAddress(s4connector, key, object):
	_d = ud.function('proxyAddesses.to_mailPrimaryAddress')  # noqa: F841
	for value in object['attributes'].get('proxyAddresses', []):
		if value.startswith('SMTP:'):
			return [value[5:]]
	return []


def to_mailAlternativeAddress(s4connector, key, object):
	_d = ud.function('proxyAddesses.to_mailAlternativeAddress')  # noqa: F841
	new_ucs_values = []
	for value in object['attributes'].get('proxyAddresses', []):
		if value.startswith('smtp:'):
			new_ucs_values.append(value[5:])
	return new_ucs_values


def merge_ucs2con(mapped_ucs_values, old_con_values=None):
	_d = ud.function('proxyAddesses.merge_ucs2con')  # noqa: F841
	new_con_values = []
	if not old_con_values:
		old_con_values = []

	# first preserve all non-smtp addresses (x500, fax, whatever)
	# and all smtp-Addresses we also have in UCS
	for con_value in old_con_values:
		if con_value.lower().startswith('smtp:'):
			if con_value in mapped_ucs_values:
				new_con_values.append(con_value)
		else:
			new_con_values.append(con_value)

	# Then add the ones we currently only have in UCS
	for mapped_ucs_value in mapped_ucs_values:
		if mapped_ucs_value not in new_con_values:
			new_con_values.append(mapped_ucs_value)

	return new_con_values
