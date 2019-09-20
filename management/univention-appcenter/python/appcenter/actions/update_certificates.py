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
#

from univention.appcenter.actions import UniventionAppAction, StoreAppAction
from univention.appcenter.app_cache import Apps
from univention.appcenter.utils import get_locale
from univention.appcenter.log import get_logfile_logger

from tempfile import NamedTemporaryFile


class UpdateCertificates(UniventionAppAction):

	'''Update certificates for an application.'''
	help = 'Update certificates for an app'

	def setup_parser(self, parser):
		super(UpdateCertificates, self).setup_parser(parser)
		parser.add_argument('apps', nargs='*', action=StoreAppAction, help='The ID of app for which the certificates should be updated (all locally installed if none given)')

	def update_certificates(self, app):
		self._run_update_certificates_script(app)

	def main(self, args):
		if not args.apps:
			args.apps = Apps().get_all_locally_installed_apps()
		self.logfile_logger = get_logfile_logger('update-certificates')
		for app in args.apps:
			self.log('updating certificates for {0}'.format(app))
			self.update_certificates(app)

	def _run_update_certificates_script(self, app):
		ext = 'update_certificates'
		with NamedTemporaryFile('r+b') as error_file:
			kwargs = {}
			kwargs['version'] = app.version
			kwargs['error_file'] = error_file.name
			locale = get_locale()
			if locale:
				kwargs['locale'] = locale
			success = self._call_cache_script(app, ext, **kwargs)
			if success is False:
				for line in error_file:
					self.fatal(line)
			return success
