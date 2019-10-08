#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
"""module: manages UDM modules"""
#
# Copyright 2011-2019 Univention GmbH
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
from ...config import ucr


class Widget(object):

	"""
	Describes a widget for the web frontend.
	"""

	def __init__(self, name, syntax_classes, default_value, subclasses=True):
		"""
		Create Widget template.
		:name: The name of the dojo widget. If name is a function, it is called
		to compute the name dynamically.
		:syntax_classes: A tuple of Python types or classes, which are matched
		against the concrete syntax. (tuple is optional for single items.)
		:default: a default value.
		:subclasses: if True, the Widget also is used when the concrete syntax
		is a subclass of syntax_classes. If False, the concrete syntax must
		exactly match a syntax_class.
		"""
		self._name = name
		self._syntax_classes = syntax_classes
		self._default_value = default_value
		self._subclasses = subclasses

	def __contains__(self, syntax):
		'''Checks if the syntax is represented by this widget'''
		if self._subclasses:
			return isinstance(syntax, self._syntax_classes) or type(syntax) in (type, ) and issubclass(syntax, self._syntax_classes)
		else:
			return inspect.isclass(syntax) and syntax in self._syntax_classes or type(syntax) in self._syntax_classes

	def name(self, syntax, udm_property):
		"""Return name of dojo widget for the UDM Python syntax."""
		if callable(self._name):
			name = self._name(syntax, udm_property)
			MODULE.info('The widget name for syntax %s is %s' % (syntax.name, name))
			return name
		return self._name

	@property
	def default_value(self):
		return self._default_value


class _UCRWidget(Widget):

	def __init__(self, props, widget, syntax_classes, default, subclasses):
		self.props = props
		self.widget = widget
		super(_UCRWidget, self).__init__(self.widget_func, syntax_classes, default, subclasses)
		self._syntax_classes_names = syntax_classes

	def widget_func(self, syntax_, property_):
		return self.props.get('property/%s/%s' % (syntax_.name, property_['id']), self.widget)

	def __contains__(self, syntax):
		# in case a syntax-reload has been done we need to reuse the newly ones
		self._syntax_classes = tuple([_f for _f in (getattr(udm_syntax, s, None) for s in self._syntax_classes_names) if _f])
		return super(_UCRWidget, self).__contains__(syntax)

	@classmethod
	def load(cls):
		identifier = 'directory/manager/web/widget/'
		syntaxes = {}
		for key, val in ucr.items():
			if not key.startswith(identifier):
				continue
			key = key[len(identifier):]
			try:
				name, key = key.split('/', 1)
			except ValueError:
				continue
			syntaxes.setdefault(name, {}).setdefault(key, val)

		widgets = []
		for name, props in syntaxes.items():
			try:
				widget = props['widget']
			except KeyError:
				MODULE.warn('Ignoring syntax-widget overwrite: %s (does not define widget)' % (name,))
				continue

			default = props.get('default', '')
			subclasses = ucr.is_true(None, False, props.get('subclasses', 'false').lower())
			syntax_classes = []
			for syntax in props.get('syntax', '').split(','):
				if not syntax:
					continue
				syntax_classes.append(syntax)

			widgets.append(cls(props, widget, syntax_classes, default, subclasses))
			MODULE.info('Added ucr widget definition for syntax classes: %r' % (syntax_classes, ))

		return widgets


__widgets = _UCRWidget.load()
__widgets.extend([
	Widget('umc/modules/udm/LockedCheckBox', (udm_syntax.locked), False),
	Widget('umc/modules/udm/MultiObjectSelect', (udm_syntax.PortalComputer), False),
	Widget('umc/modules/udm/PortalContent', (udm_syntax.PortalCategorySelection, udm_syntax.PortalEntrySelection, ), None),
	Widget('CheckBox', (udm_syntax.OkOrNot, udm_syntax.TrueFalseUp, udm_syntax.boolean), False),
	Widget('PasswordInputBox', (udm_syntax.passwd, udm_syntax.userPasswd), ''),
	Widget('DateBox', (udm_syntax.iso8601Date, udm_syntax.date), '1970-01-01'),
	Widget('TimeBox', (udm_syntax.TimeString), '00:00'),
	Widget(lambda syn, prop: 'umc/modules/udm/LinkList' if syn.viewonly else 'ComboBox', (udm_syntax.LDAP_Search, ), [], subclasses=False),
	Widget('SuggestionBox', udm_syntax.combobox, []),
	Widget('ComboBox', udm_syntax.select, []),
	Widget('TextBox', (udm_syntax.ldapDnOrNone, udm_syntax.ldapDn), '', subclasses=False),
	Widget(lambda syn, prop: 'umc/modules/udm/MultiObjectSelect' if prop['multivalue'] and len(syn.udm_modules) == 1 and not syn.simple else 'umc/modules/udm/ComboBox', udm_syntax.GroupDN, []),
	Widget(lambda syn, prop: 'umc/modules/udm/MultiObjectSelect' if prop['multivalue'] and len(syn.udm_modules) == 1 and not syn.simple else 'umc/modules/udm/ComboBox', udm_syntax.UDM_Objects, ''),
	Widget('ComboBox', udm_syntax.UDM_Attribute, ''),
	Widget(lambda syn, prop: 'umc/modules/udm/MultiObjectSelect' if prop['multivalue'] else 'ComboBox', (udm_syntax.ldapDnOrNone, udm_syntax.ldapDn), ''),
	Widget('UnixAccessRights', udm_syntax.UNIX_AccessRight, '000'),
	Widget('UnixAccessRightsExtended', udm_syntax.UNIX_AccessRight_extended, '0000'),
	Widget('MultiSelect', udm_syntax.MultiSelect, []),
	Widget('ImageUploader', udm_syntax.Base64BaseUpload, ''),
	Widget('umc/modules/udm/CertificateUploader', udm_syntax.Base64Upload, ''),
	Widget('ImageUploader', udm_syntax.jpegPhoto, ''),
	Widget('TextArea', udm_syntax.TextArea, ''),
	Widget('Editor', udm_syntax.Editor, ''),
	Widget('TextBox', udm_syntax.simple, '*'),
	Widget(lambda syn, prop: 'MultiInput' if prop['multivalue'] else 'ComplexInput', udm_syntax.complex, None),
])


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

	return {
		'staticValues': [{'id': _[0], 'label': _[1], } for _ in getattr(syntax, 'choices', [])],
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

	for widget_ in __widgets:
		if syntax in widget_:
			descr = {'type': widget_.name(syntax, udm_property)}
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

	if hasattr(syntax, '__name__'):
		name = syntax.__name__
	elif hasattr(syntax, '__class__'):
		name = syntax.__class__.__name__
	else:
		name = "Unknown class (name attribute: %s)" % (syntax.name,)
	MODULE.process('Could not convert UDM syntax %s' % (name,))

	return {}


def default_value(syntax):
	"""
	Returns a default search pattern/value for the given widget.
	"""
	for widget_ in __widgets:
		if syntax in widget_:
			return widget_.default_value

	return '*'
