#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: process overview
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

import psutil

import univention.info_tools as uit
import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.management.console.protocol.definitions import *

_ = umc.Translation('univention-management-console-modules-ucr').translate

class Instance(umcm.Base):
    def init(self):
        uit.set_language(str(self.locale))

    def query(self, request):
        processes = []

        for process in psutil.process_iter():
            p = {}
            p['user'] = process.username
            p['pid'] = process.pid
            p['cpu'] = '%.1f' % process.get_cpu_percent()
            mem = process.get_memory_info()
            p['vsize'] = mem[1]
            p['rssize'] = mem[0]
            p['mem'] = '%.1f' % process.get_memory_percent()
            p['prog'] = process.name
            p['command'] = process.cmdline
            processes.append(p)
        request.status = SUCCESS
        success = True
        self.finished(request.id, processes)

    def kill(self, request):
        cmd = ['kill']
        if request.options['signal'] == 'kill':
                cmd.append('-9')
        else:
                cmd.append('-15')

        for pid in request.options['pid']:
                cmd.append(str(pid))

        subprocess.call(cmd)

        self.finished(request.id(), None)
