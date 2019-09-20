#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app base module for freezing an app
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
from univention.appcenter.ucr import ucr_save


class Stall(UniventionAppAction):

	'''Disbales updates for this app. Useful for suppressing
	warnings when an app reached its end of life but shall still
	be used.'''
	help = 'Stalls an app'

	def setup_parser(self, parser):
		parser.add_argument('app', action=StoreAppAction, help='The ID of the App that shall be stalled')
		parser.add_argument('--undo', action='store_true', help='Reenable a previously stalled app')

	def main(self, args):
		if not args.app.is_installed():
			self.fatal('%s is not installed!' % args.app.id)
			return
		if args.undo:
			self._undo_stall(args.app)
		else:
			self._stall(args.app)

	def _undo_stall(self, app):
		ucr_save({app.ucr_status_key: 'installed', app.ucr_component_key: 'enabled'})

	def _stall(self, app):
		ucr_save({app.ucr_status_key: 'stalled', app.ucr_component_key: 'disabled'})
