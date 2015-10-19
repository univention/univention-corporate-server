# -*- coding: utf-8 -*-
#
# UCS test
#
# Copyright 2015 Univention GmbH
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

from univention.testing.strings import random_name, random_version
from univention.testing.debian_package import DebianPackage
from univention.testing.ucr import UCSTestConfigRegistry
from univention.config_registry import handler_set, ConfigRegistry
import os
import shutil
import subprocess
import urllib2


class UCSTest_Docker_Exception(Exception): pass
class UCSTest_Docker_LoginFailed(Exception): pass
class UCSTest_Docker_PullFailed(Exception): pass
class AppcenterMetainfAlreadyExists(Exception): pass
class AppcenterRepositoryAlreadyExists(Exception): pass
class UCSTest_DockerApp_InstallationFailed(Exception): pass
class UCSTest_DockerApp_UpdateFailed(Exception): pass
class UCSTest_DockerApp_UpgradeFailed(Exception): pass
class UCSTest_DockerApp_VerifyFailed(Exception): pass
class UCSTest_DockerApp_RemoveFailed(Exception): pass
class UCSTest_DockerApp_ModProxyFailed(Exception): pass


def docker_login(server='docker.software-univention.de'):
	ret = subprocess.call(['docker', 'login', '-e', 'foo@bar', '-u', 'ucs', '-p', 'readonly', server])
	if ret != 0:
		raise UCSTest_Docker_LoginFailed()


def docker_pull(image, server='docker.software-univention.de'):
	ret = subprocess.call(['docker', 'pull', '%s/%s' % (server, image)])
	if ret != 0:
		raise UCSTest_Docker_PullFailed()


def get_app_name():
	""" returns a valid app name """
	return random_name()


def get_app_version():
	return random_version()


class App:
	def __init__(self, name, version, app_directory_suffix=None, package_name=None, build_package=True):
		self.app_name = name
		self.app_version = version

		if not app_directory_suffix:
			self.app_directory_suffix = random_version()
		else:
			self.app_directory_suffix = app_directory_suffix

		self.app_directory = '%s_%s' % (self.app_name, self.app_directory_suffix)

		if package_name:
			self.package_name = package_name
		else:
			self.package_name = get_app_name()

		self.package_version = '%s.%s' % (version,get_app_version())

		self.ucr = ConfigRegistry()
		self.ucr.load()

		if build_package:
			self.package = DebianPackage(name=self.package_name, version=self.package_version)
			self.package.build()
		else:
			self.package = None

		self.ini = {}

		self.ini['ID'] = self.app_name
		self.ini['Code'] = self.app_name[0:2]
		self.ini['Name'] = self.app_name
		self.ini['Version'] = self.app_version
		self.ini['NotifyVendor'] = False
		self.ini['Categories'] = 'System services'
		if self.package:
			self.ini['DefaultPackages'] = self.package_name
		self.ini['ServerRole'] = 'domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver'

		self.scripts = {}

		self.ucs_version = self.ucr.get('version/version')

		self.installed = False

		self.admin_user = self.ucr.get('tests/domainadmin/account').split(',')[0][len('uid='):]
		self.admin_pwdfile = self.ucr.get('tests/domainadmin/pwdfile')

	def set_ini_parameter(self, **kwargs):
		for key, value in kwargs.iteritems():
			self.ini[key] = value
		pass

	def add_to_local_appcenter(self):
		self._dump_ini()
		if self.package:
			self._copy_package()
		self._dump_scripts()

	def add_script(self, **kwargs):
		for key, value in kwargs.iteritems():
			self.scripts[key] = value

	def install(self):
		self._update()
		admin_user = self.ucr.get('tests/domainadmin/account').split(',')[0][len('uid='):]
		# ret = subprocess.call('univention-app install --noninteractive --do-not-revert --username=%s --pwdfile=%s %s' %
		ret = subprocess.call('univention-app install --noninteractive --username=%s --pwdfile=%s %s' %
					(admin_user, self.ucr.get('tests/domainadmin/pwdfile'), self.app_name), shell=True)
		if ret != 0:
			raise UCSTest_DockerApp_InstallationFailed()

		self.ucr.load()
		self.container_id = self.ucr.get('appcenter/apps/%s/container' % self.app_name)

		self.installed = True

	def _update(self):
		ret = subprocess.call(['univention-app', 'update'])
		if ret != 0:
			raise UCSTest_DockerApp_UpdateFailed()

	def upgrade(self):
		self._update()
		ret = subprocess.call('univention-app upgrade --noninteractive --username=%s --pwdfile=%s %s' %
					(self.admin_user, self.admin_pwdfile, self.app_name), shell=True)
		if ret != 0:
			raise UCSTest_DockerApp_UpgradeFailed()
		self.ucr.load()
		self.container_id = self.ucr.get('appcenter/apps/%s/container' % self.app_name)
		self.installed = True

	def verify(self, joined=True):
		ret = subprocess.call('univention-app status --noninteractive --username=%s --pwdfile=%s %s' %
					(self.admin_user, self.admin_pwdfile, self.app_name), shell=True)
		if ret != 0:
			raise UCSTest_DockerApp_VerifyFailed()

		if joined:
			ret = subprocess.call('docker exec %s univention-check-join-status' % self.container_id, stderr=subprocess.STDOUT, shell=True)
			if ret != 0:
				raise UCSTest_DockerApp_VerifyFailed()

	def uninstall(self):
		if self.installed:
			ret = subprocess.call('univention-app remove --noninteractive --username=%s --pwdfile=%s %s' %
						(self.admin_user, self.admin_pwdfile, self.app_name), shell=True)
			if ret != 0:
				raise UCSTest_DockerApp_RemoveFailed()

	def execute_command_in_container(self, cmd):
		print 'Execute: %s' % cmd
		return subprocess.check_output('docker exec %s %s' % (self.container_id, cmd), stderr=subprocess.STDOUT, shell=True)

	def remove(self):
		if self.package:
			self.package.remove()

	def _dump_ini(self):
		if not os.path.exists('/var/www/meta-inf/%s' % self.ucs_version):
			os.makedirs('/var/www/meta-inf/%s' % self.ucs_version)

		target = os.path.join('/var/www/meta-inf/%s' % self.ucs_version, '%s.ini' % self.app_directory)
		f = open(target, 'w')
		print 'Write ini file: %s' % target
		f.write('[Application]\n')
		print '[Application]'
		for key in self.ini.keys():
			f.write('%s: %s\n' % (key, self.ini[key]))
			print '%s: %s' % (key, self.ini[key])
		print
		f.close()

	def _dump_scripts(self):
		for script in self.scripts.keys():
			comp_path = os.path.join('/var/www/univention-repository/%s/maintained/component' % self.ucs_version, '%s' % self.app_directory)
			if not os.path.exists(comp_path):
				os.makedirs(comp_path)
			target = os.path.join(comp_path, script)

			print 'Create %s' % target
			print self.scripts[script]

			f = open(target, 'w')
			f.write(self.scripts[script])
			f.close()

	def _copy_package(self):
		target = os.path.join('/var/www/univention-repository/%s/maintained/component' % self.ucs_version, '%s/all' % self.app_directory)
		os.makedirs(target)
		shutil.copy(self.package.get_binary_name(), target)
		subprocess.call('''
			cd /var/www/univention-repository/%(version)s/maintained/component;
			apt-ftparchive packages %(app)s/all >%(app)s/all/Packages;
			gzip -c %(app)s/all/Packages >%(app)s/all/Packages.gz
		''' % {'version': self.ucs_version, 'app': self.app_directory}, shell=True)

	def create_basic_modproxy_settings(self):
		self.add_script(setup='''#!/bin/bash
set -x -e
univention-install --yes univention-apache
mkdir /var/www/%(app_name)s
echo "TEST-%(app_name)s" >>/var/www/%(app_name)s/index.txt
/usr/share/univention-docker-container-mode/setup "$@"
''' % {'app_name': self.app_name})

	def verify_basic_modproxy_settings(self):
		fqdn = '%s.%s' % (self.ucr['hostname'], self.ucr['domainname'])
		test_string = 'TEST-%s\n' % self.app_name

		response = urllib2.urlopen('http://%s/%s/index.txt' % (fqdn, self.app_name))
		html = response.read()
		if html != test_string:
			raise UCSTest_DockerApp_ModProxyFailed(Exception)

		response = urllib2.urlopen('https://%s/%s/index.txt' % (fqdn, self.app_name))
		html = response.read()
		if html != test_string:
			raise UCSTest_DockerApp_ModProxyFailed(Exception)




class Appcenter:
	def __init__(self, version=None):
		self.meta_inf_created = False
		self.univention_repository_created = False

		self.ucr = UCSTestConfigRegistry()
		self.ucr.load()

		if os.path.exists('/var/www/meta-inf'):
			print 'ERROR: /var/www/meta-inf already exists'
			raise AppcenterMetainfAlreadyExists()
		if os.path.exists('/var/www/univention-repository'):
			print 'ERROR: /var/www/univention-repository already exists'
			raise AppcenterRepositoryAlreadyExists()

		if not version:
			version = self.ucr.get('version/version')

		self.add_ucs_version_to_appcenter(version)

	def add_ucs_version_to_appcenter(self, version):

		if not os.path.exists('/var/www/meta-inf'):
			os.makedirs('/var/www/meta-inf', 0755)
			self.meta_inf_created = True

		if not os.path.exists('/var/www/univention-repository'):
			os.makedirs('/var/www/univention-repository', 0755)
			self.univention_repository_created = True

		os.makedirs('/var/www/univention-repository/%s/maintained/component' % version)
		os.makedirs('/var/www/meta-inf/%s' % version)

		if not os.path.exists('/var/www/meta-inf/categories.ini'):
			f = open('/var/www/meta-inf/categories.ini', 'w')
			f.write('''[de]
Administration=Administration
Business=Business
Collaboration=Collaboration
Education=Schule
System services=Systemdienste
UCS components=UCS-Komponenten
Virtualization=Virtualisierung''')
			f.close()

		handler_set(['update/secure_apt=no', 'repository/app_center/server=%s.%s' % (self.ucr['hostname'], self.ucr['domainname'])])

	def update(self):
		for vv in os.listdir('/var/www/meta-inf/'):
			directory = os.path.join('/var/www/meta-inf/', vv)
			if not os.path.isdir(directory):
				continue
			print 'create_appcenter_json.py for %s' % vv
			subprocess.call('create_appcenter_json.py -u %(version)s -d /var/www -o /var/www/meta-inf/%(version)s/index.json.gz -s http://%(fqdn)s' %
				 {'version': vv, 'fqdn': '%s.%s' % (self.ucr['hostname'], self.ucr['domainname'])}, shell=True)

	def cleanup(self):
		if self.meta_inf_created:
			shutil.rmtree('/var/www/meta-inf')
		if self.univention_repository_created:
			shutil.rmtree('/var/www/univention-repository')
		self.ucr.revert_to_original_registry()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if exc_type:
			print 'Cleanup after exception: %s %s' % (exc_type, exc_value)
		self.cleanup()

def store_data_script_4_1():
	return '''#!/usr/bin/python2.7

from optparse import OptionParser
import glob
import os
import shutil
import string


# Helper function to copy all meta data of a file or directory
def copy_permissions(src, dest):
	s_stat = os.stat(src)
	os.chown(dest, s_stat.st_uid, s_stat.st_gid)
	shutil.copymode(src, dest)
	shutil.copystat(src, dest)
	d_stat = os.stat(dest)


# Helper function to copy the files and directory
def copy_to_persistent_storage(src, dest):
	l_src = string.split(src, '/')
	# Ignore first empty entry
	if l_src[0] == '':
		l_src = l_src[1:]
	for j in range(0, len(l_src)):
		s = os.path.join('/', string.join(l_src[0:j + 1], '/'))
		d = os.path.join(dest, string.join(l_src[0:j + 1], '/'))
		if os.path.isdir(s):
			if not os.path.exists(d):
				os.makedirs(d)
				copy_permissions(s, d)
		else:
			print 'cp %s %s' % (s, d)
			shutil.copy(s, d)
			copy_permissions(s, d)


def copy_files(src, dest):
	for f in glob.glob(src):
		copy_to_persistent_storage(f, dest)


def copy_recursive(src, dest):
	if not os.path.exists(src):
		return
	copy_to_persistent_storage(src, dest)
	for root, dirs, files in os.walk(src):
		for f in files:
			fullpath = os.path.join(root, f)
			copy_to_persistent_storage(fullpath, dest)

if __name__ == '__main__':
	parser = OptionParser('%prog [options]')
	parser.add_option('--app', dest='app', help='App ID')
	parser.add_option('--app-version', dest='app_version', help='Version of App')
	parser.add_option('--error-file', dest='error_file', help='Name of Error File')
	opts, args = parser.parse_args()

	dest = '/var/lib/univention-appcenter/apps/%s/conf/' % opts.app

	# The files and directories below the files directory are restored
	# automatically after the new container has been started
	store = '/var/lib/univention-appcenter/apps/%s/conf/files' % opts.app

	for f in glob.glob('/etc/univention/base*conf'):
		print 'cp %s %s' % (f, dest)
		shutil.copy(f, dest)
	copy_files('/etc/*.secret', store)
	copy_recursive('/etc/univention/ssl', store)
	copy_recursive('/var/univention-join', store)
	copy_recursive('/var/lib/univention-ldap/', store)
	copy_recursive('/var/lib/univention-directory-listener/', store)
	copy_recursive('/etc/univention/connector', store)
'''
