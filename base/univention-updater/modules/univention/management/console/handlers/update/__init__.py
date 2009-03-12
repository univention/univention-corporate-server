#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: manage updates
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
import univention.management.console.categories as umcc
import univention.management.console.protocol as umcp
import univention.management.console.handlers as umch
import univention.management.console.dialog as umcd
import univention.management.console.tools as umct

import univention.debug as ud

import univention.config_registry

from univention.updater import UniventionUpdater

import os
import subprocess, string, time
import socket

_ = umc.Translation('univention.management.console.handlers.update').translate

icon = 'update/module'
short_description = _('Online updates')
long_description = _('Manage system updates')
categories = ['all', 'system']

UCR_ALLOWED_CHARACTERS = '^[^#:@]+$'

command_description = {
	'update/overview': umch.command(
		short_description = _('Overview'),
		long_description = _('Overview'),
		method = 'overview',
		values = { },
		startup = True,
		priority = 100,
		caching = False
	),
	'update/release_settings': umch.command(
		short_description = _('Release update settings'),
		long_description = _('Release update settings'),
		method = 'release_settings',
		values = {
			'repository_server': umc.String(_('Repository server')),
			'repository_prefix': umc.String(_('Repository prefix'), required = False),
			'use_hotfixes': umc.Boolean( _( 'Use hotfix repositories' ), required = False ),
			'use_maintained': umc.Boolean( _( 'Use maintained repositories' ), required = False ),
			'use_unmaintained': umc.Boolean( _( 'Use unmaintained repositories' ), required = False ),
			},
		caching = False
	),
	'update/check_release_updates': umch.command(
		short_description = _('Check for updates'),
		method = 'check_release_updates',
		values = { },
	),
	'update/components_update': umch.command(
		short_description = _('Check for updates'),
		method = 'components_update',
		values = { },
	),
	'update/components_settings': umch.command(
		short_description = _('Component settings'),
		method = 'components_settings',
		values = {
			'component_activated': umc.Boolean(_('Enabled'), required = False),
			'component_server': umc.String(_('Server'), required = False),
			'component_prefix': umc.String(_('Prefix'), required = False),
			'component_name': umc.String(_('Name')),
			'component_description': umc.String(_('Description'), required = False),
			'component_unmaintained': umc.String(_('Unmaintained'), required = False),
			'component_username': umc.String(_('Username'), required = False),
			'component_password': umc.String(_('Password'), required = False, regex = UCR_ALLOWED_CHARACTERS),
		},
	),
	'update/install_release_updates': umch.command(
		short_description = _('Installs a release update'),
		method = 'install_release_updates',
		values = { },
	),
	'update/install_security_updates': umch.command(
		short_description = _('Installs security updates'),
		method = 'install_security_updates',
		values = { },
	),
	'update/view_logfile': umch.command(
		short_description = _('View the logfile during the update' ),
		method = 'view_logfile',
		values = {
			'filename': umc.String( _( 'Name of the log file' ), required = False ),
		},
	),
	'update/update_warning': umch.command(
		short_description = _('View an update warning'),
		method = 'update_warning',
		values = {
		},
	),

}


class handler(umch.simpleHandler):

	def __init__(self):
		_d = ud.function('update.handler.__init__')

		global command_description

		umch.simpleHandler.__init__(self, command_description)

		self.updater = UniventionUpdater()

		self.next_release_update_checked = False
		self.next_release_update = None
		self.next_securtiy_update = None

		self.ucr_reinit = False


	def overview(self, object):
		_d = ud.function('update.handler.overview')
		self.finished(object.id(), None)

	def release_settings(self, object):
		_d = ud.function('update.handler.release_settings')

		reset = False
		set_variables = []

		if object.options.has_key('repository_server') and self.updater.repository_server != object.options[ 'repository_server' ]:
			ud.debug(ud.ADMIN, ud.INFO, 'Updater: release_settings: repository_server was set to: %s' % object.options['repository_server'])
			set_variables.append( 'repository/online/server=%s' % object.options['repository_server'] )
			self.updater.repository_server=object.options['repository_server']
			reset = True
		if object.options.has_key('repository_prefix'):
			if object.options['repository_prefix'] and object.options['repository_prefix'] != self.updater.repository_prefix:
				ud.debug(ud.ADMIN, ud.INFO, 'Updater: release_settings: repository_prefix was set to: %s' % object.options['repository_prefix'])
				set_variables.append( 'repository/online/prefix=%s' % object.options['repository_prefix'] )
				self.updater.repository_prefix=object.options['repository_prefix']
			else:
				univention.config_registry.handler_unset( [ 'repository/online/prefix' ] )
			reset = True
		ud.debug( ud.ADMIN, ud.INFO, 'Updater: release_settings: options: %s' % str( object.options ) )
		if object.options.has_key( 'use_hotfixes' ):
			ud.debug( ud.ADMIN, ud.INFO, 'Updater: release_settings: use_hotfixes was set to: %s' % object.options[ 'use_hotfixes' ] )
			if object.options[ 'use_hotfixes' ] and not self.updater.hotfixes:
				set_variables.append( 'repository/online/hotfixes=yes' )
			elif not object.options[ 'use_hotfixes' ] and self.updater.hotfixes:
				set_variables.append( 'repository/online/hotfixes=no' )
			self.updater.hotfixes = object.options[ 'use_hotfixes' ]
			reset = True

		if object.options.has_key( 'use_maintained' ):
			ud.debug( ud.ADMIN, ud.INFO, 'Updater: release_settings: use_maintained was set to: %s' % object.options[ 'use_maintained' ] )
			if object.options[ 'use_maintained' ]:
				if not 'maintained' in self.updater.parts:
					self.updater.parts.append( 'maintained' )
					set_variables.append( 'repository/online/maintained=yes' )
			else:
				if 'maintained' in self.updater.parts:
					self.updater.parts.remove( 'maintained' )
					set_variables.append( 'repository/online/maintained=no' )
			reset = True

		if object.options.has_key( 'use_unmaintained' ):
			ud.debug( ud.ADMIN, ud.INFO, 'Updater: release_settings: use_unmaintained was set to: %s' % object.options[ 'use_unmaintained' ] )
			if object.options[ 'use_unmaintained' ]:
				if not 'unmaintained' in self.updater.parts:
					self.updater.parts.append( 'unmaintained' )
					set_variables.append( 'repository/online/unmaintained=yes' )
			else:
				if 'unmaintained' in self.updater.parts:
					self.updater.parts.remove( 'unmaintained' )
					set_variables.append( 'repository/online/unmaintained=no' )
			reset = True

		if set_variables:
			univention.config_registry.handler_set( set_variables )

		if reset:
			self.next_release_update_checked = False

		self.finished(object.id(), None)


	def check_release_updates(self, object):
		ud.debug(ud.ADMIN, ud.INFO, 'Updater: check_release_updates')

		#TODO: check for an invalid repository server
		self.next_release_update_checked = True

		try:
			#TODO: check for the latest ucs version
			self.updater.ucr_reinit()
			self.next_release_update = self.updater.release_update_available()
			self.next_security_update = self.updater.security_update_available()
		except socket.gaierror, e:
			# connection to the repository server failed
			self.next_release_update_checked = False
			import traceback
			ud.debug(ud.ADMIN, ud.ERROR, 'updater: socket.gaierror: %s' % traceback.format_exc())
			error_message = _( 'The connection to the repository server failed: %s. Please check the repository configuration and the network connection.' ) % str( e[ 1 ] )
			self.finished(object.id(), None, error_message , success = False )
		except Exception, e:
			self.next_release_update_checked = False
			import traceback
			ud.debug(ud.ADMIN, ud.ERROR, 'updater: check_release_updates: %s' % traceback.format_exc())
			self.finished(object.id(), None, 'Failed to check the update: %s' % traceback.format_exc(), success = False)

		ud.debug(ud.ADMIN, ud.PROCESS, 'The nextupdate is %s' % self.next_release_update)

		self.finished(object.id(), None)


	def components_update(self, object):
		_d = ud.function('update.handler.components_update')

		status = object.options.get('status', None)
		if status == 'check':
			p1 = subprocess.Popen(['univention-config-registry commit /etc/apt/sources.list.d/20_ucs-online-component.list; LC_ALL=C apt-get update >/dev/null; LC_ALL=C apt-get -u dist-upgrade -s'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
			(stdout,stderr) = p1.communicate()
			ud.debug(ud.ADMIN, ud.PROCESS, 'check for updates with "dist-upgrade -s", the returncode is %d' % p1.returncode)
			ud.debug(ud.ADMIN, ud.PROCESS, 'stderr=%s' % stderr)
			ud.debug(ud.ADMIN, ud.INFO, 'stdout=%s' % stdout)

			new_packages = []
			upgraded_packages = []
			for line in stdout.split('\n'):
				if line.startswith('Inst '):
					line_split = line.split(' ')
					# upgrade:
					#   Inst univention-updater [3.1.1-5] (3.1.1-6.408.200810311159 192.168.0.10)
					# inst:
					#   Inst mc (1:4.6.1-6.12.200710211124 oxae-update.open-xchange.com)
					if len(line_split) == 5: #upgrade
						upgraded_packages.append((line_split[1], line_split[2].replace('[','').replace(']',''), line_split[3].replace('(','')))
					elif len(line_split) == 4: #upgrade
						new_packages.append((line_split[1], line_split[2].replace('(','')))
					else:
						continue

			update_text = ''
			if len(upgraded_packages) > 0:
				update_text += '<h2>' +_('The following packages will be upgraded:') + '</h2>'
				update_text += '<body>'
				for p in upgraded_packages:
					update_text += '&nbsp;&nbsp; %s %s' % (p[0],p[2])
					update_text += '<br>'
				update_text += '</body>'

			if len(new_packages) > 0:
				update_text += '<h2>' + _('The following NEW packages will be installed:') + '</h2>'
				update_text += '<body>'
				for p in new_packages:
					update_text += '&nbsp;&nbsp; %s %s' % (p[0],p[1])
					update_text += '<br>'
				update_text += '</body>'

			self.finished(object.id(), {'text': update_text})

		elif status == 'warning':
			self.finished(object.id(), None)

		elif status == 'execute':
			p1 = subprocess.Popen(['echo "Starting dist-upgrade at $(date)">>/var/log/univention/upgrade.log; DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Options::=--force-confold -y --force-yes -u dist-upgrade | tee -a /var/log/univention/upgrade.log 2>&1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
			(stdout,stderr) = p1.communicate()
			ud.debug(ud.ADMIN, ud.PROCESS, 'execute the update with "dist-upgrade", the returncode is %d' % p1.returncode)
			ud.debug(ud.ADMIN, ud.PROCESS, 'stderr=%s' % stderr)
			ud.debug(ud.ADMIN, ud.INFO, 'stdout=%s' % stdout)

			if p1.returncode == 0:
				self.finished(object.id(), stdout)
			else:
				if len(stderr) > 1:
					self.finished(object.id(), stderr, success=False)
				else:
					self.finished(object.id(), stdout, success=False)

	def components_settings(self, object):
		_d = ud.function('update.handler.components_settings')

		component_activated = object.options.get('component_activated', '')
		component_server = object.options.get('component_server', '')
		component_prefix = object.options.get('component_prefix', '')
		component_name = object.options.get('component_name', '')
		component_description = object.options.get('component_description', '')
		component_unmaintained = object.options.get('component_unmaintained', '')
		component_username = object.options.get('component_username', '')
		component_password = object.options.get('component_password', '')

		ud.debug(ud.ADMIN, ud.INFO, 'Component settings for %s' % component_name)
		if component_name:
			res = []
			if component_activated:
				res.append('repository/online/component/%s=enabled' % component_name)
			else:
				res.append('repository/online/component/%s=disabled' % component_name)
			if component_description:
				res.append('repository/online/component/%s/description=%s' % (component_name,component_description))
			if component_server:
				res.append('repository/online/component/%s/server=%s' % (component_name,component_server))
			if component_prefix:
				res.append('repository/online/component/%s/prefix=%s' % (component_name,component_prefix))
			if component_username:
				res.append('repository/online/component/%s/username=%s' % (component_name,component_username))
			if component_password:
				res.append('repository/online/component/%s/password=%s' % (component_name,component_password))
			ud.debug(ud.ADMIN, ud.INFO, 'Set the following component settings: %s' % res)
			univention.config_registry.handler_set(res)
			ud.debug(ud.ADMIN, ud.INFO, 'And reinit the updater modul')
			self.updater.ucr_reinit()

		self.finished(object.id(), None)

	def update_warning(self, object):
		_d = ud.function('update.handler.release_update_warning')
		self.finished(object.id(), None)

	def install_release_updates(self, object):
		_d = ud.function('update.handler.install_release_updates')


		(returncode, returnstring) = self.__create_at_job('univention-updater net --updateto %s' % self.next_release_update)
		self.logfile = '/var/log/univention/updater.log'
		ud.debug(ud.ADMIN, ud.PROCESS, 'Created the at job: univention-updater net --updateto %s' % self.next_release_update)

		if returncode != 0:
			self.finished(object.id(), None, returnstring, success = False)
		else:
			self.finished(object.id(), None)

	def install_security_updates(self, object):
		_d = ud.function('update.handler.install_security_updates')

		(returncode, returnstring) = self.__create_at_job('univention-security-update net' )
		self.logfile = '/var/log/univention/security-updates.log'
		ud.debug(ud.ADMIN, ud.PROCESS, 'Created the at job: univention-security-update net' )

		if returncode != 0:
			self.finished(object.id(), None, returnstring, success = False)
		else:
			self.finished(object.id(), None)

	def view_logfile(self, object):
		_d = ud.function('update.handler.view_logfile')

		p1 = subprocess.Popen(['tail -n 40 %s' % object.options[ 'filename' ] ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		(stdout,stderr) = p1.communicate()

		self.finished(object.id(), stdout)


	#######################
	# The revamp functions
	#######################


	# This revamp function shows the Overview site
	def _web_overview(self, object, res):
		_d = ud.function('update.handler._web_overview')

		#### Important Information

		frame_info = None
		# Is a reboot required?
		if self.updater.configRegistry.get( 'update/reboot/required', 'no' ) == 'yes':
			list_info = umcd.List()
			frame_info = umcd.Frame( [ list_info ], _( 'Important Information' ) )
			list_info.add_row( [ umcd.InfoBox( _( 'The system has been updated to a newer version of UCS. It is suggested that the system should be rebooted after the update. This has not been done yet.' ), columns = 2 ) ] )
			cmd = umcp.Command( args = [ 'reboot/do' ], opts = { 'action' : 'reboot', 'message' : _( 'Rebooting the system after an update' ) } )
			list_info.add_row( [ '', umcd.Button( _( 'Reboot System' ), 'actions/ok', actions = [ umcd.Action( cmd ) ] ) ] )
		#### UCS Releases
		list_release = umcd.List()

		# updater log button
		req = self.__get_logfile_request( '/var/log/univention/updater.log' )
		btn_install_release_update = umcd.Button( _( 'View logfile' ), 'actions/install', actions = [ umcd.Action( req ) ] )

		# security update log button
		req = self.__get_logfile_request( '/var/log/univention/security-updates.log' )
		btn_install_sec_update = umcd.Button( _( 'View logfile' ), 'actions/install', actions = [ umcd.Action( req ) ] )

		if self.__is_updater_running():
			list_release.add_row([umcd.Text(_('The Update is still in process')), btn_install_release_update])

		elif self.__is_security_update_running():
			list_release.add_row([umcd.Text(_('The Update is still in process')), btn_install_sec_update])

		else:
			req = umcp.Command(args=['update/release_settings'])
			req.set_flag('web:startup', True)
			req.set_flag('web:startup_cache', False)
			req.set_flag('web:startup_dialog', True)
			req.set_flag('web:startup_referrer', True)
			req.set_flag('web:startup_format', _('Release settings'))
			release_button = umcd.Button(_('UCS release'), 'update/gear', actions=[umcd.Action(req)])
			security_button = umcd.Button(_('Security patch level'), 'update/gear', actions=[umcd.Action(req)])
			if self.next_release_update_checked:
				if self.next_release_update:
					btn_install_release_update = umcd.Button(_('Install this update'), 'actions/install', actions = [umcd.Action(self.__get_warning_request({'type': 'release'}))])
					list_release.add_row([release_button,umcd.Text(_('The installed version is %(old)s and %(new)s is available.') % {'old': self.updater.get_ucs_version(), 'new': self.next_release_update}), btn_install_release_update])
				else:
					list_release.add_row([release_button,umcd.Text(_('The installed version is %s and there is no update available.') % self.updater.get_ucs_version())])

				if self.next_security_update:
					btn_install_security_update = umcd.Button(_('Install this update'), 'actions/install', actions = [umcd.Action(self.__get_warning_request({'type': 'security'}))])
					list_release.add_row([security_button, umcd.Text(_('The installed security release is %(old)s and %(new)s is available') % {'old':self.updater.security_patchlevel, 'new': self.next_security_update}), btn_install_security_update])
				else:
					list_release.add_row([security_button, umcd.Text(_('The installed security release is %s and there is no update available.') % self.updater.security_patchlevel)])

			else:
				list_release.add_row([release_button,umcd.Text(_('The installed version is %s.') % self.updater.get_ucs_version())])

				list_release.add_row([security_button, umcd.Text(_('The installed security release is %s') % self.updater.security_patchlevel)])


			req = umcp.Command(args=['update/check_release_updates'])
			btn_update_check = umcd.Button(_('Check for updates'), 'actions/refresh', actions = [umcd.Action(req), umcd.Action(umcp.Command(args=['update/overview']))])
			list_release.add_row([btn_update_check])

		#### UCS Components
		list_component = umcd.List()

		# TODO: check the components
		for component_name in self.updater.get_all_components():
			component = self.updater.get_component(component_name)
			description = component.get('description', component_name)
			req = umcp.Command(args=['update/components_settings'], opts = {'component': component})
			req.set_flag('web:startup', True)
			req.set_flag('web:startup_cache', False)
			req.set_flag('web:startup_dialog', True)
			req.set_flag('web:startup_referrer', True)
			req.set_flag('web:startup_format', _('Modify component %s' )  % description )
			if component.get('activated', '').lower() in ['true', 'yes', '1', 'enabled']:
				list_component.add_row([umcd.Button(description, 'update/gear', actions=[umcd.Action(req)]), umcd.Text(_('This component is enabled'))])
			else:
				list_component.add_row([umcd.Button(description, 'update/gear', actions=[umcd.Action(req)]), umcd.Text(_('This component is disabled'))])


		#TODO: show new components from the server

		req = umcp.Command(args=['update/components_update'], opts={'status': 'check'})
		req.set_flag('web:startup', True)
		req.set_flag('web:startup_cache', False)
		req.set_flag('web:startup_dialog', True)
		req.set_flag('web:startup_referrer', False)
		req.set_flag('web:startup_format', _('Check for updates'))
		btn_update_check = umcd.Button(_('Check for updates'), 'actions/refresh', actions = [umcd.Action(req)])

		req = umcp.Command(args=['update/components_settings'])
		req.set_flag('web:startup', True)
		req.set_flag('web:startup_cache', False)
		req.set_flag('web:startup_dialog', True)
		req.set_flag('web:startup_referrer', True)
		req.set_flag('web:startup_format', _('Add a new component'))
		btn_add_component = umcd.Button(_('Add a new component'), 'actions/plus', actions = [umcd.Action(req)])

		list_component.add_row([btn_update_check, btn_add_component])

		frame_release = umcd.Frame([list_release], _('Release information'))
		frame_component = umcd.Frame([list_component], _('Components'))

		res.dialog = [frame_release, frame_component]
		if frame_info:
			res.dialog.insert( 0, frame_info )

		self.revamped(object.id(), res)


	def _web_release_settings(self, object, res):
		_d = ud.function('update.handler._web_release_settings')

		list_release = umcd.List()

		frame_release = umcd.Frame([list_release], _('Release settings'))
		inpt_server = umcd.make(self['update/release_settings']['repository_server'], default = self.updater.repository_server)
		inpt_prefix = umcd.make(self['update/release_settings']['repository_prefix'], default = self.updater.repository_prefix)
		inpt_hotfixes = umcd.make( self[ 'update/release_settings' ][ 'use_hotfixes' ], default = self.updater.hotfixes )
		inpt_maintained = umcd.make( self[ 'update/release_settings' ][ 'use_maintained' ], default = 'maintained' in self.updater.parts )
		inpt_unmaintained = umcd.make( self[ 'update/release_settings' ][ 'use_unmaintained' ], default = 'unmaintained' in self.updater.parts )

		list_release.add_row( [ inpt_server, inpt_prefix ] )
		list_release.add_row( [ '', '' ] )
		list_release.add_row( [ inpt_maintained, inpt_unmaintained ] )
		list_release.add_row( [ inpt_hotfixes, '' ] )
		req = umcp.Command(args = ['update/release_settings'])
		cancel = umcd.CancelButton()
		list_release.add_row( [ '', '' ] )
		list_release.add_row( [ umcd.SetButton( umcd.Action( req, [ inpt_server.id(), inpt_prefix.id(), inpt_hotfixes.id(), inpt_maintained.id(), inpt_unmaintained.id() ] ) ), cancel ] )


		res.dialog = [frame_release]

		self.revamped(object.id(), res)

	def _web_view_logfile(self, object, res):
		_d = ud.function('update.handler._web_view_logfile')
		result = umcd.List()

		if self.__is_updater_running() or self.__is_security_update_running():
			log = res.dialog
			html = '<h2>' + _('The updater is still in process.') + '</h2>' + '<pre>' + _('Please be patient the update may take a while. Press the refresh button to see the latest log.') + '</pre>' + '<body>' + self.__remove_status_messages(log) + '</body>'
			result.add_row([ umcd.HTML(html, attributes = { 'colspan' : str(2) })])
			btn_refresh = umcd.Button(_('Refresh'), 'actions/refresh', actions = [umcd.Action(self.__get_logfile_request())])
			result.add_row([ btn_refresh, umcd.CloseButton()])
		else:
			html = '<h2>' + _('The updater finished.') + '</h2>'
			log = res.dialog
			html +=  '<body>' + self.__remove_status_messages(log) + '</body>'
			result.add_row([ umcd.HTML(html, attributes = { 'colspan' : str(2) })])
			result.add_row([ umcd.CloseButton()])

		res.dialog = [ result]
		self.revamped(object.id(), res)


	def _web_components_settings(self, object, res):
		_d = ud.function('update.handler._web_components_settings res=%s' % res.options)

		activated = False
		name = ''
		description = ''
		server = ''
		prefix = ''
		username = ''
		password = ''

		# build the default values
		if res.options.has_key('component'):
			activated_component = res.options['component'].get('activated', '')
			if activated_component.lower() in ['true', 'yes', '1', 'enabled']:
				activated = True
			else:
				activated = False

			name = res.options['component'].get('name', '')
			description = res.options['component'].get('description', '')
			server = res.options['component'].get('server', '')
			prefix = res.options['component'].get('prefix', '')
			username = res.options['component'].get('username', '')
			password = res.options['component'].get('password', '')

		if not server:
			server=self.updater.repository_server
		if not prefix:
			prefix=self.updater.repository_prefix


		list_release = umcd.List()

		frame_release = umcd.Frame([list_release], _('Component settings'))

		inpt_activated = umcd.make(self['update/components_settings']['component_activated'], default = activated)
		inpt_name = umcd.make(self['update/components_settings']['component_name'], default = name)
		inpt_description = umcd.make(self['update/components_settings']['component_description'], default = description)
		# TODO: add a check button
		inpt_server = umcd.make(self['update/components_settings']['component_server'], default = server)
		inpt_prefix = umcd.make(self['update/components_settings']['component_prefix'], default = prefix)
		inpt_username = umcd.make(self['update/components_settings']['component_username'], default = username)
		inpt_password = umcd.make(self['update/components_settings']['component_password'], default = password)

		list_release.add_row([inpt_activated])
		list_release.add_row([inpt_name, inpt_description])
		list_release.add_row([inpt_server, inpt_prefix])
		list_release.add_row([inpt_username, inpt_password])

		req = umcp.Command(args = ['update/components_settings'])
		cancel = umcd.CancelButton()
		list_release.add_row([umcd.SetButton(umcd.Action(req, [inpt_activated.id(), inpt_name.id(), inpt_description.id(), inpt_server.id(), inpt_prefix.id(), inpt_username.id(), inpt_password.id()])), cancel])


		res.dialog = [frame_release]
		self.revamped(object.id(), res)

	def _web_components_update(self, object, res):
		_d = ud.function('update.handler._web_components_update')

		result = umcd.List()

		if object.options['status'] == 'check':
			if len(res.dialog['text']) > 0:
				result.add_row([ umcd.HTML(res.dialog['text'], attributes = { 'colspan' : str(2) })])
				req = umcp.Command(args=['update/components_update'], opts={'status': 'warning'})
				req.set_flag('web:startup', True)
				req.set_flag('web:startup_cache', False)
				req.set_flag('web:startup_dialog', True)
				req.set_flag('web:startup_referrer', False)
				req.set_flag('web:startup_format', _('Confirm the updater warning'))
				btn_continue = umcd.Button(_('Continue'), 'actions/ok', actions = [umcd.Action(req)])

				result.add_row([ btn_continue, umcd.CancelButton()])
			else:
				result.add_row([ umcd.HTML('<h2>' + _('No updates available') + '</h2>')])
				result.add_row([ umcd.CancelButton()])
		elif object.options['status'] == 'warning':
			html = self.__get_update_warning()

			result.add_row([ umcd.HTML(html, attributes = { 'colspan' : str(2) })])
			req = umcp.Command(args=['update/components_update'], opts={'status': 'execute'})
			req.set_flag('web:startup', True)
			req.set_flag('web:startup_cache', False)
			req.set_flag('web:startup_dialog', True)
			req.set_flag('web:startup_referrer', False)
			req.set_flag('web:startup_format', _('Execute the update'))
			btn_continue = umcd.Button(_('Continue'), 'actions/ok', actions = [umcd.Action(req)])

			result.add_row([ btn_continue, umcd.CancelButton()])
		elif object.options['status'] == 'execute':
			html = '<h2>' + _('The updater finished.') + '</h2>'
			if res.dialog:
				html += '<body>' + self.__remove_status_messages(res.dialog) + '</body>'
			result.add_row([ umcd.HTML(html, attributes = { 'colspan' : str(2) })])
			result.add_row([ umcd.CloseButton()])

		res.dialog = [ result]
		self.revamped(object.id(), res)

	def _web_update_warning(self, object, res):
		_d = ud.function('update.handler._web_update_warning')

		result = umcd.List()

		if res.options['type'] == 'security':
			command = 'update/install_security_updates'
		else:
			command = 'update/install_release_updates'

		html = self.__get_update_warning()

		result.add_row([ umcd.HTML(html, attributes = { 'colspan' : str(2) })])
		req = umcp.Command(args=[command])
		btn_continue = umcd.Button(_('Continue'), 'actions/ok', actions = [umcd.Action(req), umcd.Action(self.__get_logfile_request())])

		result.add_row([ btn_continue, umcd.CancelButton()])
		res.dialog = [ result]
		self.revamped(object.id(), res)


	#######################
	# Some helper scripts
	#######################

	def __create_at_job(self, command):
		script = '''
chmod -x /usr/sbin/apache2 /usr/sbin/univention-management-console-server
%s
if [ $? -eq 0 ]; then
	univention-config-registry set update/reboot/required=yes
fi
chmod +x /usr/sbin/apache2 /usr/sbin/univention-management-console-server
''' % command
		p1 = subprocess.Popen(['echo "%s" | at now' % script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		(stdout,stderr) = p1.communicate()
		ud.debug(ud.ADMIN, ud.WARN, 'executing "%s"' % command)
		ud.debug(ud.ADMIN, ud.WARN, 'install stderr=%s' % stderr)
		ud.debug(ud.ADMIN, ud.INFO, 'install stdout=%s' % stdout)
		# TODO: this should be solved in another way,
		# we have to wait a few seconds otherwise the updater process haven't started yet
		time.sleep(8)
		if p1.returncode != 0:
			return (p1.returncode,stderr)
		else:
			return (p1.returncode,stdout)

	def __is_process_running(self, command):
		p1 = subprocess.Popen(['ps -ef | egrep "%s" | grep -v grep' % command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		(stdout,stderr) = p1.communicate()
		if p1.returncode == 0:
			if len(stdout) < 1:
				p1 = subprocess.Popen(['atq  | awk "{print $1}" | while read num; do p=$(at -c $num | grep %s); if [ -n "$p"]; then echo "%s is running"; fi ; done' % (command, command)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
				(stdout,stderr) = p1.communicate()
				if p1.returncode == 0 and len(stdout) > 1:
					return True
				return False
			else:
				return True
		else:
			return False


	def __is_updater_running(self):
		# TODO: also check the at jobs
		return self.__is_process_running('python.* /usr/sbin/univention-updater net')


	def __is_security_update_running(self):
		# TODO: also check the at jobs
		return self.__is_process_running('python.* /usr/sbin/univention-security-update net')


	def __remove_status_messages(self, text):
		result = []
		for line in text.split('\n'):
			if line.startswith('\r'):
				continue
			result.append(line)
		return string.join(result, '\n').replace('\n', '<br />')


	def __get_update_warning(self):
		html = '<h2>' + _('Attention!') + '</h2>' + '<body>'
		html += _('Installing an system update is a significant change to your IT environment.<br>')
		html += _('In the normal case, undisturbed use operation cannot be guaranteed during the update,<br>')
		html += _('since system services may need to be restarted. Thus, updates shouldn\'t be installed<br>')
		html += _('on a live system. It is also recommend to evaluate the update in a test environment<br>')
		html += _('and to create a backup of the system.')
		html += '<br><br>'
		html += _('During setup, the web server may be stopped, leading to a termination of the HTTP<br>')
		html += _('connection. Nonetheless, the update proceeds and the update can be monitored from a<br>')
		html += _('new UMC session. Logfiles can be found in the directory /var/log/univention/.')
		html += '<br><br>'
		html += _('Please also consider the release notes, changelogs and references posted in the<br>')
		html += _('<a href=http://forum.univention.de>Univention Forum</a>.')
		html += '<br><br>'
		html += _('Do you really wish to proceed?')
		html += '<br><br>'
		html += '</body>'

		return html


	def __get_logfile_request( self, filename = None ):
		req = umcp.Command( args = [ 'update/view_logfile' ] )
		if filename:
			req.options[ 'filename' ] = filename
		else:
			req.options[ 'filename' ] = '/var/log/univention/updater.log'

		req.set_flag('web:startup', True)
		req.set_flag('web:startup_cache', False)
		req.set_flag('web:startup_dialog', True)
		req.set_flag('web:startup_referrer', False)
		req.set_flag('web:startup_format', _('Show the update process'))

		return req

	def __get_warning_request(self, options = None):
		req = umcp.Command(args=['update/update_warning'], opts = options)
		req.set_flag('web:startup', True)
		req.set_flag('web:startup_cache', False)
		req.set_flag('web:startup_dialog', True)
		req.set_flag('web:startup_referrer', False)
		req.set_flag('web:startup_format', _('Confirm the updater warning'))
		return req

	def __is_logfile_available( self, filename ):
		if os.path.isfile( filename ):
			try:
				size = os.stat( filename )[ 6 ]
				if size > 0:
					return True
			except:
				pass

		return False
