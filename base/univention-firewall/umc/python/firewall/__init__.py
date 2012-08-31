#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: Firewall
#
# Copyright 2012 Univention GmbH
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

import re

from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import *
import univention.management.console as umc
import univention.management.console.modules.decorators as decorators
import univention.management.console.modules.sanitizers as sanitizers

import univention.management.console.modules.firewall.backend

_ = umc.Translation('univention-management-console-module-firewall').translate

class Instance(umc.modules.Base):
	@decorators.sanitize(
		category=sanitizers.ChoicesSanitizer(
			('address', 'port', 'protocol', 'description', 'package', ),
			default='address'),
		pattern=sanitizers.PatternSanitizer(default='.*')
		)
	@decorators.simple_response
	def query(self, category, pattern):
		def match(rule):
			if category != 'port': # Simple match for most cases:
				return pattern.match(getattr(rule, category))
			# Special case 'port': Check every port number
			for port in range(*rule.port):
				match = pattern.match(str(port))
				if match:
					return match
			else:
				return None

		firewall = backend.Firewall()
		rules = []
		for rule in firewall.rules.values():
			if not rule or not match(rule):
				# rule isn't complete (e.g. missing action) or
				# rule doesn't match the pattern
				continue
			entry = {}
			entry = {'name': rule.name, 'address': rule.address,
			         'port': rule.port, 'protocol': rule.protocol,
			         'package': rule.package, 'action': rule.action,
			         'description': rule.description, }
			rules.append(entry)
		return rules

	@decorators.sanitize(
		address=sanitizers.StringSanitizer(required=True),
		port_start=sanitizers.IntegerSanitizer(required=True),
		port_end=sanitizers.IntegerSanitizer(),
		protocol=sanitizers.StringSanitizer(required=True),
		action=sanitizers.StringSanitizer(required=True),
		description=sanitizers.StringSanitizer(),
		)
	@decorators.simple_response
	@decorators.log
	def add(self, address, port_start, port_end, protocol, action, description):
		try:
			rule = backend.Rule(address, (port_start, port_end, ), protocol)
			rule.action = action
			# TODO: Add the description
		except backend.Error as e:
			return {'success': False, 'message': str(e.message)}
		# TODO: try-except
		firewall = backend.Firewall()
		firewall.add_rule(rule)
		firewall.save()
		return {'success': True}

	def remove(self): # TODO
		pass

	def modify(self): # TODO
		pass
