#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
"""module: manages UDM modules"""
#
# Copyright 2011-2022 Univention GmbH
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

import copy
import inspect

import univention.admin.syntax as udm_syntax

from ...log import MODULE


def choices(syntax, udm_property):
	"""
	Returns the choices attribute of the property's syntax as a list
	of dictionaries with id and label keys. If the attribute is not
	available an empty list is returned.
	"""
	MODULE.info('Find choices for syntax %s' % (syntax,))
	opts = None
	syntax_class = syntax if inspect.isclass(syntax) else type(syntax)
	if issubclass(syntax_class, (udm_syntax.UDM_Objects, udm_syntax.UDM_Attribute)):
		if issubclass(syntax_class, udm_syntax.UDM_Objects) and udm_property['multivalue'] and len(syntax.udm_modules) == 1 and not syntax.simple:
			opts = {'objectType': syntax.udm_modules[0]}
		else:
			opts = {
				'dynamicValues': 'udm/syntax/choices',
				'dynamicOptions': {
					'syntax': syntax.name,
				},
				'dynamicValuesInfo': 'udm/syntax/choices/info',
			}
		if issubclass(syntax_class, udm_syntax.network):
			opts['onChange'] = 'javascript:umc/modules/udm/callbacks:setNetwork'
	elif issubclass(syntax_class, (udm_syntax.ldapDnOrNone, udm_syntax.ldapDn)):
		opts = {
			'dynamicValues': 'udm/syntax/choices',
			'dynamicOptions': {
				'syntax': syntax.name,
			},
		}
	elif issubclass(syntax_class, udm_syntax.LDAP_Search):
		opts = {
			'dynamicValues': 'udm/syntax/choices',
			'dynamicOptions': {
				'syntax': syntax.name,
				'options': {
					'syntax': syntax.name,
					'filter': syntax.filter,
					'viewonly': syntax.viewonly,
					'base': getattr(syntax, 'base', ''),
					'value': syntax.value,
					'attributes': syntax.attributes,
					'empty': syntax.addEmptyValue,
					'empty_end': syntax.appendEmptyValue,
				},
			},
			'sortDynamicValues': not syntax.appendEmptyValue,
		}

	elif issubclass(syntax_class, udm_syntax.select):
		if getattr(syntax, 'depends', None) is not None:
			opts = {
				'dynamicValues': 'javascript:umc/modules/udm/callbacks:setDynamicValues',
			}
		if syntax.empty_value and syntax.choices and syntax.choices[0][0] != '':
			syntax.choices.insert(0, ('', ''))

	if getattr(syntax, 'depends', None) is not None:
		if 'dynamicOptions' not in opts:
			opts['dynamicOptions'] = {}

		opts['dynamicOptions']['$name$'] = syntax.depends
		opts['depends'] = syntax.depends

	if isinstance(opts, dict):
		return opts

	empty_value = [{'id': '', 'label': ''}] if getattr(syntax, 'empty_value', False) else []
	return {
		'staticValues': empty_value + [{'id': _[0], 'label': _[1], } for _ in getattr(syntax, 'choices', [])],
	}


def subsyntaxes(syntax, udm_property):
	"""
	Returns a list of dictionaries describing the sub types of a
	complex syntax.
	"""
	udm_prop = copy.copy(udm_property)
	udm_prop['multivalue'] = False

	def subtypes_dict(item):
		"""
		Return a single sub type dictionary.
		"""
		elem = widget(item[1], udm_prop)
		elem['size'] = item[1].size
		elem['label'] = item[0]
		return elem

	return [subtypes_dict(_) for _ in getattr(syntax, 'subsyntaxes', [])]


def widget(syntax, udm_property):
	"""
	Returns a widget description as a dictionary
	"""

	widget_name = syntax.get_widget(udm_property)
	if widget_name is None:
		MODULE.process('Could not convert UDM syntax %s' % (syntax,))
		return {}
	descr = {'type': widget_name}
	values = choices(syntax, udm_property)
	subtypes = subsyntaxes(syntax, udm_property)
	if values:
		MODULE.info("Syntax %s has the following choices: %s" % (syntax.name, values))
		descr.update(values)
	if subtypes:
		MODULE.info("Syntax %s has the following sub-types: %s" % (syntax.name, subtypes))
		descr['subtypes'] = subtypes
	if descr['type'] == 'LinkList':
		descr['multivalue'] = False
	elif 'MultiObjectSelect' in descr['type']:
		descr['multivalue'] = False
	elif udm_property['multivalue'] and descr['type'] != 'MultiInput':
		descr['subtypes'] = [{
			'type': descr['type'],
			'dynamicValues': descr.get('dynamicValues'),
			'dynamicValuesInfo': descr.get('dynamicValuesInfo'),
			'dynamicOptions': descr.get('dynamicOptions'),
			'staticValues': descr.get('staticValues'),
			'size': descr.get('size'),
			'depends': descr.get('depends'),
		}]
		descr['type'] = 'MultiInput'

	return descr
