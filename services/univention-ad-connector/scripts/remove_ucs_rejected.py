#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention AD Connector
#  Remove rejected UCS object
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2018-2024 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

from __future__ import print_function

import os
import sys
from argparse import ArgumentParser

import univention.connector
import univention.uldap


class ObjectNotFound(BaseException):
    pass


def remove_ucs_rejected(options):
    db_internal_file = '/etc/univention/%s/internal.sqlite' % CONFIGBASENAME
    config = univention.connector.configdb(db_internal_file)
    found = False
    for filename, rejected_dn in config.items('UCS rejected'):
        if options.dn:
            if univention.connector.RE_NO_RESYNC.match(rejected_dn):
                if options.dn != rejected_dn:
                    continue
            elif not univention.uldap.access.compare_dn(options.dn, rejected_dn):
                continue

        if os.path.exists(filename):
            os.remove(filename)
        config.remove_option('UCS rejected', filename)
        print('The rejected UCS object %s has been removed.' % rejected_dn)
        found = True

    os.chmod(db_internal_file, 640)
    if not found:
        raise ObjectNotFound()


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-c", "--configbasename", metavar="CONFIGBASENAME", default="connector")
    parser.add_argument('dn', nargs='?')
    parser.add_argument('--all', '-a', action='store_true')
    options = parser.parse_args()

    if not options.dn and not options.all:
        parser.error('Either give a dn or --all to delete all ucs rejects')

    CONFIGBASENAME = options.configbasename
    state_directory = '/etc/univention/%s' % CONFIGBASENAME
    if not os.path.exists(state_directory):
        parser.error("Invalid configbasename, directory %s does not exist" % state_directory)
        sys.exit(1)

    try:
        remove_ucs_rejected(options)
    except ObjectNotFound:
        print('ERROR: The object %s was not found.' % options.dn)
        sys.exit(1)
