#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: AD connector
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

from univention.lib import Translation
from univention.management.console.modules import Base
from univention.management.console.log import MODULE
from univention.management.console.config import ucr

import notifier.popen

import fnmatch
import psutil
import os, stat, shutil

import subprocess, time, grp

import string, ldap

_ = Translation('univention-management-console-module-top').translate

FN_BINDPW = '/etc/univention/connector/ad/bindpw'
DIR_WEB_AD = '/var/www/univention-ad-connector'
DO_NOT_CHANGE_PWD = '********************'

class Instance( Base ):
	def configure( self, request ):

class handler(umch.simpleHandler):

	def __init__(self):
		self.status_configured = False
		self.status_certificate = False
		self.status_running = False
		self.guessed_baseDN = None
		self.msg = { 'error': [],
					 'warn': [],
					 'hint': [] }

		self.__update_status()

	def configure(self, obj):
		self.msg = { 'error': [],
					 'warn': [],
					 'hint': [] }
		self.guessed_baseDN = None

		if obj.options.get('action','') == 'save':
			# if action == "save" then save values to UCR

			try:
				fn = '%s/.htaccess' % DIR_WEB_AD
				fd = open( fn, 'w' )
				fd.write('require user %s\n' % self._username)
				fd.close()
				os.chmod( fn, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH )
				os.chown( fn, 0, 0 )
			except Exception, e:
				self.msg['error'].append( _('An error occured while saving .htaccess (filename=%(fn)s ; exception=%(exception)s)') % { 'fn': fn, 'exception': str(e.__class__)})
				debugmsg( ud.ADMIN, ud.ERROR, 'An error occured while saving .htaccess (filename=%(fn)s ; exception=%(exception)s)' % { 'fn': fn, 'exception': str(e.__class__)} )

			for umckey, ucrkey in ( ( 'ad_ldap_host', 'connector/ad/ldap/host' ),
									( 'ad_ldap_base', 'connector/ad/ldap/base' ),
									( 'ad_ldap_binddn', 'connector/ad/ldap/binddn' ),
									( 'ad_kerberosdomain', 'connector/ad/mapping/kerberosdomain' ),
									( 'ad_poll_sleep', 'connector/ad/poll/sleep' ),
									( 'ad_retry_rejected', 'connector/ad/retryrejected' ),
									( 'debug_level', 'connector/debug/level' ),
									( 'debug_function', 'connector/debug/function' ),
									( 'ad_mapping_sync_mode', 'connector/ad/mapping/syncmode' ),
									( 'ad_mapping_group_language', 'connector/ad/mapping/group/language' ),
									):
				val = obj.options.get(umckey)
				# Workaround for Bug #13139 START
				if umckey in [ 'debug_level', 'debug_function' ]:
					val = val.strip('_')
				# Workaroung for Bug #13139 END
				if val:
					debugmsg( ud.ADMIN, ud.INFO, 'setting %s=%s' % (ucrkey, val) )
					univention.config_registry.handler_set( [ u'%s=%s' % (ucrkey, val) ] )

			self.configRegistry.load() # reload UCR cache
			if self.configRegistry.get('connector/ad/ldap/ldaps'):
				debugmsg( ud.ADMIN, ud.INFO, 'unsetting connector/ad/ldap/ldaps' )
				univention.config_registry.handler_unset( [ u'connector/ad/ldap/ldaps' ] )
			if self.configRegistry.get('connector/ad/ldap/port') == '636':
				debugmsg( ud.ADMIN, ud.INFO, 'setting ldap port to 389' )
				univention.config_registry.handler_set( [ u'connector/ad/ldap/port=389' ] )

			if not obj.options.get('ad_ldap_bindpw') in [ None, '', DO_NOT_CHANGE_PWD ]:
				fn = self.configRegistry.get('connector/ad/ldap/bindpw', FN_BINDPW)
				try:
					fd = open( fn ,'w')
					fd.write( obj.options.get('ad_ldap_bindpw') )
					fd.close()
					os.chmod( fn, stat.S_IRUSR | stat.S_IWUSR )
					os.chown( fn, 0, 0 )
				except Exception, e:
					self.msg['error'].append( _('saving bind password failed (filename=%(fn)s ; exception=%(exception)s)') % { 'fn': fn, 'exception': str(e.__class__)})
					debugmsg( ud.ADMIN, ud.ERROR, 'saving bind password failed (filename=%(fn)s ; exception=%(exception)s)' % { 'fn': fn, 'exception': str(e.__class__)} )
				univention.config_registry.handler_set( [ u'connector/ad/ldap/bindpw=%s' % FN_BINDPW ] )

			self.msg['hint'].append( _('Active Directory Connector settings have been saved.') )

		if obj.options.get('action','') == 'save':

			if os.path.exists( '/etc/univention/ssl/%s' % obj.options.get('ad_ldap_host') ):
				self._copy_certificate( obj )
				self.finished(obj.id(), None)
			else:
				cmd = 'univention-certificate new -name "%s"' % obj.options.get('ad_ldap_host')
				debugmsg( ud.ADMIN, ud.INFO, 'creating new SSL certificate: %s' % cmd )
				proc = notifier.popen.Shell( cmd, stdout = True )
				cb = notifier.Callback( self._configure_create_cert_return, obj )
				proc.signal_connect( 'finished', cb )
				proc.start()

		elif obj.options.get('action','') == 'guess_basedn' and obj.options.get('ad_ldap_host'):

			# if FQDN has been set and ldap_base is unknown then call ldapsearch to determine ldap_base
			cmd = 'ldapsearch -x -s base -b "" namingContexts -LLL -h "%s"' % obj.options.get('ad_ldap_host')
			debugmsg( ud.ADMIN, ud.INFO, 'determine baseDN of specified system: %s' % cmd )
			proc = notifier.popen.Shell( cmd, stdout = True )
			cb = notifier.Callback( self._configure_guess_basedn_return, obj )
			proc.signal_connect( 'finished', cb )
			proc.start()

		else:
			self.finished(obj.id(), None)


	def _copy_certificate(self, obj, error_if_missing = False):
		ssldir = '/etc/univention/ssl/%s' % obj.options.get('ad_ldap_host')
		try:
			gid_wwwdata = grp.getgrnam('www-data')[2]
		except:
			gid_wwwdata = 0
		if os.path.exists( ssldir ):
			for fn in ( 'private.key', 'cert.pem' ):
				dst = '%s/%s' % (DIR_WEB_AD, fn)
				try:
					shutil.copy2( '%s/%s' % (ssldir, fn), dst )
					os.chmod( dst, stat.S_IRUSR | stat.S_IRGRP )
					os.chown( dst, 0, gid_wwwdata )
				except Exception, e:
					self.msg['error'].append( _('copy of %s/%s to %s/%s failed (exception=%s)') % (ssldir, fn, DIR_WEB_AD, fn, str(e.__class__)) )
					debugmsg( ud.ADMIN, ud.ERROR, 'copy of %s/%s to %s/%s failed (exception=%s)' % (ssldir, fn, DIR_WEB_AD, fn, str(e.__class__)) )
		else:
			if error_if_missing:
				self.msg['error'].append( _('creation of certificate failed (%s)') % ssldir )
				debugmsg( ud.ADMIN, ud.ERROR, 'creation of certificate failed (%s)' % ssldir )


	def _configure_create_cert_return( self, pid, status, buffer, obj ):
		_d = ud.function('adconnector.handler._configure_create_cert_return')
		self._copy_certificate( obj, error_if_missing=True )
		self.finished(obj.id(), None)


	def _configure_guess_basedn_return( self, pid, status, buffer, obj ):
		_d = ud.function('adconnector.handler._configure_guess_basedn_return')
		# dn:
		# namingContexts: DC=ad,DC=univention,DC=de
		# namingContexts: CN=Configuration,DC=ad,DC=univention,DC=de
		# namingContexts: CN=Schema,CN=Configuration,DC=ad,DC=univention,DC=de
		# namingContexts: DC=DomainDnsZones,DC=ad,DC=univention,DC=de
		# namingContexts: DC=ForestDnsZones,DC=ad,DC=univention,DC=de

		self.guessed_baseDN = None
		for line in buffer:
			debugmsg( ud.ADMIN, ud.INFO, 'guess_basedn: line="%s"' % line )
			if line.startswith('namingContexts: '):
				dn = line.split(': ',1)[1].strip()
				if self.guessed_baseDN == None or len(dn) < len(self.guessed_baseDN):
					self.guessed_baseDN = dn

		if self.guessed_baseDN == None:
			self.msg['warn'].append( _('Could not determine baseDN of given ldap server. Maybe FQDN is wrong or unresolvable!') )
			debugmsg( ud.ADMIN, ud.ERROR, 'Could not determine baseDN of given ldap server. Maybe FQDN is wrong or unresolvable! FQDN=%s' % obj.options.get('ad_ldap_host') )

		debugmsg( ud.ADMIN, ud.INFO, 'guessed baseDN: %s' % self.guessed_baseDN )

		self.finished(obj.id(), None)

	def upload_cert(self, obj):
		_d = ud.function('adconnector.handler.upload_cert')
		debugmsg( ud.ADMIN, ud.INFO, 'upload_cert: options=%s' % obj.options )

		self.msg = { 'error': [],
					 'warn': [],
					 'hint': [] }

		files = obj.options.get('certfile',[])
		if len(files) == 1:
			fileitem = files[0]
			now = time.strftime( '%Y%m%d_%H%M%S', time.localtime() )
			fn = '/etc/univention/connector/ad/ad_cert_%s.pem' % now
			cmd = 'openssl x509 -inform der -outform pem -in %s -out %s 2>&1' % (fileitem['tmpfname'], fn)

			debugmsg( ud.ADMIN, ud.INFO, 'converting certificate into correct format: %s' % cmd )
			proc = notifier.popen.Shell( cmd, stdout = True, stderr = True )
			cb = notifier.Callback( self._upload_cert_return, obj, fn )
			proc.signal_connect( 'finished', cb )
			proc.start()
		else:
			debugmsg( ud.ADMIN, ud.ERROR, 'len(files)=%s  files=%s' % (len(files), files) )
			self.finished(obj.id(), None)


	def _upload_cert_return( self, pid, status, bufstdout, bufstderr, obj, fn ):
		_d = ud.function('adconnector.handler._upload_cert_return')
		if status == 0:
			univention.config_registry.handler_set( [ u'connector/ad/ldap/certificate=%s' % fn ] )
			self.msg['hint'].append( _('Certificate has been uploaded successfully.') )
			debugmsg( ud.ADMIN, ud.INFO, 'Certificate has been uploaded successfully. status=%s\nSTDOUT:\n%s\n\nSTDERR:\n%s' % (status, '\n'.join(bufstdout), '\n'.join(bufstderr)))
		else:
			self.msg['error'].append( _('Certificate upload or conversion failed.') )
			debugmsg( ud.ADMIN, ud.ERROR, 'Certificate upload or conversion failed. status=%s\nSTDOUT:\n%s\n\nSTDERR:\n%s' % (status, '\n'.join(bufstdout), '\n'.join(bufstderr)))

		self.finished(obj.id(), None)


	def setstate(self, obj):
		_d = ud.function('adconnector.handler.setstate')
		debugmsg( ud.ADMIN, ud.INFO, 'setstate: options=%s' % obj.options )

		self.msg = { 'error': [],
					 'warn': [],
					 'hint': [] }

		self.__update_status()
		action = obj.options.get('action')

		debugmsg( ud.ADMIN, ud.INFO, 'action=%s  status_running=%s' % (action, self.status_running) )

		if self.status_running and action == 'start':

			self.msg['hint'].append( _('Active Directory Connector is already running. Nothing to do.') )

		elif not self.status_running and action == 'stop':

			self.msg['hint'].append( _('Active Directory Connector is already stopped. Nothing to do.') )

		elif action in ['start', 'stop']:

			cb = notifier.Callback( self._state_changed, obj )
			func = notifier.Callback( self._run_it, action )
			thread = notifier.threads.Simple( 'service', func, cb )
			thread.run()

		elif len(action):
			self.msg['error'].append( _('Unknown command ("%s") Please report error to your local administrator') % action )
			debugmsg( ud.ADMIN, ud.ERROR, 'unknown command: action=%s' % action )

		else:
			# no action given
			self.finished(obj.id(), None)


	def _run_it( self, action ):
		_d = ud.function('adconnector.handler._run_it')
		return subprocess.call( ( 'invoke-rc.d', 'univention-ad-connector', action ) )


	def _state_changed( self, thread, result, obj ):
		_d = ud.function('adconnector.handler._state_changed')
		if result:
			self.msg['error'].append( _('Switching running state of Active Directory Connector failed.') )
			debugmsg( ud.ADMIN, ud.ERROR, 'Switching running state of Active Directory Connector failed. exitcode=%s' % result )
		else:
			if obj.options.get('action') == 'start':
				self.msg['hint'].append( _('Active Directory Connector has been started.') )
			else:
				self.msg['hint'].append( _('Active Directory Connector has been stopped.') )
		self.finished(obj.id(), None)



	#######################
	# The revamp functions
	#######################


	def __get_request(self, cmd, title, opts = {}):
		req = umcp.Command(args=[ cmd ], opts = opts)

		req.set_flag('web:startup', True)
		req.set_flag('web:startup_cache', False)
		req.set_flag('web:startup_dialog', True)
		req.set_flag('web:startup_referrer', False)
		req.set_flag('web:startup_format', title)

		return req


	def __update_status(self):
		ucr.load()
		self.status_configured = ucr.get( 'connector/ad/ldap/host' ) and ucr.get( 'connector/ad/ldap/base' ) and ucr.get( 'connector/ad/ldap/binddn' ) and ucr.get( 'connector/ad/ldap/bindpw' )
		fn = ucr.get( 'connector/ad/ldap/certificate' )
		self.status_certificate = ( fn and os.path.exists( fn ) )
		self.status_running = self.__is_process_running( '*python*univention/connector/ad/main.py*' )

	def __is_process_running( self, command ):
		for proc in psutil.process_iter():
			if fnmatch.fnmatch( proc.cmdline, command ):
				return True
		return False
