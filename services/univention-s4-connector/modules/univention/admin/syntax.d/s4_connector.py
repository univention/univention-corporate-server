# Univention S4 Connector
#  UDM syntax classes
#
# SPDX-FileCopyrightText: 2019-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import univention.admin.uexceptions
from univention.admin.syntax import _, integer


class SignedInteger(integer):  # Workaround for Bug #50591

    @classmethod
    def parse(cls, text):
        try:
            return str(int(text))
        except ValueError:
            raise univention.admin.uexceptions.valueError(_("Value must be a number!"))
