#!/usr/bin/python3
#
# Univention Management Console
#  module: system halt/reboot
#
# SPDX-FileCopyrightText: 2011-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import univention.management.console as umc
from univention.management.console.modules import Base


_ = umc.Translation('univention-management-console-module-reboot').translate


class Instance(Base):
    pass
