#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manage ad connector
#
# Copyright (C) 2009 Univention GmbH
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
import univention.management.console.categories as umcc
import univention.management.console.protocol as umcp
import univention.management.console.handlers as umch
import univention.management.console.dialog as umcd
import univention.management.console.tools as umct

import univention.debug as ud

import univention.config_registry

import notifier.popen
import os, stat, shutil

import subprocess, time, grp

FN_BINDPWD = '/etc/univention/connector/ad/bindpwd'
DIR_WEB_AD = '/var/www/univention-ad-connector'

_ = umc.Translation('univention.management.console.handlers.adconnector').translate

icon = 'adconnector/module'
short_description = _('AD Connector')
long_description = _('Configure AD Connector')
categories = ['all', 'system']

class UMC_AD_StaticSelection( umc.StaticSelection ):
	def __init__( self, required = True, title = '', choices = () ):
		umc.StaticSelection.__init__( self, unicode( title ), required = required )
		self.default_choices_list = choices
	def choices( self ):
		return self.default_choices_list
umcd.copy( umc.StaticSelection, UMC_AD_StaticSelection )


command_description = {
	'adconnector/overview': umch.command(
		short_description = _('Overview'),
		long_description = _('Overview'),
		method = 'overview',
		values = { },
		startup = True,
		priority = 100,
		caching = False
	),
	'adconnector/configure': umch.command(
		short_description = _('Configure AD Connector'),
		long_description = _('Configure AD Connector'),
		method = 'configure',
		values = {
			'action': umc.String( _('action') ),
			'ad_ldap_host': umc.String( _('Hostname of Active Directory server'), regex = '^([a-z]([a-z0-9-]*[a-z0-9])*[.])+[a-z]([a-z0-9-]*[a-z0-9])*$' ),
			'ad_ldap_base': umc.String( _('BaseDN of Active Directory') ),
			'ad_ldap_binddn': umc.String( _('DN of replication user') ),
			'ad_ldap_bindpw': umc.Password( _('Password of replication user'), required = False ),
			'ad_poll_sleep': umc.String( _('Poll Interval (seconds)'), regex = '^[0-9]+$' ),
			'ad_windows_version': UMC_AD_StaticSelection( title=_('Version of Windows server'),
													choices = ( ( 'win2000', _( 'Windows 2000' ) ), ( '', _( 'Windows 2003' ) ) ) ),
			'ad_retry_rejected': umc.String( _('Retry interval for rejected objects'), regex = '^[0-9]+$' ),
			# Workaround for Bug #13139: '_0_' up to '_4_' is a workaround
			'debug_level': UMC_AD_StaticSelection( title=_('Debug level of AD Connector'),
													choices = ( ( '_0_', _( '0' ) ), ( '_1_', _( '1' ) ), ( '_2_', _( '2' ) ), ( '_3_', _( '3' ) ), ( '_4_', _( '4' ) ) ) ),
			# Workaround for Bug #13139: '_0_' and '_1_' is a workaround
			'debug_function': UMC_AD_StaticSelection( title=_('Add debug output for functions'),
													choices = ( ( '_0_', _( 'no' ) ), ( '_1_', _( 'yes' ) ) ) ),
			'ad_mapping_sync_mode': UMC_AD_StaticSelection( title=_('AD Connector sync mode'),
															choices = (	( 'read', _( 'read (AD --> UCS)' ) ),
																		( 'write', _( 'write (UCS --> AD)' ) ),
																		( 'sync', _( 'sync (AD <--> UCS)' ) ) ) ),
			'ad_mapping_group_language': umc.LanguageSelection( _('AD Connector group mapping language') ),
			},
		caching = False
	),

	'adconnector/uploadcert': umch.command(
		short_description = _('Upload AD Connector Certificate'),
		long_description = _('Upload AD Connector Certificate'),
		method = 'upload_cert',
		values = {
			'certfile': umc.FileUploader( _('Please upload Active Directory certificate'), maxfiles=1 ),
			},
		caching = False
	),

	'adconnector/switchstate': umch.command(
		short_description = _('Start/Stop AD Connector'),
		long_description = _('Start/Stop AD Connector'),
		method = 'start_stop',
		values = {
			'action': umc.String( 'action' ),
			},
		caching = False
	),
}


import inspect
def debugmsg( component, level, msg ):
	info = inspect.getframeinfo(inspect.currentframe().f_back)[0:3]
	printInfo=[]
	if len(info[0])>25:
		printInfo.append('...'+info[0][-22:])
	else:
		printInfo.append(info[0])
	printInfo.extend(info[1:3])
	ud.debug(component, level, "%s:%s: %s" % (printInfo[0], printInfo[1], msg))


class handler(umch.simpleHandler):

	def __init__(self):
		_d = ud.function('adconnector.handler.__init__')

		umch.simpleHandler.__init__(self, command_description)

		self.configRegistry = univention.config_registry.ConfigRegistry()
		self.configRegistry.load()
		self.status_configured = False
		self.status_certificate = False
		self.status_running = False
		self.guessed_baseDN = None
		self.msg = { 'error': [],
					 'warn': [],
					 'hint': [] }

		self.__update_status()



	def overview(self, obj):
		_d = ud.function('adconnector.handler.overview')
		self.msg = { 'error': [],
					 'warn': [],
					 'hint': [] }
		self.finished(obj.id(), None)



	def configure(self, obj):
		_d = ud.function('adconnector.handler.configure')
		debugmsg( ud.ADMIN, ud.INFO, 'configure: options=%s' % obj.options )

		self.msg = { 'error': [],
					 'warn': [],
					 'hint': [] }
		self.guessed_baseDN = None

		debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 1' )

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

			debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 10' )

			for umckey, ucrkey in ( ( 'ad_ldap_host', 'connector/ad/ldap/host' ),
									( 'ad_ldap_base', 'connector/ad/ldap/base' ),
									( 'ad_ldap_binddn', 'connector/ad/ldap/binddn' ),
									( 'ad_poll_sleep', 'connector/ad/poll/sleep' ),
									( 'ad_retry_rejected', 'connector/ad/retryrejected' ),
									( 'debug_level', 'connector/debug/level' ),
									( 'debug_function', 'connector/debug/function' ),
									( 'ad_mapping_sync_mode', 'connector/ad/mapping/syncmode' ),
									( 'ad_mapping_group_language', 'connector/ad/mapping/language' ),
									):
				val = obj.options.get(umckey)
				if val:
					# Workaround for Bug #13139 START
					if umckey in [ 'debug_level', 'debug_function' ]:
						val = val.strip('_')
					# Workaroung for Bug #13139 END
					debugmsg( ud.ADMIN, ud.INFO, 'setting %s=%s' % (umckey, val) )
					univention.config_registry.handler_set( [ u'%s=%s' % (ucrkey, val) ] )

			# special handling for connector/ad/windows_version
			val = obj.options.get('ad_windows_version')
			if obj.options.get( val ):
					debugmsg( ud.ADMIN, ud.INFO, 'setting %s=%s' % (umckey, val) )
					univention.config_registry.handler_set( [ u'%s=%s' % (ucrkey, val) ] )
			else:
					debugmsg( ud.ADMIN, ud.INFO, 'unsetting %ss' % (umckey) )
					univention.config_registry.handler_unset( [ u'%s' % ucrkey ] )

			debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 11' )

			if obj.options.get('ad_ldap_bindpw'):
				fn = self.configRegistry.get('connector/ad/ldap/bindpwd', FN_BINDPWD)
				try:
					fd = open( fn ,'w')
					fd.write( obj.options.get('ad_ldap_bindpw') )
					fd.close()
					os.chmod( fn, stat.S_IRUSR | stat.S_IWUSR )
					os.chown( fn, 0, 0 )
				except Exception, e:
					self.msg['error'].append( _('saving bind password failed (filename=%(fn)s ; exception=%(exception)s)') % { 'fn': fn, 'exception': str(e.__class__)})
					debugmsg( ud.ADMIN, ud.ERROR, 'saving bind password failed (filename=%(fn)s ; exception=%(exception)s)' % { 'fn': fn, 'exception': str(e.__class__)} )
				univention.config_registry.handler_set( [ u'connector/ad/ldap/bindpw=%s' % FN_BINDPWD ] )

			self.msg['hint'].append( _('AD connector settings have been saved.') )
			debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 22' )
		debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 23' )

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
			debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 3' )
			self.finished(obj.id(), None)

		debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 4' )



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

		debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 10' )
		debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: buffer=%s' % buffer )
		self.guessed_baseDN = None
		for line in buffer:
			debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: line="%s"' % line )
			if line.startswith('namingContexts: '):
				debugmsg( ud.ADMIN, ud.INFO, line )
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

		files = umcobject.options.get('fileupload',[])
		if len(files) == 1:
			fileitem = files[0]
			now = time.strftime( '%Y%m%d_%H%M%S', time.localtime() )
			fn = '/etc/univention/connector/ad/ad_cert_%s.pem' % now
			cmd = 'openssl x509 -inform der -outform pem -in %s -out %s' % (fileitem['tmpfname'], fn)

			debugmsg( ud.ADMIN, ud.INFO, 'determine baseDN of specified system: %s' % cmd )
			proc = notifier.popen.Shell( cmd, stdout = True )
			cb = notifier.Callback( self._upload_cert_return, obj, fn )
			proc.signal_connect( 'finished', cb )
			proc.start()
		else:
			debugmsg( ud.ADMIN, ud.ERROR, 'ERROR: len(files)=%s  files=%s' % (len(files), files) )
			self.finished(obj.id(), None)


	def _upload_cert_return( self, pid, status, buffer, obj, fn ):
		_d = ud.function('adconnector.handler._upload_cert_return')
		if status == 0:
			univention.config_registry.handler_set( [ u'connector/ad/ldap/certificate=%s' % fn ] )
			self.msg['hint'].append( _('Certificate has been uploaded successfully.') )
			debugmsg( ud.ADMIN, ud.INFO, _('Certificate has been uploaded successfully.') )
		else:
			self.msg['error'].append( _('Certificate upload and conversion failed.') )
			debugmsg( ud.ADMIN, ud.ERROR, _('Certificate upload and conversion failed. status=%s  output=%s' % (status, buffer)) )

		self.finished(obj.id(), None)


	#######################
	# The revamp functions
	#######################


	def bool2yesno(self, val):
		if val:
			return _('yes')
		return _('no')


	def __get_request(self, cmd, title):
		req = umcp.Command(args=[ cmd ])

		req.set_flag('web:startup', True)
		req.set_flag('web:startup_cache', False)
		req.set_flag('web:startup_dialog', True)
		req.set_flag('web:startup_referrer', False)
		req.set_flag('web:startup_format', title)

		return req


	def __update_status(self):
		self.configRegistry.load()
		self.status_configured = (  self.configRegistry.get('connector/ad/ldap/host') and \
									self.configRegistry.get('connector/ad/ldap/base') and \
									self.configRegistry.get('connector/ad/ldap/binddn') and \
									self.configRegistry.get('connector/ad/ldap/bindpw')
									)
		self.status_certificate = False
		self.status_running = self.__is_process_running('python.* /usr/sbin/univention-ad-connector')


	def __is_process_running(self, command):
		p1 = subprocess.Popen(['ps -ef | egrep "%s" | grep -v grep' % command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		p1.communicate()
		return (p1.returncode == 0)   # p1.returncode is 0 if process is running


	# This revamp function shows the Overview site
	def _web_overview(self, obj, res):
		_d = ud.function('adconnector.handler._web_overview')

		self.__update_status()

		#### AD Connector Status Frame
		list_status = umcd.List()

		list_status.add_row( [ umcd.Text( _('Configured:') ), umcd.Text( self.bool2yesno( self.status_configured ) ) ] )
		list_status.add_row( [ umcd.Text( _('AD certificate installed:') ), umcd.Text( self.bool2yesno( self.status_certificate ) ) ] )
		list_status.add_row( [ umcd.Text( _('Running:') ), umcd.Text( self.bool2yesno( self.status_running ) ) ] )

		frame_status = umcd.Frame( [list_status], _('AD connector status'))


		#### AD Connector Actions Frame
		list_actions = umcd.List()


		btn_configure = umcd.Button(_('Configure AD connector'), 'actions/configure',
									actions = [ umcd.Action( self.__get_request( 'adconnector/configure', _('Configure AD Connector') ) ) ] )
		list_actions.add_row( [ btn_configure ] )


		img = umcd.Link( description = _('IMG'),                                       link='/univention-ad-connector/', icon=icon )
		btn = umcd.Link( description = _('Download .msi package and UCS certificate'), link='/univention-ad-connector/' )
		list_actions.add_row( [ (img,btn) ] )


		btn_upload_cert = umcd.Button(_('Upload AD certificate'), 'actions/configure',
									 actions = [ umcd.Action( self.__get_request( 'adconnector/uploadcert', _('Upload AD certificate') ) ) ] )
		list_actions.add_row( [ btn_upload_cert ] )


		if self.status_running:
			title = _('Stop AD connector')
		else:
			title = _('Start AD connector')
		btn_startstop = umcd.Button( title, 'actions/configure',
									actions = [ umcd.Action( self.__get_request( 'adconnector/startstop', title ) ) ] )
		list_actions.add_row( [ btn_startstop ] )


		frame_actions = umcd.Frame( [list_actions], _('Actions'))


		res.dialog = [frame_status, frame_actions]

		self.revamped(obj.id(), res)


	# This revamp function shows the Overview site
	def _web_configure(self, obj, res):
		_d = ud.function('adconnector.handler._web_configure')
		debugmsg( ud.ADMIN, ud.INFO, 'web_configure: options=%s' % obj.options )

		self.__update_status()

		list_id = []

		debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 20' )

		# ask for ldap_host
		if obj.options.get('action','') == 'guess_basedn':
			ldaphost = obj.options.get('ad_ldap_host')
		else:
			ldaphost = self.configRegistry.get('connector/ad/ldap/host', '')
		inp_ldap_host = umcd.make( self['adconnector/configure']['ad_ldap_host'], default = ldaphost )
		list_id.append( inp_ldap_host.id() )

		# create guess basedn button
		opts = { 'action': 'guess_basedn' }
		req = umcp.Command( args = [ 'adconnector/configure' ], opts = opts )
		actions = ( umcd.Action( req, [ inp_ldap_host.id() ] ), )
		btn_guess = umcd.Button( _('Determine BaseDN'), 'actions/ok', actions = actions, close_dialog = False )

		debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 21' )

		# ask for ldap_base and/or display a first guess based on ldapsearch call
		if obj.options.get('action','') == 'guess_basedn' and self.guessed_baseDN:
			basedn = self.guessed_baseDN
			if basedn:
				self.msg['hint'].append( _('BaseDN of %s has been determined successfully. Suggestion for replication user has been set.') % obj.options.get('ad_ldap_host') )
				debugmsg( ud.ADMIN, ud.ERROR, 'BaseDN of %s has been determined successfully. Suggestion for replication user has been set.' % obj.options.get('ad_ldap_host') )
		else:
			basedn = self.configRegistry.get('connector/ad/ldap/base', '')
		inp_ldap_base = umcd.make( self['adconnector/configure']['ad_ldap_base'], default = basedn )
		list_id.append( inp_ldap_base.id() )

		# ask for ldap_binddn and/or display a first guess based on ldapsearch call
		if obj.options.get('action','') == 'guess_basedn' and self.guessed_baseDN:
			binddn = 'cn=Administrator,cn=users,%s' % basedn
		else:
			binddn = self.configRegistry.get('connector/ad/ldap/binddn', '')
		inp_ldap_binddn = umcd.make( self['adconnector/configure']['ad_ldap_binddn'], default = binddn )
		list_id.append( inp_ldap_binddn.id() )

		debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 22' )

		# get bind password if UCR variable is already set and file exists
		pwd = ''
		fn = self.configRegistry.get('connector/ad/ldap/bindpwd')
		if not fn or not os.path.exists( fn ):
			self.msg['hint'].append( _('Password of replication user has not been set yet!') )
			debugmsg( ud.ADMIN, ud.WARN, 'Password of replication user has not been set yet' )

		# ask for ldap_bindpwd
		inp_ldap_bindpwd = umcd.make( self['adconnector/configure']['ad_ldap_bindpw'], default = '' )
		list_id.append( inp_ldap_bindpwd.id() )

		# ask for windows version
		inp_windows_version = umcd.make( self['adconnector/configure']['ad_windows_version'], default = self.configRegistry.get('connector/ad/windows_version', '') )
		list_id.append( inp_windows_version.id() )

		# ask for mapping syncmode
		inp_sync_mode = umcd.make( self['adconnector/configure']['ad_mapping_sync_mode'], default = self.configRegistry.get('connector/ad/mapping/syncmode', 'sync') )
		list_id.append( inp_sync_mode.id() )

		# ask for mapping language
		inp_mapping_language = umcd.make( self['adconnector/configure']['ad_mapping_group_language'], default = self.configRegistry.get('connector/ad/mapping/group/language', 'de') )
		list_id.append( inp_mapping_language.id() )

		# ask for retry rejected
		inp_retry_rejected = umcd.make( self['adconnector/configure']['ad_retry_rejected'], default = self.configRegistry.get('connector/ad/retryrejected', '10') )
		list_id.append( inp_retry_rejected.id() )

		# ask for poll_sleep
		inp_poll_sleep = umcd.make( self['adconnector/configure']['ad_poll_sleep'], default = self.configRegistry.get('connector/ad/poll/sleep', '5') )
		list_id.append( inp_poll_sleep.id() )
		debugmsg( ud.ADMIN, ud.ERROR, 'DEBUG: 23' )

		# ask for debug level
		inp_debug_level = umcd.make( self['adconnector/configure']['debug_level'], default = self.configRegistry.get('connector/debug/level', '_1_') )
		list_id.append( inp_debug_level.id() )

		# ask for debug level
		inp_debug_function = umcd.make( self['adconnector/configure']['debug_function'], default = self.configRegistry.get('connector/debug/function', '_0_') )
		list_id.append( inp_debug_function.id() )


		# create save button
		opts = { 'action': 'save' }
		req = umcp.Command( args = [ 'adconnector/configure' ], opts = opts )
		actions = ( umcd.Action( req, list_id ), )
		btn_set = umcd.Button( _('Save Changes'), 'actions/ok', actions = actions, close_dialog = False )

		btn_close = umcd.CloseButton()

		# create layout
		list_items = umcd.List()

		list_items.add_row( [ inp_ldap_host, inp_ldap_base ] )
		list_items.add_row( [ inp_ldap_binddn, inp_ldap_bindpwd ] )
		list_items.add_row( [ inp_windows_version, inp_sync_mode ] )
		list_items.add_row( [ inp_mapping_language, inp_retry_rejected ] )
		list_items.add_row( [ inp_debug_level, inp_poll_sleep ] )
		list_items.add_row( [ inp_debug_function ] )
		list_items.add_row( [ btn_guess ] )
		list_items.add_row( [ btn_set, btn_close ] )
		frame = umcd.Frame( [list_items], _('AD Connector Configuration'))

		res.dialog = []
		if self.msg['error'] or self.msg['warn'] or self.msg['hint']:
			lst = umcd.List()
			for key in ( 'error', 'warn', 'hint' ):
				for msg in self.msg[key]:
					img = umcd.Image( 'adconnector/%s' % key )
					txt = umcd.Text( msg )
					lst.add_row( [ ( img, txt ) ] )
			res.dialog.append( umcd.Frame( [lst], _('Messages') ) )

		res.dialog.append(frame)

		self.revamped(obj.id(), res)




