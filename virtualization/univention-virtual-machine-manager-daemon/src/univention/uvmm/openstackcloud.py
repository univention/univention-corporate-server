# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Daemon
#  cloud connection to openstack instances
#
# Copyright 2014 Univention GmbH
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
"""UVMM cloud openstack handler"""

from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
import libcloud.security
libcloud.security.VERIFY_SSL_CERT = False

import time
import logging
import threading
import fnmatch
import re

from helpers import CloudConnection, TranslatableException
from protocol import Cloud_Data_Connection, Cloud_Data_Instance, Cloud_Data_Image, Cloud_Data_Size, Cloud_Data_Region, Cloud_Data_Keypair
import univention.config_registry as ucr

configRegistry = ucr.ConfigRegistry()
configRegistry.load()

logger = logging.getLogger('uvmmd.openstackconnection')

# Mapping of ldap attribute to libcloud parameter name
OPENSTACK_ATTRIBUTES = {
		"username": "key",
		"password": "secret",
		"url": "ex_force_auth_url",
		"auth_version": "ex_force_auth_version",
		"service_type": "ex_force_service_type",
		"service_name": "ex_force_service_name",
		"tenant": "ex_tenant_name",
		"service_region": "ex_force_service_region",
		"auth_token": "ex_force_auth_token",
		"base_url": "ex_force_base_url",
		}


class OpenStackCloudConnectionError(TranslatableException):
	pass


class OpenStackCloudConnection(CloudConnection):
	def __init__(self, cloud):
		super(OpenStackCloudConnection, self).__init__(cloud)
		self._check_connection_attributes(cloud)

		self._instances = []
		self.current_frequency = 10000
		self.timerEvent = threading.Event()

		self.publicdata = Cloud_Data_Connection()
		self.publicdata.name = cloud["name"]
		self.publicdata.url = cloud["url"]

		self._create_connection(cloud)
		logger.debug("new openstack connection")

		# Start thread for periodic updates
		self.updatethread = threading.Thread(group=None, target=self.run, name="%s-%s" % (self.publicdata.name, self.publicdata.url), args=(), kwargs={})
		self.updatethread.start()

	def _check_connection_attributes(self, cloud):
		if "username" not in cloud:
			raise OpenStackCloudConnectionError("username attribute is required")
		if "password" not in cloud:
			raise OpenStackCloudConnectionError("password attribute is required")
		if "url" not in cloud:
			raise OpenStackCloudConnectionError("url attribute is required")

	def _create_connection(self, cloud):
		logger.debug("Creating connection to %s" % cloud["url"])
		params = {}
		for param in cloud:
			if param in OPENSTACK_ATTRIBUTES:
				params[OPENSTACK_ATTRIBUTES[param]] = cloud[param]
		os = get_driver(Provider.OPENSTACK)

		logger.debug("params passed to driver: %s" % params)
		self.driver = os(**params)

	def unregister(self, wait=False):
		# Wakeup thread, wait for termination
		if self.updatethread is not None:
			thread = self.updatethread
			self.updatethread = None
			self.timerEvent.set()
			while wait:
				thread.join(1.0)
				if thread.isAlive():
					logger.warning("Thread still alive: %s" % self.publicdata.name)
				else:
					wait = False

		super(OpenStackCloudConnection, self).unregister()

	def run(self):
		logger.info("Starting update thread for %s: %s" % (self.publicdata.name, self.publicdata.url))
		while self.updatethread is not None:
			try:
				self.update()
			except Exception:
				# Catch all exceptions and do not crash the thread
				logger.error("Exception in thread %s: %s" % (self.publicdata.name, self.publicdata.url), exc_info=True)
			self.timerEvent.clear()
			self.timerEvent.wait(self.current_frequency / 1000.0)

		logger.info("Stopping update thread for %s: %s" % (self.publicdata.name, self.publicdata.url))

	def update(self):
		logger.debug("Updating information for %s: %s" % (self.publicdata.name, self.publicdata.url))
		try:
			self._last_update_try = time.time()
			self._instances = self.driver.list_nodes()
			self._images = self.driver.list_images()
			self._sizes = self.driver.list_sizes()
			self._regions = self.driver.list_locations()
			self._keypairs = self.driver.list_key_pairs()
			self.publicdata.last_update = time.time()
			logger.debug("Updating took %s seconds for %s: %s" % (self.publicdata.last_update - self._last_update_try, self.publicdata.name, self.publicdata.url))
		except Exception:
			logger.error("Exception in update in thread %s: %s" % (self.publicdata.name, self.publicdata.url), exc_info=True)
		self._last_update_try = self.publicdata.last_update

	def set_frequency(self, hz):
		self.current_frequency = hz
		self.timerEvent.set()

	def list_instances(self, pattern="*"):
		regex = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
		instances = []
		for instance in self._instances:
			if regex.match(instance.name) is not None:
				i = Cloud_Data_Instance()
				i.name = instance.name
				i.extra = instance.extra
				i.id = instance.id
				i.image = instance.image
				i.private_ips = instance.private_ips
				i.public_ips = instance.public_ips
				i.size = instance.size
				i.state = instance.state
				i.uuid = instance.uuid
				i.available = self.publicdata.last_update == self._last_update_try

				instances.append(i)

		return instances

	def list_images(self, pattern="*"):
		regex = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
		images = []
		for image in self._images:
			if regex.match(image.name) is not None:
				i = Cloud_Data_Image()
				i.name = image.name
				i.extra = image.extra
				i.id = image.id
				i.driver = image.driver.name
				i.uuid = image.uuid

				images.append(i)

		return images

	def list_sizes(self):
		sizes = []
		for size in self._sizes:
			i = Cloud_Data_Size()
			i.name = size.name
			i.extra = size.extra
			i.id = size.id
			i.driver = size.driver.name
			i.uuid = size.uuid
			i.ram = size.ram
			i.disk = size.disk
			i.bandwidth = size.bandwidth
			i.price = size.price

			sizes.append(i)

		return sizes

	def list_regions(self):
		regions = []
		for region in self._regions:
			i = Cloud_Data_Region()
			i.name = region.name
			i.id = region.id
			i.driver = region.driver.name
			i.country = region.country

			regions.append(i)

		return regions

	def list_keypairs(self):
		keypairs = []
		for keypair in self._keypairs:
			i = Cloud_Data_Keypair()
			i.name = keypair.name
			i.driver = keypair.driver.name
			i.fingerprint = keypair.fingerprint
			i.public_key = keypair.public_key
			i.private_key = keypair.private_key
			i.extra = keypair.extra

			keypairs.append(i)

		return keypairs


if __name__ == '__main__':
	import doctest
	doctest.testmod()
