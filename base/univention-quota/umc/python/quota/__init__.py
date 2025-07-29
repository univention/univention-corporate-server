#!/usr/bin/python3
#
# Univention Management Console
#  module: manages quota support for locale hard drives
#
# SPDX-FileCopyrightText: 2006-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import univention.management.console as umc
import univention.management.console.modules as umcm

from . import partition, user


_ = umc.Translation('univention-management-console-module-quota').translate


class Instance(umcm.Base, partition.Commands, user.Commands):

    def __init__(self):
        umcm.Base.__init__(self)
        partition.Commands.__init__(self)
        user.Commands.__init__(self)
