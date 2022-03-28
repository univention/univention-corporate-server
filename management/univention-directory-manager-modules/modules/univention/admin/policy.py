# -*- coding: utf-8 -*-
#
# Copyright 2015-2022 Univention GmbH
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

"""
|UDM| policy utilities
"""

from typing import Any, Dict, Tuple  # noqa: F401

import univention.admin.localization
import univention.admin.syntax
from univention.admin.mapping import ListToString, mapping as MappingType  # noqa: F401
from univention.admin.layout import Tab

translation = univention.admin.localization.translation('univention.admin')
_ = translation.translate


def register_policy_mapping(mapping):
	# type: (MappingType) -> None
	mapping.register('requiredObjectClasses', 'requiredObjectClasses')
	mapping.register('prohibitedObjectClasses', 'prohibitedObjectClasses')
	mapping.register('fixedAttributes', 'fixedAttributes')
	mapping.register('emptyAttributes', 'emptyAttributes')
	mapping.register('ldapFilter', 'ldapFilter', None, ListToString)


def policy_object_tab():
	# type: () -> Tab
	return Tab(_('Object'), _('Object'), advanced=True, layout=[
		['ldapFilter'],
		['requiredObjectClasses', 'prohibitedObjectClasses'],
		['fixedAttributes', 'emptyAttributes']
	])


def requiredObjectClassesProperty(**kwargs):
	# type: (**Any) -> Tuple[str, univention.admin.property]
	pargs = dict(
		short_description=_('Required object class'),
		long_description='',
		syntax=univention.admin.syntax.ldapObjectClass,
		multivalue=True,
	)
	pargs.update(kwargs)
	return 'requiredObjectClasses', univention.admin.property(**pargs)


def prohibitedObjectClassesProperty(**kwargs):
	# type: (**Any) -> Tuple[str, univention.admin.property]
	pargs = dict(
		short_description=_('Excluded object class'),
		long_description='',
		syntax=univention.admin.syntax.ldapObjectClass,
		multivalue=True,
	)
	pargs.update(kwargs)
	return 'prohibitedObjectClasses', univention.admin.property(**pargs)


def fixedAttributesProperty(**kwargs):
	# type: (**Any) -> Tuple[str, univention.admin.property]
	pargs = dict(
		short_description=_('Fixed attribute'),
		long_description='',
		multivalue=True,
	)
	pargs.update(kwargs)
	return 'fixedAttributes', univention.admin.property(**pargs)


def emptyAttributesProperty(**kwargs):
	# type: (**Any) -> Tuple[str, univention.admin.property]
	pargs = dict(
		short_description=_('Empty attribute'),
		long_description='',
		multivalue=True,
	)
	pargs.update(kwargs)
	return 'emptyAttributes', univention.admin.property(**pargs)


def ldapFilterProperty(**kwargs):
	# type: (**Any) -> Tuple[str, univention.admin.property]
	pargs = dict(
		short_description=_('LDAP filter'),
		long_description=_('This policy applies only to objects which matches this LDAP filter.'),
		syntax=univention.admin.syntax.ldapFilter,
	)
	pargs.update(kwargs)
	return 'ldapFilter', univention.admin.property(**pargs)
