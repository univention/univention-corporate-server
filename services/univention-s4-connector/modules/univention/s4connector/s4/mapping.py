#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  some mapping helper functions
#
# Copyright 2004-2019 Univention GmbH
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

import string
import univention.config_registry as ucr
import univention.debug2 as ud
import univention.s4connector.s4

from univention.s4connector.s4 import format_escaped

configRegistry = ucr.ConfigRegistry()
configRegistry.load()


def ignore_filter_from_tmpl(template, ucr_key, default=''):
	"""
	Construct an `ignore_filter` from a `ucr_key`
	(`connector/s4/mapping/*/ignorelist`, a comma delimited list of values), as
	specified by `template` while correctly escaping the filter-expression.

	`template` must be formatted as required by `format_escaped`.

	>>> ignore_filter_from_tmpl('(cn={0!e})',
	... 'connector/s4/mapping/nonexistend/ignorelist',
	... 'one,two,three')
	'(|(cn=one)(cn=two)(cn=three))'
	"""
	variables = [v for v in configRegistry.get(ucr_key, default).split(',') if v]
	filter_parts = [format_escaped(template, v) for v in variables]
	if filter_parts:
		return '(|{})'.format(''.join(filter_parts))
	return ''


def ignore_filter_from_attr(attribute, ucr_key, default=''):
	"""
	Convenience-wrapper around `ignore_filter_from_tmpl()`.

	This expects a single `attribute` instead of a `template` argument.

	>>> ignore_filter_from_attr('cn',
	... 'connector/s4/mapping/nonexistend/ignorelist',
	... 'one,two,three')
	'(|(cn=one)(cn=two)(cn=three))'
	"""
	template = '({}={{0!e}})'.format(attribute)
	return ignore_filter_from_tmpl(template, ucr_key, default)


def ucs2s4_sid(s4connector, key, object):
	_d = ud.function('mapping.ucs2s4_sid -- not implemented')  # noqa: F841


def s42ucs_sid(s4connector, key, object):
	_d = ud.function('mapping.s42ucs_sid')  # noqa: F841
	return univention.s4connector.s4.decode_sid(object['objectSid'])


def ucs2s4_givenName(s4connector, key, object):
	_d = ud.function('mapping.ucs2s4_givenName')  # noqa: F841
	if object.has_key('firstname') and object.has_key('lastname'):
		return '%s %s' % (object['firstname'], object['lastname'])
	elif object.has_key('firstname'):
		return object['firstname']
	elif object.has_key('lastname'):
		return object['lastname']


def s42ucs_givenName(s4connector, key, object):
	_d = ud.function('mapping.s42ucs_givenName -- not implemented')  # noqa: F841


def ucs2s4_dn_string(dn):
	_d = ud.function('mapping.ucs2s4_dn_string')  # noqa: F841
	return string.replace(dn, configRegistry['ldap/base'], configRegistry['connector/s4/ldap/base'])


def ucs2s4_dn(s4connector, key, object):
	_d = ud.function('mapping.ucs2s4_dn')  # noqa: F841
	return ucs2s4_dn_string(object.dn)


def s42ucs_dn_string(dn):
	_d = ud.function('mapping.s42ucs_dn_string')  # noqa: F841
	return string.replace(dn, configRegistry['connector/s4/ldap/base'], configRegistry['ldap/base'])


def s42ucs_dn(s4connector, key, object):
	_d = ud.function('mapping.s42ucs_dn')  # noqa: F841
	return s42ucs_dn_string(object.dn)


def ucs2s4_user_dn(s4connector, key, object):
	_d = ud.function('mapping.ucs2s4_user_dn')  # noqa: F841
	return string.replace(ucs2s4_dn(s4connector, key, object), "uid=", "cn=")


def s42ucs_user_dn(s4connector, key, object):
	_d = ud.function('mapping.s42ucs_user_dn')  # noqa: F841
	return string.replace(s42ucs_dn(s4connector, key, object), "cn=", "uid=")


def ucs2s4_sambaGroupType(s4connector, key, object):
	_d = ud.function('mapping.ucs2s4_sambaGroupType -- not implemented')  # noqa: F841
	return "-2147483644"


def s42ucs_sambaGroupType(s4connector, key, object):
	_d = ud.function('mapping.s42ucs_sambaGroupType -- not implemented')  # noqa: F841
