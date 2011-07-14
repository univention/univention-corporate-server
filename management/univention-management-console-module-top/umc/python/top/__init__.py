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

import subprocess

import univention.management.console as umc
import univention.management.console.modules as umcm
import univention.management.console.tools as umct
from univention.management.console.protocol.definitions import *

import univention.info_tools as uit

_ = umc.Translation('univention-management-console-modules-ucr').translate

class Instance(umcm.Base):
    def init(self):
        uit.set_language(str(self.locale))

    def __popen(self, CommandTuple, Input=None, MergeErrors=False, RequireZeroExit=False):
        stderr = subprocess.PIPE
        if MergeErrors:
            stderr = subprocess.STDOUT
        try:
            process = subprocess.Popen(CommandTuple, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr, close_fds=True)
            (stdoutdata, stderrdata) = process.communicate(input=Input)
            if RequireZeroExit and process.returncode != 0:
                return ('Command %s exited with status %d:\n%s\n%s' % (repr(CommandTuple), process.returncode, stdoutdata, stderrdata), None, None)
            else:
                return (process.returncode, stdoutdata, stderrdata)
        except (OSError, IOError), error:
            return ('Could not execute %s:\n%s' % (repr(CommandTuple), ' '.join(map(str, error.args))), None, None)

    def query(self, request):
        columns = ['user', 'pid', 'pcpu', 'vsize', 'rssize', 'pmem', 'command']
        psCommand = ['ps', 'h', '-eo', ','.join(columns)]
        processes = []

        (errorMessage, stdoutData, stderrData) = self.__popen(psCommand, RequireZeroExit=True)
        if errorMessage:
            request.status = MODULE_ERR
            success = False
        else:
            for line in stdoutData.split('\n'):
                dictLine = {}
                for key, value in zip(columns, line.split(None, 6)):
                    dictLine[key] = value
                processes.append(dictLine)

            #processes = [line.split(None, 6) for line in stdoutData.split('\n')]
            request.status = SUCCESS
            success = True

        #self.finished(request.id, {'success': success, 'processes': processes})
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
