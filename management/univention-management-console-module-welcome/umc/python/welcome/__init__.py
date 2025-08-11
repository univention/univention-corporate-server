#!/usr/bin/python3
# SPDX-FileCopyrightText: 2021-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from univention.lib.i18n import Translation
from univention.management.console.modules import Base
from univention.management.console.modules.decorators import simple_response


_ = Translation('univention-management-console-module-welcome').translate


class Instance(Base):

    @simple_response
    def welcome(self):
        return True
