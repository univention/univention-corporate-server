import subprocess
import os

from univention.fstab import fstab, mntent
import univention.testing.utils as utils
import univention.testing.udm as udm_test
import univention.testing.strings as uts
import univention.testing.ucr as ucr_test
from univention.testing.umc import Client
import quota_cache as qc


class QuotaCheck(object):

	def __init__(self, quota_type="usrquota", fs_type="ext4"):
		ucr = ucr_test.UCSTestConfigRegistry()
		ucr.load()
		self.ldap_base = ucr.get('ldap/base')
		self.my_fqdn = '%s.%s' % (ucr.get('hostname'), ucr.get('domainname'))
		account = utils.UCSTestDomainAdminCredentials()
		self.umc_client = Client(self.my_fqdn, username=account.username, password=account.bindpw)
		self.share_name = uts.random_name()
		self.share_name2 = uts.random_name()
		self.username = uts.random_name()
		self.quota_type = quota_type
		self.fs_type = fs_type

	def _activate_quota(self, loop_dev):
		print("Enable quota")
		options = {"partitionDevice": loop_dev}
		result = self.umc_client.umc_command('quota/partitions/activate', options).result
		if not result.get('success'):
			utils.fail("Activating quota failed:\n{}".format(result))

	def _check_quota_settings(self, loop_dev, expected_values={}):
		print("Check quota settings")
		options = {"filter": "*", "partitionDevice": loop_dev}
		user_quotas = self.umc_client.umc_command('quota/users/query', options).result
		expected_user_quota = {
			u'fileLimitHard': u'{}'.format(expected_values.get('fhard', 15)),
			u'fileLimitSoft': u'{}'.format(expected_values.get('fsoft', 10)),
			u'fileLimitTime': u'-',
			u'fileLimitUsed': u'1',
			u'id': u'{}@{}'.format(self.username, loop_dev),
			u'partitionDevice': u'{}'.format(loop_dev),
			u'sizeLimitHard': float(expected_values.get('bhard', 4)),
			u'sizeLimitSoft': float(expected_values.get('bsoft', 1)),
			u'sizeLimitTime': u'-',
			u'sizeLimitUsed': float(0),
			u'user': u'{}'.format(self.username),
		}
		if expected_user_quota not in user_quotas:
			utils.fail("Quota was not set through pam")

	def test_quota_pam(self):
		with TempFilesystem(self.quota_type, fs_type=self.fs_type) as tfs, udm_test.UCSTestUDM() as udm:
			quota_policy = {
				"inodeSoftLimit": '10',
				"inodeHardLimit": '15',
				"spaceSoftLimit": str(1024 ** 2),
				"spaceHardLimit": str(2048 ** 2),
				"reapplyQuota": 'TRUE',
				"name": uts.random_name(),
			}

			self._activate_quota(tfs.loop_dev)
			print("Create Share")
			share = udm.create_object(
				'shares/share', name=self.share_name, path=tfs.mount_point, host=self.my_fqdn, directorymode="0777"
			)
			utils.wait_for_replication_and_postrun()
			qc.cache_must_exists(share)
			print("Create user")
			udm.create_user(username=self.username, check_for_drs_replication=False, wait_for=False)
			print("Create quota policy")
			policy = self.create_quota_policy(udm, quota_policy)
			print("Append quota policy")
			udm.modify_object("shares/share", dn=share, policy_reference=policy)
			utils.wait_for_replication_and_postrun()
			qc.check_values(
				share,
				quota_policy["inodeSoftLimit"],
				quota_policy["inodeHardLimit"],
				quota_policy["spaceSoftLimit"],
				quota_policy["spaceHardLimit"],
				quota_policy["reapplyQuota"]
			)
			self.touch_file(tfs.mount_point)
			self._check_quota_settings(tfs.loop_dev)

	def test_quota_pam_policy_removal(self):
		with TempFilesystem(self.quota_type, fs_type=self.fs_type) as tfs, udm_test.UCSTestUDM() as udm:
			quota_policy = {
				"inodeSoftLimit": '10',
				"inodeHardLimit": '15',
				"spaceSoftLimit": str(1024 ** 2),
				"spaceHardLimit": str(2048 ** 2),
				"reapplyQuota": 'TRUE',
				"name": uts.random_name(),
			}
			expected_result = {
				'bsoft': 1,
				'bhard': 4,
				'fsoft': 10,
				'fhard': 15
			}

			self._activate_quota(tfs.loop_dev)
			print("Create Share")
			share = udm.create_object(
				'shares/share', name=self.share_name, path=tfs.mount_point, host=self.my_fqdn, directorymode="0777"
			)
			utils.wait_for_replication_and_postrun()
			qc.cache_must_exists(share)
			print("Create user")
			udm.create_user(username=self.username, check_for_drs_replication=False)
			print("Create quota policy")
			policy = self.create_quota_policy(udm, quota_policy)
			print("Append quota policy")
			udm.modify_object("shares/share", dn=share, policy_reference=policy)
			utils.wait_for_replication_and_postrun()
			qc.check_values(
				share,
				quota_policy["inodeSoftLimit"],
				quota_policy["inodeHardLimit"],
				quota_policy["spaceSoftLimit"],
				quota_policy["spaceHardLimit"],
				quota_policy["reapplyQuota"]
			)
			print("Simulate login")
			self.touch_file(tfs.mount_point)
			print("Remove quota policy")
			udm.modify_object("shares/share", dn=share, policy_dereference=policy)
			utils.wait_for_replication_and_postrun()
			print("Simulate login")
			self.touch_file(tfs.mount_point)
			self._check_quota_settings(tfs.loop_dev, expected_result)

	def test_two_shares_on_one_mount(self, quota_policies, expected_result):
		with TempFilesystem(self.quota_type, fs_type=self.fs_type) as tfs, udm_test.UCSTestUDM() as udm:
			self._activate_quota(tfs.loop_dev)
			print("Create Shares")

			share1_path = os.path.join(tfs.mount_point, self.share_name)
			share2_path = os.path.join(tfs.mount_point, self.share_name2)
			os.mkdir(share1_path)
			os.mkdir(share2_path)

			share1 = udm.create_object(
				'shares/share', name=self.share_name, path=share1_path, host=self.my_fqdn, directorymode="0777"
			)
			share2 = udm.create_object(
				'shares/share', name=self.share_name2, path=share2_path, host=self.my_fqdn, directorymode="0777"
			)
			utils.wait_for_replication_and_postrun()
			qc.cache_must_exists(share1)
			qc.cache_must_exists(share2)
			print("Create user")
			udm.create_user(username=self.username, check_for_drs_replication=False)
			print("Create quota policies")
			policies = []
			for quota_policy in quota_policies:
				policies.append(self.create_quota_policy(udm, quota_policy))
			print("Append quota policies")
			udm.modify_object("shares/share", dn=share1, policy_reference=policies[0])
			udm.modify_object("shares/share", dn=share2, policy_reference=policies[1])
			utils.wait_for_replication_and_postrun()
			self.touch_file(tfs.mount_point)
			self._check_quota_settings(tfs.loop_dev, expected_result)

	def test_two_shares_on_one_mount_only_one_policy(self):
		with TempFilesystem(self.quota_type, fs_type=self.fs_type) as tfs, udm_test.UCSTestUDM() as udm:
			quota_policy = {
				"inodeSoftLimit": '10',
				"inodeHardLimit": '15',
				"spaceSoftLimit": str(1024 ** 2),
				"spaceHardLimit": str(2048 ** 2),
				"reapplyQuota": 'TRUE',
				"name": uts.random_name(),
			}

			self._activate_quota(tfs.loop_dev)
			print("Create Shares")

			share1_path = os.path.join(tfs.mount_point, self.share_name)
			share2_path = os.path.join(tfs.mount_point, self.share_name2)
			os.mkdir(share1_path)
			os.mkdir(share2_path)

			share1 = udm.create_object(
				'shares/share', name=self.share_name, path=share1_path, host=self.my_fqdn, directorymode="0777"
			)
			share2 = udm.create_object(
				'shares/share', name=self.share_name2, path=share2_path, host=self.my_fqdn, directorymode="0777"
			)
			utils.wait_for_replication_and_postrun()
			qc.cache_must_exists(share1)
			qc.cache_must_exists(share2)
			print("Create user")
			udm.create_user(username=self.username, check_for_drs_replication=False)
			print("Create quota policy")
			policy = self.create_quota_policy(udm, quota_policy)
			print("Append quota policy")
			udm.modify_object("shares/share", dn=share1, policy_reference=policy)
			utils.wait_for_replication_and_postrun()
			self.touch_file(tfs.mount_point)
			self._check_quota_settings(tfs.loop_dev)

	def touch_file(self, mountpoint):
		print("Write file on filesystem as user: {}".format(self.username))
		subprocess.check_call([
			"sudo",
			"--user",
			self.username,
			"touch",
			os.path.join(mountpoint, "foo"),
		])

	def create_quota_policy(self, udm, quota_policy):
		return udm.create_object(
			'policies/share_userquota',
			position='cn=userquota,cn=shares,cn=policies,%s' % self.ldap_base,
			name=quota_policy["name"],
			softLimitSpace=quota_policy["spaceSoftLimit"],
			hardLimitSpace=quota_policy["spaceHardLimit"],
			softLimitInodes=quota_policy["inodeSoftLimit"],
			hardLimitInodes=quota_policy["inodeHardLimit"],
			reapplyeverylogin=quota_policy["reapplyQuota"],
		)


class TempFilesystem(object):

	def __init__(self, quota_type, fs_type='ext4'):
		self.filename = "/tmp/30_quota_pam.fs"
		self.mount_point = "/mnt/30_quota_pam"
		self.quota_type = quota_type
		self.fs_type = fs_type

	def _create_filesystem(self):
		print("Create file")
		subprocess.check_call([
			"dd",
			"if=/dev/zero",
			"of={}".format(self.filename),
			"bs=1M",
			"count=20",
		])
		print("Format file")
		subprocess.check_call([
			"mkfs",
			"--type",
			self.fs_type,
			self.filename,
		])

	def _mount_filesystem(self):
		os.mkdir(self.mount_point)
		print("Setup loop device")
		self.loop_dev = subprocess.check_output(["losetup", "--find"]).strip("\n")
		subprocess.check_call(["losetup", self.loop_dev, self.filename])
		print("Mount file")
		file_mntent = mntent(self.loop_dev, self.mount_point, self.fs_type, opts=self.quota_type)
		etc_fstab = fstab()
		etc_fstab.append(file_mntent)
		etc_fstab.save()
		subprocess.check_call([
			"mount",
			"--all",
		])
		subprocess.check_call([
			"chmod",
			"0777",
			self.mount_point,
		])

	def _umount_filesystem(self):
		print("Unmount file")
		subprocess.check_call([
			"umount",
			self.mount_point,
		])
		subprocess.check_call([
			"losetup",
			"--detach",
			self.loop_dev,
		])
		etc_fstab = fstab()
		for entry in list(etc_fstab):
			if entry.fsname == self.loop_dev:
				break
		etc_fstab.remove(entry)
		etc_fstab.save()

	def __enter__(self):
		self._create_filesystem()
		self._mount_filesystem()
		return self

	def __exit__(self, *args):
		self._umount_filesystem()
		os.rmdir(self.mount_point)
		os.remove(self.filename)
