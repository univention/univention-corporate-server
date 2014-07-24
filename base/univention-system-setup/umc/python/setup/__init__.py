#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: system setup
#
# Copyright 2011-2014 Univention GmbH
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
from univention.lib.i18n import Translation, Locale
import univention.config_registry
import util
import os
import copy
import subprocess
import simplejson as json
import locale as _locale

from univention.management.console.modules import Base
from univention.management.console.log import MODULE
from univention.management.console.modules.sanitizers import PatternSanitizer, StringSanitizer, IntegerSanitizer
from univention.management.console.modules.decorators import sanitize, simple_response
from univention.management.console.modules.setup.network import Interfaces, DeviceError

ucr = univention.config_registry.ConfigRegistry()
ucr.load()

_ = Translation('univention-management-console-module-setup').translate


RE_IPV4 = re.compile(r'^interfaces/(([^/]+?)(_[0-9])?)/(address|netmask)$')
RE_IPV6_DEFAULT = re.compile(r'^interfaces/([^/]+)/ipv6/default/(prefix|address)$')
RE_SPACE = re.compile(r'\s+')
RE_SSL = re.compile(r'^ssl/.*')

class Instance(Base):
	def __init__(self):
		Base.__init__(self)
		self._finishedLock = threading.Lock()
		self._finishedResult = True
		self._progressParser = util.ProgressParser()
		self._cleanup_required = False
		# reset umask to default
		os.umask( 0022 )

	def init( self ):
		os.environ['LC_ALL'] = str(self.locale)
		_locale.setlocale(_locale.LC_ALL, str(self.locale))
		if not util.is_system_joined():
			self._preload_city_data()

	def _preload_city_data(self):
		util.get_city_data()
		util.get_country_data()

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

	@simple_response
	def load(self):
		'''Return a dict with all necessary values for system-setup read from the current
		status of the system.'''
		return util.load_values()

	@simple_response
	def save_keymap(self, keymap=None):
		'''Set the systems x-keymap according to
		request.options[keymap]'''

		if keymap:
			xkeymap = util._xkeymap(keymap)
			subprocess.call(['/usr/bin/setxkbmap', '-display', ':0', '-layout', xkeymap['layout'], '-variant', xkeymap['variant']])
		return True

	def save(self, request):
		'''Reconfigures the system according to the values specified in the dict given as
		option named "values".'''

		# get new values
		values = request.options.get('values', {})

		def _thread(request, obj):
			# acquire the lock until the scripts have been executed
			self._finishedResult = False
			obj._finishedLock.acquire()
			try:
				self._progressParser.reset()

				# write the profile file and run setup scripts
				util.pre_save(values)

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
			success = True
			if isinstance( result, BaseException ):
				success = False
				msg = '%s\n%s: %s\n' % (''.join(traceback.format_tb(thread.exc_info[2])), thread.exc_info[0].__name__, str(thread.exc_info[1]))
				MODULE.warn( 'Exception during saving the settings: %s\n%s' % (result, msg) )
				self._progressParser.current.errors.append(_('Encountered unexpected error during setup process: %s') % result)
				self._progressParser.current.critical = True
				self._finishedResult = True

			self.finished(request.id, success)

		thread = notifier.threads.Simple( 'save',
			notifier.Callback( _thread, request, self ), _finished )
		thread.run()


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
			raise Exception(_('Base systems and already joined systems cannot be joined.'))

		def _thread(request, obj, username, password):
			# acquire the lock until the scripts have been executed
			self._finishedResult = False
			obj._finishedLock.acquire()
			try:
				self._progressParser.reset()

				# write the profile file and run setup scripts
				util.auto_complete_values_for_join(values, self.locale)
				util.pre_save(values)

				# on unjoined DC master the nameserver must be set to the external nameserver
				if newrole == 'domaincontroller_master' and not orgValues.get('joined'):
					for i in range(1, 4):
						# overwrite these values only if they are set, because the UMC module
						# will save only changed values
						if values.get( 'dns/forwarder%d' % i ):
							values[ 'nameserver%d' % i ] = values.get( 'dns/forwarder%d' % i )

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
			success = True
			if isinstance( result, BaseException ):
				success = False
				msg = '%s\n%s: %s\n' % (''.join(traceback.format_tb(thread.exc_info[2])), thread.exc_info[0].__name__, str(thread.exc_info[1]))
				MODULE.warn( 'Exception during saving the settings: %s\n%s' % (result, msg) )
				self._progressParser.current.errors.append(_('Encountered unexpected error during setup process: %s') % result)
				self._progressParser.current.critical = True
				self._finishedResult = True

			self.finished(request.id, success)

		thread = notifier.threads.Simple( 'save',
			notifier.Callback(_thread, request, self, request.options.get('username'), request.options.get('password')), _finished)
		thread.run()


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

	@simple_response
	def validate(self, values=None):
		'''Validate the specified values given in the dict as option named "values".
		Return a dict (with variable names as key) of dicts with the structure:
		{ "valid": True/False, "message": "..." }'''

		# init variables
		messages = []
		values = values or {}
		orgValues = util.load_values()

		# determine new system role
		newrole = values.get('server/role', orgValues.get('server/role', ''))

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

		# host and domain name
		packages = set(values.get('components', []))
		_check('hostname', util.is_hostname, _('The hostname is not a valid fully qualified domain name in lowercase (e.g. host.example.com).'))
		_check('hostname', lambda x: len(x) <= 13, _('A valid NetBIOS name can not be longer than 13 characters. If Samba is installed, the hostname should be shortened.'), critical=('univention-samba' in packages or 'univention-samba4' in packages))
		_check('domainname', util.is_domainname, _("Please enter a valid fully qualified domain name in lowercase (e.g. host.example.com)."))
		hostname = allValues.get('hostname')
		domainname = allValues.get('domainname')
		if len(hostname + domainname) >= 63:
			_append('domainname', _('The length of fully qualified domain name is greater than 63 characters.'))
		if hostname == domainname.split('.')[0]:
			_append('domainname', _("Hostname is equal to domain name."))
		if not util.is_system_joined():
			if newrole == 'domaincontroller_master' and not values.get('domainname'):
				_append('domainname', _("No fully qualified domain name has been specified for the system."))
			elif not values.get('hostname'):
				_append('hostname', _("No hostname has been specified for the system."))

		# see whether the domain can be determined automatically
		if not util.is_system_joined() and newrole != 'domaincontroller_master' and 'domainname' not in values:
			if 'nameserver1' not in values:
				_append('nameserver1', _('A domain name server needs to specified.'))
			else:
				guessed_domain = util.get_nameserver_domain(values['nameserver1'])
				if not guessed_domain:
					_append('domainname', _('The domain cannot automatically be determined. Make sure that the correct UCS domain name server has been specified or enter a fully qualified domain name of the system.'))
				messages.append({
					'valid': True,
					'key': 'domainname',
					'value': guessed_domain,
				})

		# windows domain
		_check('windows/domain', lambda x: x == x.upper(), _("The windows domain name can only consist of upper case characters."))
		_check('windows/domain', lambda x: len(x) < 14, _("The length of the windows domain name needs to be smaller than 14 characters."))
		_check('windows/domain', util.is_windowsdomainname, _("The windows domain name is not valid."))

		# LDAP base
		_check('ldap/base', lambda x: x.find(' ') == -1, _("The LDAP base may not contain any blanks (e.g., dc=test,dc=net)."))

		# root password
		_check('root_password', lambda x: len(x) >= 8, _("The root password is too short. For security reasons, your password must contain at least 8 characters."))
		_check('root_password', util.is_ascii, _("The root password may only contain ascii characters."))

		# ssl + email
		for ikey, iname in [('ssl/state', _('State')), ('ssl/locality', _('Location'))]:
			_check(ikey, lambda x: len(x) <= 128, _('The following value is too long, only 128 characters allowed: %s') % iname)
		for ikey, iname in [('ssl/organization', _('Organization')), ('ssl/organizationalunit', _('Business unit')), ('ssl/email', _('Email address')), ('email_address', _('Email address'))]:
			_check(ikey, lambda x: len(x) <= 64, _('The following value is too long, only 64 characters allowed: %s') % iname)
		for ikey in ['ssl/email', 'email_address']:
			_check(ikey, lambda x: x.find('@') >= 0, _("Please enter a valid email address"))

		# net
		try:
			interfaces = Interfaces()
			interfaces.from_dict(allValues.get('interfaces', {}))
			interfaces.check_consistency()
		except DeviceError as exc:
			_append('interfaces', str(exc))

		# validate the primary network interface
		_check('interfaces/primary', lambda x: not x or x in interfaces, _('The primary network device must exist.'))

		# check nameservers
		for ikey, iname in [('nameserver[1-3]', _('Domain name server')), ('dns/forwarder[1-3]', _('External name server'))]:
			reg = re.compile('^(%s)$' % ikey)
			for jkey, jval in values.iteritems():
				if reg.match(jkey):
					if not values.get(jkey):
						# allow empty value
						continue
					_check(jkey, util.is_ipaddr, _('The specified IP address (%s) is not valid: %s') % (iname, jval))

		if not any(interface.ip4dynamic or interface.ip6dynamic for interface in interfaces.values()) and not allValues.get('nameserver1') and not allValues.get('nameserver2') and not allValues.get('nameserver3'):
			_append('nameserver1', _('At least one domain name server needs to be given if DHCP or SLAAC is not specified.'))

		# check gateways
		if values.get('gateway'): # allow empty value
			_check('gateway', util.is_ipv4addr, _('The specified gateway IPv4 address is not valid: %s') % values.get('gateway'))
		if values.get('ipv6/gateway'): # allow empty value
			_check('ipv6/gateway', util.is_ipv6addr, _('The specified gateway IPv6 address is not valid: %s') % values.get('ipv6/gateway'))

		# proxy
		_check('proxy/http', util.is_proxy, _('The specified proxy address is not valid (e.g., http://10.201.1.1:8080): %s') % allValues.get('proxy/http', ''))

		# software checks
		if 'univention-virtual-machine-manager-node-kvm' in packages and 'univention-virtual-machine-manager-node-xen' in packages:
			_append('components', _('It is not possible to install KVM and XEN components on one system. Please select only one of these components.'))
		if 'univention-samba' in packages and 'univention-samba4' in packages:
			_append('components', _('It is not possible to install Samba 3 and Samba 4 on one system. Please select only one of these components.'))

		return messages

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

	@simple_response
	def net_interfaces(self):
		'''Return a list of all available network interfaces.'''
		return [ idev['name'] for idev in util.detect_interfaces() ]

	@simple_response
	def net_dhclient(self, interface, timeout=45):
		'''Request a DHCP address. Expects as options a dict containing the key
		"interface" and optionally the key "timeout" (in seconds).'''

		return util.dhclient(interface, timeout)

	@sanitize(locale=StringSanitizer(default='en_US'))
	@simple_response
	def set_locale(self, locale):
		locale = Locale(locale)
		locale.codeset = self.locale.codeset
		MODULE.info('Switching language to: %s' % locale)
		try:
			_locale.setlocale(_locale.LC_ALL, str(locale))
		except _locale.Error as exc:
			MODULE.warn('Locale %s is not supported, using fallback locale "C" instead.' % locale)
			_locale.setlocale(_locale.LC_ALL, 'C')
		self.locale = locale

	@sanitize(pattern=StringSanitizer(), max_results=IntegerSanitizer(minimum=1, default=5))
	@simple_response
	def find_city(self, pattern, max_results):
		pattern = pattern.decode(self.locale.codeset).lower()
		MODULE.info('pattern: %s' % pattern);
		if not pattern:
			return []

		# for the given pattern, find matching cities
		city_data = util.get_city_data()
		matches = []
		for icity in city_data:
			match = None
			for jlabel in icity.get('label', {}).itervalues():
				label = jlabel.decode(self.locale.codeset).lower()
				if pattern in label:
					# matching score is the overlap if the search pattern and the matched text
					# (as fraction between 0 and 1)
					match_score = len(pattern) / float(len(label))
					if match and match_score < match['match_score']:
						# just keep the best match of a city
						continue
					if match_score > 0.1:
						# found a match with more than 10% overlap :)
						match = icity.copy()
						match['match'] = jlabel
						match['match_score'] = match_score
			if match:
				matches.append(match)
		MODULE.info('Search for pattern "%s" with %s matches' % (pattern, len(matches)))
		if not matches:
			return None

		# add additional score w.r.t. the population size of the city
		# such that the largest city gains additional 0.4 on top
		max_population = max([imatch['population'] for imatch in matches])
		weighted_inv_max_population = 0.6 / float(max_population)
		for imatch in matches:
			imatch['final_score'] = imatch['match_score'] + weighted_inv_max_population * imatch['population']

		# sort matches...
		def _cmp(imatch, jmatch):
			'''Sort matched cities after their match score and then after their population.'''
			result = -cmp(imatch['match_score'], jmatch['match_score'])
			if result:
				return result
			return -cmp(imatch['population'], jmatch['population'])

		matches.sort(key=lambda x: x['final_score'], reverse=True)
		MODULE.info('Top 5 matches: %s' % json.dumps(matches[:5], indent=2))
		matches = matches[:max_results]

		# add additional information about keyboard layout, time zone etc. and
		# get the correct localized labels
		def _get_lang(label_dict):
			return label_dict.get(self.locale.language) or label_dict.get('en', '') or label_dict.get('', '')

		country_data = util.get_country_data()
		for imatch in matches:
			match_country = country_data.get(imatch.get('country'))
			if match_country:
				imatch.update(util.get_random_nameserver(match_country))
				imatch.update(dict(
					default_keyboard=match_country.get('default_keyboard'),
					default_lang=match_country.get('default_lang'),
					country_label=_get_lang(match_country.get('label', {})),
					label=_get_lang(imatch.get('label')) or imatch.get('match'),
				))

		return matches

	@simple_response
	def apps_query(self):
		return util.get_apps()


