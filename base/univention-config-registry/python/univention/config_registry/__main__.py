#
#  main configuration registry classes
#
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Univention Configuration Registry."""


import sys

from univention.config_registry.backend import StrictModeException
from univention.config_registry.frontend import main


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except StrictModeException as ex2:
        print(('E: UCR is running in strict mode and thus cannot accept the given input:'), file=sys.stderr)
        print(ex2, file=sys.stderr)
        sys.exit(1)
