#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for running an app container
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

import shlex
from argparse import REMAINDER

from univention.appcenter.actions import UniventionAppAction, StoreAppAction
from univention.appcenter.actions.docker_base import DockerActionMixin


class Run(UniventionAppAction, DockerActionMixin):

	'''Essentially a wrapper around docker run.'''
	help = 'Run an app container'

	def setup_parser(self, parser):
		parser.add_argument('app', action=StoreAppAction, help='The ID of the App in whose environment COMMANDS shall be executed')
		parser.add_argument('commands', nargs=REMAINDER, help='Command to be run. Defaults to an interactive shell')
		parser.add_argument('--do-not-remove', default='store_false', dest='remove', help='Keep container after the command has been run')
		parser.add_argument('--entrypoint', help='Use another entrypoint than the App\'s default one')


	def main(self, args):
		commands = args.commands[:]
		if not args.app.docker or not args.app.one_shot:
			self.fatal('%s is not supported' % args.app.id)
			return False
		if not commands:
			commands = shlex.split(args.app.docker_shell_command)
		image = args.app.get_docker_image_name()
		self.debug('Calling %s: %r' % (image, commands))
		docker = self._get_docker(args.app)
		return docker.run(commands, entrypoint=args.entrypoint, remove=args.remove)
