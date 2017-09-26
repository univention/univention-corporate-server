from vminstall.utils import copy_through_ssh, execute_through_ssh


class TestDudleInstallation(object):

	def test_install_dudle(self, role, ip_address, master_ip, password):
		self.ip = ip_address
		self.master_ip = master_ip if role != 'master' else self.ip
		self.password = password
		if role != 'basesystem':
			self.import_license_on_vm()
			execute_through_ssh(self.password, 'echo %s > pwdfile' % (self.password,), self.ip)
			execute_through_ssh(self.password, 'univention-app install dudle --noninteractive --pwdfile=pwdfile', self.ip)

	def import_license_on_vm(self):
		copy_through_ssh(self.password, 'utils/license_client.py', 'root@%s:/root/' % (self.master_ip,))
		copy_through_ssh(self.password, '/var/lib/jenkins/ec2/license/license.secret', 'root@%s:/etc/license.secret' % (self.master_ip,))
		execute_through_ssh(self.password, 'python license_client.py "$(ucr get ldap/base)" "$(date -d +1\ year +%d.%m.%Y)"', self.master_ip)
		execute_through_ssh(self.password, 'univention-license-import ./ValidTest.license && univention-license-check', self.master_ip)
