# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Daemon
#  python module
#
# Copyright 2014-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

from __future__ import absolute_import
import logging
import stat
import hashlib
import os
import threading
import time
import re
import fnmatch
import pickle

from .protocol import Cloud_Data_Connection, Cloud_Data_Image, Cloud_Data_Keypair
from .helpers import TranslatableException, ms, uri_encode
try:
	from typing import Any, Callable, Dict, List, Optional  # noqa
	from .protocol import Cloud_Data_Instance, Cloud_Data_Size, Cloud_Data_Network, Cloud_Data_Subnet  # noqa
	from libcloud.compute.base import NodeDriver  # noqa
except ImportError:
	pass

logger = logging.getLogger('uvmmd.cloudconnection')


class CloudConnectionError(TranslatableException):

	"""Error while handling cloud connection."""


class CloudConnection(object):

	def __init__(self, cloud, cache_dir):
		# type: (Dict[str, Any], str) -> None
		self.type = cloud["type"]
		self.DEFAULT_FREQUENCY = 15 * 1000  # ms
		self.MAX_UPDATE_INTERVAL = 5 * 60 * 1000  # ms
		self.EXPENSIVE_UPDATE_INTERVAL = 5 * 60 * 1000  # ms
		self.FAST_UPDATE_FREQUENCY = 2 * 1000  # ms

		self._cache_dir = cache_dir
		self._cache_hash = ""

		self.driver = None  # type: NodeDriver
		self.updatethread = None
		self.config_default_frequency = self.DEFAULT_FREQUENCY
		self.current_frequency = self.DEFAULT_FREQUENCY
		self.fast_update_config_default_frequency = 0
		self.fast_update_time = 0.0
		self.timerEvent = threading.Event()

		self.publicdata = Cloud_Data_Connection()
		self.publicdata.dn = ""
		if 'dn' in cloud:
			self.publicdata.dn = cloud['dn']
		self.publicdata.name = cloud["name"]
		self.publicdata.cloudtype = cloud["type"]
		self.publicdata.last_update = -1
		self.publicdata.last_update_try = -1
		self.publicdata.available = False
		self.publicdata.last_error_message = ""
		self.publicdata.search_pattern = cloud['search_pattern']

		self._preselected_images = []  # type: List[str]
		if "preselected_images" in cloud and cloud["preselected_images"]:
			logger.debug("Preselected images: %s" % cloud["preselected_images"])
			self._preselected_images = cloud["preselected_images"]

		self.publicdata.ucs_images = cloud['ucs_images']

		self._last_expensive_update = -1000000

		self._instances = []  # type: List[Cloud_Data_Instance]
		self._keypairs = []  # type: List[Cloud_Data_Keypair]
		self._images = []  # type: List[Cloud_Data_Image]
		self._sizes = []  # type: List[Cloud_Data_Size]
		self._networks = []  # type: List[Cloud_Data_Network]
		self._subnets = []  # type: List[Cloud_Data_Subnet]

	def _create_connection(self, cloud, testconnection=True):
		# type: (Dict[str, Any], bool) -> None
		pass

	def connect(self, cloud, testconnection=True):
		# type: (Dict[str, Any], bool) -> None
		self.cache_restore()
		self._create_connection(cloud, testconnection)

	def unregister(self, wait=False):
		# type: (bool) -> None
		logger.debug("in unregister %s" % self.publicdata.name)
		"""
		Remove connection to this service
		"""
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
		logger.debug("Removed connection to %s" % self.publicdata.name)

	def set_frequency(self, freq):
		# type: (int) -> None
		self.config_default_frequency = freq
		self.current_frequency = freq
		self.timerEvent.set()

	def set_frequency_fast_update(self):
		# type: () -> None
		if self.fast_update_time == 0:
			self.fast_update_time = time.time()
			self.fast_update_config_default_frequency = self.config_default_frequency
			self.set_frequency(self.FAST_UPDATE_FREQUENCY)

	def run(self):
		# type: () -> None
		logger.info("Starting update thread for %s: %s", self.publicdata.name, self.publicdata.url)
		while self.updatethread is not None:
			try:
				self.update()
			except Exception:
				# Catch all exceptions and do not crash the thread
				logger.error("Exception in thread %s: %s", self.publicdata.name, self.publicdata.url, exc_info=True)
			self.timerEvent.clear()
			self.timerEvent.wait(self.current_frequency / 1000.0)

		logger.info("Stopping update thread for %s: %s", self.publicdata.name, self.publicdata.url)

	def update(self):
		# type: () -> None
		try:
			logger.debug("Updating information for %s: %s", self.publicdata.name, self.publicdata.url)
			# double update frequency in case an update error occurs
			# this is reset if no exception occurs at the end of this try: statement
			self.current_frequency = min(self.current_frequency * 2, self.MAX_UPDATE_INTERVAL)

			self.publicdata.last_update_try = time.time()
			self._instances = self._exec_libcloud(lambda: self.driver.list_nodes())

			# Fast update if
			# reset self.config_default_frequency if fast update was more than self.DEFAULT_FREQUENCY
			if self.fast_update_time > 0 and (self.publicdata.last_update_try - self.fast_update_time) * 1000 > self.DEFAULT_FREQUENCY:
				self.fast_update_time = 0
				self.config_default_frequency = self.fast_update_config_default_frequency

			# Expensive update if
			# last expensive update was more than self.EXPENSIVE_UPDATE_INTERVAL ago
			if (self.publicdata.last_update - self._last_expensive_update) * 1000 > self.EXPENSIVE_UPDATE_INTERVAL:
				self.update_expensive()

			self.publicdata.last_update = time.time()
			logger.debug("Updating took %s seconds for %s", self.publicdata.last_update - self.publicdata.last_update_try, self.publicdata.name)
			self.publicdata.last_update_try = self.publicdata.last_update
			self.cache_save()
			self.current_frequency = self.config_default_frequency
			self.publicdata.last_error_message = ""
		except Exception:
			logger.error("Exception in update() for connection %s; Endpoint: %s" % (self.publicdata.name, self.publicdata.url), exc_info=False)

		logger.debug("Next update for %s: %s", self.publicdata.name, ms(self.current_frequency))
		self.publicdata.available = self.publicdata.last_update == self.publicdata.last_update_try

	def update_expensive(self):
		# type: () -> None
		pass

	# Caching
	def cache_file_name(self, suffix=".pic"):
		# type: (str) -> str
		return os.path.join(self._cache_dir, uri_encode(self.publicdata.name) + suffix)

	def cache_save(self):
		# type: () -> None
		instances = self.list_instances()
		new_name = self.cache_file_name(suffix=".new")
		old_name = self.cache_file_name()

		data = pickle.dumps(instances)
		data_hash = hashlib.md5(data).hexdigest()
		if data_hash == self._cache_hash:  # No change in data, no need to write changes
			return
		self._cache_hash = data_hash

		fd = os.open(new_name, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, stat.S_IREAD | stat.S_IWRITE)
		try:
			os.write(fd, data)
		finally:
			os.close(fd)
		os.rename(new_name, old_name)

	def cache_restore(self):
		# type: () -> None
		# check if there is a cache file
		cache_file_name = self.cache_file_name()
		if os.path.isfile(cache_file_name):
			with open(cache_file_name, 'r') as cache_file:
				data = pickle.Unpickler(cache_file)
				if data:
					self._instances = data.load()
					for instance in self._instances:
						logger.debug("loaded cached instance %s" % instance.name)
						instance.available = False
						instance.state = 4  # state UNKNOWN

	def _get_instance_by_id(self, instance_id):
		"""
		Find and return the Node object which has the id <instance_id>
		Raise OpenStackCloudConnectionError if <instance_id> can not be found
		"""
		instance = [x for x in self._instances if x.id == instance_id]
		if not instance:
			raise CloudConnectionError("No instance with id:%s for connection %s" % (instance_id, self.publicdata.name))
		# instance.id is unique for a connection
		return instance[0]

	def list_keypairs(self):
		# type: () -> List[Cloud_Data_Keypair]
		keypairs = []
		for keypair in self._keypairs:
			k = Cloud_Data_Keypair()
			k.name = keypair.name
			k.driver = keypair.driver.name
			k.fingerprint = keypair.fingerprint
			k.public_key = keypair.public_key
			k.private_key = keypair.private_key
			k.extra = keypair.extra

			keypairs.append(k)

		return keypairs

	def to_cloud_data_image(self, image):
		# type: (Any) -> Cloud_Data_Image
		cloud_data_image = Cloud_Data_Image()
		cloud_data_image.name = image.name
		cloud_data_image.extra = image.extra
		cloud_data_image.id = image.id
		cloud_data_image.driver = image.driver.name
		cloud_data_image.uuid = image.uuid
		return cloud_data_image

	def list_images(self):
		# type: () -> List[Cloud_Data_Image]
		# Copied from ucs2cloud.list_images, but without ucs_images and without extra['owner_id'] and a different name attribute
		regex = None
		if self.publicdata.search_pattern:
			# Expand pattern with *
			regex = re.compile(fnmatch.translate('*%s*' % self.publicdata.search_pattern), re.IGNORECASE)
		images = []
		for image in self._images:
			include = False
			if self.publicdata.ucs_images:
				logger.debug("ucs image definition not implemented, use preselected images")
			if '%s' % image.id in self._preselected_images:
				include = True
			if regex:
				for attr in [image.name, image.id]:
					if attr and regex.match(attr):
						include = True
						break
			if include:
				images.append(self.to_cloud_data_image(image))
		return images

	def list_instances(self, pattern="*"):
		# type: (str) -> List[Any]
		raise NotImplementedError()

	def _exec_libcloud(self, func):
		# type: (Callable) -> Any
		raise NotImplementedError()

	def logerror(self, logger, msg):
		# type: (logging.Logger, str) -> None
		"""
		Log the error with the traceback.
		Set self.publicdata.last_error_message to the error message in order to
		give the frontend the possibility to show it to the user
		"""
		logger.error(msg, exc_info=True)
		self.publicdata.last_error_message = msg


if __name__ == '__main__':
	import doctest
	doctest.testmod()
