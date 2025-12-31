#!/usr/bin/python3
#
# Univention Directory Listener
#
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Read LDAP from the Primary Directory Node and create LDIF file (and update local schema)"""


import argparse
import gzip
import io
import logging
import os
import sys

import ldap
import ldif
from ldap.controls import SimplePagedResultsControl

import univention.config_registry
from univention import uldap


sys.path.append("/usr/lib/univention-directory-listener/system/")
import replication  # noqa: E402


logger = logging.getLogger(__name__)

LDIF = '/var/lib/univention-directory-listener/master.ldif.gz'
SCHEMA = '/var/lib/univention-ldap/schema.conf'
OIDS = set(replication.BUILTIN_OIDS) | {'1.3.6.1.4.1.4203.666.11.1.4.2.12.1'}


def update_schema(lo: uldap.access) -> None:
    """update the ldap schema file"""
    logger.info('Fetching Schema ...')
    res = lo.search(base="cn=Subschema", scope=ldap.SCOPE_BASE, filter='(objectclass=*)', attr=['+', '*'])
    replication.update_schema(res[0][1])


def create_ldif_from_master(lo: uldap.access, ldif_file: str, base: str, page_size: int) -> None:
    """create ldif file from everything from lo"""
    logger.info('Fetching LDIF ...')
    output = sys.stdout if ldif_file == "-" else io.StringIO()

    lc = SimplePagedResultsControl(
        criticality=True,
        size=page_size,
        cookie='')
    page_ctrl_oid = lc.controlType

    writer = ldif.LDIFWriter(output, cols=10000)
    while True:
        msgid = lo.lo.search_ext(base, ldap.SCOPE_SUBTREE, '(objectclass=*)', ['+', '*'], serverctrls=[lc])
        _rtype, rdata, _rmsgid, serverctrls = lo.lo.result3(msgid)

        for dn, data in rdata:
            logger.debug('Processing %s ...', dn)
            for attr in replication.EXCLUDE_ATTRIBUTES:
                data.pop(attr, None)

            writer.unparse(dn, data)

        pctrls = [
            c
            for c in serverctrls
            if c.controlType == page_ctrl_oid
        ]
        if pctrls:
            cookie = lc.cookie = pctrls[0].cookie

            if not cookie:
                break
        else:
            logger.warning("Server ignores RFC 2696 Simple Paged Results Control.")
            break

    if isinstance(output, io.StringIO):
        if os.path.isfile(ldif_file):
            os.unlink(ldif_file)
        with gzip.open(ldif_file, 'w') as fd:
            fd.write(output.getvalue().encode('UTF-8'))
    output.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-l", "--ldif", action="store_true", default=replication.LDIF_FILE, help="Create LDIF file")
    parser.add_argument("-s", "--schema", action="store_true", help="Update LDAP schema [%s]" % replication.SCHEMA_FILE)
    parser.add_argument("-o", "--outfile", default=LDIF, help="File to store gzip LDIF data [%(default)s]")
    parser.add_argument("-p", "--pagesize", type=int, default=1000, help="page size to use for LDAP paged search")
    parser.add_argument("-v", "--verbose", action="count", help="Increase verbosity")
    opts = parser.parse_args()

    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG if opts.verbose else logging.WARNING, format='%(levelname)s: %(message)s')

    ucr = univention.config_registry.ConfigRegistry()
    ucr.load()
    base = ucr.get("ldap/base")
    if ucr.get("server/role", "") == "domaincontroller_backup":
        lo = uldap.getAdminConnection()
    else:
        lo = uldap.getMachineConnection(ldap_master=True)

    if opts.schema:
        update_schema(lo)

    if opts.ldif:
        create_ldif_from_master(lo, opts.outfile, base, opts.pagesize)


if __name__ == "__main__":
    main()
