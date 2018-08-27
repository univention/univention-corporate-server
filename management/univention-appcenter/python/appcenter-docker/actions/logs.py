#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for getting log output from a docker app
#
# Copyright 2015-2017 Univention GmbH
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
#

import subprocess

from univention.appcenter.actions import UniventionAppAction, StoreAppAction
from univention.appcenter.actions.docker_base import DockerActionMixin
from univention.appcenter.exceptions import ShellAppNotRunning

class Logs(UniventionAppAction, DockerActionMixin):

	'''Get log output from a docker app.'''
	help = 'Get log output from a docker app.'

	def setup_parser(self, parser):
		parser.add_argument('app', action=StoreAppAction, help='The ID of the App whose logs shall be output')
		parser.add_argument('--details', action='store_true', default=False, help='Show extra details provided to logs')
		parser.add_argument('-f', '--follow', action='store_true', default=False, help='Follow log output')
		parser.add_argument('--tail', action='store', metavar='int', help='Number of lines to show from the end of the logs')
		parser.add_argument('--since', action='store', metavar='timestamp', help='Show logs since timestamp')
		parser.add_argument('-t', '--timestamps', action='store_true', default=False, help='Show timestamps')


	def main(self, args):
		docker = self._get_docker(args.app)
		docker_logs = ['docker', 'logs']
		if args.details:
			docker_logs.append('--details')
		if args.follow:
			docker_logs.append('--follow')
		if args.since:
			docker_logs.append('--since')
			docker_logs.append(args.since)
		if args.tail:
			docker_logs.append('--tail')
			docker_logs.append(args.tail)
		if args.timestamps:
			docker_logs.append('--timestamps')
		if not args.app.docker:
			raise ShellAppNotRunning(args.app)
		return subprocess.call(docker_logs + [docker.container])
