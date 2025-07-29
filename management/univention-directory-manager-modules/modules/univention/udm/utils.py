#
# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import logging
import sys

import univention.logging


UDebug = univention.logging.getLogger('ADMIN')
UDebug.warn = UDebug.warning
UDebug.all = UDebug.debug
UDebug.process = UDebug.info

is_interactive = bool(getattr(sys, 'ps1', sys.flags.interactive))
if is_interactive:
    class InteractiveStreamHandler(logging.Handler):
        def emit(self, record):
            msg = self.format(record)
            if record.level >= logging.INFO:
                print('%s: %s' % (record.levelname, msg))
    UDebug.addHandler(InteractiveStreamHandler())
