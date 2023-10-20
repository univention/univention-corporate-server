#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  quota module: show quota information for a user
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2006-2023 Univention GmbH
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

from __future__ import absolute_import

from univention.lib import fstab
from univention.management.console import Translation
from univention.management.console.error import UMC_Error
from univention.management.console.log import MODULE
from univention.management.console.modules.decorators import SimpleThread, sanitize, simple_response, threaded
from univention.management.console.modules.quota import tools
from univention.management.console.modules.sanitizers import IntegerSanitizer, PatternSanitizer, StringSanitizer


_ = Translation('univention-management-console-module-quota').translate


class LimitSanitizer(IntegerSanitizer):

    def _sanitize(self, value, name, further_arguments):
        if not value:
            return self.default
        return super(LimitSanitizer, self)._sanitize(value, name, further_arguments)


class Commands(object):

    @sanitize(
        partitionDevice=StringSanitizer(required=True),
        filter=PatternSanitizer(default='.*'),
    )
    def users_query(self, request):
        partitionDevice = request.options['partitionDevice']
        self._check_error(partitionDevice)

        def _thread(request):
            stdout, returncode = tools.repquota(request.options['partitionDevice'])
            return self._users_query(partitionDevice, request, stdout, returncode)

        thread = SimpleThread('repquota', _thread, lambda r, t: self.thread_finished_callback(r, t, request))
        thread.run(request)

    def _users_query(self, partition, request, stdout, status):
        """
        This function is invoked when a repquota process has died and
        there is output to parse that is restructured as UMC Dialog
        """
        if status != 0:
            MODULE.warn(f'repquota failed with exit code: {status}')
        # general information
        devs = fstab.File()
        devs.find(spec=partition)

        callbackResult = stdout.splitlines()

        # skip header
        header = 0
        try:
            while not callbackResult[header].startswith(b'----'):
                header += 1
        except IndexError:
            pass
        output = [x.decode('UTF-8', 'replace') for x in callbackResult[header + 1:]]
        quotas = tools.repquota_parse(partition, output)
        return [q for q in quotas if request.options['filter'].match(q['user'])]

    @sanitize(
        partitionDevice=StringSanitizer(required=True),
        user=StringSanitizer(required=True),
        sizeLimitSoft=LimitSanitizer(default=0, required=True),
        sizeLimitHard=LimitSanitizer(default=0, required=True),
        fileLimitSoft=LimitSanitizer(default=0, required=True),
        fileLimitHard=LimitSanitizer(default=0, required=True),
    )
    @simple_response
    def users_set(self, partitionDevice, user, sizeLimitSoft, sizeLimitHard, fileLimitSoft, fileLimitHard):
        def _thread(self, request):
            self._check_error(partitionDevice)

            if tools.setquota(partitionDevice, user, tools.byte2block(sizeLimitSoft), tools.byte2block(sizeLimitHard), fileLimitSoft, fileLimitHard):
                raise UMC_Error(_('Failed to modify quota settings for user %(user)s on partition %(partition)s.') % {'user': user, 'partition': partitionDevice})
        return _thread

    @threaded
    def users_remove(self, request):
        partitions = []
        failed = []

        # Determine different partitions
        for obj in request.options:
            partitions.append(obj['object'].split('@', 1)[-1])
        for partition in set(partitions):
            self._check_error(partition)

        # Remove user quota
        for obj in request.options:
            (user, _, partition) = obj['object'].partition('@')
            if not isinstance(user, str):  # Py2
                user = user.encode('utf-8')
            if tools.setquota(partition, user, 0, 0, 0, 0):
                failed.append(user)

        if failed:
            raise UMC_Error(_('Could not remove the following user: %s') % ', '.join(failed))

    def _check_error(self, partition_name):
        try:
            fs = fstab.File('/etc/fstab')
            mt = fstab.File('/etc/mtab')
        except IOError as error:
            MODULE.error(f'Could not open {error.filename}')
            raise UMC_Error(_('Could not open %s') % error.filename, 500)

        partition = fs.find(spec=partition_name)
        if partition:
            mounted_partition = mt.find(spec=partition.spec)
            if mounted_partition:
                if not mounted_partition.hasopt('usrquota') and not mounted_partition.hasopt('usrjquota=aquota.user'):
                    raise UMC_Error(_('The following partition is mounted without quota support: %s') % partition_name)
            else:
                raise UMC_Error(_('The following partition is currently not mounted: %s') % partition_name)
        else:
            raise UMC_Error(_('No partition found (%s)') % partition_name)
