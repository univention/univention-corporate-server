import subprocess
import os

import univention.testing.utils as utils
import univention.testing.udm as udm_test
import univention.testing.strings as uts
import univention.testing.ucr as ucr_test
import quota_cache as qc


class QuoataCheck(object):

	def __init__(self, quota_type="usrquota"):
		ucr = ucr_test.UCSTestConfigRegistry()
		ucr.load()
		self.my_fqdn = '%s.%s' % (ucr.get('hostname'), ucr.get('domainname'))
		self.share_name = uts.random_name()
		self.username = uts.random_name()
		self.quota_type = quota_type
		self.quota_policy = {
			"inodeSoftLimit": '10',
			"inodeHardLimit": '15',
			"spaceSoftLimit": '1024',
			"spaceHardLimit": '2048',
			"reapplyQuota": 'TRUE',
			"name": uts.random_name(),
			"position": 'cn=userquota,cn=shares,cn=policies,%s' % ucr.get('ldap/base'),
		}

	def test_quota_pam(self):
		with TempFilesystem(self.quota_type) as mount_point, udm_test.UCSTestUDM() as udm:
			print("Create Share")
			share = udm.create_object(
				'shares/share', name=self.share_name, path=mount_point, host=self.my_fqdn, directorymode="0777"
			)
			utils.wait_for_replication_and_postrun()
			qc.cache_must_exists(share)
			print("Create user")
			udm.create_user(username=self.username, check_for_drs_replication=False)
			print("Create quota policy")
			policy = udm.create_object(
				'policies/share_userquota',
				position=self.quota_policy["position"],
				name=self.quota_policy["name"],
				softLimitSpace=self.quota_policy["spaceSoftLimit"],
				hardLimitSpace=self.quota_policy["spaceHardLimit"],
				softLimitInodes=self.quota_policy["inodeSoftLimit"],
				hardLimitInodes=self.quota_policy["inodeHardLimit"],
				reapplyeverylogin=self.quota_policy["reapplyQuota"],
			)
			print("Append quota policy")
			udm.modify_object("shares/share", dn=share, policy_reference=policy)
			utils.wait_for_replication_and_postrun()
			qc.check_values(
				share,
				self.quota_policy["inodeSoftLimit"],
				self.quota_policy["inodeHardLimit"],
				self.quota_policy["spaceSoftLimit"],
				self.quota_policy["spaceHardLimit"],
				self.quota_policy["reapplyQuota"]
			)
			print("Write file on filesystem as user: {}".format(self.username))
			subprocess.check_call([
				"sudo",
				"--user",
				self.username,
				"touch",
				os.path.join(mount_point, "foo"),
			])
			quota_settings = subprocess.check_output([
				"repquota",
				"--user",
				"--verbose",
				"--output",
				"csv",
				mount_point,
			])
			print("Quota settings:\n{}".format(quota_settings))
			quota_settings = quota_settings.split("\n")
			user_quota = "{},ok,ok,0,{},{},,1,{},{},".format(
				self.username,
				str(int(self.quota_policy["spaceSoftLimit"]) / 1024),
				str(int(self.quota_policy["spaceHardLimit"]) / 1024),
				self.quota_policy["inodeSoftLimit"],
				self.quota_policy["inodeHardLimit"],
			)
			if user_quota not in quota_settings:
				utils.fail("Quota was not set through pam")


class TempFilesystem(object):

	def __init__(self, quota_type):
		self.filename = "/tmp/30_quota_pam.fs"
		self.mount_point = "/mnt/30_quota_pam"
		self.quota_type = quota_type

	def _create_filesystem(self):
		print("Create file")
		subprocess.check_call([
			"dd",
			"if=/dev/zero",
			"of={}".format(self.filename),
			"bs=1M",
			"count=10",
		])
		print("Format file")
		subprocess.check_call([
			"mkfs",
			"--type",
			"ext4",
			self.filename,
		])

	def _mount_filesystem(self):
		os.mkdir(self.mount_point)
		print("Mount file")
		subprocess.check_call([
			"mount",
			self.filename,
			self.mount_point,
			"--options",
			self.quota_type,
		])
		subprocess.check_call([
			"chmod",
			"0777",
			self.mount_point,
		])

	def _enable_quoata_on_filesystem(self):
		print("Create user quota file")
		subprocess.check_call([
			"quotacheck",
			"--user",
			"--create-files",
			"--no-remount",
			self.mount_point,
		])
		print("Enable user quota")
		subprocess.check_call([
			"quotaon",
			"--user",
			self.mount_point,
		])

	def __enter__(self):
		self._create_filesystem()
		self._mount_filesystem()
		self._enable_quoata_on_filesystem()
		return self.mount_point

	def __exit__(self, *args):
		print("Unmount file")
		subprocess.check_call([
			"umount",
			self.mount_point,
		])
		os.rmdir(self.mount_point)
		os.remove(self.filename)
