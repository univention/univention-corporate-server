#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages UDM modules
#
# Copyright 2011-2015 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

import copy
import inspect

import univention.admin.syntax as udm_syntax

from ...log import MODULE
from ...config import ucr


class Widget(object):

	'''Describes a widget for the web frontend'''

	def __init__(self, name, syntax_classes, default_value, subclasses=True, widget_func=None):
		self._name = name
		self._syntax_classes = syntax_classes
		self._default_value = default_value
		self._subclasses = subclasses
		self._widget_func = widget_func

	def __contains__(self, syntax):
		'''Checks if the syntax is represented by this widget'''
		if self._subclasses:
			return isinstance(syntax, self._syntax_classes) or type(syntax) in (type, ) and issubclass(syntax, self._syntax_classes)
		else:
			return inspect.isclass(syntax) and syntax in self._syntax_classes or type(syntax) in self._syntax_classes

	def name(self, syntax, udm_property):
		if self._name is None and callable(self._widget_func):
			MODULE.info('The widget name for syntax %s is %s' % (syntax.name, self._widget_func(syntax, udm_property)))
			return self._widget_func(syntax, udm_property)
		return self._name

	@property
	def default_value(self):
		return self._default_value

	def __repr__(self):
		if isinstance(self._syntax_classes, (list, tuple)):
			syntax = ','.join(getattr(x, 'name', str(x)) for x in self._syntax_classes)
		else:
			syntax = self._syntax_classes.name
		return '<Widget(%s, syntax=%s, default=%r)>' % (self._name, syntax, self._default_value)


class _UCRWidget(Widget):

	def __init__(self, props, widget, syntax_classes, default, subclasses):
		self.props = props
		self.widget = widget
		super(_UCRWidget, self).__init__(None, syntax_classes, default, subclasses, self.widget_func)
		self._syntax_classes_names = syntax_classes

	def widget_func(self, syntax_, property_):
		return self.props.get('%s/property/%s' % (syntax_.name, property_['id']), self.widget)

	def __contains__(self, syntax):
		# in case a syntax-reload has been done we need to reuse the newly ones
		self._syntax_classes = tuple(filter(None, (getattr(udm_syntax, s, None) for s in self._syntax_classes_names)))
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
		for name, props in syntaxes.iteritems():
			try:
				widget = props['widget']
			except KeyError:
				MODULE.warn('Ignoring syntax-widget overwrite: %s (does not define widget)' % (name,))
				continue

			default = props.get('default')
			subclasses = ucr.is_true(None, props.get('subclasses', 'false'), False)
			syntax_classes = []
			for syntax in props.get('syntax', '').split(','):
				if not syntax:
					continue
				if not hasattr(udm_syntax, syntax):
					MODULE.warn('Ignoring unknown syntax class: %s' % (syntax,))
					continue
				syntax_classes.append(syntax)

			widgets.append(cls(props, widget, syntax_classes, default, subclasses))
			MODULE.info('Added widget definition: %r' % (widgets[-1],))

		return widgets


__widgets = _UCRWidget.load()
__widgets.extend([
	Widget('CheckBox', (udm_syntax.OkOrNot, udm_syntax.TrueFalseUp, udm_syntax.boolean), False),
	Widget('PasswordInputBox', (udm_syntax.passwd, udm_syntax.userPasswd), ''),
	Widget('DateBox', (udm_syntax.iso8601Date, udm_syntax.date), '1970-01-01'),
	Widget('TimeBox', (udm_syntax.TimeString), '00:00'),
	Widget(None, (udm_syntax.LDAP_Search, ), [], subclasses=False, widget_func=lambda syn, prop: syn.viewonly and 'LinkList' or 'ComboBox'),
	Widget('ComboBox', udm_syntax.select, []),
	Widget('TextBox', (udm_syntax.ldapDnOrNone, udm_syntax.ldapDn), '', subclasses=False),
	Widget(None, udm_syntax.UDM_Objects, '', widget_func=lambda syn, prop: prop['multivalue'] and len(syn.udm_modules) == 1 and syn.simple == False and 'umc/modules/udm/MultiObjectSelect' or 'umc/modules/udm/ComboBox'),
	Widget('ComboBox', udm_syntax.UDM_Attribute, ''),
	Widget(None, (udm_syntax.ldapDnOrNone, udm_syntax.ldapDn), '', widget_func=lambda syn, prop: prop['multivalue'] and 'umc/modules/udm/MultiObjectSelect' or 'ComboBox'),
	Widget('UnixAccessRights', udm_syntax.UNIX_AccessRight, '000'),
	Widget('UnixAccessRightsExtended', udm_syntax.UNIX_AccessRight_extended, '0000'),
	Widget('MultiSelect', udm_syntax.MultiSelect, []),
	Widget('umc/modules/udm/CertificateUploader', udm_syntax.Base64Upload, ''),
	Widget('ImageUploader', udm_syntax.jpegPhoto, ''),
	Widget('TextArea', udm_syntax.TextArea, ''),
	Widget('TextBox', udm_syntax.simple, '*'),
	Widget(None, udm_syntax.complex, None, widget_func=lambda syn, prop: prop['multivalue'] and 'MultiInput' or 'ComplexInput'),
])


def choices(syntax, udm_property):
	"""Returns the choices attribute of the property's syntax as a list
	of dictionaries with id and label keys. If the attribute is not
	available an empty list is returned."""
	MODULE.info('Find choices for syntax %s' % syntax)
	opts = None
	if inspect.isclass(syntax) and issubclass(syntax, (udm_syntax.UDM_Objects, udm_syntax.UDM_Attribute)):
		if issubclass(syntax, udm_syntax.UDM_Objects) and udm_property['multivalue'] and len(syntax.udm_modules) == 1 and syntax.simple == False:
			opts = {'objectType': syntax.udm_modules[0]}
		else:
			opts = {'dynamicValues': 'udm/syntax/choices', 'dynamicOptions': {'syntax': syntax.__name__}, 'dynamicValuesInfo': 'udm/syntax/choices/info'}
		if issubclass(syntax, udm_syntax.network):
			opts['onChange'] = 'javascript:umc/modules/udm/callbacks:setNetwork'
	elif isinstance(syntax, (udm_syntax.ldapDnOrNone, udm_syntax.ldapDn)) or inspect.isclass(syntax) and issubclass(syntax, (udm_syntax.ldapDnOrNone, udm_syntax.ldapDn)):
		opts = {'dynamicValues': 'udm/syntax/choices', 'dynamicOptions': {'syntax': inspect.isclass(syntax) and syntax.__name__ or syntax.__class__.__name__}}
	elif isinstance(syntax, udm_syntax.LDAP_Search):
		opts = {'dynamicValues': 'udm/syntax/choices', 'dynamicOptions': {'syntax': syntax.__class__.__name__, 'options': {'syntax': syntax.name, 'filter': syntax.filter, 'viewonly': syntax.viewonly, 'base': getattr(syntax, 'base', ''), 'value': syntax.value, 'attributes': syntax.attributes, 'empty': syntax.addEmptyValue, 'empty_end': syntax.appendEmptyValue}}, 'sortDynamicValues': not syntax.appendEmptyValue}

	elif inspect.isclass(syntax) and issubclass(syntax, udm_syntax.select):
		if getattr(syntax, 'depends', None) is not None:
			opts = {'dynamicValues': 'javascript:umc/modules/udm/callbacks:setDynamicValues'}
		if syntax.empty_value and syntax.choices and syntax.choices[0][0] != '':
			syntax.choices.insert(0, ('', ''))

	if getattr(syntax, 'depends', None) is not None:
		if 'dynamicOptions' not in opts:
			opts['dynamicOptions'] = {}

		opts['dynamicOptions']['$name$'] = syntax.depends
		opts['depends'] = syntax.depends

	if isinstance(opts, dict):
		return opts

	return {'staticValues': map(lambda x: {'id': x[0], 'label': x[1]}, getattr(syntax, 'choices', []))}


def subsyntaxes(syntax, udm_property):
	"""Returns a list of dictionaries describing the the sub types of a
	complex syntax"""
	udm_prop = copy.copy(udm_property)
	udm_prop['multivalue'] = False

	def subtypes_dict(item):
		elem = widget(item[1], udm_prop)
		elem['size'] = item[1].size
		elem['label'] = item[0]
		return elem

	return map(subtypes_dict, getattr(syntax, 'subsyntaxes', []))


def widget(syntax, udm_property):
	"""Returns a widget description as a dictionary"""
	global __widgets

	for widget in __widgets:
		if syntax in widget:
			descr = {'type': widget.name(syntax, udm_property)}
			values = choices(syntax, udm_property)
			subtypes = subsyntaxes(syntax, udm_property)
			if values:
				MODULE.info("Syntax %s has the following choices: %s" % (syntax.name, values))
				descr.update(values)
			if subtypes:
				MODULE.info("Syntax %s has the following sub-types: %s" % (syntax.name, subtypes))
				descr['subtypes'] = subtypes
			return descr

	if hasattr(syntax, '__name__'):
		name = syntax.__name__
	elif hasattr(syntax, '__class__'):
		name = syntax.__class__.__name__
	else:
		name = "Unknown class (name attribute :%s)" % syntax.name
	MODULE.process('Could not convert UDM syntax %s' % name)

	return {}


def default_value(syntax):
	"""Returns a default search pattern/value for the given widget"""
	global __widgets

	for widget in __widgets:
		if syntax in widget:
			return widget.default_value

	return '*'
