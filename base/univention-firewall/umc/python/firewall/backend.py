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

import ipaddr
import re

from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import *
import univention.config_registry as ucr
import univention.management.console as umc

_ = umc.Translation('univention-management-console-module-firewall').translate

REGEX_RULE = re.compile(r'^security/packetfilter' # prefix
                        r'(/package/(?P<package>[^/]+))?/' # package rule
                        r'(?P<protocol>tcp|udp)/' # protocol
                        r'(?P<port>[^/]+)/' # port
                        r'(?P<address>[^/]+)' # address
                        r'(/(?P<property>[^/]+))?') # property (e.g. 'en')
REGEX_RULE_PORT = re.compile(r'^(?P<start>[0-9]+)' # start port
                             r'((:|-)(?P<end>[0-9]+))?$') # end port
REGEX_RULE_ADDRESS = re.compile(r'^(all|ipv4|ipv6)$')

class Error(Exception):
	pass


class Firewall(object):
	def __init__(self):
		self._default_policy = None
		self._disabled = None
		self._use_packages = None
		self._rules = {}

		# initialize firewall
		self._load_config()

	def _load_config(self):
		def parse_port(string):
			(start, end, ) = REGEX_RULE_PORT.match(string).groupdict().values()
			start = int(start)
			if end:
				end = int(end)
			return (start, end, )

		def parse_boolean(string):
			string = string.lower()
			if string in (u'true', u'yes', u'on', u'1', ):
				return True
			elif string in (u'false', u'no', u'off', u'0', ):
				return False
			else:
				return None

		config_registry = ucr.ConfigRegistry()
		config_registry.load()

		# set global firewall settings
		self.default_policy = config_registry.get( # TODO: logging?
			u'security/packetfilter/defaultpolicy', u'REJECT')
		self.disabled = parse_boolean(
			config_registry.get(u'security/packetfilter/disabled', 'False'))
		self.use_packages = parse_boolean(
			config_registry.get(u'security/packetfilter/use_packages', 'True'))

		# parse all firewall related UCR variables
		rules = {}
		for (key, value, ) in config_registry.items():
			matched_rule = REGEX_RULE.match(key)
			if not matched_rule:
				continue

			rule_props = matched_rule.groupdict()
			try:
				rule = Rule(rule_props[u'address'],
				            parse_port(rule_props[u'port']),
				            rule_props[u'protocol'],
				            rule_props[u'package'])
				# rule already exists?
				if rule.name in rules:
					rule = rules[rule.name]
				else:
					rules[rule.name] = rule

				# check for other rule properties
				if not rule_props[u'property']:
					# only the action remains
					rule.action = value
				else:
					rule.description[rule_props[u'property']] = value
			except Error as err:
				pass # TODO: logging
			else:
				self._rules = rules

	@property
	def disabled(self):
		return self._disabled

	@disabled.setter
	def disabled(self, disabled):
		self._disabled = bool(disabled)

	@property
	def use_packages(self):
		return self._use_packages

	@use_packages.setter
	def use_packages(self, use_packages):
		self._use_packages = bool(use_packages)

	@property
	def default_policy(self):
		return self._default_policy

	@default_policy.setter
	def default_policy(self, policy):
		policy = policy.upper()
		if policy not in (u'DROP', u'REJECT', u'ACCEPT', ):
			raise Error(_(u"Not a valid default policy"))
		self._default_policy = policy

	@property
	def rules(self):
		return self._rules

	def add_rule(self, rule):
		if rule.name in self.rules:
			raise Error(_(u"Rule already exists"))
		self._rules[rule.name] = rule

	def remove_rule(self, name):
		try:
			del self._rules[name]
		except KeyError:
			raise Error(_(u"No such rule"))

	def save(self):
		config_registry = ucr.ConfigRegistry()
		config_registry.load()

		org_dict = {}
		for (key, value, ) in config_registry.items():
			if REGEX_RULE.match(key):
				org_dict[key] = value
		new_dict = {}
		for rule in self.rules.values():
			if rule:
				new_dict = dict(new_dict.items() + rule.dict.items())

		diff = DictDiffer(new_dict, org_dict)
		ucr.handler_unset(diff.removed())
		changed = []
		for key in diff.changed().union(diff.added()):
			changed.append(u'%s=%s' % (key, new_dict[key]))
		ucr.handler_set(changed)


class Rule(object):
	def __init__(self, address, port, protocol, package=None):
		self._address = self._validate_address(address.lower())
		self._port = self._validate_port(*port)
		self._protocol = self._validate_protocol(protocol.lower())
		self._package = package # TODO: validate package name
		self._action = ''
		self._description = {}

	def __nonzero__(self):
		return bool(self.action)

	def _validate_address(self, address):
		try:
			if not REGEX_RULE_ADDRESS.match(address):
				ipaddr.IPAddress(address)
		except ValueError:
			raise Error(_(u"Not a valid IP address"))
		return address

	def _validate_port(self, start, end=None):
		if end is None:
			end = start + 1
		if not 0 < start < end <= 2**16:
			raise Error(_(u"Not a valid port number or range"))
		return (start, end, )

	def _validate_protocol(self, protocol):
		if protocol not in (u'all', u'tcp', u'udp', ):
			raise Error(_(u"Not a valid protocol type"))
		return protocol

	@property
	def address(self):
		return self._address

	@property
	def port(self):
		return self._port

	@property
	def protocol(self):
		return self._protocol

	@property
	def package(self):
		return self._package

	@property
	def name(self):
		(start, end, ) = self.port
		if start == (end - 1):
			port = start
		else:
			port = u'%s:%s' % (start, end, )

		name = u'%s/%s/%s' % (self.protocol, port, self.address, )
		if self.package:
			name = u'package/%s/%s' % (self.package, name, )
		return name

	@property
	def action(self):
		return self._action

	@action.setter
	def action(self, action):
		action = action.upper()
		if action not in (u'DROP', u'REJECT', u'ACCEPT', ):
			raise Error(_(u"Not a valid action"))
		self._action = action

	@property
	def description(self):
		return self._description

	def add_description(self, lang, description):
		lang = lang.lower()
		if lang not in (u'en', u'de', ):
			raise Error(_(u"Not a valid description language"))
		self.description[lang] = description

	def remove_description(self, lang):
		del self.description[lang]

	@property
	def dict(self):
		prefix = u'%s/%s' % (u'security/packetfilter', self.name, )
		result = {prefix: self.action, }
		for (lang, description, ) in self.description.items():
			result[u'%s/%s' % (prefix, lang, )] = description
		return result


class DictDiffer(object):
	def __init__(self, current_dict, past_dict):
		self._current_dict = current_dict
		self._past_dict = past_dict
		self._set_current = set(current_dict.keys())
		self._set_past = set(past_dict.keys())
		self._intersect = self._set_current.intersection(self._set_past)

	def added(self):
		return self._set_current - self._intersect

	def removed(self):
		return self._set_past - self._intersect

	def changed(self):
		return set(o for o in self._intersect
		           if self._past_dict[o] != self._current_dict[o])

	def unchanged(self):
		return set(o for o in self._intersect
		           if self._past_dict[o] == self._current_dict[o])
