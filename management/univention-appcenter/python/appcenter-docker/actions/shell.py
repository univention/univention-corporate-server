#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for running commands in an app env
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
import shlex
from argparse import REMAINDER

from univention.appcenter.actions import UniventionAppAction, StoreAppAction
from univention.appcenter.exceptions import ShellNoCommandError, ShellAppNotRunning
from univention.appcenter.actions.docker_base import DockerActionMixin
from univention.appcenter.utils import app_is_running


class Shell(UniventionAppAction, DockerActionMixin):

	'''Run commands within a docker app.'''
	help = 'Run in app env'

	def setup_parser(self, parser):
		parser.add_argument('app', action=StoreAppAction, help='The ID of the App in whose environment COMMANDS shall be executed')
		parser.add_argument('commands', nargs=REMAINDER, help='Command to be run. Defaults to an interactive shell')
		parser.add_argument('-u', '--user', default='root', help='User used to run the command inside the container (default: %(default)s)')
		parser.add_argument('-i', '--interactive', action='store_true', default=False, help='Keep STDIN open even if not attached')
		parser.add_argument('-t', '--tty', action='store_true', default=False, help='Allocate a pseudo-TTY')

	def main(self, args):
		docker = self._get_docker(args.app)
		docker_exec = ['docker', 'exec', '-u', args.user]
		commands = args.commands[:]
		if not commands:
			commands = shlex.split(args.app.docker_shell_command)
			args.interactive = True
			args.tty = True
		if args.interactive:
			docker_exec.append('-i')
		if args.tty:
			docker_exec.append('-t')
		if not commands:
			raise ShellNoCommandError()
		if not app_is_running(args.app):
			raise ShellAppNotRunning(args.app)
		self.debug('Calling %s' % commands[0])
		return subprocess.call(docker_exec + [docker.container] + commands)
