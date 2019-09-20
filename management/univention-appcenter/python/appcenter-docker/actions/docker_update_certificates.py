#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for configuring an app
#
# Copyright 2015-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

from univention.appcenter.actions.update_certificates import UpdateCertificates
from univention.appcenter.actions.docker_base import DockerActionMixin
from univention.appcenter.ucr import ucr_get

import os


class UpdateCertificates(UpdateCertificates, DockerActionMixin):

	def _copy_host_cert(self, docker, host_ssl_dir, dest):
		docker.execute('mkdir', '-p', dest, _logger=self.logfile_logger)
		docker.execute('chmod', '750', dest, _logger=self.logfile_logger)
		docker.cp_to_container('{0}/cert.pem'.format(host_ssl_dir), '{0}/cert.perm'.format(dest), _logger=self.logfile_logger)
		docker.cp_to_container('{0}/private.key'.format(host_ssl_dir), '{0}/private.key'.format(dest), _logger=self.logfile_logger)

	def update_certificates(self, app):
		hostname = ucr_get('hostname')
		domain = ucr_get('domainname')
		docker_host_cert = '/etc/univention/ssl/' + hostname + '.' + domain
		if app.docker:
			docker = self._get_docker(app)
			if docker.is_running():
				ca_path = '/etc/univention/ssl/ucsCA/CAcert.pem'
				if os.path.isfile(ca_path):
					# update-ca-certificates, debian, ubuntu, appbox
					docker.execute('mkdir', '-p', '/usr/local/share/ca-certificates', _logger=self.logfile_logger)
					docker.cp_to_container(ca_path, '/usr/local/share/ca-certificates/ucs.crt', _logger=self.logfile_logger)
					if docker.execute('which', 'update-ca-certificates', _logger=self.logfile_logger).returncode == 0:
						docker.execute('update-ca-certificates', _logger=self.logfile_logger)
					# appboox ca cert
					docker.execute('mkdir', '-p', '/etc/univention/ssl/ucsCA/', _logger=self.logfile_logger)
					docker.cp_to_container(ca_path, ca_path, _logger=self.logfile_logger)
				# docker host cert canonical name and ucs path
				if os.path.isfile('{0}/cert.pem'.format(docker_host_cert)) and os.path.isfile('{0}/private.key'.format(docker_host_cert)):
					# canonical name
					self._copy_host_cert(docker, docker_host_cert, '/etc/univention/ssl/docker-host-certificate')
					# ucs name
					self._copy_host_cert(docker, docker_host_cert, docker_host_cert)
			else:
				self.warn('Could not update certificates for {0}, app is not running'.format(app))
		super(UpdateCertificates, self).update_certificates(app)
