#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: system setup
#
# Copyright 2011-2012 Univention GmbH
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
from univention.lib.i18n import Translation
import univention.management.console.modules as umcm
import util
import os
import copy
import locale
import univention.config_registry
import subprocess

from univention.management.console.log import MODULE
from univention.management.console.protocol.definitions import *
from univention.management.console.modules.sanitizers import PatternSanitizer
from univention.management.console.modules.decorators import sanitize, simple_response

_ = Translation('univention-management-console-module-setup').translate

PATH_SYS_CLASS_NET = '/sys/class/net'

RE_IPV4 = re.compile(r'^interfaces/(([^/_]+)(_[0-9])?)/(address|netmask)$')
RE_IPV4_ADDRESS = re.compile(r'^interfaces/(([^/_]+)(_[0-9])?)/address$')
RE_IPV4_DYNAMIC = re.compile(r'^interfaces/(([^/_]+)(_[0-9])?)/type$')
RE_IPV6 = re.compile(r'^interfaces/([^/]+)/ipv6/([^/]+)/(prefix|address)$')
RE_IPV6_ADDRESS = re.compile(r'^interfaces/([^/]+)/ipv6/([^/]+)/address$')
RE_IPV6_DEFAULT = re.compile(r'^interfaces/([^/]+)/ipv6/default/(prefix|address)$')
RE_IPV6_DYNAMIC = re.compile(r'^interfaces/([^/]+)/ipv6/acceptRA$')
RE_IPV6_ID = re.compile(r'^[a-zA-Z0-9]+$')
RE_SPACE = re.compile(r'\s+')
RE_SSL = re.compile(r'^ssl/.*')

class Instance(umcm.Base):
	def __init__(self):
		umcm.Base.__init__(self)
		self._finishedLock = threading.Lock()
		self._finishedResult = True
		self._progressParser = util.ProgressParser()
		self._cleanup_required = False
		# reset umask to default
		os.umask( 0022 )

	def init( self ):
		util.installer_i18n.set_language( str( self.locale ) )
		os.environ[ 'LC_ALL' ] =  str( self.locale )

	def destroy(self):
		if self._cleanup_required:
			MODULE.info('Appliance mode: cleanup by timeout')
			# cleanup restarts umc, so MODULE.info will never
			# be called. but leave it that way, maybe it can
			# be called in the future.
			if util.cleanup():
				MODULE.info('... cleanup successful')
			else:
				MODULE.warn('... cleanup operation failed')
		return super(Instance, self).destroy()

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
		if self._check_thread_error( thread, result, request ):
			return

		self.finished( request.id, result )

	def load(self, request):
		'''Return a dict with all necessary values for system-setup read from the current
		status of the system.'''
		values = util.load_values()
		self.finished(request.id, values)

	def save_keymap(self, request):
		'''Set the systems x-keymap according to
		request.options[keymap]'''

		keymap = request.options.get('keymap')
		if keymap:
			xkeymap = util._xkeymap(keymap)
			subprocess.call(['/usr/bin/setxkbmap', '-display', ':0', '-layout', xkeymap['layout'], '-variant', xkeymap['variant']])
		self.finished(request.id, True)

	def save(self, request):
		'''Reconfigures the system according to the values specified in the dict given as
		option named "values".'''

		# get old and new values
		orgValues = util.load_values()
		values = request.options.get('values', {})

		def _thread(request, obj):
			# acquire the lock until the scripts have been executed
			self._finishedResult = False
			obj._finishedLock.acquire()
			try:
				self._progressParser.reset()

				# write the profile file and run setup scripts
				orgValues = util.load_values()
				util.pre_save(values, orgValues)

				MODULE.info('saving profile values')
				util.write_profile(values)

				if not values:
					MODULE.error( 'No property "values" given for save().' )
					return False

				# in case of changes of the IP address, restart UMC server and web server
				# for this we ignore changes of virtual or non-default devices
				MODULE.info('Check whether ip addresses have been changed')
				restart = False
				for ikey, ival in values.iteritems():
					if RE_IPV4.match(ikey) or RE_IPV6_DEFAULT.match(ikey) or RE_SSL.match(ikey):
						restart = True
						break
				MODULE.info('Restart servers: %s' % restart)

				# on a joined system or on a basesystem, we can run the setup scripts
				MODULE.info('runnning system setup scripts')
				util.run_scripts( self._progressParser, restart )

				# done :)
				self._finishedResult = True
				return True
			finally:
				obj._finishedLock.release()


		def _finished( thread, result ):
			if isinstance( result, BaseException ):
				MODULE.warn( 'Exception during saving the settings: %s' % str( result ) )

		thread = notifier.threads.Simple( 'save',
			notifier.Callback( _thread, request, self ), _finished )
		thread.run()

		self.finished(request.id, True)

	def join(self, request):
		'''Join and reconfigure the system according to the values specified in the dict given as
		option named "values".'''

		# get old and new values
		orgValues = util.load_values()
		values = request.options.get('values', {})

		# determine new system role
		oldrole = orgValues.get('server/role', '')
		newrole = values.get('server/role', oldrole)
		if newrole == 'basesystem' or orgValues.get('joined'):
			raise Exception( _('Base systems and already joined systems cannot be joined.') )

		def _thread(request, obj, username, password):
			# acquire the lock until the scripts have been executed
			self._finishedResult = False
			obj._finishedLock.acquire()
			try:
				self._progressParser.reset()

				# write the profile file and run setup scripts
				util.pre_save(values, orgValues)

				# on unjoined DC master the nameserver must be set to the external nameserver
				if newrole == 'domaincontroller_master' and not orgValues.get('joined'):
					for i in range(1,4):
						# overwrite these values only if they are set, because the UMC module
						# will save only changed values
						if values.get( 'dns/forwarder%d'%i ):
							values[ 'nameserver%d'%i ] = values.get( 'dns/forwarder%d'%i )

				MODULE.info('saving profile values')
				util.write_profile(values)

				# unjoined DC master (that is not being converted to a basesystem) -> run the join script
				MODULE.info('runnning system setup join script')
				util.run_joinscript( self._progressParser, username, password )

				# done :)
				self._finishedResult = True

				# we should do a cleanup now
				self._cleanup_required = True

				return True
			finally:
				obj._finishedLock.release()

		def _finished( thread, result ):
			if isinstance( result, BaseException ):
				MODULE.warn( 'Exception during saving the settings: %s' % str( result ) )

		thread = notifier.threads.Simple( 'save',
			notifier.Callback( _thread, request, self, request.options.get('username'), request.options.get('password')),_finished )
		thread.run()

		self.finished(request.id, True)

	def check_finished(self, request):
		'''Check whether the join/setup scripts are finished. This method implements a long
		polling request, i.e., the request is only finished at the moment when all scripts
		have been executed or due to a timeout. If it returns because of the timeout, a new
		try can be started.'''
		def _thread(request, obj):
			def progress_info(state, **kwargs):
				info = { 'component' : state.fractionName,
					 'info' : state.message,
					 'errors' : state.errors,
					 'critical' : state.critical,
					 'steps' : state.percentage }
				info.update(kwargs)
				return info
			# acquire the lock in order to wait for the join/setup scripts to finish
			# do this for 30 sec and then return anyway
			SLEEP_TIME = 0.200
			WAIT_TIME = 30
			ntries = WAIT_TIME / SLEEP_TIME
			while not obj._finishedLock.acquire(False):
				if ntries <= 0 or self._progressParser.changed and self._progressParser.current:
					state = self._progressParser.current
					return progress_info(state, finished=False)
				time.sleep( SLEEP_TIME )
				ntries -= 1

			obj._finishedLock.release()

			# scripts are done, return final result
			# return all errors that we gathered throughout the setup
			state = self._progressParser.current
			return progress_info(state, finished=obj._finishedResult)

		thread = notifier.threads.Simple( 'check_finished',
			notifier.Callback( _thread, request, self ),
			notifier.Callback( self._thread_finished, request ) )
		thread.run()

	def cleanup(self, request):
		# shut down the browser in appliance mode
		# call finished() directly, so the browser will get the response in any case
		# (see Bug #27632)
		MODULE.info('Appliance mode: cleanup')
		self.finished(request.id, True)
		# put it here just in case destroy gets called during util
		self._cleanup_required = False
		if util.cleanup():
			MODULE.info('... cleanup successful')
		else:
			MODULE.warn('... cleanup operation failed')

	def validate(self, request):
		'''Validate the specified values given in the dict as option named "values".
		Return a dict (with variable names as key) of dicts with the structure:
		{ "valid": True/False, "message": "..." }'''

		# init variables
		messages = []
		values = request.options.get('values', {})
		orgValues = util.load_values()

		# determine new system role
		newrole = values.get('server/role', orgValues.get('server/role',''))

		# mix original and new values
		allValues = copy.copy(values)
		for ikey, ival in orgValues.iteritems():
			if ikey not in allValues:
				allValues[ikey] = ival

		# helper functions
		# TODO: 'valid' is not correctly evaluated in frontend
		# i.e. if valid you may continue without getting message
		def _check(key, check, message, critical=True):
			if key not in values:
				return
			if not check(values[key]):
				messages.append({
					'message': message,
					'valid': not critical,
					'key': key
				})

		def _append(key, message):
			messages.append({
				'key': key,
				'valid': False,
				'message': message
			})

		# system role
		_check('server/role', lambda x: not(orgValues.get('joined')) or (orgValues.get('server/role') == values.get('server/role')), _('The system role may not change on a system that has already joined to domain.'))

		# basis
		components = RE_SPACE.split(values.get('components', ''))
		packages = set(reduce(lambda x, y: x + y, [ i.split(':') for i in components ]))

		_check('hostname', util.is_hostname, _('The hostname is not a valid fully qualified domain name in lowercase (e.g. host.example.com).'))
		_check('hostname', lambda x: len(x) <= 13, _('A valid NetBIOS name can not be longer than 13 characters. If Samba is installed, the hostname should be shortened.'), critical=('univention-samba' in packages or 'univention-samba4' in packages))

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
		checkedIpv4 = set()
		for ikey, ival in values.iteritems():
			if not ival:
				continue
			m = RE_IPV4.match(ikey)
			if m:
				# get the parts
				iname, idev, ivirt, itype = m.groups()

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
		checkedIpv6 = set()
		for ikey, ival in values.iteritems():
			if not ival:
				continue
			m = RE_IPV6.match(ikey)
			if m:
				# get the parts
				idev, iid, itype = m.groups()

				# have we already tested this device?
				addressKey = 'interfaces/%s/ipv6/%s/address' % (idev, iid)
				prefixKey = 'interfaces/%s/ipv6/%s/prefix' % (idev, iid)
				if addressKey in checkedIpv6:
					continue
				checkedIpv6.add(addressKey)

				# make sure that the ID is correct
				if not RE_IPV6_ID.match(iid):
					_append(addressKey, _('The specified IPv6 identifier may only consist of letters and numbers: %s') % iid)

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
					if not values.get(jkey):
						# allow empty value
						continue
					_check(jkey, util.is_ipaddr, _('The specified IP address (%s) is not valid: %s') % (iname, jval))

		# check gateways
		if values.get('gateway'): # allow empty value
			_check('gateway', util.is_ipv4addr, _('The specified gateway IPv4 address is not valid: %s') % values.get('gateway'))
		if values.get('ipv6/gateway'): # allow empty value
			_check('ipv6/gateway', util.is_ipv6addr, _('The specified gateway IPv6 address is not valid: %s') % values.get('ipv6/gateway'))

		# proxy
		_check('proxy/http', util.is_proxy, _('The specified proxy address is not valid (e.g., http://10.201.1.1:8080): %s') % allValues.get('proxy/http', ''))

		# check global network settings
		isSetIpv4 = False
		ipv4HasAddress = False
		ipv4HasDynamic = False
		devIpv4VirtualDevices = set()

		isSetIpv6 = False
		ipv6HasAddress = False
		hasIpv6DefaultDevices = True
		ipv6HasDynamic = False

		tmpUCR = univention.config_registry.ConfigRegistry()
		devIpv6HasDefaultID = {}
		for ikey, ival in allValues.iteritems():
			m = RE_IPV6_ADDRESS.match(ikey)
			if m:
				idev, iid = m.groups()

				# see whether the device is in the dict
				if idev not in devIpv6HasDefaultID:
					devIpv6HasDefaultID[idev] = False

				# identifier 'default'
				devIpv6HasDefaultID[idev] |= (iid == 'default')

				# ipv6 address
				ipv6HasAddress |= util.is_ipv6addr(ival)

			# ipv4 address
			if RE_IPV4_ADDRESS.match(ikey):
				ipv4HasAddress |= util.is_ipv4addr(ival)

			# dynamic ipv4
			ipv4HasDynamic |= bool(RE_IPV4_DYNAMIC.match(ikey) and ival in ('dynamic', 'dhcp'))

			# dynamic ipv6
			if RE_IPV6_DYNAMIC.match(ikey):
				tmpUCR[ikey] = ival;
				if tmpUCR.is_true(ikey):
					ipv6HasDynamic = True

			# ipv6 configuration
			if RE_IPV6.match(ikey) and ival:
				isSetIpv6 = True

			# ipv4 configuration
			m = RE_IPV4.match(ikey)
			if m and ival:
				isSetIpv4 = True

				# check whether this entry is a virtual device
				idev, ivirt = m.groups()[1:3]
				if ivirt:
					devIpv4VirtualDevices.add(idev)

		# check whether all virtual devices have a real device that is defined
		for idev in devIpv4VirtualDevices:
			mask = allValues.get('interfaces/%s/netmask' % idev)
			address = allValues.get('interfaces/%s/address' % idev)
			if not mask or not address or not util.is_ipv4netmask('%s/%s' % (address, mask)):
				_append('interfaces/%s/address' % idev, _('A virtual device cannot be specified alone: %s') % idev)
				break

		# check whether all devices have a default entry
		for idev, iset in devIpv6HasDefaultID.iteritems():
			hasIpv6DefaultDevices &= iset

		# global checks
		if not (isSetIpv4 or ipv4HasDynamic) and not (isSetIpv6 or ipv6HasDynamic):
			_append('interfaces/eth0/address', _('At least one network device (either IPv4 or IPv6) needs to be configured.'))
		if isSetIpv6 and not hasIpv6DefaultDevices:
			_append('interfaces/eth0/ipv6/default/address', _('A default entry with the identifier "default" needs to be specified for each network device.'))
		if newrole in ['domaincontroller_master', 'domaincontroller_backup', 'domaincontroller_slave', 'memberserver'] and isSetIpv4 and not ipv4HasAddress:
			_append('interfaces/eth0/address', _('At least one IPv4 address needs to be specified.'))
		if not ipv4HasDynamic and not ipv6HasDynamic and not allValues.get('nameserver1') and not allValues.get('nameserver2') and not allValues.get('nameserver3'):
			_append('nameserver1', _('At least one domain name server needs to be given if DHCP or SLAAC is not specified.'))

		# software checks
		if 'univention-virtual-machine-manager-node-kvm' in packages and 'univention-virtual-machine-manager-node-xen' in packages:
			_append('components', _('It is not possible to install KVM and XEN components on one system. Please select only one of these components.'))
		if 'univention-samba' in packages and 'univention-samba4' in packages:
			_append('components', _('It is not possible to install Samba 3 and Samba 4 on one system. Please select only one of these components.'))

		self.finished(request.id, messages)

	@sanitize(pattern=PatternSanitizer(default='.*', required=True, add_asterisks=False))
	@simple_response
	def lang_locales(self, pattern, category='language_en'):
		'''Return a list of all available locales.'''
		return util.get_available_locales(pattern, category)

	def lang_default_timezone(self, request):
		'''Returns default timezone for given locale.'''
		countrycode = request.options.get('countrycode', '')
		timezone = None
		file = open('/lib/univention-installer/locale/countrycode2timezone')

		reader = csv.reader(file, delimiter=' ')
		for row in reader:
			if row[0].startswith("#"): continue
			if len(row) > 1:
				if countrycode.upper() == row[0].upper():
					timezone = row[1]
					break
		file.close()

		if timezone is None:
			timezone = 'Europe/Berlin'
		self.finished(request.id, timezone)

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

	def lang_default_keymap(self, request):
		'''Returns default timezone for given locale.'''
		# use "or ''" to be sure to not get None
		countrycode = (request.options.get('countrycode') or  '').upper()
		keymap = None
		file = open('/lib/univention-installer/locale/default-kmaps')

		reader = csv.reader(file, delimiter=':')
		for row in reader:
			if row[0].startswith("#"): continue
			if len(row) > 1:
				if row[1].upper().startswith(countrycode):
					keymap = row[1]
					break
		file.close()

		if keymap is None:
			keymap = 'us'
		self.finished(request.id, keymap)

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

		# add the value from ucr value to the list
		# this is required because invalid values will be unset in frontend
		# Bug #26409
		tmpUCR = univention.config_registry.ConfigRegistry()
		tmpUCR.load()
		ssl_country = tmpUCR.get('ssl/country')
		if ssl_country not in [ i['id'] for i in countries ]:
			countries.append( {'label': ssl_country, 'id': ssl_country} )

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
			self.finished(request.id, None, success = False, message = message)
			return

		res = util.dhclient(interface, timeout)
		self.finished(request.id, res)

	def software_components(self, request):
		'''Return a list of all available software packages. Entries have the properties
		"id", "label", and "packages" which is an array of the Debian package names.'''
		role = request.options.get('role')
		choices = [ { 'id': i['id'], 'label': i['Name'], 'packages': i['Packages'] }
				for i in util.get_components(role=role) ]
		self.finished(request.id, choices)
