from vminstall.utils import copy_through_ssh, execute_through_ssh


class TestDudleInstallation(object):

    def test_install_dudle(self, role, ip_address, master_ip, password):
        self.ip = ip_address
        self.master_ip = master_ip if role != 'master' else self.ip
        self.password = password
        if role != 'basesystem':
            self.import_license_on_vm()
            execute_through_ssh(self.password, f'echo {self.password} > pwdfile', self.ip)
            execute_through_ssh(self.password, 'univention-app install dudle --noninteractive --pwdfile=pwdfile', self.ip)

    def import_license_on_vm(self):
        copy_through_ssh(self.password, 'utils/license_client.py', f'root@{self.master_ip}:/root/')
        copy_through_ssh(self.password, '/var/lib/jenkins/ec2/license/license.secret', f'root@{self.master_ip}:/etc/license.secret')
        execute_through_ssh(self.password, r'python license_client.py "$(ucr get ldap/base)" "$(date -d +1\ year +%d.%m.%Y)"', self.master_ip)
        execute_through_ssh(self.password, 'univention-license-import ./ValidTest.license && univention-license-check', self.master_ip)
