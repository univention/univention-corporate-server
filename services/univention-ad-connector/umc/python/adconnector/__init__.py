#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: AD connector
#
# Copyright 2011-2013 Univention GmbH
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

import univention.config_registry
from univention.lib import Translation, admember
from univention.management.console.modules import Base
from univention.management.console.log import MODULE
from univention.management.console.config import ucr
from univention.management.console.modules.decorators import file_upload, sanitize, simple_response
from univention.management.console.modules.mixins import ProgressMixin
from univention.management.console.modules.sanitizers import StringSanitizer
from univention.management.console.modules import UMC_CommandError

import notifier.popen

import fnmatch
import psutil
import os.path
import subprocess
import time
import pipes

_ = Translation('univention-management-console-module-adconnector').translate

FN_BINDPW = '/etc/univention/connector/ad/bindpw'
DO_NOT_CHANGE_PWD = '********************'


class Instance(Base, ProgressMixin):
	OPTION_MAPPING = ( ( 'LDAP_Host', 'connector/ad/ldap/host', '' ),
					   ( 'LDAP_Base', 'connector/ad/ldap/base', '' ),
					   ( 'LDAP_BindDN', 'connector/ad/ldap/binddn', '' ),
					   ( 'KerberosDomain', 'connector/ad/mapping/kerberosdomain', '' ),
					   ( 'PollSleep', 'connector/ad/poll/sleep', 5 ),
					   ( 'RetryRejected', 'connector/ad/retryrejected', 10 ),
					   ( 'DebugLevel', 'connector/debug/level', 1 ),
					   ( 'DebugFunction', 'connector/debug/function', False ),
					   ( 'MappingSyncMode', 'connector/ad/mapping/syncmode', 'sync' ),
					   ( 'MappingGroupLanguage', 'connector/ad/mapping/group/language', 'de' ) )

	def __init__( self ):
		Base.__init__( self )
		self.guessed_baseDN = None
		self.__update_status()

	def state( self, request ):
		"""Retrieve current status of the UCS Active Directory Connector configuration and the service

		options: {}

		return: { 'configured' : (True|False), 'certificate' : (True|False), 'running' : (True|False) }
		"""

		self.__update_status()
		self.finished(request.id, {
			'certificate' : self.status_certificate,
			'mode_admember' : self.status_mode_admember,
			'mode_adconnector' : self.status_mode_adconnector,
			'configured' : self.status_mode_adconnector or self.status_mode_admember,
			'server_role': ucr.get('server/role'),
		})

	def load( self, request ):
		"""Retrieve current status of the UCS Active Directory Connector configuration and the service

		options: {}

		return: { <all AD connector UCR variables> }
		"""

		result = {}
		for option, var, default in Instance.OPTION_MAPPING:
			result[ option ] = ucr.get( var, default )

		pwd_file = ucr.get( 'connector/ad/ldap/bindpw' )
		result[ 'passwordExists' ] = bool( pwd_file and os.path.exists( pwd_file ) )

		self.finished( request.id, result )

	@sanitize(LDAP_Host=StringSanitizer(required=True))
	def save( self, request ):
		"""Saves the UCS Active Directory Connector configuration

		options:
			LDAP_Host: hostname of the AD server
			LDAP_Base: LDAP base of the AD server
			LDAP_BindDN: LDAP DN to use for authentication
			KerberosDomain: kerberos domain
			PollSleep: time in seconds between polls
			RetryRejected: how many time to retry a synchronisation
			MappingSyncMode: synchronisation mode
			MappingGroupLanguage: language of the AD server

		return: { 'success' : (True|False), 'message' : <details> }
		"""

		self.required_options( request, *map( lambda x: x[ 0 ], Instance.OPTION_MAPPING ) )
		self.guessed_baseDN = None

		for umckey, ucrkey, default in Instance.OPTION_MAPPING:
			val = request.options[ umckey ]
			if val:
				if isinstance( val, bool ):
					val = val and 'yes' or 'no'
				MODULE.info( 'Setting %s=%s' % ( ucrkey, val ) )
				univention.config_registry.handler_set( [ u'%s=%s' % ( ucrkey, val ) ] )

		ucr.load()
		if ucr.get('connector/ad/ldap/ldaps' ):
			MODULE.info( 'Unsetting connector/ad/ldap/ldaps' )
			univention.config_registry.handler_unset( [ u'connector/ad/ldap/ldaps' ] )
		if ucr.get( 'connector/ad/ldap/port' ) == '636':
			MODULE.info( 'Setting ldap port to 389' )
			univention.config_registry.handler_set( [ u'connector/ad/ldap/port=389' ] )

		if not request.options.get( 'LDAP_Password' ) in ( None, '', DO_NOT_CHANGE_PWD ):
			fn = ucr.get( 'connector/ad/ldap/bindpw', FN_BINDPW )
			try:
				fd = open( fn ,'w')
				fd.write( request.options.get( 'LDAP_Password' ) )
				fd.close()
				os.chmod( fn, 0600 )
				os.chown( fn, 0, 0 )
				univention.config_registry.handler_set( [ u'connector/ad/ldap/bindpw=%s' % fn ] )
			except Exception, e:
				MODULE.info( 'Saving bind password failed (filename=%(fn)s ; exception=%(exception)s)' % { 'fn' : fn, 'exception' : str( e.__class__ ) } )
				self.finished( request.id, { 'success' : False, 'message' : _( 'Saving bind password failed (filename=%(fn)s ; exception=%(exception)s)' ) % { 'fn' : fn, 'exception' : str(e.__class__ ) } } )
				return

		ssldir = '/etc/univention/ssl/%s' % request.options.get('LDAP_Host')
		if not os.path.exists(ssldir):
			self._create_certificate(request)
			return

		self.finished(request.id, { 'success' : True, 'message' :  _('UCS Active Directory Connector settings have been saved.')})

	def _create_certificate(self, request):
		ssldir = '/etc/univention/ssl/%s' % request.options.get('LDAP_Host')
		def _return(pid, status, buffer, request):
			if not os.path.exists(ssldir):
				MODULE.error( 'Creation of certificate failed (%s)' % ssldir )
				self.finished(request.id,  {'success' : False, 'message': _('Creation of certificate failed (%s)') % ssldir})
			self.finished(request.id,  {'success' : True, 'message' :  _('UCS Active Directory Connector settings have been saved and a new certificate for the Active Directory server has been created.')})

		cmd = '/usr/sbin/univention-certificate new -name %s' % pipes.quote(request.options['LDAP_Host'])
		MODULE.info( 'Creating new SSL certificate: %s' % cmd )
		proc = notifier.popen.Shell( cmd, stdout = True )
		cb = notifier.Callback( _return, request )
		proc.signal_connect( 'finished', cb )
		proc.start()

	@sanitize(LDAP_Host=StringSanitizer(required=True))
	def guess( self, request ):
		"""Tries to guess some values like the base DN of the AD server

		options: { 'LDAP_Host': <ad server fqdn> }

		return: { 'LDAP_Base' : <LDAP base>, 'success' : (True|False) }
		"""

		def _return( pid, status, buffer, request ):
			# dn:
			# namingContexts: DC=ad,DC=univention,DC=de
			# namingContexts: CN=Configuration,DC=ad,DC=univention,DC=de
			# namingContexts: CN=Schema,CN=Configuration,DC=ad,DC=univention,DC=de
			# namingContexts: DC=DomainDnsZones,DC=ad,DC=univention,DC=de
			# namingContexts: DC=ForestDnsZones,DC=ad,DC=univention,DC=de

			self.guessed_baseDN = None
			for line in buffer:
				if line.startswith( 'namingContexts: ' ):
					dn = line.split(': ',1)[1].strip()
					if self.guessed_baseDN is None or len( dn ) < len( self.guessed_baseDN ):
						self.guessed_baseDN = dn

			if self.guessed_baseDN is None:
				self.finished( request.id, { 'success' : False, 'message' : _('The LDAP base of the given Active Directory server could not be determined. Maybe the full-qualified hostname is wrong or unresolvable.' ) } )
				MODULE.process( 'Could not determine baseDN of given ldap server. Maybe FQDN is wrong or unresolvable! FQDN=%s' % request.options[ 'LDAP_Host' ] )
			else:
				self.finished( request.id, { 'success' : True, 'LDAP_Base' : self.guessed_baseDN } )

			MODULE.info( 'Guessed the LDAP base: %s' % self.guessed_baseDN )


		cmd = '/usr/bin/ldapsearch -x -s base -b "" namingContexts -LLL -h %s' % pipes.quote(request.options['LDAP_Host'])
		MODULE.info( 'Determine LDAP base for AD server of specified system FQDN: %s' % cmd )
		proc = notifier.popen.Shell( cmd, stdout = True )
		cb = notifier.Callback( _return, request )
		proc.signal_connect( 'finished', cb )
		proc.start()

	def private_key(self, request):
		self._serve_file(request, 'private.key')

	def cert_pem(self, request):
		self._serve_file(request, 'cert.pem')

	def _serve_file(self, request, filename):
		ucr.load()

		host = ucr.get('connector/ad/ldap/host')
		if not host:
			raise UMC_CommandError('Not configured yet')

		host = host.replace('/', '')
		filepath = '/etc/univention/ssl/%s/%s' % (host, filename)

		if not os.path.exists(filepath):
			raise UMC_CommandError('File does not exists')

		with open(filepath, 'rb') as fd:
			self.finished(request.id, fd.read(), mimetype='application/octet-stream')

	@file_upload
	def upload_certificate( self, request ):
		def _return( pid, status, bufstdout, bufstderr, request, fn ):
			success = True
			if status == 0:
				univention.config_registry.handler_set( [ u'connector/ad/ldap/certificate=%s' % fn ] )
				message = _( 'Certificate has been uploaded successfully.' )
				MODULE.info( 'Certificate has been uploaded successfully. status=%s\nSTDOUT:\n%s\n\nSTDERR:\n%s' % ( status, '\n'.join( bufstdout ), '\n'.join( bufstderr ) ) )
			else:
				success = False
				message = _( 'Certificate upload or conversion failed.' )
				MODULE.process( 'Certificate upload or conversion failed. status=%s\nSTDOUT:\n%s\n\nSTDERR:\n%s' % ( status, '\n'.join( bufstdout ), '\n'.join( bufstderr ) ) )

			self.finished( request.id, [ { 'success' : success, 'message' : message } ] )

		upload = request.options[ 0 ][ 'tmpfile' ]
		now = time.strftime( '%Y%m%d_%H%M%S', time.localtime() )
		fn = '/etc/univention/connector/ad/ad_cert_%s.pem' % now
		cmd = '/usr/bin/openssl x509 -inform der -outform pem -in %s -out %s 2>&1' % ( pipes.quote(upload), fn )

		MODULE.info( 'Converting certificate into correct format: %s' % cmd )
		proc = notifier.popen.Shell( cmd, stdout = True, stderr = True )
		cb = notifier.Callback( _return, request, fn )
		proc.signal_connect( 'finished', cb )
		proc.start()

	def service( self, request ):
		MODULE.info( 'State: options=%s' % request.options )
		self.required_options( request, 'action' )

		self.__update_status()
		action = request.options[ 'action' ]

		MODULE.info( 'State: action=%s  status_running=%s' % ( action, self.status_running ) )

		success = True
		message = None
		if self.status_running and action == 'start':
			message = _( 'Active Directory Connector is already running. Nothing to do.' )
		elif not self.status_running and action == 'stop':
			message =_( 'Active Directory Connector is already stopped. Nothing to do.' )
		elif action not in ( 'start', 'stop' ):
			MODULE.process( 'State: unknown command: action=%s' % action )
			message = _( 'Unknown command ("%s") Please report error to your local administrator' ) % action
			success = False

		if message is not None:
			self.finished( request.id, { 'success' : success, 'message' : message } )
			return

		def _run_it( action ):
			return subprocess.call( ( 'invoke-rc.d', 'univention-ad-connector', action ) )

		def _return( thread, result, request ):
			success = not result
			if result:
				message = _('Switching running state of Active Directory Connector failed.')
				MODULE.info( 'Switching running state of Active Directory Connector failed. exitcode=%s' % result )
			else:
				if request.options.get( 'action' ) == 'start':
					message = _( 'UCS Active Directory Connector has been started.' )
				else:
					message = _( 'UCS Active Directory Connector has been stopped.' )

			self.finished( request.id, { 'success' : success, 'message' : message } )

		cb = notifier.Callback( _return, request )
		func = notifier.Callback( _run_it, action )
		thread = notifier.threads.Simple( 'service', func, cb )
		thread.run()

	def __update_status( self ):
		ucr.load()
		fn = ucr.get( 'connector/ad/ldap/certificate' )
		self.status_certificate = bool( fn and os.path.exists( fn ) )
		self.status_running = self.__is_process_running( '*python*univention/connector/ad/main.py*' )
		self.status_mode_admember = admember.is_localhost_in_admember_mode(ucr)
		self.status_mode_adconnector = admember.is_localhost_in_adconnector_mode(ucr)

	def __is_process_running( self, command ):
		for proc in psutil.process_iter():
			if proc.cmdline and fnmatch.fnmatch( ' '.join( proc.cmdline ), command ):
				return True
		return False

	@sanitize(
		username=StringSanitizer(required=True),
		password=StringSanitizer(required=True),
		ad_server_ip=StringSanitizer(required=True),
	)
	@simple_response
	def admember_check_domain(self, username, password, ad_server_ip):
		try:
			admember.check_server_role()
			ad_domain_info = admember.lookup_adds_dc(ad_server_ip)
			admember.check_domain(ad_domain_info)
			admember.check_connection(ad_server_ip, username, password)
		except admember.invalidUCSServerRole as exc:
			MODULE.warn('Failure: %s' % exc)
			raise UMC_CommandError(_('The AD member mode cannot only be configured on a DC master server.'))
		except admember.failedADConnect as exc:
			MODULE.warn('Failure: %s' % exc)
			raise UMC_CommandError(_('Could not connect to AD Server %s. Please verify that the specified address is correct.') % ad_domain_info['DC DNS Name'])
		except admember.domainnameMismatch as exc:
			MODULE.warn('Failure: %s' % exc)
			raise UMC_CommandError(_('The domain name of the AD Server (%s) does not match the local UCS domain name (%s). For the AD member mode, it is necessary to setup a UCS system with the same domain name as the AD Server.') % (ad_domain_info["Domain"], ucr['domainname']))
		except admember.connectionFailed as exc:
			MODULE.warn('Failure: %s' % exc)
			raise UMC_CommandError(_('Could not connect to AD Server %s. Please verify that username and password are correct.') % ad_domain_info['DC DNS Name'])

		# final info dict that is returned... replace spaces in the keys with '_'
		MODULE.info('Preparing info dict...')
		info = dict([(key.replace(' ', '_'), value) for key, value in ad_domain_info.iteritems()])
		info['ssl_supported'] = admember.server_supports_ssl(server=ad_domain_info["DC DNS Name"])
		MODULE.info(str(info))
		return info

	@sanitize(
		username=StringSanitizer(required=True),
		password=StringSanitizer(required=True),
		ad_server_ip=StringSanitizer(required=True),
	)
	@simple_response(with_progress=True)
	def admember_join(self, username, password, ad_server_ip, progress):
		progress.title =_('Joining UCS into Active Directory domain')
		progress.total = 100

		def _progress(steps, msg):
			progress.current = steps
			progress.message = msg

		admember.check_server_role()
		ad_domain_info = admember.lookup_adds_dc(ad_server_ip)

		_progress(10, _('Configuring time synchronization...'))
		admember.time_sync(ad_server_ip)
		admember.set_timeserver(ad_server_ip)

		_progress(20, _('Configuring DNS server...'))
		admember.set_nameserver([ad_server_ip])
		admember.prepare_ucr_settings()
		admember.add_admember_service_to_localhost()

		_progress(30, _('Configuring Kerberos settings...'))
		admember.disable_local_heimdal()
		admember.disable_local_samba4()

		_progress(50, _('Configuring Administrator account...'))
		admember.prepare_administrator(username, password)

		_progress(60, _('Configuring software components...'))
		admember.remove_install_univention_samba()
		admember.run_samba_join_script(username, password)

		_progress(80, _('Configuring DNS entries...'))
		admember.add_domaincontroller_srv_record_in_ad(ad_server_ip)

		_progress(90, _('Configuring synchronization from AD...'))
		admember.prepare_connector_settings(username, password, ad_domain_info)

		if admember.server_supports_ssl(server=ad_domain_info["DC DNS Name"]):
			_progress(95, _('Configuring SSL settings...'))
			admember.enable_ssl()
		else:
			print "WARNING: ssl is not supported"
			admember.disable_ssl()

		_progress(100, _('Join has been finished successfully'))
		if hasattr(progress, 'result'):
			# some error probably occurred -> return the result in the progress
			return progress.result

		return {'success': True}
