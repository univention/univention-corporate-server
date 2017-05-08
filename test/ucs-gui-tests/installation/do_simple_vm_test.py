#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Python VNC automate
#
# Copyright 2016 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

import argparse
import re
import subprocess
import sys
import unicodedata

import create_license


def parse_args():
	parser = argparse.ArgumentParser(description='Test a fully installed virtual machine, by installing the app dudle on it.')
	parser.add_argument('--password', dest="password", default="univention", help='The password which is used by the root account of the virtual machine. Default is univention.')
	parser.add_argument('ip', help='The IP address which is used by the virtual machine.')
	return parser.parse_args()


# FIXME: Would be nicer to use a library, but this would add a dependency.
def slugify(txt):
	slug = unicodedata.normalize('NFKD', txt.decode())
	slug = slug.encode('ascii', 'ignore').lower()
	slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
	slug = re.sub(r'[-]+', '-', slug)
	return slug.encode()


class VmTester(object):
	def __init__(self):
		self.args = parse_args()
		self.ldap_base = self.get_ldap_base_of_vm()
		self.license_file = self.ldap_base_to_license_filename(
			self.ldap_base
		)

	def get_ldap_base_of_vm(self):
		self.execute_through_ssh('ucr get ldap/base > target_vm_ldap_base')
		self.copy_through_ssh('root@%s:~/target_vm_ldap_base' % (self.args.ip,), '.')
		with open('target_vm_ldap_base', 'r') as ldap_base_file:
			ldap_base = ldap_base_file.read()
			return ldap_base.strip('\n\r')

	def ldap_base_to_license_filename(self, ldap_base):
		ldap_base_slug = slugify(ldap_base)
		filename = "%s.license" % (ldap_base_slug,)
		filepath = '/var/lib/jenkins/ec2/license/%s' % (filename,)
		return filepath

	def test_vm(self):
		self.create_license_for_ldap_base()
		self.import_license_on_vm()
		self.install_dudle_on_vm()
		self.exit_with_exitcode_of_dudle_installation()

	def create_license_for_ldap_base(self):
		license_creator = create_license.LicenseCreator(self.ldap_base, self.license_file)
		license_creator.provide_valid_license()

	def import_license_on_vm(self):
		self.copy_through_ssh(self.license_file, 'root@%s:~/tmp.license' % (self.args.ip,))
		self.execute_through_ssh('univention-license-import tmp.license')

	def install_dudle_on_vm(self):
		self.execute_through_ssh('echo %s > pwdfile' % (self.args.password,))
		self.execute_through_ssh('univention-app install dudle --noninteractive --pwdfile=pwdfile')
		self.execute_through_ssh('echo $? > app_installation_return_code')

	def exit_with_exitcode_of_dudle_installation(self):
		self.copy_through_ssh(
			'root@%s:app_installation_return_code' % (self.args.ip,), '.'
		)
		with open('app_installation_return_code', 'r') as return_code_file:
			sys.exit(int(return_code_file.read()))

	def execute_through_ssh(self, command):
		subprocess.call(
			'sshpass -p %s ssh root@%s -o StrictHostKeyChecking=no "%s"' %
			(self.args.password, self.args.ip, command), shell=True
		)

	def copy_through_ssh(self, source_file, target_file):
		subprocess.call(
			"sshpass -p %s scp -o StrictHostKeyChecking=no %s %s" %
			(self.args.password, source_file, target_file), shell=True
		)


if __name__ == '__main__':
	tester = VmTester()
	tester.test_vm()
