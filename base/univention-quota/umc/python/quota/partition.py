#!/usr/bin/python3
#
# Univention Management Console
#  quota module: handles partition related commands
#
# SPDX-FileCopyrightText: 2006-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import univention.management.console as umc
from univention.lib import fstab
from univention.management.console.error import UMC_Error
from univention.management.console.log import MODULE
from univention.management.console.modules.decorators import simple_response
from univention.management.console.modules.quota import df, tools


_ = umc.Translation('univention-management-console-module-quota').translate


class Commands:

    def partitions_query(self, request):
        result = []
        try:
            fs = fstab.File('/etc/fstab')
            mt = fstab.File('/etc/mtab')
        except OSError as error:
            MODULE.error('Could not open %s' % error.filename)
            raise UMC_Error(_('Could not open %s') % error.filename, 500)

        partitions = fs.get(['xfs', 'ext4', 'ext3', 'ext2'], False)
        for partition in partitions:
            list_entry = {}
            list_entry['partitionDevice'] = partition.spec
            list_entry['mountPoint'] = partition.mount_point
            list_entry['partitionSize'] = None
            list_entry['freeSpace'] = None
            list_entry['inUse'] = tools.quota_is_enabled(partition)
            mounted_partition = mt.find(spec=partition.spec)
            if mounted_partition:
                partition_info = df.DeviceInfo(partition.mount_point)
                list_entry['partitionSize'] = tools.block2byte(partition_info.size(), 'GB', 1)
                list_entry['freeSpace'] = tools.block2byte(partition_info.free(), 'GB', 1)
            result.append(list_entry)
        self.finished(request.id, result)

    def partitions_info(self, request):
        result = {}
        try:
            fs = fstab.File('/etc/fstab')
            mt = fstab.File('/etc/mtab')
        except OSError as error:
            MODULE.error('Could not open %s' % error.filename)
            raise UMC_Error(_('Could not open %s') % error.filename, 500)

        partition = fs.find(spec=request.options['partitionDevice'])
        if not partition:
            raise UMC_Error(_('No partition found'))
        mounted_partition = mt.find(spec=partition.spec)
        if not mounted_partition:
            raise UMC_Error(_('This partition is currently not mounted'))

        result['mountPoint'] = mounted_partition.mount_point
        result['filesystem'] = mounted_partition.type
        result['options'] = mounted_partition.options
        self.finished(request.id, result)

    @simple_response
    def partitions_activate(self, partitionDevice):
        MODULE.info('quota/partitions/activate: %s' % (partitionDevice,))

        def _thread(self, request):
            return tools.activate_quota(partitionDevice, True)
        return _thread

    @simple_response
    def partitions_deactivate(self, partitionDevice):
        MODULE.info('quota/partitions/deactivate: %s' % (partitionDevice,))

        def _thread(self, request):
            return tools.activate_quota(partitionDevice, False)
        return _thread
