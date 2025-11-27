#!/usr/bin/python3
#
# Univention AD Connector
#  Remove rejected AD object
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


def remove_ad_rejected(ad_dn):
    db_internal_file = f'/etc/univention/{CONFIGBASENAME}/internal.sqlite'
    config = univention.connector.configdb(db_internal_file)
    found = False
    for usn, rejected_dn, _retry_count in config.items('AD rejected'):
        if univention.uldap.access.compare_dn(ad_dn, rejected_dn):
            config.remove_option('AD rejected', usn)
            config.remove_option('AD rejected reason', usn)
            found = True
    os.chmod(db_internal_file, 640)
    if not found:
        raise ObjectNotFound()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-c", "--configbasename", help="", metavar="CONFIGBASENAME", default="connector")
    parser.add_argument('dn')
    options = parser.parse_args()

    CONFIGBASENAME = options.configbasename
    state_directory = f'/etc/univention/{CONFIGBASENAME}'
    if not os.path.exists(state_directory):
        parser.error(f"Invalid configbasename, directory {state_directory} does not exist")

    ad_dn = options.dn

    try:
        remove_ad_rejected(ad_dn)
    except ObjectNotFound:
        print(f'ERROR: The object {ad_dn} was not found.')
        sys.exit(1)

    print(f'The rejected AD object {ad_dn} has been removed.')
