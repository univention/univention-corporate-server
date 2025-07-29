#!/usr/bin/python3
#
# Univention Management Console
#  Module lib containing low-lewel commands to control the UMC server
#
# SPDX-FileCopyrightText: 2012-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from univention.lib.i18n import Translation
from univention.management.console.modules import Base

from .server import Server


_ = Translation('univention-management-console-module-lib').translate


class Instance(Base, Server):
    pass
