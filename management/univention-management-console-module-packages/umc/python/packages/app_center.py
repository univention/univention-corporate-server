#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: software management / app center
#
# Copyright 2012 Univention GmbH
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
import urllib2
import os.path

from univention.lib.package_manager import PackageManager
from univention.management.console.log import MODULE

class Licence(object):
	uuid = 'fc452bc8-ae06-11e1-abab-00216a6f69f2'
	email_permission = True

LICENCE = Licence()

class Application(object):
	def __init__(self, id, icon, name, categories, description, email_sending, package_name=None, master_packages=None):
		self.id = id
		self.icon = icon
		self.name = name
		self.categories = categories
		self.description = description
		self.email_sending = email_sending
		if package_name is None:
			package_name = self.id
		self.package_name = package_name
		self.master_packages = master_packages

	@classmethod
	def all(cls):
		return [
			cls('agorum',
				'agorum',
				'agorum© core',
				['CMS', 'DMS'],
				'Dokumentenmangement / Enterprise Content Management',
				True,
				),
			cls('ox',
				'ox',
				'Open-Xchange',
				['Groupware'],
				'Email and collaboration suite',
				True,
				),
			cls('curl',
				'curl',
				'Curl',
				['System'],
				'Component does not exist but you should be able to install it',
				False,
				master_packages=['ack-grep'],
				),
			cls('zarafa',
				'zarafa',
				'Zarafa',
				['Groupware'],
				'The number one MS Exchange replacement',
				True,
				package_name='zarafa4ucs',
				master_packages=['zarafa-udm', 'zarafa-master'],
				),
			cls('owncloud',
				'owncloud',
				'Own Cloud',
				['Cloud software'],
				'Your Cloud, Your Data, Your Way!',
				False,
				),
		]

	def sends_email(self):
		return self.email_sending and LICENCE.email_permission

	def to_dict_overwiew(self):
		return {
			'id' : self.id,
			'icon' : self.icon,
			'name' : self.name,
			'categories' : self.categories,
			'description' : self.description,
		}

	def to_dict_detail(self, module_instance):
		can_uninstall = module_instance.package_manager.is_installed(self.package_name)
		email_agreed = LICENCE.email_permission
		is_joined = os.path.exists('/var/univention-join/joined')
		is_master = module_instance.ucr.get('server/role') == 'domaincontroller_master'
		return {
			'id' : self.id,
			'icon' : self.icon,
			'name' : self.name,
			'categories' : self.categories,
			'commercial_support' : 'Available at: <a target="_blank" href="http://www.%(id)s.com">www.%(id)s.com</a>' % {'id' : self.id},
			'description' : self.description,
			'master_packages' : self.master_packages,
			'email_sending' : self.email_sending,
			'email_agreed' : email_agreed,
			'is_joined' : is_joined,
			'is_master' : is_master,
			'can_install' : not can_uninstall and (is_joined or not self.master_packages),
			'can_uninstall' : can_uninstall,
		}

	@classmethod
	def find(cls, id):
		for application in cls.all():
			if application.id == id:
				return application

	def uninstall(self, module_instance):
		try:
			module_instance.package_manager.set_max_steps(200)
			module_instance.package_manager.uninstall(self.package_name)
			module_instance.package_manager.add_hundred_percent()
			module_instance._del_component(self.id)
			module_instance.package_manager.update()
			module_instance.package_manager.add_hundred_percent()
			status = 200
		except:
			status = 500
		return self._send_information('uninstall', status)

	def install(self, module_instance):
		try:
			is_master = module_instance.ucr.get('server/role') == 'domaincontroller_master'
			to_install = [self.package_name]
			if is_master and self.master_packages:
				to_install.extend(self.master_packages)
			max_steps = 100 + len(to_install) * 100
			MODULE.warn(str(max_steps))
			module_instance.package_manager.set_max_steps(max_steps)
			data = {
				'server' : 'appcenter.software-univention.de',
				'prefix' : '',
				'maintained' : True,
				'unmaintained' : False,
				'enabled' : True,
				'name' : self.id,
				'description' : self.description,
				'username' : '',
				'password' : '',
				'version' : 'current',
				}
			with module_instance.set_save_commit_load() as super_ucr:
				module_instance._put_component(data, super_ucr)
			module_instance.package_manager.update()
			module_instance.package_manager.add_hundred_percent()
			for package in to_install:
				module_instance.package_manager.install(package)
				module_instance.package_manager.add_hundred_percent()
			status = 200
		except Exception as e:
			MODULE.warn(str(e))
			status = 500
		return self._send_information('install', status)

	def _send_information(self, action, status):
		try:
			url = 'https://appcenter.software-univention.de/index.py?uuid=%(uuid)s&app=%(app)s&action=%(action)s&status=%(status)s'
			url = 'http://www.univention.de/index.py?uuid=%(uuid)s&app=%(app)s&action=%(action)s&status=%(status)s'
			url = url % {'uuid' : LICENCE.uuid, 'app' : self.id, 'action' : action, 'status' : status}
			request = urllib2.Request(url, headers={'User-agent' : 'UMC/AppCenter'})
			#urllib2.urlopen(request)
			return url
		except Exception as e:
			MODULE.warn(str(e))
			raise

