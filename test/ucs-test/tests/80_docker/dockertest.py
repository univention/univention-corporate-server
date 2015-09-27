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

class UCSTest_Docker_Exception(Exception): pass
class UCSTest_Docker_LoginFailed(Exception): pass
class UCSTest_Docker_PullFailed(Exception): pass
class AppcenterMetainfAlreadyExists(Exception): pass
class AppcenterRepositoryAlreadyExists(Exception): pass
class UCSTest_DockerApp_InstallationFailed(Exception): pass
class UCSTest_DockerApp_UpdateFailed(Exception): pass
class UCSTest_DockerApp_VerifyFailed(Exception): pass
class UCSTest_DockerApp_RemoveFailed(Exception): pass

def docker_login(server='docker.software-univention.de'):
	ret = subprocess.call(['docker','login','-e','foo@bar','-u','ucs','-p','readonly',server])
	if ret != 0:
		raise UCSTest_Docker_LoginFailed()

def docker_pull(image, server='docker.software-univention.de'):
	ret = subprocess.call(['docker','pull','%s/%s' % (server, image)])
	if ret != 0:
		raise UCSTest_Docker_PullFailed()

def get_app_name():
	""" returns a valid app name """
	return random_name()

def get_app_version():
	return random_version()

class App:
	def __init__(self, name, version):
		self.app_name = name
		self.app_version = version
		self.app_directory_suffix = random_name()

		self.app_directory = '%s_%s' % (self.app_name,self.app_directory_suffix)

		self.package_name = get_app_name()
		self.package_version = get_app_version()

		self.ucr = ConfigRegistry()
		self.ucr.load()

		self.package = DebianPackage(name=self.package_name, version=self.package_version)
		self.package.build()

		self.ini = {}

		self.ini['ID'] = self.app_name
		self.ini['Code'] = self.app_name[0:2]
		self.ini['Name'] = self.app_name
		self.ini['Version'] = self.app_version
		self.ini['NotifyVendor'] = False
		self.ini['Categories'] = 'System services'
		self.ini['DefaultPackages'] = self.package_name
		self.ini['ServerRole'] = 'domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver'


	def set_ini_parameter(self, **kwargs):
		for key, value in kwargs.iteritems():
			self.ini[key] = value
		pass

	def add_to_local_appcenter(self):
		self._dump_ini()
		self._copy_package()

	def install(self):
		ret = subprocess.call('univention-app update', shell=True)
		if ret != 0:
			raise UCSTest_DockerApp_UpdateFailed()
		admin_user = self.ucr.get('tests/domainadmin/account').split(',')[0][len('uid='):]
		ret = subprocess.call('univention-app install --noninteractive --username=%s --pwdfile=%s %s' %
					(admin_user, self.ucr.get('tests/domainadmin/pwdfile'), self.app_name), shell=True)
		if ret != 0:
			raise UCSTest_DockerApp_InstallationFailed()

		self.ucr.load()
		self.container_id = self.ucr.get('appcenter/apps/%s/container' % self.app_name)

	def verify(self):
		ret = subprocess.call(['univention-app', 'status', self.app_name])
		if ret != 0:
			raise UCSTest_DockerApp_VerifyFailed()

	def uninstall(self):
		ret = subprocess.call(['univention-app', 'remove', self.app_name])
		if ret != 0:
			raise UCSTest_DockerApp_RemoveFailed()

	def execute_command_in_container(self, cmd):
		print 'Execute: %s' % cmd
		return subprocess.check_output('docker exec %s %s' % (self.container_id, cmd), stderr=subprocess.STDOUT, shell=True)
		
	def remove(self):
		self.package.remove()

	def _dump_ini(self):
		target = os.path.join('/var/www/meta-inf/%s' % self.ucr.get('version/version'), '%s.ini' % self.app_directory)
		f = open(target, 'w')
		f.write('[Application]\n')
		for key in self.ini.keys():
			f.write('%s: %s\n' % (key, self.ini[key]))
		f.close()

	def _copy_package(self):
		target = os.path.join('/var/www/univention-repository/%s/maintained/component' % self.ucr.get('version/version'), '%s/all' % self.app_directory)
		os.makedirs(target)
		shutil.copy(self.package.get_binary_name(), target)
		subprocess.call('''
			cd /var/www/univention-repository/%(version)s/maintained/component;
			apt-ftparchive packages %(app)s/all >%(app)s/all/Packages;
			gzip -c %(app)s/all/Packages >%(app)s/all/Packages.gz
		''' % {'version': self.ucr.get('version/version'), 'app': self.app_directory}, shell=True)

class Appcenter:
	def __init__(self):
		self.meta_inf_created = False
		self.univention_repository_created = False
		
		self.ucr = UCSTestConfigRegistry()
		self.ucr.load()

		self.version = self.ucr.get('version/version')

		if os.path.exists('/var/www/meta-inf'):
			print 'ERROR: /var/www/meta-inf already exists'
			raise AppcenterMetainfAlreadyExists()
		if os.path.exists('/var/www/univention-repository'):
			print 'ERROR: /var/www/univention-repository already exists'
			raise AppcenterRepositoryAlreadyExists()

		os.makedirs('/var/www/meta-inf', 0755)
		self.meta_inf_created = True

		os.makedirs('/var/www/univention-repository', 0755)
		self.univention_repository_created = True

		os.makedirs('/var/www/univention-repository/%s/maintained/component' % self.version)
		os.makedirs('/var/www/meta-inf/%s' % self.version)

		handler_set(['update/secure_apt=no', 'repository/app_center/server=%s.%s' % (self.ucr['hostname'], self.ucr['domainname'])])

	def update(self):
		subprocess.call('create_appcenter_json.py -u %(version)s -d /var/www -o /var/www/meta-inf/%(version)s/index.json.gz -s http://%(fqdn)s' %
			 {'version': self.version, 'fqdn': '%s.%s' % (self.ucr['hostname'], self.ucr['domainname'])}, shell=True)

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
