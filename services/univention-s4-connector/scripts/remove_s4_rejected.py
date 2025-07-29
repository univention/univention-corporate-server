#!/usr/bin/python3
#
# Univention S4 Connector
#  Remove rejected S4 object
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


def remove_s4_rejected(s4_dn):
    db_internal_file = '/etc/univention/connector/s4internal.sqlite'
    config = univention.s4connector.configdb(db_internal_file)
    found = False
    for usn, rejected_dn in config.items('S4 rejected'):
        if univention.uldap.access.compare_dn(s4_dn, rejected_dn):
            config.remove_option('S4 rejected', usn)
            found = True
    os.chmod(db_internal_file, 640)
    if not found:
        raise ObjectNotFound()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('dn')
    args = parser.parse_args()

    s4_dn = args.dn

    try:
        remove_s4_rejected(s4_dn)
    except ObjectNotFound:
        print('ERROR: The object %s was not found.' % s4_dn)
        sys.exit(1)

    print('The rejected S4 object %s has been removed.' % s4_dn)
    sys.exit(0)
