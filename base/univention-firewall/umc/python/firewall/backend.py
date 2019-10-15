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

import re

import ipaddr

import univention.config_registry as ucr
import univention.management.console as umc


_ = umc.Translation('univention-management-console-module-firewall').translate

REGEX_RULE = re.compile(
	r'^security/packetfilter'  # prefix
	r'(/package/(?P<package>[^/]+))?/'  # package rule
	r'(?P<protocol>tcp|udp)/'  # protocol
	r'(?P<port>[^/]+)/'  # port
	r'(?P<address>[^/]+)'  # address
	r'(/(?P<property>[^/]+))?')  # property (e.g. 'en')
REGEX_RULE_PORT = re.compile(
	r'^(?P<start>[0-9]+)'  # start port
	r'((:|-)(?P<end>[0-9]+))?$')  # end port
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
		self._load_configuration()

	def _load_configuration(self):
		def parse_port(string):
			(start, end, ) = REGEX_RULE_PORT.match(string).groupdict().values()
			start = int(start)
			if end:
				end = int(end)
			return (start, end, )

		def parse_boolean(key, default=None):
			if config_registry.is_true(key):
				return True
			elif config_registry.is_false(key):
				return False
			else:
				# TODO: throw an error?
				return default

		config_registry = ucr.ConfigRegistry()
		config_registry.load()

		# load global firewall settings
		self.default_policy = config_registry.get(u'security/packetfilter/defaultpolicy', u'REJECT')
		self.disabled = parse_boolean(u'security/packetfilter/disabled', False)
		self.use_packages = parse_boolean(u'security/packetfilter/use_packages', True)

		# parse all firewall related UCR variables
		rules = {}
		for (key, value, ) in config_registry.items():
			matched_rule = REGEX_RULE.match(key)
			if not matched_rule:
				continue

			rule_props = matched_rule.groupdict()
			try:
				rule = Rule(
					rule_props[u'protocol'],
					parse_port(rule_props[u'port']),
					rule_props[u'address'],
					rule_props[u'package']
				)
				# rule already exists?
				if rule.identifier in rules:
					rule = rules[rule.identifier]
				else:
					rules[rule.identifier] = rule

				# TODO: use regex instead
				# check for other rule properties
				if not rule_props[u'property']:
					# only the action remains
					rule.action = value
				else:
					rule.description[rule_props[u'property']] = value
			except Error:
				pass  # TODO
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
		if rule.identifier in self.rules:
			raise Error(_(u"Rule already exists"))
		self._rules[rule.identifier] = rule

	def remove_rule(self, identifier):
		if self._rules[identifier].package:
			raise Error(_(u"Cannot remove package rules"))
		try:
			del self._rules[identifier]
		except KeyError:
			raise Error(_(u"No such rule"))

	def save(self):
		def rule_to_dict(rule):
			prefix = u'%s/%s' % (u'security/packetfilter', rule.identifier, )
			result = {prefix: rule.action, }
			for (lang, description, ) in rule.description.items():
				result[u'%s/%s' % (prefix, lang, )] = description
			return result

		config_registry = ucr.ConfigRegistry()
		config_registry.load()

		# set global firewall settings
		bool_to_string = {True: u'true', False: u'false', }
		global_options = {
			u'security/packetfilter/defaultpolicy': self.default_policy,
			u'security/packetfilter/disabled': bool_to_string[self.disabled],
			u'security/packetfilter/use_packages': bool_to_string[self.use_packages],
		}
		ucr.handler_set(global_options)

		org_dict = {}
		for (key, value, ) in config_registry.items():
			if REGEX_RULE.match(key):
				org_dict[key] = value
		new_dict = {}
		for rule in self.rules.values():
			if rule:
				new_dict = dict(new_dict.items() + rule_to_dict(rule).items())

		diff = DictDiffer(new_dict, org_dict)
		ucr.handler_unset(diff.removed())
		changed = []
		for key in diff.changed().union(diff.added()):
			changed.append(u'%s=%s' % (key, new_dict[key]))
		ucr.handler_set(changed)


class Rule(object):

	def __init__(self, protocol, port, address, package=None, action=None):
		self._protocol = self._validate_protocol(protocol.lower())
		self._port = self._validate_port(*port)
		self._address = self._validate_address(address.lower())
		self._package = package
		self._action = None
		self._description = {}

		if action:
			self.action = action

	def __nonzero__(self):
		return bool(self.action)

	def _validate_protocol(self, protocol):
		if protocol not in (u'tcp', u'udp', ):
			raise Error(_(u"Not a valid protocol type"))
		return protocol

	def _validate_port(self, start, end=None):
		if end is None:
			end = start + 1
		if not 0 < start < end <= 2**16:
			raise Error(_(u"Not a valid port number or range"))
		return (start, end, )

	def _validate_address(self, address):
		try:
			if not REGEX_RULE_ADDRESS.match(address):
				ipaddr.IPAddress(address)
		except ValueError:
			raise Error(_(u"Not a valid IP address"))
		return address

	@property
	def protocol(self):
		return self._protocol

	@property
	def port(self):
		return self._port

	@property
	def address(self):
		return self._address

	@property
	def package(self):
		return self._package

	@property
	def identifier(self):
		(start, end, ) = self.port
		if start == (end - 1):
			port = u'%s' % (start, )
		else:
			port = u'%s:%s' % (start, end, )

		identifier = u'%s/%s/%s' % (self.protocol, port, self.address, )
		if self.package:
			identifier = u'package/%s/%s' % (self.package, identifier, )
		return identifier

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
		self.description[lang] = description

	def remove_description(self, lang):
		try:
			del self.description[lang]
		except KeyError:
			raise Error(_(u'Description not found'))


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
		return set(o for o in self._intersect if self._past_dict[o] != self._current_dict[o])

	def unchanged(self):
		return set(o for o in self._intersect if self._past_dict[o] == self._current_dict[o])
