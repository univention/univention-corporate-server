import subprocess


class TestDudleInstallation(object):

	def test_install_dudle(self, role, ip_address, master_ip, password):
		self.ip = ip_address
		self.master_ip = master_ip if role != 'master' else self.ip
		self.password = password
		if role != 'basesystem':
			self.remove_old_sshkey()
			self.import_license_on_vm()
			self.execute_through_ssh('echo %s > pwdfile' % (self.password,))
			self.execute_through_ssh('univention-app install dudle --noninteractive --pwdfile=pwdfile')

	def remove_old_sshkey(self):
		subprocess.check_call((
			'ssh-keygen',
			'-R',
			self.ip
		))

	def import_license_on_vm(self):
		self.copy_through_ssh('utils/license_client.py', 'root@%s:/root/' % (self.master_ip,))
		self.copy_through_ssh('/root/ec2/license/license.secret', 'root@%s:/etc/license.secret' % (self.master_ip,))
		self.execute_through_ssh('python license_client.py "$(ucr get ldap/base)" "$(date -d +1\ year +%d.%m.%Y)"', self.master_ip)
		self.execute_through_ssh('univention-license-import ./ValidTest.license && univention-license-check', self.master_ip)

	def execute_through_ssh(self, command, ip=None):
		subprocess.check_call((
			'sshpass',
			'-p', self.password,
			'ssh',
			'-o', 'StrictHostKeyChecking=no',
			'root@%s' % (ip or self.ip,),
			command
		))

	def copy_through_ssh(self, source_file, target_file):
		subprocess.check_call((
			'sshpass',
			'-p', self.password,
			'scp',
			'-o', 'StrictHostKeyChecking=no',
			source_file, target_file
		))
