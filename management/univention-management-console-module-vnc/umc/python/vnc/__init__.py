#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: VNC client
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

import os
import socket
import subprocess

from univention.lib.i18n import Translation

import univention.info_tools as uit
import univention.management.console.modules as umcm
from univention.management.console.log import MODULE
from univention.management.console.config import ucr
from univention.management.console.protocol.definitions import *

_ = Translation('univention-management-console-module-vnc').translate

class Instance(umcm.Base):
	def _get_status(self):
		vnc_dir = os.path.join('/home', self._username, '.vnc')
		if os.path.isfile(os.path.join(vnc_dir, 'passwd')):
			passwd_exists = True
		else:
			passwd_exists = False

		is_running = False
		if os.path.isdir(vnc_dir):
			for item in os.listdir(vnc_dir):
				if os.path.isfile(os.path.join(vnc_dir, item)) and item.endswith('.pid'):
					try:
						fd = open(os.path.join(vnc_dir, item), 'r')
						pid = fd.readline()[: -1]
						fd.close()
						if os.path.isfile(os.path.join('/proc', pid, 'cmdline')):
							is_running = True
					except:
						pass
					break
		return is_running, passwd_exists

	def _get_cmdline(self):
		vnc_dir = os.path.join('/home', self._username, '.vnc')
		pidfile = None
		if os.path.isdir(vnc_dir):
			for item in os.listdir(vnc_dir):
				if os.path.isfile(os.path.join(vnc_dir, item)) and item.endswith('.pid'):
					pidfile = os.path.join(vnc_dir, item)
					break

		if not pidfile:
			return ()

		fd = open(pidfile, 'r')
		pid = fd.readline()[: -1]
		fd.close()
		try:
			fd = open(os.path.join('/proc', pid, 'cmdline'), 'r')
			cmdline = fd.readline()[: -1]
			fd.close()
			return cmdline.split('\x00')
		except:
			os.unlink(pidfile)
			pass
		return ()

	def status(self, request):
		message = None
		if self.permitted('vnc/status', request.options):
			(is_running, passwd_exists, ) = self._get_status()
			result = {'isRunning': is_running, 'isSetPassword': passwd_exists}
			request.status = SUCCESS
			self.finished(request.id, result)
		else:
			message = _('You are not permitted to run this command.')
			request.status = MODULE_ERR
			self.finished(request.id, None, message)

	def start(self, request):
		message = None
		(is_running, passwd_exists, ) = self._get_status()
		result = 0
		if not is_running:
			result = subprocess.call(('/bin/su', '-',  self._username, '-c',
			                          'vncserver -geometry 1024x768'))

		if result == 0:
			message = _('Server successfully started')
			request.status = SUCCESS
		else:
			message = _('Could not start server')
			request.status = MODULE_ERR

		self.finished(request.id, None, message)

	def stop(self, request):
		message = None
		(is_running, passwd_exists, ) = self._get_status()
		if is_running:
			args = self._get_cmdline()
			if '-rfbport' in args:
				port = args[args.index('-rfbport') + 1]
				port = int(port) - 5900
				subprocess.call(('/bin/su', '-', self._username, '-c',
				                 'vncserver -kill :%d' % port))
				message = _('Server successfully stopped')

		self.finished(request.id, None, message)

	def connect(self, request):
		url = None
		(is_running, passwd_exists, ) = self._get_status()
		port = None
		host = None
		if is_running:
			args = self._get_cmdline()
			if '-rfbport' in args:
				port = args[args.index('-rfbport') + 1]

			fqdn = '%s.%s' % ( ucr.get( 'hostname' ), ucr.get( 'domainname' ) )
			VNC_LINK_BY_NAME, VNC_LINK_BY_IPV4, VNC_LINK_BY_IPV6 = range(3)
			vnc_link_format = VNC_LINK_BY_IPV4
			if vnc_link_format == VNC_LINK_BY_IPV4:
				addrs = socket.getaddrinfo( fqdn, port, socket.AF_INET )
				(family, socktype, proto, canonname, sockaddr) = addrs[0]
				host = sockaddr[0]
			elif vnc_link_format == VNC_LINK_BY_IPV6:
				addrs = socket.getaddrinfo( fqdn, port, socket.AF_INET6 )
				(family, socktype, proto, canonname, sockaddr) = addrs[0]
				host = '[%s]' % sockaddr[0]

		self.finished( request.id, { 'port': port, 'host' : host } )

	def set_password(self, request):
		message = None
		if self.permitted('vnc/password', request.options):
			# TODO: Check result
			cmd = ('/bin/su', '-', self._username, '-c',
			       '/usr/share/univention-management-console-module-vnc/univention-vnc-setpassword %s' % request.options['password'])
			if subprocess.call(cmd):
				message = _('Could not set password')
				request.status = MODULE_ERR
			else:
				message = _('Successfully set password')
				request.status = SUCCESS
			self.finished(request.id, None, message)
		else:
			message = _('You are not permitted to run this command.')
			request.status = MODULE_ERR
			self.finished(request.id, None, message)
