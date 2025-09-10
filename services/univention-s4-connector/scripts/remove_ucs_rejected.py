#!/usr/bin/python3
#
# Univention S4 Connector
#  Remove rejected UCS object
#
# SPDX-FileCopyrightText: 2014-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import os
import sys
from argparse import ArgumentParser

import univention.s4connector
import univention.uldap


class ObjectNotFound(BaseException):
    pass


def remove_ucs_rejected(ucs_dn):
    db_internal_file = '/etc/univention/connector/s4internal.sqlite'
    config = univention.s4connector.configdb(db_internal_file)
    found = False
    for filename, rejected_dn in config.items('UCS rejected'):
        if univention.s4connector.RE_NO_RESYNC.match(rejected_dn):
            if ucs_dn != rejected_dn:
                continue
        elif not univention.uldap.access.compare_dn(ucs_dn, rejected_dn):
            continue

        if os.path.exists(filename):
            os.remove(filename)
        config.remove_option('UCS rejected', filename)
        found = True
    os.chmod(db_internal_file, 640)
    if not found:
        raise ObjectNotFound()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('dn')
    args = parser.parse_args()

    ucs_dn = args.dn

    try:
        remove_ucs_rejected(ucs_dn)
    except ObjectNotFound:
        print(f'ERROR: The object {ucs_dn} was not found.')
        sys.exit(1)

    print(f'The rejected UCS object {ucs_dn} has been removed.')
    sys.exit(0)
