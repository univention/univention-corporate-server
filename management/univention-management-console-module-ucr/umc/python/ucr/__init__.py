#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manages Univention Config Registry variables
#
# Copyright 2006-2019 Univention GmbH
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

from io import BytesIO

from univention.lib.i18n import Translation
from univention.management.console.base import Base, UMC_Error
from univention.management.console.config import ucr

from univention.management.console.modules.decorators import simple_response, sanitize
from univention.management.console.modules.sanitizers import PatternSanitizer, ChoicesSanitizer, DictSanitizer, StringSanitizer

from univention.config_registry import handler_set, handler_unset, ConfigRegistry, validate_key
from univention.config_registry_info import ConfigRegistryInfo, Variable

import univention.info_tools as uit

_ = Translation('univention-management-console-module-ucr').translate


class UCRKeySanitizer(StringSanitizer):

	def _sanitize(self, value, name, further_arguments):
		value = super(UCRKeySanitizer, self)._sanitize(value, name, further_arguments)
		b = BytesIO()
		if not validate_key(value, b):
			error_message = b.getvalue()
			self.raise_validation_error('%s %s' % (_('A valid UCR variable name must contain at least one character and can only contain letters, numerals, "/", ".", ":", "_" and "-".'), error_message))
			return
		return value


class Instance(Base):

	def init(self):
		# set the language in order to return the correctly localized labels/descriptions
		uit.set_language(self.locale.language)

	def __create_variable_info(self, options):
		all_info = ConfigRegistryInfo(registered_only=False)
		info = ConfigRegistryInfo(install_mode=True)
		info.read_customized()
		var = Variable()

		# description
		for line in options['descriptions']:
			text = line['text']
			if not text:
				continue
			if 'lang' in line:
				var['description[%s]' % line['lang']] = text
			else:
				var['description'] = text
		# categories
		if options['categories']:
			var['categories'] = ','.join(options['categories'])

		# type
		var['type'] = options['type']

		# are there any modifications?
		old_value = all_info.get_variable(options['key'])
		if old_value != var:
			# save
			info.add_variable(options['key'], var)
			info.write_customized()

	def is_readonly(self, key):
		ucrinfo_system = ConfigRegistryInfo(registered_only=False, load_customized=False)
		var = ucrinfo_system.get_variable(key)
		if var:
			return var.get('readonly') in ('yes', '1', 'true')
		return False

	@sanitize(DictSanitizer({
		'object': DictSanitizer({
			'key': UCRKeySanitizer(required=True),
			'value': StringSanitizer(default=''),
		})
	}))
	def add(self, request):
		# does the same as put
		ucr.load()
		already_set = set(ucr.keys()) & set(v['object']['key'] for v in request.options)
		if already_set:
			raise UMC_Error(_('The UCR variable %s is already set.') % ('", "'.join(already_set)))

		self.put(request)

	@sanitize(DictSanitizer({
		'object': DictSanitizer({
			'key': UCRKeySanitizer(required=True),
			'value': StringSanitizer(default=''),
		})
	}))
	def put(self, request):
		for _var in request.options:
			var = _var['object']
			value = var['value'] or ''
			key = var['key']
			if self.is_readonly(key):
				raise UMC_Error(_('The UCR variable %s is read-only and can not be changed!') % (key,))
			arg = ['%s=%s' % (key.encode(), value.encode())]
			handler_set(arg)

			# handle descriptions, type, and categories
			if 'descriptions' in var or 'type' in var or 'categories' in var:
				self.__create_variable_info(var)
		self.finished(request.id, True)

	def remove(self, request):
		variables = [x for x in [x.get('object') for x in request.options] if x is not None]
		for var in variables:
			if self.is_readonly(var):
				raise UMC_Error(_('The UCR variable %s is read-only and can not be removed!') % (var,))

		handler_unset(variables)
		self.finished(request.id, True)

	def get(self, request):
		ucrReg = ConfigRegistry()
		ucrReg.load()
		ucrInfo = ConfigRegistryInfo(registered_only=False)

		# iterate over all requested variables
		results = []
		for key in request.options:
			info = ucrInfo.get_variable(str(key))
			value = ucrReg.get(str(key))
			if not info and (value or '' == value):
				# only the value available
				results.append({'key': key, 'value': value})
			elif info:
				# info (categories etc.) available
				info['value'] = value
				info['key'] = key
				results.append(info.normalize())
			else:
				# variable not available, request failed
				raise UMC_Error(_('The UCR variable %(key)s could not be found') % {'key': key})
		self.finished(request.id, results)

	def categories(self, request):
		ucrInfo = ConfigRegistryInfo(registered_only=False)
		categories = []
		for id, obj in ucrInfo.categories.items():
			name = obj['name']
			if ucrInfo.get_variables(id):
				categories.append({
					'id': id,
					'label': name
				})
		self.finished(request.id, categories)

	@sanitize(pattern=PatternSanitizer(default='.*'), key=ChoicesSanitizer(['all', 'key', 'value', 'description'], required=True))
	@simple_response
	def query(self, pattern, key, category=None):
		'''Returns a dictionary of configuration registry variables
		found by searching for the (wildcard) expression defined by the
		UMCP request. Additionally a list of configuration registry
		categories can be defined.

		The dictionary returned is compatible with the Dojo data store
		format.'''
		variables = []
		if category == 'all':
			# load _all_ config registry variables
			base_info = ConfigRegistryInfo(registered_only=False)
		else:
			# load _all registered_ config registry variables
			base_info = ConfigRegistryInfo()

		if category in ('all', 'all-registered'):
			category = None

		def _match_value(name, var):
			return var.value and pattern.match(var.value)

		def _match_key(name, var):
			return pattern.match(name)

		def _match_description(name, var):
			descr = var.get('description')
			return descr and pattern.match(descr)

		def _match_all(name, var):
			return _match_value(name, var) or _match_description(name, var) or _match_key(name, var)

		func = locals().get('_match_%s' % key)
		for name, var in base_info.get_variables(category).items():
			if func(name, var):
				variables.append({
					'key': name,
					'value': var.value,
					'description': var.get('description', None),
				})

		return variables
