#!/usr/share/ucs-test/runner pytest-3 -l -vv
## desc: "Test univention-directory-logger."
## packages:
##  - univention-directory-notifier
##  - univention-directory-listener
##  - univention-directory-logger
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous
## bugs: [51772]

import os


class Test_DellogProcess(object):
	"""Tests regarding the delete log files in ldap/logging/dellogdir"""

	def test_correct_files(self, udm, ucr):
		"""Create and remove a ldap user object.

		The slapd-daemon will log this process in the 'dellogdir'.
		The directory-logger module should consume/remove
		the log files in the 'dellodir'
		"""
		dellog_directory = ucr["ldap/logging/dellogdir"]

		user = udm.create_user()

		udm.remove_user(user[1])

		# No files expected, the directory-logger
		# should remove all files if working correctly
		assert len(os.listdir(dellog_directory)) == 0

	def test_corrupted_file(self, udm, ucr):
		"""Test effects of a corrupted file

		In Bug #51772 a corrupted file leads to an accumulation of files
		in the 'dellogdir'. This test verifies that the bug is fixed.
		"""
		dellog_directory = ucr["ldap/logging/dellogdir"]

		# Create corrupted file
		corrupted_file_path = os.path.join(dellog_directory, "00001")
		with open(corrupted_file_path, "w") as f:
			f.write("")

		# analogous to test case 'test_correct_files'
		try:
			user = udm.create_user()

			udm.remove_user(user[1])

			directory_content = os.listdir(dellog_directory)
			assert len(directory_content) == 0

		finally:
			if os.path.exists(corrupted_file_path):
				os.remove(corrupted_file_path)
