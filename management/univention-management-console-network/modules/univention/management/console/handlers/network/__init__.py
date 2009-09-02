#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: network configuration
#
# Copyright (C) 2008-2009 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import univention.management.console as umc
import univention.management.console.handlers as umch
import univention.management.console.dialog as umcd
import univention.management.console.tools as umct
import univention.management.console.protocol as umcp

import univention.debug as ud

import os

import notifier.popen

import univention.config_registry as ucr
import univention.service_info as usi

import re

_ = umc.Translation('univention.management.console.handlers.network').translate

name = 'network'
icon = 'network/module'
short_description = _('Networking')
long_description = _('Configure networking parameters')
categories = [ 'system', 'all' ]

command_description = {
	'network/overview': umch.command(
		short_description = _('Overview'),
		long_description = _('Overview'),
		method = 'network_overview',
		values = { },
		startup = True,
		),
	'network/addinterface': umch.command(
		short_description = _('Add interface'),
		long_description = _('Add interface'),
		method = 'network_addinterface',
		values = {},
		),
	'network/interface': umch.command(
		short_description = _('Configure interface'),
		long_description = _('Configure interface'),
		method = 'network_interface',
		values = { },
		),
	'network/gateway': umch.command(
		short_description = _('Configure gateway'),
		long_description = _('Configure gateway'),
		method = 'network_gateway',
		values = { },
		),
	'network/nameserver': umch.command(
		short_description = _('Configure nameservers'),
		long_description = _('Configure nameservers'),
		method = 'network_nameserver',
		values = { },
		),
	'network/dnsforwarder': umch.command(
		short_description = _('Configure DNS forwarders'),
		long_description = _('Configure DNS forwarders'),
		method = 'network_dnsforwarder',
		values = { },
		),
	'network/proxyhttp': umch.command(
		short_description = _('Configure HTTP proxy'),
		long_description = _('Configure HTTP proxy'),
		method = 'network_proxyhttp',
		values = { },
		),
	'network/proxyusername': umch.command(
		short_description = _('Configure proxy username'),
		long_description = _('Configure proxy username'),
		method = 'network_proxyusername',
		values = { },
		),
	'network/proxypassword': umch.command(
		short_description = _('Configure proxy password'),
		long_description = _('Configure proxy password'),
		method = 'network_proxypassword',
		values = { },
		),
}

subnetmask_prefix_map = [(  0,  0,  0,  0),
			 (128,  0,  0,  0),
			 (192,  0,  0,  0),
			 (224,  0,  0,  0),
			 (240,  0,  0,  0),
			 (248,  0,  0,  0),
			 (252,  0,  0,  0),
			 (254,  0,  0,  0),
			 (255,  0,  0,  0),
			 (255,128,  0,  0),
			 (255,192,  0,  0),
			 (255,224,  0,  0),
			 (255,240,  0,  0),
			 (255,248,  0,  0),
			 (255,252,  0,  0),
			 (255,254,  0,  0),
			 (255,255,  0,  0),
			 (255,255,128,  0),
			 (255,255,192,  0),
			 (255,255,224,  0),
			 (255,255,240,  0),
			 (255,255,248,  0),
			 (255,255,252,  0),
			 (255,255,254,  0),
			 (255,255,255,  0),
			 (255,255,255,128),
			 (255,255,255,192),
			 (255,255,255,224),
			 (255,255,255,240),
			 (255,255,255,248),
			 (255,255,255,252),
			 (255,255,255,254),
			 (255,255,255,255),]

def subnetmask_to_prefix(subnetmask):
	return subnetmask_prefix_map.index(subnetmask)

def prefix_to_subnetmask(prefix):
	return subnetmask_prefix_map[prefix]

def standard_broadcast_address(ip, prefix):
	if prefix >= 31:
		return None
	broadcast = [0,0,0,0] # will be filled in the for-loop
	mask = subnetmask_prefix_map[prefix]
	for i in xrange(4):
		broadcast[i] = ip[i] | (255 & ~mask[i])
	return tuple(broadcast)

def standard_network_address(ip, prefix):
	if prefix >= 31:
		return None
	network = [0,0,0,0] # will be filled in the for-loop
	mask = subnetmask_prefix_map[prefix]
	for i in xrange(4):
		network[i] = ip[i] & mask[i]
	return tuple(network)

def ip_matches_cidr(ip, cidr):
	(prefix, length) = cidr
	while length >= 8:
		if not ip[0] == prefix[0]:
			return False
		ip     =     ip[1:]
		prefix = prefix[1:]
		length = length - 8
	bitmask = 0xff00 >> length & 0xff
	if not ip[0] & bitmask == prefix[0]:
		return False
	return True

def DEBUG_ip_to_bin(ip):
	def bin(integer):
		if type(integer) == type(1) and integer > 0:
			if integer % 2:
				return bin(integer >> 1) + '1'
			else:
				return bin(integer >> 1) + '0'
		else:
			return ''
	return '.'.join(map(lambda x: x.rjust(8,'0'), map(bin, ip)))

def ip_to_string(ip):
	if ip:
		return '.'.join(map(str, ip)) #+ ' ' + DEBUG_ip_to_bin(ip)

def string_to_ip(string):
	parts = string.split('.')
	if len(parts) != 4:
		return None
	parts = map(lambda x: x.strip(), parts)
	octets = []
	for part in parts:
		try:
			octet = int(part)
		except:
			return None
		if octet < 0 or octet > 255:
			return None
		octets.append(octet)
	return tuple(octets)

def string_to_dn(string):
	parts = string.rstrip('.').split('.')
	parts = map(lambda x: x.strip(), parts)
	for part in parts:
		if len(part) == 0 or len(part) > 63: # Labels must be 63 characters or less
			return None
		if not part[0] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz': # must start with a letter
			return None
		if not part[-1] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789': # end with letter or digit
			return None
		for c in part[1:-1]:
			if not c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-': # have as interior characters only letters, digits, and hyphen
				return None
	return tuple(parts)

def dn_to_string(dn):
	if dn:
		return '.'.join(dn)

def hex_to_int(hex):
	hex = hex.decode('hex')
	x = 0
	for i in xrange(len(hex)):
		x <<= 8
		x += ord(hex[i])
	return x

def int_to_hex(i):
	string = ''
	while i > 0:
		string = chr(i % 256) + string
		i >>= 8
	return string.encode('hex').lstrip('0')

def parse_proxy_url(string):
	string = string.strip()
	errors = []
	if string.lower().startswith('http://'): # remove leading 'http://' if it exists
		string = string[7:].strip()
	string = string.rstrip('/') # remove trailing '/'
	# split into host and port
	string = string.rsplit(':', 1)
	host = string[0]
	if len(string) == 2:
		port = string[1]
	else:
		port = None
	if host[0] in '0123456789': # IPv4
		ip = string_to_ip(host)
		if not ip:
			errors.append(_('Invalid IP address "%s"') % host)
		else:
			host = ip_to_string(ip)
	elif host[0] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz':
		dn = string_to_dn(host)
		if not dn:
			errors.append(_('Invalid domain name "%s"') % host)
		else:
			host = dn_to_string(dn)
	else:
		errors.append(_('Invalid host "%s"') % host)
	if port is not None:
		try:
			port = int(port)
		except:
			host = None
			port = None
			errors.append(_('Invalid port "%s"') % port)
	if port is not None:
		if port < 1 or port > 0xffff:
			errors.append(_('Port must be within 1 and 65535 and thus cannot be %d') % port)
	if not errors:
		if not type(port) == type(1):
			port = 80
		ret = 'http://%s:%d' % (host, port)
		return ret
	else:
		return errors

def parse_proxy_username(string):
	return str(string)

def parse_proxy_password(string):
	return str(string)

def merge_config(config_a, config_b):
	config_new = {}
	for key in config_a:
		if type(config_a[key]) == type({}):
			config_new[key] = merge_config(config_a[key], config_b.get(key, {}))
		else:
			config_new[key] = config_b.get(key, config_a[key])
	for key in config_b:
		if key not in config_a:
			config_new[key] = config_b[key]
	return config_new


class handler( umch.simpleHandler ):
	def __init__( self ):
		global command_description
		umch.simpleHandler.__init__( self, command_description )
		self.existing_interfaces = []
		for interface in map(lambda s: s.split(':',1)[0], open("/proc/net/dev").read().replace(' ','').split('\n')[2:-1]):
			if re.match('^eth[0-3]$', interface):
				self.existing_interfaces.append(interface)
		self.cr = ucr.ConfigRegistry()
		self.cr.load()
		self.actual_config = {'interfaces': { },}
		self.staged_config = {'interfaces': { },}
		# Initialize self.actual_config and self.staged_config
		for i in xrange(4):
			for j in [None,] + range(4):
				if j is None:
					interface = 'eth%d' % (i)
				else:
					interface = 'eth%d:%d' % (i, j)
				self.actual_config['interfaces'][interface] = {'ip_addr': (0,0,0,0),'prefix': 0, 'enabled': False}
				if 'interfaces/%s/address' % interface in self.cr.keys(): # this means the interface is active
					ip_addr = string_to_ip(self.cr['interfaces/%s/address' % interface])
					if ip_addr is not None:
						self.actual_config['interfaces'][interface]['ip_addr'] = ip_addr
					self.actual_config['interfaces'][interface]['enabled'] = True
				if 'interfaces/%s/netmask' % interface in self.cr.keys():
					prefix = string_to_ip(self.cr['interfaces/%s/netmask' % interface])
					if prefix in subnetmask_prefix_map:
						prefix = subnetmask_to_prefix(prefix)
						self.actual_config['interfaces'][interface]['prefix'] = prefix
				self.staged_config['interfaces'][interface] = {}
		for ucr_var in ('gateway',
				'nameserver1',
				'nameserver2',
				'nameserver3',
				'dns/forwarder1',
				'dns/forwarder2',
				'dns/forwarder3',):
			if ucr_var in self.cr.keys():
				self.actual_config[ucr_var] = string_to_ip(self.cr[ucr_var])
			else:
				self.actual_config[ucr_var] = None
		for ucr_var in ('proxy/http',
				'proxy/username',
				'proxy/password',):
			if ucr_var in self.cr.keys():
				self.actual_config[ucr_var] = self.cr[ucr_var]
			else:
				self.actual_config[ucr_var] = None

	def network_overview( self, object ):
		config = merge_config(self.actual_config, self.staged_config)

		if object.options.get('action', None) == 'apply':
			# fill blanks
			if config['nameserver2'] is None and config['nameserver3'] is not None:
				config['nameserver2'] = config['nameserver3']
				config['nameserver3'] = None
			if config['nameserver1'] is None and config['nameserver2'] is not None:
				config['nameserver1'] = config['nameserver2']
				config['nameserver2'] = config['nameserver3']
				config['nameserver3'] = None
			if config['dns/forwarder2'] is None and config['dns/forwarder3'] is not None:
				config['dns/forwarder2'] = config['dns/forwarder3']
				config['dns/forwarder3'] = None
			if config['dns/forwarder1'] is None and config['dns/forwarder2'] is not None:
				config['dns/forwarder1'] = config['dns/forwarder2']
				config['dns/forwarder2'] = config['dns/forwarder3']
				config['dns/forwarder3'] = None
			vars_to_set = []
			vars_to_unset = []
			for ucr_var in ('gateway',
							'nameserver1',
							'nameserver2',
							'nameserver3',
							'dns/forwarder1',
							'dns/forwarder2',
							'dns/forwarder3',):
				if config[ucr_var] is not None:
					vars_to_set.append("%s=%s" % (ucr_var, ip_to_string(config[ucr_var])))
			for ucr_var in ('proxy/http',
							'proxy/username',
							'proxy/password',):
				if config[ucr_var] is not None:
					vars_to_set.append("%s=%s" % (ucr_var, config[ucr_var]))
			for interface in config['interfaces']:
				if config['interfaces'][interface]['enabled']:
					ip_addr = config['interfaces'][interface]['ip_addr']
					prefix = config['interfaces'][interface]['prefix']
					vars_to_set.append('interfaces/%s/address=%s' % (interface.replace(':','_'), ip_to_string(ip_addr)))
					vars_to_set.append('interfaces/%s/netmask=%s' % (interface.replace(':','_'), ip_to_string(prefix_to_subnetmask(prefix))))
					vars_to_set.append('interfaces/%s/network=%s' % (interface.replace(':','_'), ip_to_string(standard_network_address(ip_addr, prefix))))
					vars_to_set.append('interfaces/%s/broadcast=%s' % (interface.replace(':','_'), ip_to_string(standard_broadcast_address(ip_addr, prefix))))
					vars_to_unset.append('interfaces/%s/type' % (interface.replace(':','_'))) # unset type => no dhcp
				else:
					vars_to_unset.append('interfaces/%s/address' % (interface.replace(':','_')))
					vars_to_unset.append('interfaces/%s/netmask' % (interface.replace(':','_')))
					vars_to_unset.append('interfaces/%s/network' % (interface.replace(':','_')))
					vars_to_unset.append('interfaces/%s/broadcast' % (interface.replace(':','_')))
					vars_to_unset.append('interfaces/%s/type' % (interface.replace(':','_')))
			ucr.handler_unset(vars_to_unset)
			ucr.handler_set(vars_to_set)
			self.finished(object.id(), None, report = _('The settings have been applied.'), success = True)
			return
		elif object.options.get('action', None) == 'revert':
			self.staged_config = {'interfaces': { },}
			for i in xrange(4):
				for j in [None,] + range(4):
					if j is None:
						interface = 'eth%d' % (i)
					else:
						interface = 'eth%d:%d' % (i, j)
					self.staged_config['interfaces'][interface] = {}
			config = merge_config(self.actual_config, self.staged_config)
		###
		# Network interfaces
		###
		interface_list = umcd.List()
		interface_list.add_row([umcd.Text(_("Click on the interface's name to change its settings.")),])
		for if_name in sorted(config['interfaces'].keys()):
			if not config['interfaces'][if_name]['enabled']:
				continue
			if_config = config['interfaces'][if_name]
			cmd = umcp.SimpleCommand('network/interface', {'interface': if_name},
						 startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False, startup_format = _('Configure interface %s') % if_name)
			interface_list.add_row([
					umcd.Button(if_name, 'network/interface', actions = [ umcd.Action(cmd) ]),
					umcd.Text(ip_to_string(if_config['ip_addr'])),
					])
		# startup_dialog == True ==> Close on error, startup_dialog == False ==> Stay open
		cmd = umcp.SimpleCommand('network/addinterface', startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False)
		interface_list.add_row([umcd.Button(_("Add interface"), 'actions/add', actions = [ umcd.Action(cmd) ])])

		###
		# Routing
		###
		routing_list = umcd.List()
		routing_list.add_row([umcd.Text(_("Click on an entry's name to change it.")),])
		cmd = umcp.SimpleCommand('network/gateway',
					 startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False, startup_format = _('Configure gateway'))
		routing_list.add_row([
				umcd.Button(_('Gateway:'), 'network/routing', actions = [ umcd.Action(cmd) ] ),
				umcd.Text(str(ip_to_string(config['gateway']))), #also call str() because gateway may be <None>
				])

		###
		# Name resolution
		###
		cmd = umcp.SimpleCommand('network/nameserver', startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False, startup_format = _('Configure nameservers'))
		nameserver_list = [umcd.Button(_('Nameserver:'), 'network/nameserver', actions = [ umcd.Action(cmd) ])]
		for key in ('nameserver1','nameserver2','nameserver3'):
			if config[key]:
				nameserver_list.append(umcd.Text(ip_to_string(config[key])))
		if len(nameserver_list) == 1: #contains no entries
			nameserver_list.append(umcd.Text(_("None")))

		cmd = umcp.SimpleCommand('network/dnsforwarder', startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False, startup_format = _('Configure DNS forwarders'))
		forwarder_list = [umcd.Button(_('DNS forwarder:'), 'network/nameserver', actions = [ umcd.Action(cmd) ])]
		for key in ('dns/forwarder1','dns/forwarder2','dns/forwarder3'):
			if config[key]:
				forwarder_list.append(umcd.Text(ip_to_string(config[key])))
		if len(forwarder_list) == 1: # contains no entries
			forwarder_list.append(umcd.Text(_("None")))

		nameresolution_list = umcd.List()
		nameresolution_list.add_row([umcd.Text(_("Click on an entry's name to change it.")),])
		nameresolution_list.add_row(nameserver_list)
		nameresolution_list.add_row(forwarder_list)

		###
		# Proxy
		###
		proxy_list = umcd.List()
		proxy_list.add_row([umcd.Text(_("Click on an entry's name to change it.")),])

		cmd = umcp.SimpleCommand('network/proxyhttp', startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False, startup_format = _('Configure HTTP proxy'))
		if config['proxy/http']:
			proxyhttp = str(config['proxy/http'])
		else:
			proxyhttp = _("None")
		proxy_list.add_row([umcd.Button(_("HTTP proxy:"), 'network/proxy', actions = [ umcd.Action(cmd) ]), umcd.Text(proxyhttp)])

		cmd = umcp.SimpleCommand('network/proxyusername', startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False, startup_format = _('Configure proxy username'))
		if config['proxy/username']:
			proxyusername = str(config['proxy/username'])
		else:
			proxyusername = _("None")
		proxy_list.add_row([umcd.Button(_("proxy username:"), 'network/proxy', actions = [ umcd.Action(cmd) ]), umcd.Text(proxyusername)])

		if config['proxy/password']:
			password = '*' * len(config['proxy/password'])
		else:
			password = _("None")
		cmd = umcp.SimpleCommand('network/proxypassword', startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False, startup_format = _('Configure proxy password'))
		proxy_list.add_row([umcd.Button(_("proxy password:"), 'network/proxy', actions = [ umcd.Action(cmd) ]), umcd.Text(password)])

		###
		# [Put everything together]
		###
		interface_frame = umcd.Frame([interface_list,], _("Network interfaces"))
		nameresolution_frame = umcd.Frame([nameresolution_list], _('Name resolution'))
		routing_frame = umcd.Frame([routing_list], _("Routing"))
		proxy_frame = umcd.Frame([proxy_list], _("Proxy"))

		action_buttons = umcd.List()
		cmd_apply  = umcp.SimpleCommand('network/overview', {'action': 'apply' }, startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False)
		cmd_revert = umcp.SimpleCommand('network/overview', {'action': 'revert'}, startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False)
		action_buttons.add_row([
				umcd.Button(_("Apply changes"),
					    'actions/ok',
					    actions = [ umcd.Action(cmd_apply ) ]
					    ),
				umcd.Button(_("Revert changes"),
					    'actions/refresh',
					    actions = [ umcd.Action(cmd_revert) ]
					    ),
				])
		res = umcp.Response(object)
		res.dialog = [interface_frame, routing_frame, nameresolution_frame, proxy_frame, action_buttons]
		self.finished( object.id(), res)

	def network_addinterface(self, object):
		if_name = str(object.options.get('if_name', ''))
		config = merge_config(self.actual_config, self.staged_config)
		errors = []
		if object.options.get('action', None) == 'create':
			if not re.match('^eth[0-3](:[0-3])?$', if_name):
				self.finished(object.id(), None, report = _('"%s" is not a valid interface name!') % if_name, success = False)
				return
			elif if_name in config['interfaces'] and config['interfaces'][if_name]['enabled']:
				self.finished(object.id(), None, report = _('There is already an interface named "%s" - please reconfigure that instead.') % if_name, success = False)
				return
			elif if_name.split(':', 1)[0] not in self.existing_interfaces:
				self.finished(object.id(), None,
					      report = _('There is no hardware interface named "%s". Available hardware interfaces are: %s' % (if_name, ', '.join(self.existing_interfaces))),
					      success = False)
			else:
				if not 'interfaces' in self.staged_config:
					self.staged_config['interfaces'] = {}
				self.staged_config['interfaces'][if_name] = {
					'ip_addr': (0,0,0,0),
					'prefix': 0,
					'enabled': True,
					}
				self.finished(object.id(), None, report = _('The interface "%s" has been added.') % if_name, success = True)
				return
		res = umcp.Response(object)
		res.dialog = []
		interface_list = umcd.List()
		interface_list.add_row([umcd.Text(_('Please enter the name of the new interface you whish to configure:'))])
		inpt_interfacename = umcd.TextInput(('if_name', umc.String(_('Interface name'), required = False)), if_name)
		interface_list.add_row([inpt_interfacename])
		interface_list.add_row([umcd.Text(_('Valid names are "eth0" to "eth3" for hardware interfaces and "ethX:0" to "ethX:3" for virtual interfaces on hardware interface "ethX".'))])
		interface_frame = umcd.Frame([interface_list],_('Add a new interface'))
		button_list = umcd.List()
		cmd = umcp.SimpleCommand('network/addinterface', {'interface': object.options.get('if_name',''), 'action': 'create'},
					 startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False)
		button_list.add_row([umcd.Button(_("Add interface"), 'actions/ok', actions = [ umcd.Action(cmd, [inpt_interfacename.id()]) ]), umcd.CloseButton()])
		res.dialog.append(interface_frame)
		res.dialog.append(button_list)
		self.finished(object.id(), res)

	def network_interface(self, object):
		interface = object.options.get('interface', None)
		if not interface:
			self.finished(object.id(), None, report = "...---...", success = False)
			return
		errors = []
		warnings = []
		changed = set()
		reset = set()
		erroneous = set()
		dubious = set()
		option_names = {'ip_addr': _('IP address'),
				'subnetmask': _('Subnet mask'),
				}
		config = merge_config(self.actual_config, self.staged_config)
		if object.options.get('action', None) == 'store':
			newconfig = {}
			for option in ('ip_addr','subnetmask'):
				value = object.options.get(option, None)
				if value is None: # user emptied the field
					if option in ('ip_addr'):
						if config['interfaces'][interface][option] != None:
							newconfig[option] = None
					elif option in ('subnetmask'):
						if config['interfaces'][interface]['prefix'] != None:
							newconfig['prefix'] = None
				if type(value) in (type(''), type(u'')): # user entered something in (or did not change) the field
					newvalue = string_to_ip(value) # try to parse IP address
					if newvalue is None:
						errors.append(_('Invalid IP address (%(value)s) in "%(option)s"') % {'option': option_names[option], 'value': value})
						if option == 'subnetmask':
							erroneous.add('prefix')
						else:
							erroneous.add(option)
						continue
					else:
						value = newvalue
				if type(value) == type( () ): # IP address was parsed successfully
					if option in ('ip_addr'):
						if ip_matches_cidr(value, ((0,0,0,0),8)):
							errors.append(_('You cannot assign an IP address from this range! (0.0.0.0-0.255.255.255)'))
							erroneous.add(option)
						if ip_matches_cidr(value, ((127,0,0,0),8)):
							errors.append(_('You cannot assign a loopback IP address to an interface! (127.0.0.0-127.255.255.255)'))
							erroneous.add(option)
						if ip_matches_cidr(value, ((169,254,0,0),16)):
							errors.append(_('The IP address %s is reserved for link-local/auto-configuration addresses. (169.254.0.0-169.254.255.255)') % ip_to_string(value))
							erroneous.add(option)
						if ip_matches_cidr(value, ((192,0,2,0),24)):
							errors.append(_('The IP address %s is reserved for use in documentation and examples. (192.0.2.0-192.0.2.255)') % ip_to_string(value))
							erroneous.add(option)
						if ip_matches_cidr(value, ((224,0,0,0),4)):
							errors.append(_('You cannot assign a multicast IP address to an interface! (224.0.0.0-239.255.255.255)'))
							erroneous.add(option)
						if ip_matches_cidr(value, ((240,0,0,0),4)):
							if value == (255,255,255,255):
								errors.append(_('You cannot assign the "limited broadcast" IP address to an interface! (255.255.255.255)'))
								erroneous.add(option)
							else:
								errors.append(_('You cannot assign a reserved IP address to an interface! (240.0.0.0-255.255.255.255)'))
								erroneous.add(option)
#TODO						for if_name in sorted(config['interfaces'].keys()):
#check if this						if if_name != interface and if_name[:4] == interface[:4]: # ethX == ethX:*
#check makes							if config['interfaces'][if_name]['ip_addr'] == value:
#sense									errors.append(_('You cannot assign the same IP address to one hardware interface twice!'))
#TODO									erroneous.add(option)
					if option in ('subnetmask'):
						if value in subnetmask_prefix_map:
							value = subnetmask_prefix_map.index(value)
							option = 'prefix'
						else:
							errors.append(_('Invalid %(option)s: "%(value)s"') % {'option': option_names[option], 'value': ip_to_string(value)})
							erroneous.add(option)
							continue
					if config['interfaces'][interface][option] != value:
						newconfig[option] = value
			if not errors and newconfig:
				if not 'interfaces' in self.staged_config:
					self.staged_config['interfaces'] = {}
				if not interface in self.staged_config['interfaces']:
					self.staged_config['interfaces'][interface] = {}
				for (key, value) in newconfig.items():
					if value is None:
						if key in self.staged_config['interfaces'][interface]:
							del self.staged_config['interfaces'][interface][key]
							reset.add(key)
					else:
						if key in self.staged_config['interfaces'][interface] and value == self.actual_config['interfaces'][interface][key]:
							del self.staged_config['interfaces'][interface][key]
							reset.add(key)
						else:
							self.staged_config['interfaces'][interface][key] = value
							changed.add(key)
				config = merge_config(self.actual_config, self.staged_config)
		elif object.options.get('action', None) == "remove":
			self.staged_config['interfaces'][interface]['enabled'] = False
			self.finished(object.id(), None, report = _('The interface "%s" has been marked for deletion.') % interface, success = True)
			return

		###
		# Generate dialog
		###
		if not errors:
			ipaddress = config['interfaces'][interface]['ip_addr']
			if ip_matches_cidr(ipaddress, ((198,18,0,0),15)):
				warnings.append(_("This interface's IP address is reserved for use in benchmarking-activities. (198.18.0.0-198.18.127.255)"))
				dubious.add('ip_addr')
			if ip_matches_cidr(ipaddress, ((192,88,99,0),24)):
				warnings.append(_("This interface's IP address is reserved for use in 6to4 anycast relays. (192.88.99.0-192.88.99.255)"))
				dubious.add('ip_addr')
			if not (ip_matches_cidr(ipaddress, ((10,0,0,0),8)) or
				ip_matches_cidr(ipaddress, ((172,16,0,0),12)) or
				ip_matches_cidr(ipaddress, ((192,168,0,0),16))):
				warnings.append(_("This interface's IP address does not come from the address space for private networks (10.0.0.0-10.255.255.255 172.16.0.0-172.31.255.255 192.168.0.0-192.168.255.255)"))
				dubious.add('ip_addr')
			prefix = config['interfaces'][interface]['prefix']
			for if_name in sorted(config['interfaces'].keys()):
				if not config['interfaces'][if_name]['enabled']:
					continue
				if if_name != interface and config['interfaces'][if_name]['ip_addr'] == ipaddress:
					warnings.append(_('This interface\'s IP address is the same as the IP address of interface "%s"') % if_name)
					dubious.add('ip_addr')
			inpt_ipaddress  = umcd.TextInput((   'ip_addr', umc.String(_('IP address'),  required = False)), ip_to_string(ipaddress))
			inpt_subnetmask = umcd.TextInput(('subnetmask', umc.String(_('Subnet mask'), required = False)), ip_to_string(prefix_to_subnetmask(prefix)))
		else:
			inpt_ipaddress  = umcd.TextInput((   'ip_addr', umc.String(_('IP address'),  required = False)), object.options.get('ip_addr'))
			inpt_subnetmask = umcd.TextInput(('subnetmask', umc.String(_('Subnet mask'), required = False)), object.options.get('subnetmask'))
		interface_list = umcd.List( )
		interface_list.add_row([umcd.Fill(2, text = _("To reset a value to the current configuration remove the IP address from that field."))])
		for (key, element) in (('ip_addr',inpt_ipaddress),
				       ('prefix', inpt_subnetmask),):
			tmplist = [ element ]
			if key in changed:
				tmplist.append(umcd.Text(_('Change recorded.')))
			elif key in reset:
				tmplist.append(umcd.Text(_('Reset to current value.')))
			if key in erroneous:
				tmplist.append(umcd.Image('network/error', umct.SIZE_SMALL))
			elif key in dubious:
				tmplist.append(umcd.Image('network/warning', umct.SIZE_SMALL))
			interface_list.add_row(tmplist)
		button_list = umcd.List()
		cmd = umcp.SimpleCommand('network/interface', {'interface': interface, 'action': 'store' }, startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False)
		cmd_del = umcp.SimpleCommand('network/interface', {'interface': interface, 'action': 'remove' }, startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False)
		button_list.add_row([
				umcd.Button(_('Update settings'),
					    'actions/ok',
					    actions = [umcd.Action(cmd, [
								inpt_ipaddress.id(),
								inpt_subnetmask.id(),
								])],
					    close_dialog = False,
					    ),
				umcd.CloseButton(),
				umcd.Button(_("Delete interface"),
					    'actions/remove',
					    actions = [umcd.Action(cmd_del, [])],
					    close_dialog = True,
					    ),
				])
		interface_frame = umcd.Frame([interface_list], _('Configure interface %s') % str(object.options.get('interface','')))
		res = umcp.Response( object )
		res.dialog = []
		if errors or warnings:
			msg_list = umcd.List()
			for error in errors:
				img = umcd.Image('network/error', umct.SIZE_SMALL)
				txt = umcd.Text(error)
				msg_list.add_row([img, txt])
			for warning in warnings:
				img = umcd.Image('network/warning', umct.SIZE_SMALL)
				txt = umcd.Text(warning)
				msg_list.add_row([img, txt])
			res.dialog.append(msg_list)
		res.dialog.append(interface_frame)
		res.dialog.append(button_list)
		self.finished( object.id(), res )

	def network_gateway(self, object):
		errors = []
		warnings = []
		changed = False
		reset = False
		config = merge_config(self.actual_config, self.staged_config)
		if object.options.get('action', None) == 'store':
			value = object.options.get('gateway', None)
			if value is None:
				if 'gateway' in self.staged_config:
					del self.staged_config['gateway']
					reset = True
			if type(value) in (type(''), type(u'')):
				newvalue = string_to_ip(value) # try to parse IP address
				if newvalue is None:
					errors.append(_('Invalid IP address "%s"') % value)
				else:
					value = newvalue
			if type(value) == type( () ):
				# TODO implement checks:
				# * is gateway link-local on any interface
				# * is gateway link-loacl on only exactly one interface
				# * is gateway not broadcast/network-address of interface
				if value == self.actual_config['gateway']:
					if 'gateway' in self.staged_config:
						del self.staged_config['gateway']
						reset = True
				else:
					self.staged_config['gateway'] = value
					changed = True
		elif object.options.get('action', None) == 'remove':
			if self.actual_config['gateway'] is None:
				if 'gateway' in self.staged_config:
					del self.staged_config['gateway']
					reset = True
			else:
				self.staged_config['gateway'] = None
				changed = True
		if changed or reset:
			config = merge_config(self.actual_config, self.staged_config)
		###
		# Generate dialog
		###
		if not errors:
			gateway = config['gateway']
			inpt_gateway = umcd.TextInput(('gateway', umc.String(_('Gateway'), required = False)), ip_to_string(gateway))
			if gateway is None:
				warnings.append(_('There is no gateway set; This machine will not be able to access the internet.'))
		else:
			inpt_gateway = umcd.TextInput(('gateway', umc.String(_('Gateway'), required = False)), object.options.get('gateway'))
		gateway_list = umcd.List()
		gateway_list.add_row([umcd.Fill(2, text = _("To reset the value to the current configuration remove the IP address from the field."))])
		tmplist = [inpt_gateway]
		if changed:
			tmplist.append(umcd.Text(_('Change recorded.')))
		elif reset:
			tmplist.append(umcd.Text(_('Reset to current value.')))
		if errors:
			tmplist.append(umcd.Image('network/error', umct.SIZE_SMALL))
		elif warnings:
			tmplist.append(umcd.Image('network/warning', umct.SIZE_SMALL))
		gateway_list.add_row(tmplist)
		gateway_list.add_row([umcd.Fill(2, text = _('The gateway is the IP address of the router to use. Packets with an IP address that cannot be sent to their destination directly via a network interface (that is: the address does not belong to the a corresponding subnet of an interface) are sent to the router for forwarding. The gateway must therefore have an IP address that does belong to the subnet of a network interface.'))])
		interface_list = umcd.List()
		for if_name in sorted(config['interfaces'].keys()):
			if_config = config['interfaces'][if_name]
			if if_config['enabled']:
				interface_list.add_row([
						umcd.Text(if_name),
						umcd.Text(str(ip_to_string(if_config['ip_addr']))),
						umcd.Text(str(ip_to_string(prefix_to_subnetmask(if_config['prefix'])))),
						])
		button_list = umcd.List()
		cmd_update = umcp.SimpleCommand('network/gateway', {'action': 'store' }, startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False)
		cmd_remove = umcp.SimpleCommand('network/gateway', {'action': 'remove'}, startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False)
		button_list.add_row([
				umcd.Button(_('Update setting'),
					    'actions/ok',
					    actions = [umcd.Action(cmd_update, [ inpt_gateway.id() ])],
					    close_dialog = False,
					    ),
				umcd.CloseButton(),
				umcd.Button(_("Remove gateway"),
					    'actions/remove',
					    actions = [umcd.Action(cmd_remove, [])],
					    close_dialog = False,
					    ),
				])
		gateway_frame = umcd.Frame([gateway_list], _('Configure gateway'))
		interface_frame = umcd.Frame([interface_list], _('Already configured interfaces'))
		res = umcp.Response(object)
		res.dialog = []
		if errors or warnings:
			msg_list = umcd.List()
			for error in errors:
				img = umcd.Image('network/error', umct.SIZE_SMALL)
				txt = umcd.Text(error)
				msg_list.add_row([img, txt])
			for warning in warnings:
				img = umcd.Image('network/warning', umct.SIZE_SMALL)
				txt = umcd.Text(warning)
				msg_list.add_row([img, txt])
			res.dialog.append(msg_list)
		res.dialog.append(gateway_frame)
		res.dialog.append(button_list)
		res.dialog.append(interface_frame)
		self.finished(object.id(), res)

	def input_3_ip(self, object, DialogID, DialogTitle, CollapseWarning, VarID1, VarName1, VarID2, VarName2, VarID3, VarName3):
		errors = []
		warnings = []
		changed = set()
		reset = set()
		erroneous = set()
		dubious = set()
		config = merge_config(self.actual_config, self.staged_config)
		if object.options.get('action', None) == "store":
			for var in (VarID1, VarID2, VarID3):
				value = object.options.get(var, None)
				if value is None:
					if var in self.staged_config:
						del self.staged_config[var]
						reset.add(var)
				if type(value) in (type(''), type(u'')):
					newvalue = string_to_ip(value) # try to parse IP address
					if newvalue is None:
						errors.append(_('Invalid IP address "%s"') % value)
						erroneous.add(var)
					else:
						value = newvalue
				if type(value) == type( () ):
					if self.actual_config[var] == value: # reset
						if var in self.staged_config:
							del self.staged_config[var]
							reset.add(var)
					elif config[var] != value: # change if necessary
						self.staged_config[var] = value
						changed.add(var)
			config = merge_config(self.actual_config, self.staged_config)
		elif object.options.get('action', None) == "remove" and object.options.get('what', None) in (VarID1, VarID2, VarID3):
			varnames = {
				VarID1: VarName1,
				VarID2: VarName2,
				VarID3: VarName3,
				}
			for var in (VarID1, VarID2, VarID3):
				if object.options.get(var, None) != ip_to_string(config[var]): # if input differs from current config => input was changed
					errors.append(_('You can only remove an entry if you leave the fields unchanged, otherwise you would lose your input. (The value for "%s" was changed)') % varnames[var])
					erroneous.add(var)
			if not errors:
				to_remove = object.options.get('what')
				removed = False
				previous = None
				newvals = {}
				for var in (VarID1, VarID2, VarID3):
					if var == to_remove: # remove
						assert var not in newvals
						newvals[var] = None
						removed = True
					elif removed: # move up
						newvals[previous] = config[var]
					previous = var
				if removed: # remove
					assert previous not in newvals
					newvals[previous] = None
				for var in newvals:
					newval = newvals[var]
					if config[var] != newval:
						if self.actual_config[var] == newval:
							if var in self.staged_config:
								del self.staged_config[var]
								reset.add(var)
						else:
							self.staged_config[var] = newval
							changed.add(var)
				config = merge_config(self.actual_config, self.staged_config)
		###
		# Generate dialog
		###
		if not errors:
			var1 = config.get(VarID1,'')
			var2 = config.get(VarID2,'')
			var3 = config.get(VarID3,'')
			if (not var1 and var2) or (not var2 and var3): # there is an unset variable before a set one
				warnings.append(CollapseWarning)
				if not var1:
					dubious.add(VarID1)
				if not var2:
					dubious.add(VarID2)
			inpt_var1 = umcd.TextInput((VarID1, umc.String(VarName1, required = False)), ip_to_string(var1))
			inpt_var2 = umcd.TextInput((VarID2, umc.String(VarName2, required = False)), ip_to_string(var2))
			inpt_var3 = umcd.TextInput((VarID3, umc.String(VarName3, required = False)), ip_to_string(var3))
		else:
			inpt_var1 = umcd.TextInput((VarID1, umc.String(VarName1, required = False)), object.options.get(VarID1))
			inpt_var2 = umcd.TextInput((VarID2, umc.String(VarName2, required = False)), object.options.get(VarID2))
			inpt_var3 = umcd.TextInput((VarID3, umc.String(VarName3, required = False)), object.options.get(VarID3))
		var_list = umcd.List()
		var_list.add_row([umcd.Fill(3, text = _('To reset the value to the current configuration remove the IP address from the field.'))])
		for (key, inpt) in ((VarID1, inpt_var1),
				    (VarID2, inpt_var2),
				    (VarID3, inpt_var3),):
			tmplist = [inpt]
			cmd_remove = umcp.SimpleCommand(DialogID, {'action': 'remove', 'what': key}, startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False)
			tmplist.append(
					umcd.Button(_('Remove'),
						    'actions/remove',
						    actions = [umcd.Action(cmd_remove, [ inpt_var1.id(), inpt_var2.id(), inpt_var3.id() ])],
						    close_dialog = False,
						    ),
					)
			if key in reset:
				tmplist.append(umcd.Text(_('Reset to current value.')))
			elif key in changed:
				tmplist.append(umcd.Text(_('Change recorded.')))
			if key in erroneous:
				tmplist.append(umcd.Image('network/error', umct.SIZE_SMALL))
			elif key in dubious:
				tmplist.append(umcd.Image('network/warning', umct.SIZE_SMALL))
			var_list.add_row(tmplist)
		button_list = umcd.List()
		cmd_update = umcp.SimpleCommand(DialogID, {'action': 'store' }, startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False)
		button_list.add_row([
				umcd.Button(_('Update settings'),
					    'actions/ok',
					    actions = [umcd.Action(cmd_update, [ inpt_var1.id(), inpt_var2.id(), inpt_var3.id() ])],
					    close_dialog = False,
					    ),
				umcd.CloseButton(),
				])
		var_frame = umcd.Frame([var_list], DialogTitle)
		res = umcp.Response(object)
		res.dialog = []
		if errors or warnings:
			msg_list = umcd.List()
			for error in errors:
				img = umcd.Image('network/error', umct.SIZE_SMALL)
				txt = umcd.Text(error)
				msg_list.add_row([img, txt])
			for warning in warnings:
				img = umcd.Image('network/warning', umct.SIZE_SMALL)
				txt = umcd.Text(warning)
				msg_list.add_row([img, txt])
			res.dialog.append(msg_list)
		res.dialog.append(var_frame)
		res.dialog.append(button_list)
		self.finished(object.id(), res)

	def network_nameserver(self, object):
		return self.input_3_ip(object,
				       'network/nameserver', _('Configure nameservers'),
				       _('As you cannot configure a nameserver without configuring all the nameservers above it the nameservers will be moved up to fill the blanks.'),
				       'nameserver1', _('Nameserver 1'),
				       'nameserver2', _('Nameserver 2'),
				       'nameserver3', _('Nameserver 3'),
				       )

	def network_dnsforwarder(self, object):
		return self.input_3_ip(object,
				       'network/dnsforwarder', _('Configure DNS forwarders'),
				       _('As you cannot configure a DNS forwarder without configuring all the DNS forwarders above it the DNS forwarders will be moved up to fill the blanks.'),
				       'dns/forwarder1', _('DNS forwarder 1'),
				       'dns/forwarder2', _('DNS forwarder 2'),
				       'dns/forwarder3', _('DNS forwarder 3'),
				       )

	def network_proxyhttp(self, object):
		errors = []
		warnings = []
		changed = False
		reset = False
		config = merge_config(self.actual_config, self.staged_config)
		if object.options.get('action', None) == 'store':
			value = object.options.get('proxyhttp', None)
			if value is None:
				if 'proxy/http' in self.staged_config:
					del self.staged_config['proxy/http']
					reset = True
			else:
				newvalue = parse_proxy_url(value)
				if type(newvalue) in (type(''), type(u'')):
					value = newvalue
					if value != config['proxy/http']:
						# TODO implement checks: which?
						if value == self.actual_config['proxy/http']:
							if 'proxy/http' in self.staged_config:
								del self.staged_config['proxy/http']
								reset = True
						else:
							self.staged_config['proxy/http'] = value
							changed = True
				elif type(newvalue) == type( [] ):
					errors = newvalue
		elif object.options.get('action', None) == 'remove':
			if self.actual_config['proxy/http'] is None:
				if 'proxy/http' in self.staged_config:
					del self.staged_config['proxy/http']
					reset = True
			else:
				self.staged_config['proxy/http'] = None
				changed = True
		if changed or reset:
			config = merge_config(self.actual_config, self.staged_config)
		###
		# Generate dialog
		###
		if not errors:
			proxyhttp = config['proxy/http']
			if proxyhttp is None:
				proxyhttp = ''
			inpt_proxyhttp = umcd.TextInput(('proxyhttp', umc.String(_('HTTP Proxy'), required = False)), proxyhttp)
			# TODO add warnings here
		else:
			inpt_proxyhttp = umcd.TextInput(('proxyhttp', umc.String(_('HTTP Proxy'), required = False)), object.options.get('proxyhttp'))
		proxyhttp_list = umcd.List()
		proxyhttp_list.add_row([umcd.Fill(2, text = _("To reset the value to the current configuration remove the value from the field."))])
		tmplist = [inpt_proxyhttp]
		if changed:
			tmplist.append(umcd.Text(_('Change recorded.')))
		elif reset:
			tmplist.append(umcd.Text(_('Reset to current value.')))
		if errors:
			tmplist.append(umcd.Image('network/error', umct.SIZE_SMALL))
		elif warnings:
			tmplist.append(umcd.Image('network/warning', umct.SIZE_SMALL))
		proxyhttp_list.add_row(tmplist)
		proxyhttp_list.add_row([umcd.Fill(2, text = _('TODO Explain proxyhttp.'))])
		button_list = umcd.List()
		cmd_update = umcp.SimpleCommand('network/proxyhttp', {'action': 'store' }, startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False)
		cmd_remove = umcp.SimpleCommand('network/proxyhttp', {'action': 'remove'}, startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False)
		button_list.add_row([
				umcd.Button(_('Update setting'),
					    'actions/ok',
					    actions = [umcd.Action(cmd_update, [ inpt_proxyhttp.id() ])],
					    close_dialog = False,
					    ),
				umcd.CloseButton(),
				umcd.Button(_("Remove HTTP proxy"),
					    'actions/remove',
					    actions = [umcd.Action(cmd_remove, [])],
					    close_dialog = False,
					    ),
				])
		proxyhttp_frame = umcd.Frame([proxyhttp_list], _('Configure HTTP proxy'))
		res = umcp.Response(object)
		res.dialog = []
		if errors or warnings:
			msg_list = umcd.List()
			for error in errors:
				img = umcd.Image('network/error', umct.SIZE_SMALL)
				txt = umcd.Text(error)
				msg_list.add_row([img, txt])
			for warning in warnings:
				img = umcd.Image('network/warning', umct.SIZE_SMALL)
				txt = umcd.Text(warning)
				msg_list.add_row([img, txt])
			res.dialog.append(msg_list)
		res.dialog.append(proxyhttp_frame)
		res.dialog.append(button_list)
		self.finished(object.id(), res)

	def network_proxyusername(self, object):
		errors = []
		warnings = []
		changed = False
		reset = False
		config = merge_config(self.actual_config, self.staged_config)
		if object.options.get('action', None) == 'store':
			value = object.options.get('proxyusername', None)
			if value is None:
				if 'proxy/username' in self.staged_config:
					del self.staged_config['proxy/username']
					reset = True
			else:
				newvalue = parse_proxy_username(value)
				if type(newvalue) in (type(''), type(u'')):
					value = newvalue
					if value != config['proxy/username']:
						if value == self.actual_config['proxy/username']:
							if 'proxy/username' in self.staged_config:
								del self.staged_config['proxy/username']
								reset = True
						else:
							self.staged_config['proxy/username'] = value
							changed = True
				elif type(newvalue) == type( [] ):
					errors = newvalue
		elif object.options.get('action', None) == 'remove':
			if self.actual_config['proxy/username'] is None:
				if 'proxy/username' in self.staged_config:
					del self.staged_config['proxy/username']
					reset = True
			else:
				self.staged_config['proxy/username'] = None
				changed = True
		if changed or reset:
			config = merge_config(self.actual_config, self.staged_config)
		###
		# Generate dialog
		###
		if not errors:
			proxyusername = config['proxy/username']
			if proxyusername is None:
				proxyusername = ''
			inpt_proxyusername = umcd.TextInput(('proxyusername', umc.String(_('Proxy username'), required = False)), proxyusername)
		else:
			inpt_proxyusername = umcd.TextInput(('proxyusername', umc.String(_('Proxy username'), required = False)), object.options.get('proxyusername'))
		proxyusername_list = umcd.List()
		proxyusername_list.add_row([umcd.Fill(2, text = _("To reset the value to the current configuration remove the value from the field."))])
		tmplist = [inpt_proxyusername]
		if changed:
			tmplist.append(umcd.Text(_('Change recorded.')))
		elif reset:
			tmplist.append(umcd.Text(_('Reset to current value.')))
		if errors:
			tmplist.append(umcd.Image('network/error', umct.SIZE_SMALL))
		elif warnings:
			tmplist.append(umcd.Image('network/warning', umct.SIZE_SMALL))
		proxyusername_list.add_row(tmplist)
		proxyusername_list.add_row([umcd.Fill(2, text = _('Please configure the username to be used to authenticate to the HTTP proxy.'))])
		button_list = umcd.List()
		cmd_update = umcp.SimpleCommand('network/proxyusername', {'action': 'store' }, startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False)
		cmd_remove = umcp.SimpleCommand('network/proxyusername', {'action': 'remove'}, startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False)
		button_list.add_row([
				umcd.Button(_('Update setting'),
					    'actions/ok',
					    actions = [umcd.Action(cmd_update, [ inpt_proxyusername.id() ])],
					    close_dialog = False,
					    ),
				umcd.CloseButton(),
				umcd.Button(_("Remove proxy username"),
					    'actions/remove',
					    actions = [umcd.Action(cmd_remove, [])],
					    close_dialog = False,
					    ),
				])
		proxyusername_frame = umcd.Frame([proxyusername_list], _('Configure proxy username'))
		res = umcp.Response(object)
		res.dialog = []
		if errors or warnings:
			msg_list = umcd.List()
			for error in errors:
				img = umcd.Image('network/error', umct.SIZE_SMALL)
				txt = umcd.Text(error)
				msg_list.add_row([img, txt])
			for warning in warnings:
				img = umcd.Image('network/warning', umct.SIZE_SMALL)
				txt = umcd.Text(warning)
				msg_list.add_row([img, txt])
			res.dialog.append(msg_list)
		res.dialog.append(proxyusername_frame)
		res.dialog.append(button_list)
		self.finished(object.id(), res)

	def network_proxypassword(self, object):
		errors = []
		warnings = []
		changed = False
		reset = False
		config = merge_config(self.actual_config, self.staged_config)
		if object.options.get('action', None) == 'store':
			value = object.options.get('proxypassword', None)
			if value is None:
				if 'proxy/password' in self.staged_config:
					del self.staged_config['proxy/password']
					reset = True
			else:
				newvalue = parse_proxy_password(value)
				if type(newvalue) in (type(''), type(u'')):
					value = newvalue
					if value != config['proxy/password']:
						value = newvalue
						if value == self.actual_config['proxy/password']:
							if 'proxy/password' in self.staged_config:
								del self.staged_config['proxy/password']
								reset = True
						else:
							self.staged_config['proxy/password'] = value
							changed = True
				elif type(newvalue) == type( [] ):
					errors = newvalue
		elif object.options.get('action', None) == 'remove':
			if self.actual_config['proxy/password'] is None:
				if 'proxy/password' in self.staged_config:
					del self.staged_config['proxy/password']
					reset = True
			else:
				self.staged_config['proxy/password'] = None
				changed = True
		if changed or reset:
			config = merge_config(self.actual_config, self.staged_config)
		###
		# Generate dialog
		###
		if not errors:
			proxypassword = config['proxy/password']
			if proxypassword is None:
				proxypassword = ''
			inpt_proxypassword = umcd.SecretInput(('proxypassword', umc.Password(_('Proxy password'), required = False)), proxypassword)
		else:
			inpt_proxypassword = umcd.SecretInput(('proxypassword', umc.Password(_('Proxy password'), required = False)), object.options.get('proxypassword'))
		proxypassword_list = umcd.List()
		proxypassword_list.add_row([umcd.Fill(2, text = _("To reset the value to the current configuration remove the value from the field."))])
		tmplist = [inpt_proxypassword]
		if changed:
			tmplist.append(umcd.Text(_('Change recorded.')))
		elif reset:
			tmplist.append(umcd.Text(_('Reset to current value.')))
		if errors:
			tmplist.append(umcd.Image('network/error', umct.SIZE_SMALL))
		elif warnings:
			tmplist.append(umcd.Image('network/warning', umct.SIZE_SMALL))
		proxypassword_list.add_row(tmplist)
		proxypassword_list.add_row([umcd.Fill(2, text = _('Please configure the password to be used to authenticate to the HTTP proxy.'))])
		button_list = umcd.List()
		cmd_update = umcp.SimpleCommand('network/proxypassword', {'action': 'store' }, startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False)
		cmd_remove = umcp.SimpleCommand('network/proxypassword', {'action': 'remove'}, startup = True, startup_cache = False, startup_dialog = True, startup_referrer = False)
		button_list.add_row([
				umcd.Button(_('Update setting'),
					    'actions/ok',
					    actions = [umcd.Action(cmd_update, [ inpt_proxypassword.id() ])],
					    close_dialog = False,
					    ),
				umcd.CloseButton(),
				umcd.Button(_("Remove proxy password"),
					    'actions/remove',
					    actions = [umcd.Action(cmd_remove, [])],
					    close_dialog = False,
					    ),
				])
		proxypassword_frame = umcd.Frame([proxypassword_list], _('Configure proxy password'))
		res = umcp.Response(object)
		res.dialog = []
		if errors or warnings:
			msg_list = umcd.List()
			for error in errors:
				img = umcd.Image('network/error', umct.SIZE_SMALL)
				txt = umcd.Text(error)
				msg_list.add_row([img, txt])
			for warning in warnings:
				img = umcd.Image('network/warning', umct.SIZE_SMALL)
				txt = umcd.Text(warning)
				msg_list.add_row([img, txt])
			res.dialog.append(msg_list)
		res.dialog.append(proxypassword_frame)
		res.dialog.append(button_list)
		self.finished(object.id(), res)
