#!/usr/share/ucs-test/runner pytest-3 -vvv
## desc: test univention-samba4-backup of univention-samba4 package
## exposure: dangerous
## tags: []
## roles: [domaincontroller_master]
## packages:
##   - univention-samba4

import datetime
import subprocess
from pathlib import Path
from time import sleep

import pytest


@pytest.fixture(scope='module')
def backup_file_paths():
	backup_path_str = Path("/var/univention-backup/samba/")
	backup_files = ["samba4_private.%s.tar.bz2", "sysvol.%s.tar.bz2"]
	backup_files_paths = [backup_path_str / (path % (datetime.datetime.now().strftime("%Y-%m-%d"))) for path in backup_files]
	renamed_backup_files = [Path(str(path) + ".back") for path in backup_files_paths]
	# check if today backup file exists
	for index, file_path in enumerate(backup_files_paths):
		if file_path.exists():
			# move to not overwrite
			file_path.rename(renamed_backup_files[index])
	try:
		yield backup_files_paths
	finally:
		while Path("/tmp/wait").exists():
			sleep(1)
		# remove new file
		for file_path in backup_files_paths:
			file_path.unlink()
		for index, renamed_file in enumerate(renamed_backup_files):
			if renamed_file.exists():
				renamed_file.rename(backup_files_paths[index])


def test_samba4_backup(backup_file_paths):
	# execute the command
	command = ["/usr/sbin/univention-samba4-backup"]
	print("To run %s" % command)
	status = subprocess.check_call(command)
	assert status == 0
	# check that new backup files is created
	assert backup_file_paths[0].exists()
	assert backup_file_paths[1].exists()
