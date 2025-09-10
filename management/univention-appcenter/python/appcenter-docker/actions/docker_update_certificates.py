#!/usr/bin/python3
#
# Univention App Center
#  univention-app module for configuring an app
#
# SPDX-FileCopyrightText: 2015-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os

from univention.appcenter.actions.docker_base import DockerActionMixin
from univention.appcenter.actions.update_certificates import UpdateCertificates
from univention.appcenter.ucr import ucr_get


class UpdateCertificates(UpdateCertificates, DockerActionMixin):

    def _copy_host_cert(self, docker, host_ssl_dir, dest):
        docker.execute('mkdir', '-p', dest, _logger=self.logfile_logger)
        docker.execute('chmod', '750', dest, _logger=self.logfile_logger)
        docker.cp_to_container(f'{host_ssl_dir}/cert.pem', f'{dest}/cert.perm', _logger=self.logfile_logger)
        docker.cp_to_container(f'{host_ssl_dir}/private.key', f'{dest}/private.key', _logger=self.logfile_logger)

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
                if os.path.isfile(f'{docker_host_cert}/cert.pem') and os.path.isfile(f'{docker_host_cert}/private.key'):
                    # canonical name
                    self._copy_host_cert(docker, docker_host_cert, '/etc/univention/ssl/docker-host-certificate')
                    # ucs name
                    self._copy_host_cert(docker, docker_host_cert, docker_host_cert)
            else:
                self.warn("Could not update certificates for %s, app is not running", app)
        super().update_certificates(app)
