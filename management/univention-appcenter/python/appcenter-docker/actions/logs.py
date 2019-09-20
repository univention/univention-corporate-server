#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for getting log output from a docker app
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

import subprocess

from univention.appcenter.actions import UniventionAppAction, StoreAppAction
from univention.appcenter.actions.docker_base import DockerActionMixin
from univention.appcenter.exceptions import ShellAppNotRunning

class Logs(UniventionAppAction, DockerActionMixin):

	'''Get log output of an app.'''
	help = 'Get log output of an app.'

	def setup_parser(self, parser):
		parser.add_argument('app', action=StoreAppAction, help='The ID of the App whose logs shall be output')

	def main(self, args):
		if not args.app.docker or not args.app.is_installed():
			self.log('ERROR: Currently the logs command only works for installed docker apps.')
			return

		return self.show_docker_logs(args)

	def show_docker_logs(self, args):
		docker = self._get_docker(args.app)
		self.log("#### 'docker logs {}' output:".format(docker.container))
		return subprocess.call(['docker', 'logs', docker.container])
