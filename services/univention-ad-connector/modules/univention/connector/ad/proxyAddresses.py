#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  Mapping functions for proxyAddresses
#
# Copyright 2016-2022 Univention GmbH
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
	if isinstance(val, bytes):
		if b':' not in val:
			return val
		else:
			if val.lower().startswith(b'smtp:'):
				return val
	else:
		if ':' not in val:
			return val
		else:
			if val.lower().startswith('smtp:'):
				return val


def equal(values1, values2):
	''' This is called in these two ways:
		1. in sync_from_ucs: values1 are mapped ucs and values2 are        con
		2. in __set_values:  values1 are        ucs and values2 are mapped con
	'''
	ud.debug(ud.LDAP, ud.ALL, "proxyAddesses: values1: %r" % (values1,))
	ud.debug(ud.LDAP, ud.ALL, "proxyAddesses: values2: %r" % (values2,))
	values_normalized = []
	for values in (values1, values2):
		if not isinstance(values, (list, tuple)):
			values = [values]
		values_normalized.append(
			[v for v in map(valid_mailaddress, values) if v]
		)
	return set(values_normalized[0]) == set(values_normalized[1])


def to_proxyAddresses(s4connector, key, object):
	new_con_values = []
	ucs_values = object['attributes'].get('mailPrimaryAddress', [])
	mailPrimaryAddress = ucs_values[0] if ucs_values else None
	if mailPrimaryAddress:
		new_con_value = b'SMTP:' + mailPrimaryAddress
		new_con_values.append(new_con_value)
	for v in object['attributes'].get('mailAlternativeAddress', []):
		if v == mailPrimaryAddress:
			continue
		new_con_value = b'smtp:' + v
		new_con_values.append(new_con_value)
	return new_con_values


def to_mailPrimaryAddress(s4connector, key, object):
	for value in object['attributes'].get('proxyAddresses', []):
		if value.startswith(b'SMTP:'):
			return [value[5:]]
	return []


def to_mailAlternativeAddress(s4connector, key, object):
	new_ucs_values = []
	for value in object['attributes'].get('proxyAddresses', []):
		if value.startswith(b'smtp:'):
			new_ucs_values.append(value[5:])
	return new_ucs_values
