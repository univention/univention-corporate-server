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
from univention.config_registry import ConfigRegistry
from univention.testing.debian_package import DebianPackage
import os
import shutil
import subprocess

class UCSTest_Docker_Exception(Exception): pass
class UCSTest_Docker_LoginFailed(Exception): pass
class UCSTest_Docker_PullFailed(Exception): pass
class AppcenterMetainfAlreadyExists(Exception): pass
class AppcenterRepositoryAlreadyExists(Exception): pass

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

		self.package_name = get_app_name()
		self.package_version = get_app_version()

		self.package = DebianPackage(name=self.package_name, version=self.package_version)
		self.package.build()

	def build(self):
		pass

	def add_to_local_appcenter(self):
		pass

	def install(self):
		pass

	def verify(self):
		pass

	def uninstall(self):
		pass

	def remove(self):
		self.package.remove()

class Appcenter:
	def __init__(self):
		self.meta_inf_created = False
		self.univention_repository_created = False
		
		ucr = ConfigRegistry()
		ucr.load()

		version = ucr.get('version/version')

		if os.path.exists('/var/www/meta-inf'):
			print 'ERROR: /var/www/meta-inf already exists'
			raise AppcenterMetainfAlreadyExists
		if os.path.exists('/var/www/univention-repository'):
			print 'ERROR: /var/www/univention-repository already exists'
			raise AppcenterRepositoryAlreadyExists

		os.makedirs('/var/www/meta-inf', 0755)
		self.meta_inf_created = True

		os.makedirs('/var/www/univention-repository', 0755)
		self.univention_repository_created = True

		os.makedirs('/var/www/univention-repository/%s/maintained/component' % version)
		os.makedirs('/var/www/meta-inf/%s' % version)

	def cleanup(self):
		if self.meta_inf_created:
			shutil.rmtree('/var/www/meta-inf')
		if self.univention_repository_created:
			shutil.rmtree('/var/www/univention-repository')

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if exc_type:
			print 'Cleanup after exception: %s %s' % (exc_type, exc_value)
		self.cleanup()
