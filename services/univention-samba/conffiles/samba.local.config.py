#!/usr/bin/python3
#
# Univention Samba
#  this script creates samba configurations from ucr values
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import sys


try:
    from univention.lib.share_restrictions import ShareConfiguration
except ImportError as exc:
    print('Could not import ShareConfiguration: %s' % (exc,), file=sys.stderr)
    sys.exit(0)

# main
if __name__ == '__main__':
    conf = ShareConfiguration()

    conf.read()

    # DEBUGGING
    # import pprint
    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(conf.shares)
    # pp.pprint(conf.globals)
    # pp.pprint(conf.printers)
    # sys.exit(0)

    conf.write()
