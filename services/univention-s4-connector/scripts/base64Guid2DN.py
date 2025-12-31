#!/usr/bin/python3
#
# Univention S4 Connector
#  Upgrade script for gPLink
#  Convert base64 objectGuid to S4 DN as used in s4cache.sqlite
#
# SPDX-FileCopyrightText: 2014-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import base64
from argparse import ArgumentParser

import ldb
from ldap.filter import filter_format
from samba.auth import system_session
from samba.credentials import Credentials
from samba.dcerpc import misc
from samba.ndr import ndr_unpack
from samba.param import LoadParm
from samba.samdb import SamDB


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('base64_guid')
    args = parser.parse_args()

    guid = str(ndr_unpack(misc.GUID, base64.b64decode(args.base64_guid)))

    lp = LoadParm()
    creds = Credentials()
    creds.guess(lp)
    samdb = SamDB(url='/var/lib/samba/private/sam.ldb', session_info=system_session(), credentials=creds, lp=lp)

    domain_dn = samdb.domain_dn()
    res = samdb.search(domain_dn, scope=ldb.SCOPE_SUBTREE, expression=(filter_format("(objectGuid=%s)", (guid,))), attrs=["dn"])
    for msg in res:
        print(msg.get("dn", idx=0))
