#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: system setup
#
# Copyright 2011 Univention GmbH
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

import threading
import traceback
import time
import notifier
import notifier.threads
import re
import csv
import univention.info_tools as uit
import univention.management.console as umc
import univention.management.console.modules as umcm
import util
import os
import copy
import univention.config_registry

from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import *

_ = umc.Translation('univention-management-console-module-setup').translate

PATH_SYS_CLASS_NET = '/sys/class/net'

class TimeoutError(Exception):
	pass

class Instance(umcm.Base):
	def __init__(self):
		umcm.Base.__init__(self)
		self._finishedLock = threading.Lock()
		self._finishedResult = True
		# reset umask to default
		os.umask( 0022 )

	def _check_thread_error( self, thread, result, request ):
		"""Checks if the thread returned an exception. In that case in
		error response is send and the function returns True. Otherwise
		False is returned."""
		if not isinstance( result, BaseException ):
			return False

		msg = '%s\n%s: %s\n' % ( ''.join( traceback.format_tb( thread.exc_info[ 2 ] ) ), thread.exc_info[ 0 ].__name__, str( thread.exc_info[ 1 ] ) )
		MODULE.process( 'An internal error occurred: %s' % msg )
		self.finished( request.id, None, msg, False )
		return True

	def _thread_finished( self, thread, result, request ):
		"""This method is invoked when a threaded request function is
		finished. The result is send back to the client. If the result
		is an instance of BaseException an error is returned."""
		if request:
			if self._check_thread_error( thread, result, request ):
				return

			self.finished( request.id, result )

	def load(self, request):
		'''Return a dict with all necessary values for system-setup read from the current
		status of the system.'''
		values = util.load_values()
		self.finished(request.id, values)

	def save(self, request):
		'''Reconfigures the system according to the values specified in the dict given as
		option named "values".'''

		def _thread(request, obj, values, username, password):
			# acquire the lock until the scripts have been executed
			self._finishedResult = False
			obj._finishedLock.acquire()

			# write the profile file and run setup scripts
			orgValues = util.load_values()
			util.pre_save(values, orgValues)
			MODULE.info('saving profile values')
			util.write_profile(values)
			
			if orgValues['server/role'] == 'basesystem' or os.path.exists('/var/univention-join/joined'):
				if not values:
					MODULE.error( 'No property "values" given for save().' )
					obj._finishedLock.release()
					return False

				# in case of changes of the IP address, restart UMC server and web server
				# for this we ignore changes of virtual or non-default devices
				MODULE.info('Check whether ip addresses have been changed')
				regIpv6 = re.compile(r'^interfaces/(eth[0-9]+)/ipv6/default/(prefix|address)$')
				regIpv4 = re.compile(r'^interfaces/(eth[0-9]+)/(address|netmask)$')
				regSsl = re.compile(r'^ssl/.*')
				restart = False
				for ikey, ival in values.iteritems():
					if regIpv4.match(ikey) or regIpv6.match(ikey) or regSsl.match(ikey):
						restart = True
						break
				MODULE.info('Restart servers: %s' % restart)

				# on a joined system or on a basesystem, we can run the setup scripts
				MODULE.info('runnning system setup scripts')
				util.run_scripts(restart)
			else:
				# unjoined system and not a basesystem -> run the join script
				MODULE.info('runnning system setup join script')
				util.run_joinscript(username, password)

			# done :)
			self._finishedResult = True
			obj._finishedLock.release()
			return True

		thread = notifier.threads.Simple( 'check_finished', 
			notifier.Callback( _thread, request, self, request.options.get('values'), request.options.get('username'), request.options.get('password')),
			notifier.Callback( self._thread_finished, None ) )
		thread.run()

		self.finished(request.id, True)

	def check_finished(self, request):
		'''Check whether the join/setup scripts are finished. This method implements a long
		polling request, i.e., the request is only finished at the moment when all scripts
		have been executed. When the connection breaks down on the client side (due to
		timeout), the error may be ignored and a new try can be started.'''
		def _thread(request, obj):
			# acquire the lock in order to wait for the join/setup scripts to finish
			# do this one minute long on then return an error
			ntries = 60
			while not obj._finishedLock.acquire(False):
				time.sleep(1)
				ntries -= 1
				if ntries <= 0:
					raise TimeoutError('setup/finished has reached its timeout')

			obj._finishedLock.release()

			# scripts are done, return final result
			return obj._finishedResult
			
		thread = notifier.threads.Simple( 'check_finished', 
			notifier.Callback( _thread, request, self ),
			notifier.Callback( self._thread_finished, request ) )
		thread.run() 

	def shutdown_browser(self, request):
		if self._username != '__systemsetup__':
			MODULE.warn('Tried to shut down the web browser, however, system is not in appliance mode.')
			self.finished(request.id, False, message=_('Not allowed to shut down the web browser.'))
			return

		# shut down the browser in appliance mode
		MODULE.info('Appliance mode: try to shut down the browser')
		if util.shutdown_browser():
			MODULE.info('... shutting down successful')
			self.finished(request.id, True)
		else:
			MODULE.warn('... shutting down operation failed')
			self.finished(request.id, False, message=_('Failed to shut down the web browser.'))

	def validate(self, request):
		'''Validate the specified values given in the dict as option named "values".
		Return a dict (with variable names as key) of dicts with the structure:
		{ "valid": True/False, "message": "..." }'''
		
		# init variables
		messages = []
		values = request.options.get('values', {})
		orgValues = util.load_values()

		# mix original and new values
		allValues = copy.copy(values)
		for ikey, ival in orgValues.iteritems():
			if ikey not in allValues:
				allValues[ikey] = ival

		# helper functions
		def _check(key, check, message):
			if not key in values:
				return
			if not check(values[key]):
				messages.append({
					'message': message,
					'valid': False,
					'key': key
				})

		def _append(key, message):
			messages.append({ 
				'key': key, 
				'valid': False,
				'message': message
			})

		# basis
		_check('hostname', util.is_hostname, _('The hostname is not a valid fully qualified domain name in lowercase (e.g. host.example.com).'))
		_check('hostname', lambda x: len(x) <= 15, _('A valid netbios name can not be longer than 15 characters. If samba is installed, the hostname should be shortened.'))

		_check('domainname', util.is_domainname, _("Please enter a valid fully qualified domain name in lowercase (e.g. host.example.com)."))

		hostname = allValues.get('hostname')
		domainname = allValues.get('domainname')
		if len(hostname + domainname) >= 63:
			_append('domainname', _('The length of fully qualified domain name is greater than 63 characters.'))
		if hostname == domainname.split('.')[0]:
			_append('domainname', _("Hostname is equal to domain name."))

		_check('windows/domain', lambda x: x == x.upper(), _("The windows domain name can only consist of upper case characters."))
		_check('windows/domain', lambda x: len(x) < 14, _("The length of the windows domain name needs to be smaller than 14 characters."))
		_check('windows/domain', util.is_windowsdomainname, _("The windows domain name is not valid."))

		_check('ldap/base', lambda x: x.find(' ') == -1, _("The LDAP base may not contain any blanks (e.g., dc=test,dc=net)."))

		_check('root_password', lambda x: len(x) >= 8, _("The root password is too short. For security reasons, your password must contain at least 8 characters."))
		_check('root_password', util.is_ascii, _("The root password may only contain ascii characters."))

		# ssl
		for ikey, iname in [('ssl/state', _('State')), ('ssl/locality', _('Location'))]:
			_check(ikey, lambda x: len(x) <= 128, _('The following value is too long, only 128 characters allowed: %s') % iname)
		for ikey, iname in [('ssl/organization', _('Organization')), ('ssl/organizationalunit', _('Business unit')), ('ssl/email', _('Email address'))]:
			_check(ikey, lambda x: len(x) <= 64, _('The following value is too long, only 64 characters allowed: %s') % iname)
		_check('ssl/email', lambda x: x.find('@') >= 0, _("Please enter a valid email address"))

		# net
		# validate all ipv4 addresses and there netmask
		regIpv4 = re.compile(r'^interfaces/((eth[0-9]+)(_[0-9])?)/(address|netmask)$')
		checkedIpv4 = set()
		for ikey, ival in values.iteritems():
			if not ival:
				continue
			m = regIpv4.match(ikey)
			if m:
				# get the parts
				idev = m.groups()[1]
				iname = m.groups()[0]
				ivirt = m.groups()[2]
				itype = m.groups()[3]

				# have we already tested this device?
				addressKey = 'interfaces/%s/address' % iname
				maskKey = 'interfaces/%s/netmask' % iname
				if addressKey in checkedIpv4:
					continue
				checkedIpv4.add(addressKey)

				# make sure that address and netmask are correct
				virtStr = ''
				if ivirt:
					virtStr = _(' (virtual)')
				if not util.is_ipv4addr(allValues.get(addressKey)):
					_append(addressKey, _('IPv4 address is not valid [%s%s]: "%s"') % (idev, virtStr, allValues.get(addressKey)))
				elif not allValues.get(maskKey) or not util.is_ipv4netmask('%s/%s' % (allValues.get(addressKey), allValues.get(maskKey))):
					_append(maskKey, _('IPv4 netmask is not valid [%s%s]: "%s"') % (idev, virtStr, allValues.get(maskKey, '')))

		# validate all ipv6 addresses, their prefix, and identifier
		regIpv6 = re.compile(r'^interfaces/(eth[0-9]+)/ipv6/(.*)/(prefix|address)$')
		regIpv6Id = re.compile(r'^[a-zA-Z0-9]+$')
		checkedIpv6 = set()
		for ikey, ival in values.iteritems():
			if not ival:
				continue
			m = regIpv6.match(ikey)
			if m:
				# get the parts
				idev = m.groups()[0]
				iid = m.groups()[1]
				itype = m.groups()[2]

				# have we already tested this device?
				addressKey = 'interfaces/%s/ipv6/%s/address' % (idev, iid)
				prefixKey = 'interfaces/%s/ipv6/%s/prefix' % (idev, iid)
				if addressKey in checkedIpv6:
					continue
				checkedIpv6.add(addressKey)

				# make sure that the ID is correct
				if not regIpv6Id.match(iid):
					_append(addressKey, _('The specified IPv6 identifier may only consit of letters and numbers: %s') % iid)

				# make sure that address and prefix are correct
				if not util.is_ipv6addr(allValues.get(addressKey)):
					_append(addressKey, _('IPv6 address is not valid [%s]: %s') % (idev, allValues.get(addressKey)))
				if not allValues.get(prefixKey) or not util.is_ipv6netmask('%s/%s' % (allValues.get(addressKey), allValues.get(prefixKey))):
					_append(prefixKey, _('IPv6 prefix is not valid [%s]: %s') % (idev, allValues.get(prefixKey, '')))

		# check nameservers
		for ikey, iname in [('nameserver[1-3]', _('Domain name server')), ('dns/forwarder[1-3]', _('External name server'))]:
			reg = re.compile('^(%s)$' % ikey)
			for jkey, jval in values.iteritems():
				if reg.match(jkey):
					_check(jkey, util.is_ipaddr, _('The specified IP address (%s) is not valid: %s') % (iname, jval))
			
		# check gateways
		_check('gateway', util.is_ipv4addr, _('The specified gateway IPv4 address is not valid: %s') % values.get('gateway'))
		_check('ipv6/gateway', util.is_ipv6addr, _('The specified gateway IPv6 address is not valid: %s') % values.get('ipv6/gateway'))

		# proxy
		_check('proxy/http', util.is_proxy, _('The specified proxy address is not valid (e.g., http://10.201.1.1:8080): %s') % allValues.get('proxy/http', ''))

		# check global network settings
		isSetIpv4 = False
		ipv4HasAddress = False
		ipv4HasDynamic = False
		devIpv4VirtualDevices = set()

		regIpv4Address = re.compile(r'^interfaces/((eth[0-9]+)(_[0-9])?)/address$')
		regIpv4Dynamic = re.compile(r'^interfaces/((eth[0-9]+)(_[0-9])?)/type$')
		
		isSetIpv6 = False
		ipv6HasAddress = False
		hasIpv6DefaultDevices = True
		ipv6HasDynamic = False
		
		regIpv6Address = re.compile(r'^interfaces/(eth[0-9]+)/ipv6/(.*)/address$')
		regIpv6Dynamic = re.compile(r'^interfaces/(eth[0-9]+)/ipv6/acceptRA$')
		
		tmpUCR = univention.config_registry.ConfigRegistry()
		devIpv6HasDefaultID = {}
		for ikey, ival in allValues.iteritems():
			m = regIpv6Address.match(ikey) 
			if m:
				idev = m.groups()[0]
				iid = m.groups()[1]

				# see whether the device is in the dict
				if idev not in devIpv6HasDefaultID:
					devIpv6HasDefaultID[idev] = False

				# identifier 'default'
				devIpv6HasDefaultID[idev] |= (iid == 'default')

				# ipv6 address
				ipv6HasAddress |= util.is_ipv6addr(ival)
			
			# ipv4 address
			if regIpv4Address.match(ikey):
				ipv4HasAddress |= util.is_ipv4addr(ival)

			# dynamic ipv4
			ipv4HasDynamic |= bool(regIpv4Dynamic.match(ikey) and ival in ('dynamic', 'dhcp'))
		
			# dynamic ipv6
			if regIpv6Dynamic.match(ikey):
				tmpUCR[ikey] = ival;
				if tmpUCR.is_true(ikey):
					ipv6HasDynamic = True

			# ipv6 configuration
			if regIpv6.match(ikey) and ival:
				isSetIpv6 = True

			# ipv4 configuration
			m = regIpv4.match(ikey) 
			if m and ival:
				isSetIpv4 = True

				# check whether this entry is a virtual device
				ivirt = m.groups()[2]
				idev = m.groups()[1]
				if ivirt:
					devIpv4VirtualDevices.add(idev)

		# check whether all virtual devices have a real device that is defined
		for idev in devIpv4VirtualDevices:
			mask = allValues.get('interfaces/%s/netmask' % idev)
			address = allValues.get('interfaces/%s/address' % idev)
			if not mask or not address or not util.is_ipv4netmask('%s/%s' % (address, mask)):
				_append('interfaces/eth0/address', _('A virtual device cannot be specified alone: %s') % idev)
				break

		# check whether all devices have a default entry
		for idev, iset in devIpv6HasDefaultID.iteritems():
			hasIpv6DefaultDevices &= iset

		# global checks
		if not isSetIpv4 and not isSetIpv6:
			_append('interfaces/eth0/address', _('At least one network device (either IPv4 or IPv6) needs to be configured.'))
		if ipv6HasDynamic and not ipv6HasAddress:
			_append('interfaces/eth0/ipv6/default/address', _('At least one IPv6 address needs to be specified.'))
		if isSetIpv6 and not hasIpv6DefaultDevices:
			_append('interfaces/eth0/ipv6/default/address', _('A default entry with the identifier "default" needs to be specified for each network device.'))
		if orgValues.get('server/role', '') in ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'] and isSetIpv4 and not ipv4HasAddress:
			_append('interfaces/eth0/address', _('At least one IPv4 address needs to be specified.'))
		if not ipv4HasDynamic and not ipv6HasDynamic and not allValues.get('nameserver1') and not allValues.get('nameserver2') and not allValues.get('nameserver3'):
			_append('nameserver1', _('At least one domain name server needs to be given if DHCP or SLAAC is not specified.'))

		# software checks
		regSpaces = re.compile(r'\s+')
		components = regSpaces.split(values.get('components', ''))
		packages = set(reduce(lambda x, y: x + y, [ i.split(':') for i in components ]))
		if 'univention-virtual-machine-manager-node-kvm' in packages and 'univention-virtual-machine-manager-node-xen' in packages:
			_append('components', _('It is not possible to install KVM and XEN components on one system. Please select only one of these components.'))
		if 'univention-samba' in packages and 'univention-samba4' in packages:
			_append('components', _('It is not possible to install Samba 3 and Samba 4 on one system. Please select only one of these components.'))

		self.finished(request.id, messages)


	def lang_locales(self, request):
		'''Return a list of all available locales.'''
		try:
			fsupported = open('/usr/share/i18n/SUPPORTED')
			flanguages = open('/lib/univention-installer/locale/languagelist')
		except:
			MODULE.error( 'Cannot find locale data for languages in /lib/univention-installer/locale' )
			self.finished(request.id, None)
			return

		# get all locales that are supported
		rsupported = csv.reader(fsupported, delimiter=' ')
		supportedLocales = { 'C': True }
		regLocale = re.compile(r'([^.@ ]+).*')
		for ilocale in rsupported:
			# we only support UTF-8
			if ilocale[1] != 'UTF-8':
				continue

			# get the locale
			m = regLocale.match(ilocale[0])
			if m:
				supportedLocales[m.groups()[0]] = True

		# open all languages
		rlanguages = csv.reader(flanguages, delimiter=';')
		locales = []
		for ilang in rlanguages:
			if ilang[0].startswith('#'):
				continue

			# each language might be spoken in several countries
			ipath = '/lib/univention-installer/locale/short-list/%s.short' % ilang[0]
			if os.path.exists(ipath):
				try:
					# open the short list with countries belonging to the language
					fshort = open(ipath)
					rshort = csv.reader(fshort, delimiter='\t')

					# create for each country a locale entry
					for jcountry in rshort:
						code = '%s_%s' % (ilang[0], jcountry[0])
						if code in supportedLocales:
							locales.append({
								'id': '%s.UTF-8:UTF-8' % code,
								'label': '%s (%s)' % (ilang[1], jcountry[2])
							})
					continue
				except Exception, e:
					pass

			# get the locale code
			code = ilang[0]
			if code.find('_') < 0 and code != 'C':
				# no underscore -> we need to build the locale ourself
				code = '%s_%s' % (ilang[0], ilang[4])

			# final entry
			if code in supportedLocales:
				locales.append({
					'id': '%s.UTF-8:UTF-8' % code,
					'label': ilang[1]
				})

		self.finished(request.id, locales)

	def lang_timezones(self, request):
		'''Return a list of all available time zones.'''
		try:
			file = open('/lib/univention-installer/locale/timezone')
		except:
			MODULE.error( 'Cannot find locale data for timezones in /lib/univention-installer/locale' )
			self.finished(request.id, None)
			return

		timezones = [ i.strip('\n') for i in file if not i.startswith('#') ]

		self.finished(request.id, timezones)

	def lang_keymaps(self, request):
		'''Return a list of all available keyboard layouts.'''
		try:
			file = open('/lib/univention-installer/locale/all-kmaps')
		except:
			MODULE.error( 'Cannot find locale data for keymaps in /lib/univention-installer/locale' )
			self.finished(request.id, None)
			return

		r = csv.reader(file, delimiter=':')
		keymaps = [ { 'label': i[0], 'id': i[1] } for i in r if not i[0].startswith('#') ]

		self.finished(request.id, keymaps)
	
	def lang_countrycodes(self, request):
		'''Return a list of all countries with their two letter chcountry codes.'''
		try:
			file = open('/lib/univention-installer/locale/country_codes')
		except:
			MODULE.error( 'Cannot find locale data for keymaps in /lib/univention-installer/locale' )
			self.finished(request.id, None)
			return

		r = csv.reader(file, delimiter=':')
		countries = [ { 'label': i[0], 'id': i[1] } for i in r if not i[0].startswith('#') ]

		self.finished(request.id, countries)


	def net_read(self, request):
		'''Return a dict of all current network settings.'''

	def net_interfaces(self, request):
		'''Return a list of all available network interfaces.'''
		interfaces = [ idev['name'] for idev in util.detect_interfaces() ]
		self.finished(request.id, interfaces)

	def net_dhclient(self, request):
		'''Request a DHCP address. Expects as options a dict containing the key
		"interface" and optionally the key "timeout" (in seconds).'''
		interface = request.options.get('interface')
		timeout = request.options.get('timeout', 45)
		if not interface:
			message = 'No property "interface" given for dhclient().'
			MODULE.error(message)
			self.finished(request.id, None, success = false, message = message)
			return

		res = util.dhclient(interface, timeout)
		self.finished(request.id, res)

	def software_components(self, request):
		'''Return a list of all available software packages. Entries have the properties 
		"id", "label", and "packages" which is an array of the Debian package names.'''
		choices = [ { 'id': i['id'], 'label': i['Name'], 'packages': i['Packages'] }
				for i in util.get_components() ]
		self.finished(request.id, choices)


