#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention AD Connector
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
from univention.config_registry import ConfigRegistry
import univention.debug2 as ud

from univention.connector.ad import format_escaped

baseConfig = ConfigRegistry()
baseConfig.load()


def ignore_filter_from_tmpl(template, ucr_key, default=''):
	"""
	Construct an `ignore_filter` from a `ucr_key`
	(`connector/ad/mapping/*/ignorelist`, a comma delimited list of values), as
	specified by `template` while correctly escaping the filter-expression.

	`template` must be formatted as required by `format_escaped`.

	>>> ignore_filter_from_tmpl('(cn={0!e})',
	... 'connector/ad/mapping/nonexistend/ignorelist',
	... 'one,two,three')
	'(|(cn=one)(cn=two)(cn=three))'
	"""
	variables = [v for v in baseConfig.get(ucr_key, default).split(',') if v]
	filter_parts = [format_escaped(template, v) for v in variables]
	if filter_parts:
		return '(|{})'.format(''.join(filter_parts))
	return ''


def ignore_filter_from_attr(attribute, ucr_key, default=''):
	"""
	Convenience-wrapper around `ignore_filter_from_tmpl()`.

	This expects a single `attribute` instead of a `template` argument.

	>>> ignore_filter_from_attr('cn',
	... 'connector/ad/mapping/nonexistend/ignorelist',
	... 'one,two,three')
	'(|(cn=one)(cn=two)(cn=three))'
	"""
	template = '({}={{0!e}})'.format(attribute)
	return ignore_filter_from_tmpl(template, ucr_key, default)


def ucs2ad_sid(connector, key, object):
	_d = ud.function('mapping.ucs2ad_sid -- not implemented')  # noqa: F841


def ad2ucs_sid(connector, key, object):
	_d = ud.function('mapping.ad2ucs_sid')  # noqa: F841
	return univention.connector.ad.decode_sid(object['objectSid'])


def ucs2ad_givenName(connector, key, object):
	_d = ud.function('mapping.ucs2ad_givenName')  # noqa: F841
	if 'firstname' in object and 'lastname' in object:
		return '%s %s' % (object['firstname'], object['lastname'])
	elif 'firstname' in object:
		return object['firstname']
	elif 'lastname' in object:
		return object['lastname']


def ad2ucs_givenName(connector, key, object):
	_d = ud.function('mapping.ad2ucs_givenName -- not implemented')  # noqa: F841


def ucs2ad_dn_string(dn):
	_d = ud.function('mapping.ucs2ad_dn_string')  # noqa: F841
	return string.replace(dn, baseConfig['ldap/base'], baseConfig['connector/ad/ldap/base'])


def ucs2ad_dn(connector, key, object):
	_d = ud.function('mapping.ucs2ad_dn')  # noqa: F841
	return ucs2ad_dn_string(object.dn)


def ad2ucs_dn_string(dn):
	_d = ud.function('mapping.ad2ucs_dn_string')  # noqa: F841
	return string.replace(dn, baseConfig['connector/ad/ldap/base'], baseConfig['ldap/base'])


def ad2ucs_dn(connector, key, object):
	_d = ud.function('mapping.ad2ucs_dn')  # noqa: F841
	return ad2ucs_dn_string(object.dn)


def ucs2ad_user_dn(connector, key, object):
	_d = ud.function('mapping.ucs2ad_user_dn')  # noqa: F841
	return string.replace(ucs2ad_dn(connector, key, object), "uid=", "cn=")


def ad2ucs_user_dn(connector, key, object):
	_d = ud.function('mapping.ad2ucs_user_dn')  # noqa: F841
	return string.replace(ad2ucs_dn(connector, key, object), "cn=", "uid=")


def ucs2ad_sambaGroupType(connector, key, object):
	_d = ud.function('mapping.ucs2ad_sambaGroupType -- not implemented')  # noqa: F841
	return "-2147483644"


def ad2ucs_sambaGroupType(connector, key, object):
	_d = ud.function('mapping.ad2ucs_sambaGroupType -- not implemented')  # noqa: F841
