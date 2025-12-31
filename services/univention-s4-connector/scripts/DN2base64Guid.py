#!/usr/bin/python3
#
# Univention S4 Connector
#  Convert S4 DN to base64 objectGuid as used in s4cache.sqlite
#
# SPDX-FileCopyrightText: 2014-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import base64
import sys
from argparse import ArgumentParser

import ldb
from samba.auth import system_session
from samba.credentials import Credentials
from samba.param import LoadParm
from samba.samdb import SamDB


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('dn')
    args = parser.parse_args()

    lp = LoadParm()
    creds = Credentials()
    creds.guess(lp)
    samdb = SamDB(url='/var/lib/samba/private/sam.ldb', session_info=system_session(), credentials=creds, lp=lp)

    domain_dn = samdb.domain_dn()
    res = samdb.search(args.dn, scope=ldb.SCOPE_BASE, attrs=["objectGuid"])

    for msg in res:
        guid = msg.get("objectGuid", idx=0)
        print(base64.b64encode(guid).decode('ASCII'))

    sys.exit(0)
