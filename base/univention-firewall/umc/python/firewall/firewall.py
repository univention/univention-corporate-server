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

import subprocess
import re
import ipaddr

import univention.config_registry as ucr
import univention.management.console as umc
from univention.lib.i18n import Translation
from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import * # urghs...

_ = umc.Translation('univention-management-console-module-firewall').translate

REGEX_UCR_RULE = re.compile(u'^security/packetfilter' # prefix
                            u'(/package/(?P<package>[^/]+))?/' # package rule
                            u'(?P<protocol>tcp|udp)/' # protocol
                            u'(?P<port>[^/]+)/' # port
                            u'(?P<address>[^/]+)' # address
                            u'(/(?P<property>[^/]+))?') # property (e.g. 'en')

REGEX_RULE_PORT = re.compile(u'^(?P<begin>[\d]+)((:|-)(?P<end>[\d]+))?$')
REGEX_RULE_ADDRESS = re.compile(u'^(all|ipv4|ipv6)$')

class Firewall(object):
	def __init__(self):
		self._default_policy = str
		self._disabled = bool
		self._use_packages = bool
		self._rules = dict

		# initialize firewall
		self._load_config()

	def _load_config(self):
		config_registry = ucr.ConfigRegistry()
		config_registry.load()

		# set global firewall settings
		self.default_policy = config_registry.get(
			u'security/packetfilter/defaultpolicy', u'REJECT')
		self.disabled = self._to_boolean(
			config_registry.get(u'security/packetfilter/disabled', u'false'))
		self.use_packages = self._to_boolean(
			config_registry.get(u'security/packetfilter/use_packages', u'true'))

		# parse all firewall related UCR variables
		rules = {}
		for (key, value, ) in config_registry.items():
			matched_rule = REGEX_UCR_RULE.match(key)
			if not matched_rule:
				continue

			rule_props = matched_rule.groupdict()
			rule = Rule(rule_props[u'address'], rule_props[u'port'],
			            rule_props[u'protocol'], rule_props[u'package'])
			# rule already exists?
			if rule.name not in rules:
				rules[rule.name] = rule
			else:
				# get existing rule
				rule = rules[rule.name]

			# check for other rule properties
			if not rule_props[u'property']:
				# only the action remains
				rule.action = value
			elif rule_props[u'property'] == u'disabled':
				rule.disabled = self._to_boolean(value)
			else:
				rule.description[rule_props[u'property']] = value
		self._rules = rules

	def _to_boolean(self, string):
		if string.lower() in (u'true', u'yes', u'1', ):
			return True
		else:
			return False

	@property
	def disabled(self):
		return self._disabled

	@disabled.setter
	def disabled(self, flag):
		self._disabled = bool(flag)

	@property
	def use_packages(self):
		return self._use_packages

	@use_packages.setter
	def use_packages(self, flag):
		self._use_packages = bool(flag)

	@property
	def default_policy(self):
		return self._default_policy

	@default_policy.setter
	def default_policy(self, policy):
		policy = policy.upper()
		if policy in (u'DROP', u'REJECT', u'ACCEPT', ):
			self._default_policy = policy
		else:
			raise ValueError(u'Not a valid default policy')

	@property
	def rules(self):
		return self._rules

	def add_rule(self, rule):
		if isinstance(rule, Rule):
			self._rules[rule.name] = rule
		else:
			raise TypeError(u'Invalid object type')

	def remove_rule(self, name):
		# TODO: raise
		del self._rules[name]

	def save(self):
		pass


class Rule(object):
	def __init__(self, address, port, protocol, package):
		self._address = self._validate_address(address)
		self._port = self._validate_port(port)
		self._protocol = self._validate_protocol(protocol)
		self._package = package
		self._name = self._get_name()
		self._action = str()
		self._description = dict()
		self._disabled = False

	def _validate_address(self, address):
		try:
			address = address.lower()
			if not REGEX_RULE_ADDRESS.match(address):
				ipaddr.IPAddress(address)
		except ValueError:
			raise ValueError(_(u'Not a valid IP address'))
		else:
			return address

	def _validate_port(self, port):
		try:
			(begin, end, ) = REGEX_RULE_PORT.match(port).groupdict().values()
			if end:
				if begin >= end:
					raise ValueError
				return (begin, end, )
			# no port range
			return (begin, )
		except (AttributeError, ValueError):
			raise ValueError(_(u'Not a valid port number or range'))

	def _validate_protocol(self, protocol):
		protocol = protocol.lower()
		if protocol in (u'all', u'tcp', u'udp', ):
			return protocol
		else:
			raise ValueError(_(u'Not a valid protocol type'))

	def _get_name(self):
		name = u'%s/%s/%s' % (self.protocol, self.port, self.address)
		if self.package:
			name = u'package/%s/%s' % (self.package, name)
		return name

	@property
	def address(self):
		return self._address

	@property
	def port(self):
		return ':'.join([str(port) for port in self._port])

	@property
	def protocol(self):
		return self._protocol

	@property
	def action(self):
		return self._action

	@action.setter
	def action(self, action):
		action = action.upper()
		if action in (u'DROP', u'REJECT', u'ACCEPT', ):
			self._action = action
		else:
			raise ValueError(u'Not a valid action')

	@property
	def description(self):
		return self._description

	@property
	def package(self):
		return self._package

	@property
	def name(self):
		return self._name

	@property
	def disabled(self):
		return self._disabled

	@disabled.setter
	def disabled(self, flag):
		self._disabled = bool(flag)

	def add_description(self, lang, description):
		# TODO: ValueError
		self._description[lang] = description

	def remove_description(self, lang):
		# TODO: ValueError
		if lang in self._description:
			del self._description[lang]

	def get_variables(self):
		if not self.action:
			# don't return incomplete rules
			return []
		variables = []
		variables.append(u'%s=%s' % (self.name, self.action, ))

		for (lang, description, ) in self.description.items():
			variables.append(u'%s/%s=%s' % (self.name, lang, description, ))

		variables.append(u'%s/disabled=%s' % (self.name,
		                                      str(self.disabled).lower(), ))

		return variables
