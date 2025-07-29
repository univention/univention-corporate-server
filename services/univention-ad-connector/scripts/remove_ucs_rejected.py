#!/usr/bin/python3
#
# Univention AD Connector
#  Remove rejected UCS object
#
# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import os
import sys
from argparse import ArgumentParser

import univention.connector
import univention.uldap


class ObjectNotFound(BaseException):
    pass


def remove_ucs_rejected(ucs_dn):
    db_internal_file = '/etc/univention/%s/internal.sqlite' % CONFIGBASENAME
    config = univention.connector.configdb(db_internal_file)
    found = False
    for filename, rejected_dn in config.items('UCS rejected'):
        if univention.connector.RE_NO_RESYNC.match(rejected_dn):
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
    parser.add_argument("-c", "--configbasename", metavar="CONFIGBASENAME", default="connector")
    parser.add_argument('dn')
    options = parser.parse_args()

    CONFIGBASENAME = options.configbasename
    state_directory = '/etc/univention/%s' % CONFIGBASENAME
    if not os.path.exists(state_directory):
        parser.error("Invalid configbasename, directory %s does not exist" % state_directory)
        sys.exit(1)

    ucs_dn = options.dn

    try:
        remove_ucs_rejected(ucs_dn)
    except ObjectNotFound:
        print('ERROR: The object %s was not found.' % ucs_dn)
        sys.exit(1)

    print('The rejected UCS object %s has been removed.' % ucs_dn)
