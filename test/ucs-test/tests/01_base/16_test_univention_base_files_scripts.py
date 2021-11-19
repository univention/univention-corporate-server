#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: test univention-policy-update-config-registry.py and nfsmounts.py
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
import univention.testing.utils as utils
from univention.lib import fstab


def test_policy_update_config_registry(udm, ucr):
	prefix = "ucs-test/base-files/policy-result/"
	registry = [(prefix + uts.random_string(), uts.random_string()) for _ in range(5)]
	registry_string_list = ["%s %s" % nu for nu in registry]

	# Create new policies/registry
	policy_name = "policy_" + uts.random_name()
	policy = udm.create_object('policies/registry', name=policy_name, registry=registry_string_list)
	utils.verify_ldap_object(policy, {'cn': [policy_name]})

	# Create new computer computers/domaincontroller_slave and attach the computer to the policy
	computer_name = "computer_" + uts.random_name()
	computer_passw = uts.random_string()
	slave_computer = udm.create_object('computers/domaincontroller_slave', name=computer_name, password=computer_passw, policy_reference=policy)

	script_path = "/usr/lib/univention-directory-policy/univention-policy-update-config-registry"
	with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8') as secret_file:
		command = [script_path, '-v', '-y', secret_file.name, slave_computer]
		os.fchmod(secret_file.fileno(), 0o600)
		secret_file.write(computer_passw)
		secret_file.flush()

		print("Executing: ", " ".join(command))
		print("Result:", subprocess.check_call(command))

		# Check that key values exists in UCR
		ucr.load()
		prefixed_ucr_keys = [(ucr_key, ucr_value) for ucr_key, ucr_value in ucr.items() if ucr_key.startswith(prefix)]
		assert sorted(prefixed_ucr_keys) == sorted(registry)


@pytest.fixture(scope='module')
def backup_fstab():
	shutil.copy('/etc/fstab', '/tmp/fstab')
	try:
		yield
	finally:
		shutil.move('/tmp/fstab', '/etc/fstab')


def test_nfsmount(udm, ucr, lo, backup_fstab):
	# create tempdir for mount point
	with tempfile.TemporaryDirectory(prefix="source_", dir="/home/") as shared_path, \
		tempfile.TemporaryDirectory(prefix="dest_", dir="/mnt/") as shared_dest:

		os.chmod(shared_path, 0o007)
		os.chmod(shared_path, 0o007)

		# create shares in udm
		share_name = "share_" + uts.random_name()
		share = udm.create_object(
			'shares/share', name=share_name, path=shared_path, host='localhost', directorymode="0077",
			position='cn=shares,%s' % (ucr['ldap/base'],),
		)
		utils.verify_ldap_object(share, {'cn': [share_name]})

		# muha! best trick ever. univentionShareHost is single value in UDM but not in LDAP. setting localhost + FQDN causes listener and nfsmounts script to be tricked
		lo.modify(share, [('univentionShareHost', None, ('%(hostname)s.%(domainname)s' % ucr).encode())])
		utils.wait_for_listener_replication_and_postrun()

		# touch a file in source
		source_file_name = "source_to_dest.txt"
		(Path(shared_path) / source_file_name).touch()
		print("file created:", (Path(shared_path) / source_file_name))

		# create policy in UDM with the shared assigned
		policy_name = "policy_" + uts.random_name()
		policy = udm.create_object(
			'policies/nfsmounts', name=policy_name, nfsMounts=['%s %s' % (share, shared_dest)],
			position='cn=nfsmounts,cn=policies,%s' % (ucr['ldap/base'])
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

			assert (Path(shared_dest) / source_file_name).exists()

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
			expected_line = "\"{shared_path}\" -rw,root_squash,sync,subtree_check * # LDAP:{ldap_share}".format(ldap_share=share, shared_path=shared_path)
			exports_lines = Path("/etc/exports").read_text().splitlines()
			assert expected_line in exports_lines

		finally:
			udm._cleanup[computer_type].append(ucr['ldap/hostdn'])
			try:
				udm.modify_object(computer_type, dn=ucr['ldap/hostdn'], policy_dereference=policy)
			finally:
				udm._cleanup[computer_type].remove(ucr['ldap/hostdn'])
			subprocess.check_call(["umount", shared_dest])
