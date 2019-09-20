#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: software management
#
# Copyright 2013-2019 Univention GmbH
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

# standard library
import locale

# univention
from univention.management.console.modules.decorators import simple_response
import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.management.console.modules.appcenter.sanitizers import error_handling
from univention.appcenter.app_cache import Apps
from univention.appcenter.log import log_to_logfile
from univention.appcenter.actions import get_action

_ = umc.Translation('univention-management-console-module-apps').translate


class Instance(umcm.Base):

	def init(self):
		locale.setlocale(locale.LC_ALL, str(self.locale))
		try:
			log_to_logfile()
		except IOError:
			pass

	@simple_response
	def get(self, application):
		app = Apps().find(application)
		domain = get_action('domain')
		if app is None:
			return None
		return domain.to_dict([app])[0]

	def error_handling(self, etype, exc, etraceback):
		error_handling(etype, exc, etraceback)
		return super(Instance, self).error_handling(exc, etype, etraceback)
