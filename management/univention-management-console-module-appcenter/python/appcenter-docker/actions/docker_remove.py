#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for uninstalling an app
#  (docker version)
#
# Copyright 2015 Univention GmbH
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

import os

from univention.config_registry import ConfigRegistry

from univention.appcenter.docker import Docker
from univention.appcenter.actions.remove import Remove
from univention.appcenter.actions.service import Stop
from univention.appcenter.actions.docker_base import DockerActionMixin
from univention.appcenter.udm import remove_object_if_exists

class Remove(Remove, DockerActionMixin):
	def setup_parser(self, parser):
		super(Remove, self).setup_parser(parser)
		parser.add_argument('--keep-data', action='store_true', help='Do not store the current data. New installations will not be able to restore them')

	def _do_it(self, app, args):
		self._unregister_host(app, args)
		self.percentage = 5
		super(Remove, self)._do_it(app, args)

	def _unregister_host(self, app, args):
		ucr = ConfigRegistry()
		ucr.load()
		hostdn = ucr.get(app.ucr_hostdn_key)
		if not hostdn:
			self.log('No hostdn for %s found. Nothing to remove' % app.id)
			return
		lo, pos = self._get_ldap_connection(args)
		remove_object_if_exists('computers/%s' % app.docker_server_role, lo, pos, hostdn)

	def _remove_app(self, app, args):
		if not app.docker:
			super(Remove, self)._remove_app(app, args)
		else:
			self._remove_docker_image(app, args)

	def _remove_docker_image(self, app, args):
		Stop.call(app=app)
		if not args.keep_data:
			docker = Docker(app, self.logger)
			if docker.container:
				docker.rm()

	def _unregister_app(self, app, args):
		try:
			os.unlink(Stop.get_init(app))
		except OSError:
			pass
		return super(Remove, self)._unregister_app(app, args)

