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

from univention.appcenter.actions import StoreAppAction
from univention.appcenter.actions.docker_upgrade import Upgrade


class Reinitialize(Upgrade):
	'''Reinitilizes a Docker App. Essentially removes the container and
	re-creates it with the current settings. Useful for starting the
	container with changed environment variables.'''
	help = 'Reinitilize Docker App. Mainly used internally.'

	def setup_parser(self, parser):
		parser.add_argument('app', action=StoreAppAction, help='The ID of the App in whose environment COMMANDS shall be executed')

	def main(self, args):
		app = args.app
		if not app.docker:
			self.warn('Only works for Docker Apps')
			return
		if not app.is_installed():
			self.warn('Only works for installed Apps')
			return
		self.old_app = app
		if app.docker_script_setup:
			self.warn('Cannot reinitialize an App with a setup script: Credentials are not passed')
			return
		_args = self._build_namespace(
			call_join_scripts=False,
			configure=False,
			update_certificates=True,
			send_info=False,
			dry_run=False,
			only_master_packages=False,
			skip_checks=[],
			install_master_packages_remotely=False,
			revert=False,
			username=None,
			pwdfile=None,
			password=None,
			set_vars={},
			register_attributes=False,
			register_host=False,
			pull_image=True,
			remove_image=False,
			backup=True,
			noninteractive=True)
		self._upgrade_image(app, _args)
