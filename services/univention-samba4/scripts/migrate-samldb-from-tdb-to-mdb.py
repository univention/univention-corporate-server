#!/usr/bin/python3
#
# Univention helper script
#  migrate samba database from tdb to mdb
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2024 Univention GmbH
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


import argparse
import os
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime

import ldb
import lmdb
import tdb
from samba import Ldb
from samba.auth import system_session
from samba.param import LoadParm


# Default the mdb file size for the individual partitions to 8GB
DEFAULT_BACKEND_SIZE = 8 * 1024**3


def migrate_sam_ldb_backends_from_tdb_to_mdb(ldb_tdb_backend_dir, ldb_mdb_backend_dir):
    print("PROCESS: Migrating sam.ldb.d backend files from TDB to MDB")
    ldb_tdb_backend_files = [fn for fn in os.listdir(ldb_tdb_backend_dir) if fn.endswith(".ldb")]
    for fn in ldb_tdb_backend_files:
        t = tdb.Tdb(os.path.join(ldb_tdb_backend_dir, fn))
        mdb_env = lmdb.open(os.path.join(ldb_mdb_backend_dir, fn), map_size=DEFAULT_BACKEND_SIZE, subdir=False)
        os.chmod(mdb_env.path(), 0o600)

        with mdb_env.begin(write=True) as txn:
            for i in t:
                txn.put(i, t[i])
    print("PROCESS: Migration of sam.ldb.d backend files done")


@contextmanager
def sam_ldb_backends_from_tdb_to_mdb(lp):
    print("PROCESS: Creating new sam.ldb.d directory for Migration")
    sam_backend_dir = lp.private_path("sam.ldb.d")
    sam_tdb_backend_dir = lp.private_path("sam.ldb.tdb.d")
    sam_ldb = lp.private_path("sam.ldb")
    sam_ldb_bak = lp.private_path("sam.ldb.tdb")

    try:
        os.rename(sam_backend_dir, sam_tdb_backend_dir)
    except OSError:
        print("ERROR: An exception occurred, aborting migration")
        raise

    os.mkdir(sam_backend_dir)
    os.chmod(sam_backend_dir, 0o700)

    shutil.copy(sam_ldb, sam_ldb_bak)
    os.chmod(sam_ldb_bak, 0o600)

    migrate_sam_ldb_backends_from_tdb_to_mdb(sam_tdb_backend_dir, sam_backend_dir)

    try:
        yield
    except Exception:
        print("ERROR: An exception occurred, reverting sam.ldb.d to original state")
        shutil.rmtree(sam_backend_dir)
        os.rename(sam_tdb_backend_dir, sam_backend_dir)
        os.unlink(sam_ldb)
        os.rename(sam_ldb_bak, sam_ldb)
        raise

    print("PROCESS: Moving metadata file to new sam.ldb.d directory")
    os.rename(os.path.join(sam_tdb_backend_dir, "metadata.tdb"), os.path.join(sam_backend_dir, "metadata.tdb"))


def open_samdb_raw(lp):
    # Use options=["modules:"] to keep the attached LDB modules from loading
    samdb_path = lp.private_path("sam.ldb")
    return Ldb(url=samdb_path, session_info=system_session(), lp=lp, options=["modules:"])


def activate_mdb(lp):
    print("PROCESS: Switching sam.ldb from TDB to MDB")
    samdb = open_samdb_raw(lp)

    samdb.transaction_start()
    try:
        delta = ldb.Message()
        delta.dn = ldb.Dn(samdb, "@PARTITION")
        delta["backendStore"] = ldb.MessageElement("mdb", ldb.FLAG_MOD_REPLACE, "backendStore")
        samdb.modify(delta)

        delta = ldb.Message()
        delta.dn = ldb.Dn(samdb, "@SAMBA_DSDB")
        delta["requiredFeatures"] = ldb.MessageElement("lmdbLevelOne", ldb.FLAG_MOD_ADD, "requiredFeatures")
        samdb.modify(delta)
    except ldb.LdbError:
        samdb.transaction_cancel()
        print("PROCESS: Switching sam.ldb from TDB to MDB failed")
        raise
    else:
        samdb.transaction_commit()
        print("PROCESS: Switching sam.ldb from TDB to MDB successful")


@contextmanager
def stopped_samba_and_s4c():
    print("PROCESS: Stopping Samba and S4-Connector")
    subprocess.call(("systemctl", "stop", "univention-s4-connector"))
    subprocess.call(("/etc/init.d/samba", "stop"))

    try:
        yield
    except Exception:
        raise

    print("PROCESS: Starting Samba and S4-Connector again")
    subprocess.call(("/etc/init.d/samba", "start"))
    time.sleep(5)
    subprocess.call(("systemctl", "start", "univention-s4-connector"))


def sam_ldb_is_using_mdb(lp):
    samdb = open_samdb_raw(lp)
    res = samdb.search(base="@PARTITION", scope=ldb.SCOPE_BASE, attrs=["backendStore"])
    return (res and "backendStore" in res[0] and str(res[0]["backendStore"]) == "mdb")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate sam.ldb from TDB to MDB")
    parser.add_argument("--skip-dbcheck", action='store_true')
    args = parser.parse_args()

    lp = LoadParm()

    if sam_ldb_is_using_mdb(lp):
        print("INFO: Nothing to do, sam.ldb is already using MDB")
        sys.exit(0)

    with stopped_samba_and_s4c():
        if not args.skip_dbcheck:
            print("PROCESS: Running pre-migration check of sam.ldb database")
            if subprocess.call(("samba-tool", "dbcheck", "--cross-ncs")):
                sys.exit(1)

        t0 = datetime.now()

        with sam_ldb_backends_from_tdb_to_mdb(lp):
            activate_mdb(lp)

        duration = str(datetime.now() - t0).split('.')[:-1][0]
        print("INFO: Duration: %s" % duration)

        if not args.skip_dbcheck:
            print("PROCESS: Running post-migration check of sam.ldb database")
            if subprocess.call(("samba-tool", "dbcheck", "--cross-ncs")):
                sys.exit(1)
