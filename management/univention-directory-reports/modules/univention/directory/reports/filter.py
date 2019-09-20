# -*- coding: utf-8 -*-
#
# Univention Directory Reports
#  write an interpreted token structure to a file
#
# Copyright 2007-2019 Univention GmbH
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

import univention.admin.syntax as ua_syntax

import univention.admin.localization
translation = univention.admin.localization.translation('univention-directory-reports')
_ = translation.translate

__all__ = ['filter_add', 'filter_get']

_filters = []


def filter_add(types, func):
	_filters.append((types, func))


def filter_get(prop_type):
	for types, func in _filters:
		if isinstance(prop_type, types):
			return func
	return None


def _boolean_filter(prop, key, value):
	if value and value.lower() in ('1', 'yes', 'true'):
		# need to call str() here directly order to force a correct translation
		return (key, str(_('Yes')))
	else:
		# need to call str() here directly order to force a correct translation
		return (key, str(_('No')))


filter_add((ua_syntax.boolean, ua_syntax.TrueFalseUp, ua_syntax.TrueFalse, ua_syntax.TrueFalseUpper, ua_syntax.OkOrNot), _boolean_filter)


def _email_address(prop, key, value):
	if prop.multivalue:
		value = ['\mbox{%s}' % val for val in value]
	else:
		value = '\mbox{%s}' % value
	return (key, value)


filter_add((ua_syntax.emailAddress, ), _email_address)


def _samba_group_type(prop, key, value):
	# need to call str() directly in order to force a correct translation
	types = {
		'2': str(_('Domain Group')),
		'3': str(_('Local Group')),
		'5': str(_('Well-Known Group'))
	}
	if value in types.keys():
		value = types[value]
	return (key, value)


filter_add((ua_syntax.sambaGroupType, ), _samba_group_type)
