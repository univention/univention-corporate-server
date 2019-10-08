#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: system usage statistics
#
# Copyright 2011-2019 Univention GmbH
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

import os

import univention.info_tools as uit
from univention.management.console import Translation
from univention.management.console.base import Base
from univention.management.console.modules.decorators import sanitize, allow_get_request
from univention.management.console.modules.sanitizers import ChoicesSanitizer
from univention.management.console.modules import UMC_Error

_ = Translation('univention-management-console-modules-mrtg').translate


class Instance(Base):

	@allow_get_request
	@sanitize(filename=ChoicesSanitizer(choices=['ucs_0load-day.png', 'ucs_0load-year.png', 'ucs_2mem-week.png', 'ucs_3swap-month.png', 'ucs_0load-month.png', 'ucs_2mem-day.png', 'ucs_2mem-year.png', 'ucs_3swap-week.png', 'ucs_0load-week.png', 'ucs_2mem-month.png', 'ucs_3swap-day.png', 'ucs_3swap-year.png'], required=True))
	def get_statistic(self, request):
		path = '/usr/share/univention-maintenance/'
		filename = os.path.join(path, os.path.basename(request.options['filename']))
		try:
			with open(filename) as fd:
				self.finished(request.id, fd.read(), mimetype='image/png')
		except EnvironmentError:
			raise UMC_Error(_('The file does not exist.'), status=404)

	def init(self):
		uit.set_language(str(self.locale))
