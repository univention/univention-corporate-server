#!/usr/bin/python2.7
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
import re
import os
import copy
import subprocess
import simplejson as json
import locale as _locale
import lxml.etree 

import notifier
import notifier.threads

from univention.management.console.modules import Base
from univention.management.console.log import MODULE
from univention.management.console.modules.mixins import ProgressMixin
from univention.management.console.modules.sanitizers import PatternSanitizer, StringSanitizer, IntegerSanitizer
from univention.management.console.modules.decorators import sanitize, simple_response
from univention.lib.i18n import Translation, Locale
import univention.config_registry
from univention.lib.admember import lookup_adds_dc, check_connection, check_ad_account, connectionFailed, failedADConnect, notDomainAdminInAD
from univention.management.console.modules import UMC_Error

import util
from . import network

ucr = univention.config_registry.ConfigRegistry()
ucr.load()

_translation = Translation('univention-management-console-module-setup')
_ = _translation.translate

i18nXKeyboard = Translation('xkeyboard-config')

RE_IPV4 = re.compile(r'^interfaces/(([^/]+?)(_[0-9])?)/(address|netmask)$')
RE_IPV6_DEFAULT = re.compile(r'^interfaces/([^/]+)/ipv6/default/(prefix|address)$')
RE_SPACE = re.compile(r'\s+')
RE_SSL = re.compile(r'^ssl/.*')


class Instance(Base, ProgressMixin):

	def __init__(self, *args, **kwargs):
		Base.__init__(self, *args, **kwargs)
		ProgressMixin.__init__(self)
		self._finishedLock = threading.Lock()
		self._finishedResult = True
		self._progressParser = util.ProgressParser()
		self._cleanup_required = False
		self._very_first_locale = None
		self.__keep_alive_request = None
		# reset umask to default
		os.umask( 0022 )

	def init( self ):
		os.environ['LC_ALL'] = str(self.locale)
		_locale.setlocale(_locale.LC_ALL, str(self.locale))
		self._very_first_locale = copy.deepcopy(self.locale)
		MODULE.process('Very first locale is %s. Will be added if this is very first system setup' % self._very_first_locale)
		if not util.is_system_joined():
			self._preload_city_data()

	def _preload_city_data(self):
		util.get_city_data()
		util.get_country_data()

	def _get_localized_label(self, label_dict):
		# return the correctly loca
		return label_dict.get(self.locale.language) or label_dict.get('en', '') or label_dict.get('', '')

	def destroy(self):
		if self._cleanup_required:
			MODULE.info('Appliance mode: cleanup by timeout')
			# cleanup restarts umc, so MODULE.info will never
			# be called. but leave it that way, maybe it can
			# be called in the future.
			util.cleanup()
			MODULE.info('... cleanup done')
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

	def ping(self, request):
		if request.options.get('keep_alive'):
			self.__keep_alive_request = request
			return
		self.finished(request.id, None)

	@simple_response
	def load(self):
		'''Return a dict with all necessary values for system-setup read from the current
		status of the system.'''
		return util.load_values()

	@simple_response
	def save_keymap(self, layout=None):
		'''Set the systems x-keymap according to
		request.options[keymap]'''

		# Don't set in debian installer mode
		if ucr.is_true('system/setup/boot/installer'):
			return True

		if layout:
			subprocess.call(['/usr/bin/setxkbmap', '-display', ':0', '-layout', layout])
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
				subfolders = {
					'network': ['30_net'],
					'certificate': ['40_ssl'],
					'languages': ['15_keyboard', '20_language', '35_timezone'],
				}.get(request.flavor)

				self._progressParser.reset(subfolders)

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
				MODULE.info('runnning system setup scripts (flavor %r)' % (request.flavor,))

				util.run_scripts(self._progressParser, restart, subfolders)

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

	@simple_response
	def join(self, values=None, username=None, password=None):
		'''Join and reconfigure the system according to the values specified in the dict given as
		option named "values".'''

		# get old and new values
		orgValues = util.load_values()
		values = values or {}

		# determine new system role
		oldrole = orgValues.get('server/role', '')
		newrole = values.get('server/role', oldrole)
		if orgValues.get('joined'):
			raise Exception(_('Already joined systems cannot be joined.'))

		def _thread(obj, username, password):
			# acquire the lock until the scripts have been executed
			self._finishedResult = False
			obj._finishedLock.acquire()
			try:
				self._progressParser.reset()

				# write the profile file and run setup scripts
				# use the _very_first_locale not the current one
				# otherwise some strange python exceptions occur telling us
				# about unsupported locale strings...
				util.auto_complete_values_for_join(values, self._very_first_locale)

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

		def _finished(thread, result):
			if self.__keep_alive_request:
				self.finished(self.__keep_alive_request.id, None)
				self.__keep_alive_request = None

			if isinstance(result, BaseException):
				MODULE.warn( 'Exception during saving the settings: %s\n%s' % (result, ''.join(traceback.format_exception(*thread.exc_info))))
				self._progressParser.current.errors.append(_('Encountered unexpected error during setup process: %s') % (result,))
				self._progressParser.current.critical = True
				self._finishedResult = True

		thread = notifier.threads.Simple('join', notifier.Callback(_thread, self, username, password), _finished)
		thread.run()
		return

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
		util.cleanup()
		MODULE.info('... cleanup done')

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
		ad_member = values.get('ad/member', orgValues.get('ad/member', ''))

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
			MODULE.warn('Validation failed for key %s: %s' % (key, message))
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
		hostname = allValues.get('hostname', '')
		domainname = allValues.get('domainname', '')
		if len('%s%s' % (hostname, domainname)) >= 63:
			_append('domainname', _('The length of fully qualified domain name is greater than 63 characters.'))
		if hostname == domainname.split('.')[0]:
			_append('domainname', _("Hostname is equal to domain name."))
		if not util.is_system_joined():
			if newrole == 'domaincontroller_master' and not values.get('domainname'):
				_append('domainname', _("No fully qualified domain name has been specified for the system."))
			elif not values.get('hostname'):
				_append('hostname', _("No hostname has been specified for the system."))

		# windows domain
		_check('windows/domain', lambda x: x == x.upper(), _("The windows domain name can only consist of upper case characters."))
		_check('windows/domain', lambda x: len(x) <= 15, _("The windows domain name cannot be longer than 15 characters."))
		_check('windows/domain', util.is_windowsdomainname, _("The windows domain name is not valid."))

		# LDAP base
		_check('ldap/base', util.is_ldap_base, _("The LDAP base may neither contain blanks nor any special characters. Its structure needs to consist of at least two relative distinguished names (RDN) which may only use the attribute tags 'dc', 'cn', 'c', 'o', or 'l' (e.g., dc=test,dc=net)."))

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
			interfaces = network.Interfaces()
			interfaces.from_dict(allValues.get('interfaces', {}))
			interfaces.check_consistency()
		except network.DeviceError as exc:
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

		def guess_domain(obj):
			for nameserver in ('nameserver1', 'nameserver2', 'nameserver3'):
				nameserver = obj.get(nameserver)
				if nameserver:
					if obj.get('ad/member') and obj.get('ad/address'):
						try:
							ad_domain_info = lookup_adds_dc(obj.get('ad/address'), ucr={'nameserver1' : nameserver})
						except failedADConnect:
							pass
						else:
							guessed_domain = ad_domain_info['Domain']
					else:
						guessed_domain = util.get_ucs_domain(nameserver)
					if guessed_domain:
						return guessed_domain

		if not util.is_system_joined() and (newrole not in ['domaincontroller_master', 'basesystem'] or ad_member):
			if all(nameserver in values and not values[nameserver] for nameserver in ('nameserver1', 'nameserver2', 'nameserver3')):
				# 'nameserver1'-key exists → widget is displayed → = not in UCS/debian installer mode
				if not any(interface.ip4dynamic or interface.ip6dynamic for interface in interfaces.values()):
					_append('nameserver1', _('A domain name server needs to be specified.'))
					#_append('nameserver1', _('At least one domain name server needs to be given if DHCP or SLAAC is not specified.'))

			# see whether the domain can be determined automatically
			ucr.load()
			for obj in [values, ucr]:
				guessed_domain = guess_domain(obj)
				if guessed_domain:
					# communicate guessed domainname to frontend
					messages.append({
						'valid': True,
						'key': 'domainname',
						'value': guessed_domain,
					})
					break
			else:
			 	if not values.get('domainname'):
					_append('domainname', _('Cannot automatically determine the domain. Please specify the server\'s fully qualified domain name.'))

				if values.get('nameserver1'):
					_append('nameserver1', _('The specified nameserver %s is not part of a valid UCS domain.') % (values['nameserver1'],))

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

	@sanitize(pattern=PatternSanitizer(default='.*', required=True, add_asterisks=True))
	@simple_response
	def lang_locales(self, pattern, category='language_en'):
		'''Return a list of all available locales.'''
		return util.get_available_locales(pattern, category)

	def lang_timezones(self, request):
		'''Return a list of all available time zones.'''
		try:
			file = open('/usr/share/univention-system-setup/locale/timezone')
		except:
			MODULE.error( 'Cannot find locale data for timezones in /usr/share/univention-system-setup/locale' )
			self.finished(request.id, None)
			return

		timezones = [ i.strip('\n') for i in file if not i.startswith('#') ]

		self.finished(request.id, timezones)

	@simple_response
	def lang_keyboard_model(self):
		'''Return a list of all available keyboard models.'''

		tree = lxml.etree.parse(file('/usr/share/X11/xkb/rules/base.xml'))
		models = tree.xpath("//model")

		model_result = [{
			'label': i18nXKeyboard.translate(model.xpath('./configItem/description')[0].text),
			'id': model.xpath('./configItem/name')[0].text
		} for model in models]

		return model_result

	@simple_response
	def lang_keyboard_layout(self):
		'''Return a list of all available keyboard layouts.'''

		tree = lxml.etree.parse(file('/usr/share/X11/xkb/rules/base.xml'))
		layouts = tree.xpath("//layout")

		layout_result = [{
			'label': i18nXKeyboard.translate(layout.xpath('./configItem/description')[0].text),
			'id': layout.xpath('./configItem/name')[0].text,
			'language': layout.xpath('./configItem/shortDescription')[0].text,
			'countries': ':'.join([icountry.text for icountry in layout.xpath('./configItem/countryList/*')]),
		} for layout in layouts]

		return layout_result

	@sanitize(keyboardlayout=StringSanitizer(default='us'))
	@simple_response
	def lang_keyboard_variante(self, keyboardlayout):
		'''Return a list of all available keyboard variantes.'''

		variante_result = []
		tree = lxml.etree.parse(file('/usr/share/X11/xkb/rules/base.xml'))
		layouts = tree.xpath("//layout")

		for layout in layouts:
			layoutID = layout.xpath("./configItem/name")[0].text
			if layoutID != keyboardlayout:
				continue
			variants = layout.xpath("./variantList/variant")
			variante_result += [{
				'label': i18nXKeyboard.translate(variant.xpath('./configItem/description')[0].text),
				'id': variant.xpath('./configItem/name')[0].text
			} for variant in variants]

		variante_result.insert(0, { 'label': '', 'id': '' })

		return variante_result

	def lang_countrycodes(self, request):
		'''Return a list of all countries with their two letter chcountry codes.'''
		country_data = util.get_country_data()
		countries = [{
				'id': icountry,
				'label': self._get_localized_label(idata.get('label', {})),
			}
			for icountry, idata in country_data.iteritems()
			if idata.get('label')]

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
	def net_apply(self, values):
		MODULE.process('Applying network settings')
		with util.written_profile(values):
			util.run_networkscrips()
		return True

	@simple_response
	def net_interfaces(self):
		'''Return a list of all available network interfaces.'''
		return [ idev['name'] for idev in util.detect_interfaces() ]

	# workaround: use with_progress to make the method threaded
	@simple_response(with_progress=True)
	def net_dhclient(self, interface, timeout=10):
		'''Request a DHCP address. Expects as options a dict containing the key
		"interface" and optionally the key "timeout" (in seconds).'''

		return util.dhclient(interface, timeout)

	@sanitize(locale=StringSanitizer(default='en_US'))
	@simple_response
	def set_locale(self, locale):
		locale = Locale(locale)
		locale.codeset = self.locale.codeset
		MODULE.info('Switching language to: %s' % locale)
		os.environ['LC_ALL'] = str(self.locale)
		try:
			_locale.setlocale(_locale.LC_ALL, str(locale))
		except _locale.Error:
			MODULE.warn('Locale %s is not supported, using fallback locale "C" instead.' % locale)
			_locale.setlocale(_locale.LC_ALL, 'C')
		self.locale = locale

		# dynamically change the translation methods
		_translation.set_language(str(self.locale))
		i18nXKeyboard.set_language(str(self.locale))
		network._translation.set_language(str(self.locale))

		# make sure that locale information is correctly reloaded
		reload(util.app_center)

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
		country_data = util.get_country_data()
		for imatch in matches:
			match_country = country_data.get(imatch.get('country'))
			if match_country:
				imatch.update(util.get_random_nameserver(match_country))
				imatch.update(dict(
					default_lang=match_country.get('default_lang'),
					country_label=self._get_localized_label(match_country.get('label', {})),
					label=self._get_localized_label(imatch.get('label')) or imatch.get('match'),
				))

		return matches

	@simple_response
	def apps_query(self):
		return util.get_apps(True)

	@simple_response
	def check_domain(self, role, nameserver):
		result = {}
		if role == 'ad':
			try:
				ad_domain_info = lookup_adds_dc(nameserver)
				dc = ad_domain_info['DC DNS Name']
				if dc:
					result['dc_name'] = dc
					result['domain'] = ad_domain_info['Domain']
					result['ucs_master'] = util.is_ucs_domain(nameserver, ad_domain_info['Domain'])
			except (failedADConnect, connectionFailed) as e:
				MODULE.warn('ADDS DC lookup failed: %s' % e)
		elif role == 'nonmaster':
			fqdn = util.get_fqdn(nameserver)
			if fqdn:
				result['dc_name'] = fqdn
				domain = '.'.join(fqdn.split('.')[1:])
				result['ucs_master'] = util.is_ucs_domain(nameserver, domain)
		return result

	@simple_response
	def check_credentials(self, role, dns, nameserver, address, username, password):
		if role == 'ad':
			try:
				ad_domain_info = lookup_adds_dc(address, ucr={'nameserver1' : nameserver})
				check_connection(ad_domain_info, username, password)
				check_ad_account(ad_domain_info, username, password)
			except failedADConnect:
				# Not checked... no AD!
				return None
			except connectionFailed:
				# checked: failed!
				return False
			except notDomainAdminInAD: # check_ad_account()
				# checked: Not a Domain Administrator!
				raise UMC_Error(_("The given user is not member of the Domain Admins group in AD."))
			else:
				return ad_domain_info['Domain']
		elif role == 'nonmaster':
			if dns:
				domain = util.get_ucs_domain(nameserver)
			else:
				domain = '.'.join(address.split('.')[1:])
			if not domain:
				# Not checked... no UCS domain!
				return None
			with util._temporary_password_file(password) as password_file:
				return_code = subprocess.call(['univention-ssh', password_file, '%s@%s' % (username, address), 'echo', 'WORKS'])
				return return_code == 0 and domain
		# master? basesystem? no domain check necessary
		return True

