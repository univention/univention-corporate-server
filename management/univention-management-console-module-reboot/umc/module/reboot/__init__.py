#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: system halt/reboot
#
# Copyright 2011 Univention GmbH
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

import univention.info_tools as uit
import univention.management.console as umc

_ = umc.Translation('univention-management-console-modules-reboot').translate

class Instance(umcm.Base):
	def init(self):
		# set the language in order to return the correctly localized labels/descriptions
		uit.set_language(str(self.locale))

        def execute(self, request):
                # TODO
                # check if args are valid
                if request.options['action'] == 'halt':
                        do="h"
                        target=_('The system is going down for system halt NOW with following message: ')
                elif request.options['action'] == 'reboot':
                        do = "r"
                        target=_('The system is going down for reboot NOW with following message: ')

                request.options['reason'] = target + request.options['reason']
                # TODO
                # logger?
                try:
                        subprocess.call(('shutdown', '-%s' %do, 'now', str(request.options['reason'])))
                        request.status = SUCCESS
                        success = True
                except:
                        request.status = MODULE_ERR
                        success = False

		self.finished(request.id, success)
