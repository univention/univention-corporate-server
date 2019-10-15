#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: Firewall
#
# Copyright 2013-2019 Univention GmbH
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

from univention.management.console.log import MODULE
import univention.management.console as umc
import univention.management.console.modules.decorators as decorators
import univention.management.console.modules.sanitizers as sanitizers

from univention.management.console.modules.firewall import backend


_ = umc.Translation('univention-management-console-module-firewall').translate


class Instance(umc.modules.Base):

	def _get_description(self, description):
		# Try to return the localised description or
		# use english as a fallback
		if self.locale.language in description:
			return description[self.locale.language]
		elif u'en' in description:
			return description[u'en']
		else:
			return None

	@decorators.sanitize(
		category=sanitizers.ChoicesSanitizer(
			(u'protocol', u'port', u'address', u'packageName', u'description', ),
			default=u'port'),
		pattern=sanitizers.PatternSanitizer(default=u'.*'))
	@decorators.simple_response
	def rules_query(self, category, pattern):
		"""Searches for firewall rules

		requests.options = [
			'category': 'protocol' | 'port' | 'address' | 'package' |
			'description',
			'pattern': <str>,
		]
		"""
		def match(rule):
			if category == u'port':
				# Check every port number
				for port in range(*rule.port):
					match = pattern.match(str(port))
					if match:
						return match
				else:
					return False
			elif category == u'packageName':
				if rule.package:
					return pattern.match(rule.package)
				else:
					return False
			elif category == u'description':
				for language in rule.description.values():
					match = pattern.match(language)
					if match:
						return match
				else:
					return False
			else:
				# Simple match for most cases:
				return pattern.match(getattr(rule, category))

		def get_address(address):
			if address == u'all':
				return _(u'All addresses')
			elif address == u'ipv4':
				return _(u'All IPv4 addresses')
			elif address == u'ipv6':
				return _(u'All IPv6 addresses')
			else:
				return address

		# Try to load firewall configuration
		try:
			firewall = backend.Firewall()
		except backend.Error as e:
			message = _(u"Could not load firewall configuration")
			MODULE.error(u"%s: %s" % (message, str(e), ))
			raise umc.modules.UMC_CommandError(message)

		result = []
		for rule in firewall.rules.values():
			if not rule or not match(rule):
				# rule isn't complete (e.g. missing action) or
				# rule doesn't match the pattern
				continue
			entry = {}
			entry = {
				u'identifier': rule.identifier,
				u'protocol': rule.protocol,
				u'portStart': rule.port[0],
				u'portEnd': (rule.port[1] - 1),
				u'address': get_address(rule.address),
				u'packageName': rule.package,
				u'action': rule.action.lower(),
				u'description': self._get_description(rule.description),
			}
			result.append(entry)
		return result

	def _add_or_edit(self, iterator, object, edit=False):
		def get_address(address_type, address_value):
			if address_type == u'specific':
				return address_value
			else:
				return address_type

		# Try to load firewall configuration
		try:
			firewall = backend.Firewall()
		except backend.Error as e:
			message = _(u"Could not load firewall configuration")
			MODULE.error(u"%s: %s" % (message, str(e), ))
			raise umc.modules.UMC_CommandError(message)

		for (object, ) in iterator:
			try:
				if edit:
					firewall.remove_rule(object[u'identifier'])

				port = (object[u'portStart'], (object[u'portEnd'] + 1), )
				address = get_address(object[u'addressType'], object[u'addressValue'])

				rule = backend.Rule(object[u'protocol'], port, address, None, object[u'action'].lower())
				firewall.add_rule(rule)
			except backend.Error as e:
				if edit:
					yield {u'object': object[u'identifier'], u'success': False, u'details': str(e), }
				else:
					yield {u'success': False, u'details': str(e), }
			else:
				yield {u'object': rule.identifier, u'success': True, }

		# Try to save firewall configuration
		try:
			firewall.save()
		except backend.Error as e:
			message = _(u"Could not save firewall configuration")
			MODULE.error(u"%s: %s" % (message, str(e), ))
			raise umc.modules.UMC_CommandError(message)

	@decorators.sanitize(sanitizers.DictSanitizer({u'object': sanitizers.DictSanitizer({
		u'protocol': sanitizers.ChoicesSanitizer((u'tcp', u'udp', ), required=True),
		u'portStart': sanitizers.IntegerSanitizer(minimum=1, maximum=2**16, maximum_strict=True, required=True),
		u'portEnd': sanitizers.IntegerSanitizer(minimum=1, maximum=2**16, maximum_strict=True, required=True),
		u'addressType': sanitizers.ChoicesSanitizer((u'all', u'ipv4', u'ipv6', u'specific', ), required=True),
		u'addressValue': sanitizers.StringSanitizer(default=u''),
		u'action': sanitizers.ChoicesSanitizer((u'accept', u'reject', u'drop', ), required=True),
	}, required=True), }))
	@decorators.multi_response
	@decorators.log
	def rules_add(self, iterator, object):
		"""Add the specified new rules:

		requests.options = [{
			'object': {
				'protocol': 'tcp' | 'udp',
				'portStart': <int>,
				'portEnd': <int>,
				'addressType': 'all' | 'ipv4' | 'ipv6' | 'specific',
				'addressValue': <string>
				'action': 'accept' | 'reject' | 'drop,
			}
		}, ]
		"""
		return self._add_or_edit(iterator, object, edit=False)

	@decorators.sanitize(sanitizers.StringSanitizer(required=True))
	@decorators.multi_response(single_values=True)
	@decorators.log
	def rules_get(self, iterator):
		"""Returns the specified rules

		requests.options = [
			<string>,
		]
		"""
		def get_address_type(address):
			if backend.REGEX_RULE_ADDRESS.match(address):
				return address
			else:
				return u'specific'

		def get_address_value(address):
			if backend.REGEX_RULE_ADDRESS.match(address):
				return None
			else:
				return address

		# Try to load firewall configuration
		try:
			firewall = backend.Firewall()
		except backend.Error as e:
			message = _(u"Could not load firewall configuration")
			MODULE.error(u"%s: %s" % (message, str(e), ))
			raise umc.modules.UMC_CommandError(message)

		for identifier in iterator:
			try:
				rule = firewall.rules[identifier]

				entry = {
					u'identifier': rule.identifier,
					u'protocol': rule.protocol,
					u'portStart': rule.port[0],
					u'portEnd': (rule.port[1] - 1),
					u'addressType': get_address_type(rule.address),
					u'addressValue': get_address_value(rule.address),
					u'packageName': rule.package,
					u'action': rule.action.lower(),
					u'description': self._get_description(rule.description),
				}
			except (backend.Error, KeyError) as e:
				message = _(u"Could not get firewall rule")
				MODULE.error(u"%s: %s" % (message, str(e), ))
				raise umc.modules.UMC_CommandError(message)
			else:
				yield entry

	@decorators.sanitize(sanitizers.DictSanitizer({
		u'object': sanitizers.DictSanitizer({
			u'identifier': sanitizers.StringSanitizer(required=True),
			u'protocol': sanitizers.ChoicesSanitizer((u'tcp', u'udp', ), required=True),
			u'portStart': sanitizers.IntegerSanitizer(minimum=1, maximum=2**16, maximum_strict=True, required=True),
			u'portEnd': sanitizers.IntegerSanitizer(minimum=1, maximum=2**16, maximum_strict=True, required=True),
			u'addressType': sanitizers.ChoicesSanitizer((u'all', u'ipv4', u'ipv6', u'specific', ), required=True),
			u'addressValue': sanitizers.StringSanitizer(default=u''),
			u'action': sanitizers.ChoicesSanitizer((u'accept', u'reject', u'drop', ), required=True),
		}),
	}, required=True))
	@decorators.multi_response
	@decorators.log
	def rules_put(self, iterator, object):
		"""Edit the specified rules:

		requests.options = [{
			'object': {
				'identifier': <str>,
				'protocol': 'tcp' | 'udp',
				'portStart': <int>,
				'portEnd': <int>,
				'addressType': 'all' | 'ipv4' | 'ipv6' | 'specific',
				'addressValue': <string>
				'action': 'accept' | 'reject' | 'drop,
			}
		}, ]
		"""
		return self._add_or_edit(iterator, object, edit=True)

	@decorators.sanitize(sanitizers.DictSanitizer({u'object': sanitizers.StringSanitizer(required=True), }, required=True))
	@decorators.multi_response
	@decorators.log
	def rules_remove(self, iterator, object):
		"""Remove the specified rules

		requests.options = [{
			'object': <string>,
		}, ]
		"""
		# Try to load firewall configuration
		try:
			firewall = backend.Firewall()
		except backend.Error as e:
			message = _(u"Could not load firewall configuration")
			MODULE.error(u"%s: %s" % (message, str(e), ))
			raise umc.modules.UMC_CommandError(message)

		for (object, ) in iterator:
			try:
				firewall.remove_rule(object)
			except backend.Error as e:
				yield {u'object': object, u'success': False, u'details': str(e), }
			else:
				yield {u'object': object, u'success': True, }
		# Try to save firewall configuration
		try:
			firewall.save()
		except backend.Error as e:
			message = _(u"Could not save firewall configuration")
			MODULE.error(u"%s: %s" % (message, str(e), ))
			raise umc.modules.UMC_CommandError(message)
