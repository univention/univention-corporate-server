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

from libcloud.common.types import LibcloudError, MalformedResponseError, ProviderError, InvalidCredsError
from libcloud.compute.types import Provider, NodeState
from libcloud.compute.providers import get_driver
import libcloud.security
libcloud.security.VERIFY_SSL_CERT = False

import time
import logging
import threading
import fnmatch
import re
import errno
import os
import stat
import hashlib
try:
	import cPickle as pickle
except ImportError:
	import pickle

from node import PersistentCached
from helpers import CloudConnection, TranslatableException, ms, uri_encode
from protocol import Cloud_Data_Connection, Cloud_Data_Instance, Cloud_Data_Image, Cloud_Data_Size, Cloud_Data_Location, Cloud_Data_Keypair, Cloud_Data_Network, Cloud_Data_Secgroup, Cloud_Data_Secgroup_Rule
import univention.config_registry as ucr

configRegistry = ucr.ConfigRegistry()
configRegistry.load()

logger = logging.getLogger('uvmmd.openstackconnection')

# Mapping of ldap attribute to libcloud parameter name
OPENSTACK_CONNECTION_ATTRIBUTES = {
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

OPENSTACK_CREATE_ATTRIBUTES = {
		"name": "name",
		"keyname": "ex_keyname",
		"size_id": "size",
		"image_id": "image",
		"location_id": "location",
		"userdata": "ex_userdata",
		"security_group_ids": "ex_security_groups",
		"metadata": "ex_metadata",
		"network_ids": "networks",
		"disk_config": "ex_disk_config",
		"admin_pass": "ex_admin_pass",
		"availability_zone": "ex_availability_zone",
	}


"""
LIBCLOUD Standard states for a node
:cvar RUNNING: Node is running.
:cvar REBOOTING: Node is rebooting.
:cvar TERMINATED: Node is terminated. This node can't be started later on.
:cvar STOPPED: Node is stopped. This node can be started later on.
:cvar PENDING: Node is pending.
:cvar UNKNOWN: Node state is unknown.
"""
LIBCLOUD_UVMM_STATE_MAPPING = {
		NodeState.RUNNING: "RUNNING",
		NodeState.REBOOTING: "PENDING",
		NodeState.TERMINATED: "NOSTATE",
		NodeState.PENDING: "PENDING",
		NodeState.UNKNOWN: "NOSTATE",
		NodeState.STOPPED: "SHUTDOWN"
		}


class OpenStackCloudConnectionError(TranslatableException):
	pass


class OpenStackCloudConnection(CloudConnection, PersistentCached):
	def __init__(self, cloud, cache_dir):
		super(OpenStackCloudConnection, self).__init__(cloud)
		self._check_connection_attributes(cloud)
		self._cache_dir = cache_dir
		self._cache_hash = ""

		self._instances = []
		self._images = []
		self._sizes = []
		self._locations = []
		self._keypairs = []
		self._security_groups = []
		self._networks = []

		self.config_default_frequency = self.DEFAULT_FREQUENCY
		self.current_frequency = self.DEFAULT_FREQUENCY
		self.timerEvent = threading.Event()

		self.publicdata = Cloud_Data_Connection()
		self.publicdata.name = cloud["name"]
		self.publicdata.cloudtype = cloud["type"]
		self.publicdata.url = cloud["url"]
		self.publicdata.last_update = -1
		self.publicdata.last_update_try = -1
		self.publicdata.available = False
		self._last_expensive_update = -1000000

		self.cache_restore()
		self._create_connection(cloud)

		# Start thread for periodic updates
		self.updatethread = threading.Thread(group=None, target=self.run, name="%s-%s" % (self.publicdata.name, self.publicdata.url), args=(), kwargs={})
		self.updatethread.start()

	# Caching
	def cache_file_name(self, suffix=".pic"):
		return os.path.join(self._cache_dir, uri_encode(self.publicdata.name) + suffix)

	def cache_save(self):
		instances = self.list_instances()
		new_name = self.cache_file_name(suffix=".new")
		old_name = self.cache_file_name()

		data = pickle.dumps(instances)
		data_hash = hashlib.md5(data).hexdigest()
		if data_hash == self._cache_hash:  # No change in data, no need to write changes
			return
		self._cache_hash = data_hash

		try:
			fd = os.open(new_name, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, stat.S_IREAD | stat.S_IWRITE)
			os.write(fd, data)
		finally:
			os.close(fd)
		os.rename(new_name, old_name)

	def cache_restore(self):
		# check if there is a cache file
		cache_file_name = self.cache_file_name()
		if os.path.isfile(cache_file_name):
			cache_file = open(cache_file_name, 'r')
			try:
				data = pickle.Unpickler(cache_file)
				if data:
					self._instances = data.load()
					for instance in self._instances:
						logger.debug("loaded cached instance %s" % instance.name)
						instance.available = False
						instance.state = 4  # state UNKNOWN
			finally:
				cache_file.close()

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
			if param in OPENSTACK_CONNECTION_ATTRIBUTES:
				params[OPENSTACK_CONNECTION_ATTRIBUTES[param]] = cloud[param]
		os = get_driver(Provider.OPENSTACK)

		logger.debug("params passed to driver: %s" % params)
		self.driver = os(**params)

	def _get_instance_by_id(self, instance_id):
		"""
		Find and return the Node object which has the id <instance_id>
		Raise OpenStackCloudConnectionError if <instance_id> can not be found
		"""
		instance = [x for x in self._instances if x.id == instance_id]
		if not instance:
			raise OpenStackCloudConnectionError("No instance with id:%s for connection %s" % (instance_id, self.publicdata.name))
		# instance.id is unique for a connection
		return instance[0]

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
		try:
			logger.debug("Updating information for %s: %s" % (self.publicdata.name, self.publicdata.url))
			# double update freqency in case an update error occurs
			# this is reset if no exception occurs at the end of this try: statement
			self.current_frequency = min(self.current_frequency * 2, self.MAX_UPDATE_INTERVAL)

			self.publicdata.last_update_try = time.time()
			self._instances = self.driver.list_nodes()

			# Expensive update if
			# last expensive update was more than self.EXPENSIVE_UPDATE_INTERVAL ago
			if (self.publicdata.last_update - self._last_expensive_update) * 1000 > self.EXPENSIVE_UPDATE_INTERVAL:
				self.update_expensive()

			self.publicdata.last_update = time.time()
			self.publicdata.last_update_try = self.publicdata.last_update
			self.cache_save()
			self.current_frequency = self.config_default_frequency
			logger.debug("Updating took %s seconds for %s" % (self.publicdata.last_update - self.publicdata.last_update_try, self.publicdata.name))
		except InvalidCredsError as e:
			logger.error("Invalid credentials provided for connection %s: %s" % (self.publicdata.name, self.publicdata.url))
		except MalformedResponseError as e:
			logger.error("Malformed response from connection, correct endpoint specified? %s: %s; %s" % (self.publicdata.name, self.publicdata.url, str(e)))
		except ProviderError as e:
			logger.error("Connection %s: %s: httpcode: %s, %s" % (self.publicdata.name, self.publicdata.url, e.http_code, e))
		except LibcloudError as e:
			logger.error("Connection %s: %s: %s" % (self.publicdata.name, self.publicdata.url, e))
		except Exception as e:
			if hasattr(e, 'errno'):
				if e.errno == errno.ECONNREFUSED:
					logger.error("Connection %s: %s refused (ECONNREFUSED)" % (self.publicdata.name, self.publicdata.url))
				else:
					logger.error("Unknown exception in update in thread %s with unknown errno %s: %s" % (self.publicdata.name, e.errno, self.publicdata.url), exc_info=True)
			else:
				logger.error("Unknown exception in update in thread %s: %s" % (self.publicdata.name, self.publicdata.url), exc_info=True)

		logger.debug("Next update for %s: %s" % (self.publicdata.name, ms(self.current_frequency)))
		self.publicdata.available = self.publicdata.last_update == self.publicdata.last_update_try

	def update_expensive(self):
		logger.debug("Expensive update for %s: %s" % (self.publicdata.name, self.publicdata.url))
		self._images = self.driver.list_images()
		self._sizes = self.driver.list_sizes()
		self._locations = self.driver.list_locations()
		self._keypairs = self.driver.list_key_pairs()
		self._security_groups = self.driver.ex_list_security_groups()
		self._networks = self.driver.ex_list_networks()
		self._last_expensive_update = time.time()

	def set_frequency(self, freq):
		self.config_default_frequency = freq
		self.current_frequency = freq
		self.timerEvent.set()

	def list_instances(self, pattern="*"):
		regex = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
		instances = []
		for instance in self._instances:
			if regex.match(instance.name) is not None or regex.match(instance.id) is not None:
				i = Cloud_Data_Instance()
				i.name = instance.name
				i.extra = instance.extra
				i.id = instance.id
				i.image = instance.extra['imageId']
				i.private_ips = instance.private_ips
				i.public_ips = instance.public_ips
				i.size = instance.size
				i.state = LIBCLOUD_UVMM_STATE_MAPPING[instance.state]
				i.uuid = instance.uuid
				i.available = self.publicdata.available

				# information not directly provided by libcloud:
				# instance size-name. Openstack provides sizeinfo in extra['flavorId']
				size_temp = [s for s in self._sizes if s.id == instance.extra['flavorId']]
				if size_temp:
					i.u_size_name = size_temp[0].name

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

	def list_locations(self):
		locations = []
		for location in self._locations:
			l = Cloud_Data_Location()
			l.name = location.name
			l.id = location.id
			l.driver = location.driver.name
			l.country = location.country

			locations.append(l)

		return locations

	def list_keypairs(self):
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

	def list_networks(self):
		networks = []
		for network in self._networks:
			s = Cloud_Data_Network()
			s.id = network.id
			s.name = network.name
			s.cidr = network.cidr
			s.driver = network.driver.name
			s.extra = network.extra

			networks.append(s)

		return networks

	def list_secgroups(self):
		secgroups = []
		for secgroup in self._security_groups:
			s = Cloud_Data_Secgroup()
			s.id = secgroup.id
			s.name = secgroup.name
			s.description = secgroup.description
			s.driver = secgroup.driver.name
			s.tenant_id = secgroup.tenant_id
			s.rules = []
			for rule in secgroup.rules:
				r = Cloud_Data_Secgroup_Rule()
				r.id = rule.id
				r.parent_group_id = rule.parent_group_id
				r.ip_protocol = rule.ip_protocol
				r.from_port = rule.from_port
				r.to_port = rule.to_port
				r.driver = rule.driver.name
				r.ip_range = rule.ip_range
				r.group = rule.group
				r.tenant_id = rule.tenant_id
				r.extra = rule.extra

				s.rules.append(r)
			s.extra = secgroup.extra

			secgroups.append(s)

		return secgroups

	def _boot_instance(self, instance):
		self.driver.ex_hard_reboot_node(instance)

	def _softreboot_instance(self, instance):
		self.driver.ex_soft_reboot_node(instance)

	def _reboot_instance(self, instance):
		self.driver.ex_hard_reboot_node(instance)

	def _pause_instance(self, instance):
		raise OpenStackCloudConnectionError("PAUSE: Not yet implemented")

	def _shutdown_instance(self, instance):
		raise OpenStackCloudConnectionError("SHUTDOWN: Not yet implemented")

	def _shutoff_instance(self, instance):
		raise OpenStackCloudConnectionError("SHUTOFF: Not yet implemented")

	def _suspend_instance(self, instance):
		raise OpenStackCloudConnectionError("SUSPEND: Not yet implemented")

	def instance_state(self, instance_id, state):
		# instance is a libcloud.Node object
		instance = self._get_instance_by_id(instance_id)

		OS_TRANSITION = {
				# (NodeState.TERMINATED, "*"): None, cannot do anything with terminated instances
				(NodeState.RUNNING,    "RUN"): None,
				(NodeState.REBOOTING,  "RUN"): None,
				(NodeState.PENDING,    "RUN"): None,
				(NodeState.UNKNOWN,    "RUN"): self._boot_instance,
				(NodeState.STOPPED,    "RUN"): self._boot_instance,
				(NodeState.RUNNING,    "SOFTRESTART"): self._softreboot_instance,
				(NodeState.RUNNING,    "RESTART"): self._reboot_instance,
				(NodeState.REBOOTING,  "RESTART"): None,
				(NodeState.PENDING,    "RESTART"): None,
				(NodeState.UNKNOWN,    "RESTART"): self._reboot_instance,
				(NodeState.STOPPED,    "RESTART"): self._reboot_instance,
				(NodeState.RUNNING,    "PAUSE"): self._pause_instance,
				(NodeState.RUNNING,    "SHUTDOWN"): self._shutdown_instance,
				(NodeState.RUNNING,    "SHUTOFF"): self._shutoff_instance,
				(NodeState.REBOOTING,  "SHUTOFF"): self._shutoff_instance,
				(NodeState.PENDING,    "SHUTOFF"): self._shutoff_instance,
				(NodeState.UNKNOWN,    "SHUTOFF"): self._shutoff_instance,
				(NodeState.RUNNING,    "SUSPEND"): self._suspend_instance
				}
		logger.debug("STATE: connection: %s instance %s (id:%s), oldstate: %s (%s), requested: %s" % (self.publicdata.name, instance.name, instance.id, instance.state, instance.state, state))
		try:
			transition = OS_TRANSITION[(instance.state, state)]
			if transition:
				transition(instance)
			else:
				logger.debug("NOP state transition: %s -> %s" % (instance.state, state))
		except KeyError:
			raise OpenStackCloudConnectionError("Unsupported State transition (%s -> %s) requested" % (instance.state, state))
		except Exception, e:
			raise OpenStackCloudConnectionError("Error trying to %s instance %s (id:%s): %s" % (state, instance.name, instance_id, e))
		logger.debug("STATE: done")
		self.timerEvent.set()

	def instance_terminate(self, instance_id):
		# instance is a libcloud.Node object
		instance = self._get_instance_by_id(instance_id)
		name = instance.name
		try:
			self.driver.destroy_node(instance)
			# Update instance information
			self.timerEvent.set()
		except Exception, e:  # Unfortunately, libcloud only throws "Exception"
			raise OpenStackCloudConnectionError("Error while destroying instance %s (id:%s): %s" % (name, instance_id, e))
		logger.info("Destroyed instance %s (id:%s), using connection %s" % (name, instance_id, self.publicdata.name))

	def instance_create(self, args):
		# Check args
		kwargs = {}
		if "name" not in args:
			raise OpenStackCloudConnectionError("<name> attribute required for new instance")
		else:
			kwargs[OPENSTACK_CREATE_ATTRIBUTES["name"]] = args["name"]

		if "keyname" not in args:
			raise OpenStackCloudConnectionError("<keyname> attribute required for new instance")
		else:
			key = [kp for kp in self._keypairs if kp.name == args["keyname"]]
			if not key:
				raise OpenStackCloudConnectionError("No keypair with name %s found." % args["keyname"])

			kwargs[OPENSTACK_CREATE_ATTRIBUTES["keyname"]] = args["keyname"]

		if "size_id" not in args:
			raise OpenStackCloudConnectionError("<size_id> attribute required for new instance")
		else:
			size = [s for s in self._sizes if s.id == args["size_id"]]
			if not size:
				raise OpenStackCloudConnectionError("No size with id %s found." % args["size_id"])

			kwargs[OPENSTACK_CREATE_ATTRIBUTES["size_id"]] = size[0]

		if "image_id" not in args:
			raise OpenStackCloudConnectionError("<image_id> attribute required for new instance")
		else:
			image = [i for i in self._images if i.id == args["image_id"]]
			if not image:
				raise OpenStackCloudConnectionError("No image with id %s found." % args["image_id"])

			kwargs[OPENSTACK_CREATE_ATTRIBUTES["image_id"]] = image[0]

		if "location_id" in args:
			if not isinstance(args["location_id"], str):
				raise OpenStackCloudConnectionError("<location_id> attribute must be a string")
			kwargs[OPENSTACK_CREATE_ATTRIBUTES["location_id"]] = args["location_id"]

		if "userdata" in args:
			if not (isinstance(args["userdata"], str) or isinstance(args["userdata"], unicode)):
				raise OpenStackCloudConnectionError("<userdata> attribute must be a string")
			kwargs[OPENSTACK_CREATE_ATTRIBUTES["userdata"]] = args["userdata"]

		if "metadata" in args:
			if not isinstance(args["metadata"], dict):
				logger.debug("metadata type: %s" % args["metadata"].__class__)
				raise OpenStackCloudConnectionError("<metadata> attribute must be a dict")
			kwargs[OPENSTACK_CREATE_ATTRIBUTES["metadata"]] = args["metadata"]

		if "availability_zone" in args:
			if not isinstance(args["availability_zone"], str):
				raise OpenStackCloudConnectionError("<availability_zone> attribute must be a string")
			kwargs[OPENSTACK_CREATE_ATTRIBUTES["availability_zone"]] = args["availability_zone"]

		if "disk_config" in args:
			if args["disk_config"] not in ["AUTO", "MANUAL"]:
				raise OpenStackCloudConnectionError("<disk_config> attribute must be AUTO or MANUAL")
			kwargs[OPENSTACK_CREATE_ATTRIBUTES["disk_config"]] = args["disk_config"]

		if "admin_pass" in args:
			if not isinstance(args["admin_pass"], str):
				raise OpenStackCloudConnectionError("<admin_pass> attribute must be a string")
			kwargs[OPENSTACK_CREATE_ATTRIBUTES["admin_pass"]] = args["admin_pass"]

		if "security_group_ids" in args:
			if not (isinstance(args["security_group_ids"], list)):
				raise OpenStackCloudConnectionError("<security_group_ids> attribute must be a list")

			secgroups = [s for s in self._security_groups if s.id in args["security_group_ids"]]
			if not secgroups:
				raise OpenStackCloudConnectionError("No security group with id %s found." % args["security_group_ids"])

			kwargs[OPENSTACK_CREATE_ATTRIBUTES["security_group_ids"]] = secgroups

		if "network_ids" in args:
			if not (isinstance(args["network_ids"], list)):
				raise OpenStackCloudConnectionError("<network_ids> attribute must be a list")

			networks = [n for n in self._networks if n.id in args["network_ids"]]
			if not networks:
				raise OpenStackCloudConnectionError("No network with id %s found." % args["network_ids"])

			kwargs[OPENSTACK_CREATE_ATTRIBUTES["network_ids"]] = networks

		# libcloud call
		try:
			logger.debug("CREATE INSTANCE. ARGS: %s" % kwargs)
			self.driver.create_node(**kwargs)
		except Exception, e:
			raise OpenStackCloudConnectionError("Instance could not be created: %s" % e)


if __name__ == '__main__':
	import doctest
	doctest.testmod()
