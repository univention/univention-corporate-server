#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: test nfsmounts.py
## exposure: dangerous
## tags: [udm]
## roles: [domaincontroller_master]
## packages:
##   - univention-base-files

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

import univention.testing.strings as uts
from univention.lib import fstab
from univention.testing import utils


@pytest.fixture(scope='module')
def backup_fstab():
    FSTAB = "/etc/fstab"
    _, tmp = tempfile.mkstemp()

    shutil.copy(FSTAB, tmp)
    try:
        yield
    finally:
        shutil.move(tmp, FSTAB)


def test_nfsmount(udm, ucr, lo, backup_fstab):
    # create tempdir for mount point
    with tempfile.TemporaryDirectory(prefix="source_", dir="/home/") as shared_path, \
            tempfile.TemporaryDirectory(prefix="dest_", dir="/mnt/") as shared_dest:

        os.chmod(shared_path, 0o770)
        os.chmod(shared_dest, 0o770)

        # create shares in udm
        share_name = "share_" + uts.random_name()
        share = udm.create_object(
            'shares/share',
            name=share_name,
            path=shared_path,
            host='%(hostname)s.%(domainname)s' % ucr,
            directorymode="0770",
            position='cn=shares,%(ldap/base)s' % ucr,
            root_squash="0",
            options=['nfs'],
        )
        utils.verify_ldap_object(share, {'cn': [share_name]})
        utils.wait_for_listener_replication_and_postrun()

        # touch a file in source
        SOURCE_FILE_NAME = "source_to_dest.txt"
        (Path(shared_path) / SOURCE_FILE_NAME).touch()
        print("file created:", (Path(shared_path) / SOURCE_FILE_NAME))

        # create policy in UDM with the shared assigned
        policy_name = "policy_" + uts.random_name()
        policy = udm.create_object(
            'policies/nfsmounts',
            name=policy_name,
            nfsMounts=['%s %s' % (share, shared_dest)],
            position='cn=nfsmounts,cn=policies,%(ldap/base)s' % ucr,
        )
        utils.verify_ldap_object(policy, {'cn': [policy_name]})

        computer_type = 'computers/%(server/role)s' % ucr
        udm._cleanup.setdefault(computer_type, []).append(ucr['ldap/hostdn'])
        try:
            udm.modify_object(computer_type, dn=ucr['ldap/hostdn'], policy_reference=policy)
            udm._cleanup[computer_type].remove(ucr['ldap/hostdn'])

            # Call script
            command = ["/usr/lib/univention-directory-policy/nfsmounts", '-v', '--dn', ucr['ldap/hostdn']]
            print("About to run %s" % (' '.join(command),))
            subprocess.check_call(command)

            assert (Path(shared_dest) / SOURCE_FILE_NAME).exists()

            # Check write to shared
            dest_file_name = "dest_to_source.txt"
            (Path(shared_dest) / dest_file_name).touch()
            assert (Path(shared_path) / dest_file_name).exists()

            # Check that shared_dest is in /etc/fstab
            fs = fstab.File()
            assert fs.find(mount_point=shared_dest, type='nfs')

            # Check that shared_dest is in /etc/mtab
            mt = fstab.File('/etc/mtab')
            assert mt.find(mount_point=shared_dest, type='nfs4')

            # Check that shared_path is in /etc/exports
            expected_line = f'"{shared_path}" -rw,no_root_squash,sync,subtree_check * # LDAP:{share}'
            exports_lines = Path("/etc/exports").read_text().splitlines()
            assert expected_line in exports_lines

        finally:
            udm._cleanup[computer_type].append(ucr['ldap/hostdn'])
            try:
                udm.modify_object(computer_type, dn=ucr['ldap/hostdn'], policy_dereference=policy)
            finally:
                udm._cleanup[computer_type].remove(ucr['ldap/hostdn'])
            subprocess.call(["umount", shared_dest])
