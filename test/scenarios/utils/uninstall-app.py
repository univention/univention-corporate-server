#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014-2015 Univention GmbH
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

from univention.management.console.modules.appcenter.app_center import Application
from univention.management.console.modules.appcenter.util import ComponentManager
from univention.lib.package_manager import PackageManager
from univention.config_registry import ConfigRegistry
from univention.updater import UniventionUpdater

import sys
import optparse

def simple_handler(f):
	def _simple_handler(msg):
		msg = '%s\n\r' % msg.strip()
		f.write(msg)
	return _simple_handler

parser = optparse.OptionParser()
parser.add_option('-a', '--app-id', help='app id to deinstall', metavar='APP_ID')
(options, args) = parser.parse_args()
if not options.app_id:
	raise Exception, 'app id missing'

ucr = ConfigRegistry()
ucr.load()
updater = UniventionUpdater(False)
package_manager = PackageManager(info_handler=simple_handler(sys.stdout), error_handler=simple_handler(sys.stderr))
component_manager = ComponentManager(ucr, updater)

app = Application.find(options.app_id)
if app:
	if not app.uninstall(package_manager, component_manager):
		raise Exception, 'deinstallation of app %s failed' % options.app_id
