#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  some mapping helper functions
#
# Copyright 2004-2020 Univention GmbH
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

import univention.config_registry as ucr

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
