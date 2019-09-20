# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Daemon
#  cloud connection to openstack instances
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
"""UVMM cloud openstack handler"""

from __future__ import absolute_import
from libcloud.common.types import LibcloudError, MalformedResponseError, ProviderError, InvalidCredsError
from libcloud.compute.types import Provider, NodeState
from libcloud.compute.providers import get_driver

import time
import logging
import threading
import fnmatch
import re
import errno
import ssl

from .node import PersistentCached
from .cloudconnection import CloudConnection, CloudConnectionError
from .protocol import Cloud_Data_Instance, Cloud_Data_Location, Cloud_Data_Secgroup, Cloud_Data_Secgroup_Rule, Cloud_Data_Size, Cloud_Data_Network
import univention.config_registry as ucr

configRegistry = ucr.ConfigRegistry()
configRegistry.load()

logger = logging.getLogger('uvmmd.openstackconnection')

# Mapping of ldap attribute to libcloud parameter name
OPENSTACK_CONNECTION_ATTRIBUTES = {
	"username": "key",
	"password": "secret",
	"auth_url": "ex_force_auth_url",
	"base_url": "ex_force_base_url",
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


LIBCLOUD_UVMM_STATE_MAPPING = {
	NodeState.RUNNING: "RUNNING",
	NodeState.REBOOTING: "PENDING",
	NodeState.TERMINATED: "NOSTATE",
	NodeState.PENDING: "PENDING",
	NodeState.UNKNOWN: "NOSTATE",
	NodeState.STOPPED: "SHUTOFF",
	NodeState.SUSPENDED: "SUSPENDED",
	NodeState.ERROR: "CRASHED",
	NodeState.PAUSED: "PAUSED",
	NodeState.UNKNOWN: "NOSTATE"
}


class OpenStackCloudConnectionError(CloudConnectionError):
	pass


class OpenStackCloudConnection(CloudConnection, PersistentCached):

	def __init__(self, cloud, cache_dir):
		self._check_connection_attributes(cloud)
		super(OpenStackCloudConnection, self).__init__(cloud, cache_dir)

		self.publicdata.url = cloud["auth_url"]

		self._locations = []
		self._security_groups = []

	def _check_connection_attributes(self, cloud):
		if "username" not in cloud:
			raise OpenStackCloudConnectionError("username attribute is required")
		if "password" not in cloud:
			raise OpenStackCloudConnectionError("password attribute is required")
		if "auth_url" not in cloud:
			raise OpenStackCloudConnectionError("auth_url attribute is required")

	def _create_connection(self, cloud, testconnection=True):
		logger.debug("Creating connection to %s" % cloud["auth_url"])
		params = {}
		for param in cloud:
			if param in OPENSTACK_CONNECTION_ATTRIBUTES and cloud[param]:
				params[OPENSTACK_CONNECTION_ATTRIBUTES[param]] = cloud[param]
		os = get_driver(Provider.OPENSTACK)

		p = params.copy()
		p["secret"] = "******"
		logger.debug("params passed to driver: %s" % p)
		self.driver = os(**params)

		# try the driver before starting the update thread
		if testconnection:
			self._instances = self._exec_libcloud(lambda: self.driver.list_nodes())

		# Start thread for periodic updates
		self.updatethread = threading.Thread(group=None, target=self.run, name="%s-%s" % (self.publicdata.name, self.publicdata.url), args=(), kwargs={})
		self.updatethread.start()

	def update_expensive(self):
		logger.debug("Expensive update for %s: %s", self.publicdata.name, self.publicdata.url)
		self._images = self._exec_libcloud(lambda: self.driver.list_images())
		self._sizes = self._exec_libcloud(lambda: self.driver.list_sizes())
		self._locations = self._exec_libcloud(lambda: self.driver.list_locations())
		self._keypairs = self._exec_libcloud(lambda: self.driver.list_key_pairs())
		self._security_groups = self._exec_libcloud(lambda: self.driver.ex_list_security_groups())
		self._networks = self._exec_libcloud(lambda: self.driver.ex_list_networks())
		self._last_expensive_update = time.time()

	def list_instances(self, pattern="*"):
		regex = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
		instances = []
		for instance in self._instances:
			if regex.match(instance.name) is not None or regex.match(instance.id) is not None:
				i = Cloud_Data_Instance()
				i.u_connection_type = "OpenStack"
				i.name = instance.name
				i.extra = instance.extra
				i.id = instance.id
				i.image = instance.extra['imageId']
				i.key_name = instance.extra['key_name']
				i.private_ips = instance.private_ips
				i.public_ips = instance.public_ips
				i.size = instance.size
				i.state = LIBCLOUD_UVMM_STATE_MAPPING[instance.state]
				i.uuid = instance.uuid
				i.available = self.publicdata.available

				# information not directly provided by libcloud:
				# instance size-name. Openstack provides sizeinfo in extra['flavorId']
				size_temp = [s for s in self._sizes if s.id == instance.extra['flavorId']]
				i.u_size_name = '<Unknown>'
				if size_temp:
					i.u_size_name = size_temp[0].name

				image_name = [im for im in self._images if im.id == instance.extra['imageId']]
				i.u_image_name = '<Unknown>'
				if image_name:
					i.u_image_name = image_name[0].name

				# TODO: no libcloud support for querying instance security groups
				i.secgroups = '<query not supported>'

				instances.append(i)

		return instances

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

	def list_secgroups(self):
		secgroups = []
		for secgroup in self._security_groups:
			s = Cloud_Data_Secgroup()
			s.id = secgroup.id
			s.name = secgroup.name
			s.description = secgroup.description
			s.driver = secgroup.driver.name
			s.tenant_id = secgroup.tenant_id
			s.in_rules = []
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

				s.in_rules.append(r)
			s.extra = secgroup.extra

			secgroups.append(s)

		return secgroups

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
			i.vcpus = size.vcpus
			i.u_displayname = "%s" % i.name

			sizes.append(i)

		return sizes

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

	def list_subnets(self):
		return []

	def _boot_instance(self, instance):
		self._exec_libcloud(lambda: self.driver.ex_hard_reboot_node(instance))

	def _softreboot_instance(self, instance):
		self._exec_libcloud(lambda: self.driver.ex_soft_reboot_node(instance))

	def _reboot_instance(self, instance):
		self._exec_libcloud(lambda: self.driver.ex_hard_reboot_node(instance))

	def _pause_instance(self, instance):
		self._exec_libcloud(lambda: self.driver.ex_pause_node(instance))

	def _unpause_instance(self, instance):
		self._exec_libcloud(lambda: self.driver.ex_unpause_node(instance))

	def _shutdown_instance(self, instance):
		raise OpenStackCloudConnectionError("SHUTDOWN: Not yet implemented")

	def _shutoff_instance(self, instance):
		raise OpenStackCloudConnectionError("SHUTOFF: Not yet implemented")

	def _suspend_instance(self, instance):
		self._exec_libcloud(lambda: self.driver.ex_suspend_node(instance))

	def _resume_instance(self, instance):
		self._exec_libcloud(lambda: self.driver.ex_resume_node(instance))

	def instance_state(self, instance_id, state):
		# instance is a libcloud.Node object
		instance = self._get_instance_by_id(instance_id)

		OS_TRANSITION = {
			# (NodeState.TERMINATED, "*"): None, cannot do anything with terminated instances
			(NodeState.RUNNING, "RUN"): None,
			(NodeState.REBOOTING, "RUN"): None,
			(NodeState.PENDING, "RUN"): None,
			(NodeState.UNKNOWN, "RUN"): self._boot_instance,
			(NodeState.STOPPED, "RUN"): self._boot_instance,
			(NodeState.SUSPENDED, "RUN"): self._resume_instance,
			(NodeState.PAUSED, "RUN"): self._unpause_instance,
			(NodeState.RUNNING, "SOFTRESTART"): self._softreboot_instance,
			(NodeState.RUNNING, "RESTART"): self._reboot_instance,
			(NodeState.REBOOTING, "RESTART"): None,
			(NodeState.PENDING, "RESTART"): None,
			(NodeState.UNKNOWN, "RESTART"): self._reboot_instance,
			(NodeState.PAUSED, "RESTART"): self._reboot_instance,
			(NodeState.STOPPED, "RESTART"): self._reboot_instance,
			(NodeState.RUNNING, "PAUSE"): self._pause_instance,
			(NodeState.RUNNING, "SHUTDOWN"): self._shutdown_instance,
			(NodeState.RUNNING, "SHUTOFF"): self._shutoff_instance,
			(NodeState.REBOOTING, "SHUTOFF"): self._shutoff_instance,
			(NodeState.PENDING, "SHUTOFF"): self._shutoff_instance,
			(NodeState.UNKNOWN, "SHUTOFF"): self._shutoff_instance,
			(NodeState.PAUSED, "SHUTOFF"): self._shutoff_instance,
			(NodeState.RUNNING, "SUSPEND"): self._suspend_instance,
		}
		logger.debug("STATE: connection: %s instance %s (id:%s), oldstate: %s (%s), requested: %s", self.publicdata.name, instance.name, instance.id, instance.state, instance.state, state)
		try:
			transition = OS_TRANSITION[(instance.state, state)]
			if transition:
				transition(instance)
			else:
				logger.debug("NOP state transition: %s -> %s", instance.state, state)
		except KeyError:
			raise OpenStackCloudConnectionError("Unsupported State transition (%s -> %s) requested" % (instance.state, state))
		except Exception as ex:
			raise OpenStackCloudConnectionError("Error trying to %s instance %s (id:%s): %s" % (state, instance.name, instance_id, ex))
		logger.debug("STATE: done")
		self.set_frequency_fast_update()

	def instance_terminate(self, instance_id):
		# instance is a libcloud.Node object
		instance = self._get_instance_by_id(instance_id)
		name = instance.name
		try:
			self._exec_libcloud(lambda: self.driver.destroy_node(instance))
			# Update instance information
			self.set_frequency_fast_update()
		except Exception as ex:  # Unfortunately, libcloud only throws "Exception"
			raise OpenStackCloudConnectionError("Error while destroying instance %s (id:%s): %s" % (name, instance_id, ex))
		logger.info("Destroyed instance %s (id:%s), using connection %s", name, instance_id, self.publicdata.name)

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

			secgroups = [s for s in self._security_groups if str(s.id) in args["security_group_ids"]]
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
			self._exec_libcloud(lambda: self.driver.create_node(**kwargs))
			self.set_frequency_fast_update()
		except Exception as ex:
			raise OpenStackCloudConnectionError("Instance could not be created: %s" % ex)

	# Execute lambda function
	def _exec_libcloud(self, func):
		try:
			return func()
		except InvalidCredsError as ex:
			self.logerror(logger, "Invalid credentials provided for connection %s: %s" % (self.publicdata.name, self.publicdata.url))
			raise
		except MalformedResponseError as ex:
			self.logerror(logger, "Malformed response from connection, correct endpoint specified? %s: %s; %s" % (self.publicdata.name, self.publicdata.url, str(ex)))
			raise
		except ProviderError as ex:
			self.logerror(logger, "Connection %s: %s: httpcode: %s, %s" % (self.publicdata.name, self.publicdata.url, ex.http_code, ex))
			raise
		except LibcloudError as ex:
			self.logerror(logger, "Connection %s: %s: %s" % (self.publicdata.name, self.publicdata.url, ex))
			raise
		except ssl.SSLError as ex:
			self.logerror(logger, "Error with SSL connection %s: %s: %s" % (self.publicdata.name, self.publicdata.url, ex))
			raise
		except Exception as ex:
			if hasattr(ex, 'errno'):
				if ex.errno == errno.ECONNREFUSED:
					self.logerror(logger, "Connection %s: %s refused (ECONNREFUSED)" % (self.publicdata.name, self.publicdata.url))
				elif ex.errno == errno.EHOSTUNREACH:
					self.logerror(logger, "Connection %s: %s no route to host (EHOSTUNREACH)" % (self.publicdata.name, self.publicdata.url))

				else:
					self.logerror(logger, "Unknown exception %s with unknown errno %s: %s" % (self.publicdata.name, ex.errno, self.publicdata.url))
			else:
				self.logerror(logger, "Unknown exception  %s: %s" % (self.publicdata.name, self.publicdata.url))
			raise


if __name__ == '__main__':
	import doctest
	doctest.testmod()
