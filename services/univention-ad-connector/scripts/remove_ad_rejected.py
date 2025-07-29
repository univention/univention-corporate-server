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
    db_internal_file = '/etc/univention/%s/internal.sqlite' % CONFIGBASENAME
    config = univention.connector.configdb(db_internal_file)
    found = False
    for usn, rejected_dn, _retry_count in config.items('AD rejected'):
        if univention.uldap.access.compare_dn(ad_dn, rejected_dn):
            config.remove_option('AD rejected', usn)
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
    state_directory = '/etc/univention/%s' % CONFIGBASENAME
    if not os.path.exists(state_directory):
        parser.error("Invalid configbasename, directory %s does not exist" % state_directory)

    ad_dn = options.dn

    try:
        remove_ad_rejected(ad_dn)
    except ObjectNotFound:
        print('ERROR: The object %s was not found.' % (ad_dn,))
        sys.exit(1)

    print('The rejected AD object %s has been removed.' % (ad_dn,))
