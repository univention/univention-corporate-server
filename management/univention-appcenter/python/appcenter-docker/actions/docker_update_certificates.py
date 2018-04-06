#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for configuring an app
#
# Copyright 2015-2018 Univention GmbH
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

from univention.appcenter.actions.update_certificates import UpdateCertificates
from univention.appcenter.actions.docker_base import DockerActionMixin
from univention.appcenter.ucr import ucr_get

import os

class UpdateCertificates(UpdateCertificates, DockerActionMixin):

	def setup_parser(self, parser):
		super(UpdateCertificates, self).setup_parser(parser)

	def update_certificates(self, app):
		hostname = ucr_get(app.ucr_hostdn_key).split('=', 1)[1].split(',', 1)[0]
		domain = ucr_get('domainname')
		fqdn = hostname + '.' + domain
		if app.docker:
			docker = self._get_docker(app)
			if docker.is_running:
				# update-ca-certificates, debian, ubuntu, appbox
				if docker.execute('which', 'update-ca-certificates', _logger=self.logfile_logger).returncode == 0:
					if os.path.isfile('/etc/univention/ssl/ucsCA/CAcert.pem'):
						docker.execute('mkdir', '-p', '/usr/local/share/ca-certificates', _logger=self.logfile_logger)
						docker.cp_to_container('/etc/univention/ssl/ucsCA/CAcert.pem', '/usr/local/share/ca-certificates/ucs.crt', _logger=self.logfile_logger)
						docker.execute('update-ca-certificates', _logger=self.logfile_logger)
				# appboox ca cert
				ca_path = '/etc/univention/ssl/ucsCA/CAcert.pem'
				if docker.execute('test', '-e', '/etc/univention/ssl/ucsCA/CAcert.pem', _logger=self.logfile_logger).returncode == 0:
					if os.path.isfile(ca_path):
						docker.cp_to_container(ca_path, ca_path, _logger=self.logfile_logger)
				# appbox computer certs
				if docker.execute('test', '-d', '/etc/univention/ssl/{0}'.format(fqdn), _logger=self.logfile_logger).returncode == 0:
					for c_file in ['cert.pem', 'private.key']:
						c_path = '/etc/univention/ssl/{0}/{1}'.format(fqdn, c_file)
						if os.path.isfile(c_path):
							docker.cp_to_container(c_path, c_path, _logger=self.logfile_logger)
			else:
				self.warn('Could not update certificates for {0}, app is not running'.format(app))
		super(UpdateCertificates, self).update_certificates(app)
