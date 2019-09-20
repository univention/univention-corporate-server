# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Daemon
#  cloud connection to EC2 instances
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
"""UVMM cloud ec2 handler"""

from __future__ import absolute_import
from libcloud.common.types import LibcloudError, MalformedResponseError, ProviderError, InvalidCredsError
from libcloud.compute.types import Provider, NodeState, KeyPairDoesNotExistError
from libcloud.compute.providers import get_driver
from libcloud.compute.drivers.ec2 import IdempotentParamError

import time
import logging
import threading
import fnmatch
import re
import errno
import ssl

from .node import PersistentCached
from .helpers import N_ as _
from .cloudconnection import CloudConnection, CloudConnectionError
from .protocol import Cloud_Data_Instance, Cloud_Data_Location, Cloud_Data_Secgroup, Cloud_Data_Size, Cloud_Data_Network, Cloud_Data_Subnet
import univention.config_registry as ucr

configRegistry = ucr.ConfigRegistry()
configRegistry.load()

logger = logging.getLogger('uvmmd.ec2connection')

# Mapping of ldap attribute to libcloud parameter name
EC2_CONNECTION_ATTRIBUTES = {
	"access_id": "key",
	"password": "secret",
	"secure": "secure",
	"host": "host",
	"port": "port",
	"region": "region",
}

EC2_CREATE_ATTRIBUTES = {
	"name": "name",
	"size_id": "size",
	"image_id": "image",
	"location": "location",
	"keyname": "ex_keyname",
	"userdata": "ex_userdata",
	"security_group_ids": {'group_name': "ex_security_groups", 'group_id': 'ex_security_group_ids'},
	"metadata": "ex_metadata",
	"min_instance_count": "ex_mincount",
	"max_instance_count": "ex_maxcount",
	"clienttoken": "ex_clienttoken",
	"blockdevicemappings": "ex_blockdevicemappings",
	"iamprofile": "ex_iamprofile",
	"ebs_optimized": "ex_ebs_optimized",
	"subnet_id": "ex_subnet"
}


LIBCLOUD_EC2_UVMM_STATE_MAPPING = {
	NodeState.RUNNING: "RUNNING",
	NodeState.PENDING: "PENDING",
	NodeState.TERMINATED: "TERMINATED",
	NodeState.UNKNOWN: "NOSTATE",
	NodeState.STOPPED: "SHUTOFF",
}


PROVIDER_MAPPING = {
	"EC2_US_EAST": "us-east-1",
	"EC2_EU_WEST": "eu-west-1",
	"EC2_US_WEST": "us-west-1",
	"EC2_US_WEST_OREGON": "us-west-2",
	"EC2_AP_SOUTHEAST": "ap-southeast-1",
	"EC2_AP_NORTHEAST": "ap-northeast-1",
	"EC2_SA_EAST": "sa-east-1",
	"EC2_AP_SOUTHEAST2": "ap-southeast-2",
	"EC2_EU_CENTRAL": "eu-central-1",
}


class EC2CloudConnectionError(CloudConnectionError):
	pass


class EC2CloudConnection(CloudConnection, PersistentCached):

	def __init__(self, cloud, cache_dir):
		self._check_connection_attributes(cloud)
		super(EC2CloudConnection, self).__init__(cloud, cache_dir)

		self.publicdata.url = cloud["region"]

		self._locations = []
		self._security_groups = []

	def _check_connection_attributes(self, cloud):
		if "access_id" not in cloud:
			raise EC2CloudConnectionError("access_id attribute is required")
		if "password" not in cloud:
			raise EC2CloudConnectionError("password attribute is required")
		if "region" not in cloud:
			raise EC2CloudConnectionError("region attribute is required")

	def _create_connection(self, cloud, testconnection=True):
		logger.debug("Creating connection to %s" % cloud["region"])
		params = {}
		for param in cloud:
			if param in EC2_CONNECTION_ATTRIBUTES and cloud[param]:
				params[EC2_CONNECTION_ATTRIBUTES[param]] = cloud[param]

		# if not explicitly set, use secure connection
		if 'secure' not in params:
			params['secure'] = True

		os = get_driver(Provider.EC2)
		params['region'] = PROVIDER_MAPPING[cloud["region"]]

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
		# self._images = self._exec_libcloud(lambda: self.driver.list_images(ex_owner="aws-marketplace"))
		self._images = self._exec_libcloud(lambda: self.driver.list_images())
		# images are not sorted
		self._images.sort(key=lambda image: unicode(image.name).lower())

		self._sizes = self._exec_libcloud(lambda: self.driver.list_sizes())
		self._locations = self._exec_libcloud(lambda: self.driver.list_locations())
		self._keypairs = self._exec_libcloud(lambda: self.driver.list_key_pairs())
		self._security_groups = self._exec_libcloud(lambda: self.driver.ex_get_security_groups())  # ex_get_ for ec2!
		self._networks = self._exec_libcloud(lambda: self.driver.ex_list_networks())
		self._subnets = self._exec_libcloud(lambda: self.driver.ex_list_subnets())
		self._last_expensive_update = time.time()

	def list_instances(self, pattern="*"):
		regex = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
		instances = []
		for instance in self._instances:
			if regex.match(instance.name) is not None or regex.match(instance.id) is not None:
				i = Cloud_Data_Instance()
				i.u_connection_type = "EC2"
				i.name = instance.name
				# filter detailed network information
				extra = instance.extra
				extra['network_interfaces'] = 'removed_by_ucs'
				i.extra = extra
				i.id = instance.id
				i.image = instance.extra['image_id']
				i.key_name = instance.extra['key_name']
				i.private_ips = instance.private_ips
				i.public_ips = instance.public_ips
				i.size = i.u_size_name = instance.extra['instance_type']
				i.state = LIBCLOUD_EC2_UVMM_STATE_MAPPING[instance.state]
				i.uuid = instance.uuid
				i.available = self.publicdata.available

				# information not directly provided by libcloud:
				image_name = [im for im in self._images if im.id == i.image]
				i.u_image_name = '<Unknown>'
				if image_name:
					i.u_image_name = image_name[0].name

				secgroups = [s['group_name'] for s in instance.extra['groups']]
				i.secgroups = '<Unknown>'
				if secgroups:
					i.secgroups = '; '.join(secgroups)

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
			s.description = secgroup.extra["description"]
			s.in_rules = secgroup.ingress_rules
			s.out_rules = secgroup.egress_rules
			s.extra = secgroup.extra
			s.tenant_id = secgroup.extra["owner_id"]
			s.driver = self.driver.name  # missing in libcloud EC2SecurityGroup
			s.network_id = secgroup.extra["vpc_id"]

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
			i.u_displayname = "%s - %s" % (i.id, i.name)

			sizes.append(i)

		return sizes

	def list_networks(self):
		networks = []
		for network in self._networks:
			s = Cloud_Data_Network()
			s.id = network.id
			s.name = network.name
			s.driver = self.driver.name  # missing in libcloud EC2Network
			s.extra = network.extra
			s.cidr = network.cidr_block

			networks.append(s)

		return networks

	def list_subnets(self):
		subnets = []
		for subnet in self._subnets:
			s = Cloud_Data_Subnet()
			s.id = subnet.id
			s.name = subnet.name
			s.driver = self.driver.name  # missing in libcloud EC2NetworkSubnet
			s.cidr = subnet.extra['cidr_block']
			s.network_id = subnet.extra["vpc_id"]
			s.extra = subnet.extra

			subnets.append(s)

		return subnets

	def to_cloud_data_image(self, image):
		cloud_data_image = super(EC2CloudConnection, self).to_cloud_data_image(image)
		cloud_data_image.name = "%s (%s)" % (image.name, image.id)
		return cloud_data_image

	def list_images(self):
		regex = None
		if self.publicdata.search_pattern:
			# Expand pattern with *
			regex = re.compile(fnmatch.translate('*%s*' % self.publicdata.search_pattern), re.IGNORECASE)
		images = []
		for image in self._images:
			include = False
			if self.publicdata.ucs_images and image.extra['owner_id'] == '223093067001':
				include = True
			if '%s' % image.id in self._preselected_images:
				include = True
			if regex:
				for attr in [image.name, image.id, image.extra['owner_id']]:
					if attr and regex.match(attr):
						include = True
						break
			if include:
				images.append(self.to_cloud_data_image(image))
		return images

	def _boot_instance(self, instance):
		self._exec_libcloud(lambda: self.driver.ex_start_node(instance))

	def _softreboot_instance(self, instance):
		self._exec_libcloud(lambda: self.driver.reboot_node(instance))

	def _reboot_instance(self, instance):
		raise EC2CloudConnectionError("RESTART: Not yet implemented")

	def _pause_instance(self, instance):
		raise EC2CloudConnectionError("PAUSE: Not yet implemented")

	def _unpause_instance(self, instance):
		raise EC2CloudConnectionError("RESUME: Not yet implemented")

	def _shutdown_instance(self, instance):
		self._exec_libcloud(lambda: self.driver.ex_stop_node(instance))

	def _shutoff_instance(self, instance):
		raise EC2CloudConnectionError("SHUTOFF: Not yet implemented")

	def _suspend_instance(self, instance):
		raise EC2CloudConnectionError("SUSPEND: Not yet implemented")

	def _resume_instance(self, instance):
		raise EC2CloudConnectionError("RESUME: Not yet implemented")

	def instance_state(self, instance_id, state):
		# instance is a libcloud.Node object
		instance = self._get_instance_by_id(instance_id)

		OS_TRANSITION = {
			# (NodeState.TERMINATED, "*"): None, cannot do anything with terminated instances
			(NodeState.RUNNING, "RUN"): None,
			(NodeState.PENDING, "RUN"): None,
			(NodeState.UNKNOWN, "RUN"): self._boot_instance,
			(NodeState.STOPPED, "RUN"): self._boot_instance,
			(NodeState.RUNNING, "SOFTRESTART"): self._softreboot_instance,
			(NodeState.PENDING, "RESTART"): None,
			(NodeState.RUNNING, "SHUTDOWN"): self._shutdown_instance,
			(NodeState.RUNNING, "SHUTOFF"): self._shutoff_instance,
			(NodeState.REBOOTING, "SHUTOFF"): self._shutoff_instance,
			(NodeState.PENDING, "SHUTOFF"): self._shutoff_instance,
			(NodeState.UNKNOWN, "SHUTOFF"): self._shutoff_instance,
		}
		logger.debug("STATE: connection: %s instance %s (id:%s), oldstate: %s (%s), requested: %s", self.publicdata.name, instance.name, instance.id, instance.state, instance.state, state)
		try:
			transition = OS_TRANSITION[(instance.state, state)]
			if transition:
				transition(instance)
			else:
				logger.debug("NOP state transition: %s -> %s", instance.state, state)
		except KeyError:
			raise EC2CloudConnectionError("Unsupported State transition (%s -> %s) requested" % (instance.state, state))
		except Exception as ex:
			raise EC2CloudConnectionError("Error trying to %s instance %s (id:%s): %s" % (state, instance.name, instance_id, ex))
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
			raise EC2CloudConnectionError("Error while destroying instance %s (id:%s): %s" % (name, instance_id, ex))
		logger.info("Destroyed instance %s (id:%s), using connection %s", name, instance_id, self.publicdata.name)

	def instance_create(self, args):
		# Check args
		kwargs = {}
		if "name" not in args:
			raise EC2CloudConnectionError("<name> attribute required for new instance")
		else:
			kwargs[EC2_CREATE_ATTRIBUTES["name"]] = args["name"]

		if "keyname" not in args:
			raise EC2CloudConnectionError("<keyname> attribute required for new instance")
		else:
			key = [kp for kp in self._keypairs if kp.name == args["keyname"]]
			if not key:
				raise EC2CloudConnectionError("No keypair with name %s found." % args["keyname"])

			kwargs[EC2_CREATE_ATTRIBUTES["keyname"]] = args["keyname"]

		if "size_id" not in args:
			raise EC2CloudConnectionError("<size_id> attribute required for new instance")
		else:
			size = [s for s in self._sizes if s.id == args["size_id"]]
			if not size:
				raise EC2CloudConnectionError("No size with id %s found." % args["size_id"])

			kwargs[EC2_CREATE_ATTRIBUTES["size_id"]] = size[0]

		if "image_id" not in args:
			raise EC2CloudConnectionError("<image_id> attribute required for new instance")
		else:
			image = [i for i in self._images if i.id == args["image_id"]]
			if not image:
				raise EC2CloudConnectionError("No image with id %s found." % args["image_id"])

			kwargs[EC2_CREATE_ATTRIBUTES["image_id"]] = image[0]

		if "location_id" in args:
			if not isinstance(args["location_id"], str):
				raise EC2CloudConnectionError("<location_id> attribute must be a string")
			kwargs[EC2_CREATE_ATTRIBUTES["location_id"]] = args["location_id"]

		if "userdata" in args:
			if not (isinstance(args["userdata"], str) or isinstance(args["userdata"], unicode)):
				raise EC2CloudConnectionError("<userdata> attribute must be a string")
			kwargs[EC2_CREATE_ATTRIBUTES["userdata"]] = args["userdata"]

		if "metadata" in args:
			if not isinstance(args["metadata"], dict):
				logger.debug("metadata type: %s" % args["metadata"].__class__)
				raise EC2CloudConnectionError("<metadata> attribute must be a dict")
			kwargs[EC2_CREATE_ATTRIBUTES["metadata"]] = args["metadata"]

		if "security_group_ids" in args:
			if not (isinstance(args["security_group_ids"], list)):
				raise EC2CloudConnectionError("<security_group_ids> attribute must be a list")

			secgroups = [s for s in self._security_groups if s.id in args["security_group_ids"]]
			if not secgroups:
				raise EC2CloudConnectionError("No security group with id %s found." % args["security_group_ids"])

			if "subnet_id" in args and args["subnet_id"] != '':  # vpc
				kwargs[EC2_CREATE_ATTRIBUTES["security_group_ids"]["group_id"]] = [s.id for s in secgroups]
			else:  # default
				kwargs[EC2_CREATE_ATTRIBUTES["security_group_ids"]["group_name"]] = [s.name for s in secgroups]

		if "min_instance_count" in args:
			if not (isinstance(args["min_instance_count"], int)):
				raise EC2CloudConnectionError("<min_instance_count> attribute must be an integer")
			kwargs[EC2_CREATE_ATTRIBUTES["min_instance_count"]] = args["min_instance_count"]

		if "max_instance_count" in args:
			if not (isinstance(args["max_instance_count"], int)):
				raise EC2CloudConnectionError("<max_instance_count> attribute must be an integer")
			kwargs[EC2_CREATE_ATTRIBUTES["max_instance_count"]] = args["max_instance_count"]

		if ("min_instance_count" in args) and ("max_instance_count" in args):
			if args["min_instance_count"] >= args["max_instance_count"]:
				raise EC2CloudConnectionError("<min_instance_count> must be smaller than <max_instance_count>")

		if "clienttoken" in args:
			if not (isinstance(args["clienttoken"], str)):
				raise EC2CloudConnectionError("<clienttoken> attribute must be a string")
			kwargs[EC2_CREATE_ATTRIBUTES["clienttoken"]] = args["clienttoken"]

		if "blockdevicemappings" in args:
			if not (isinstance(args["blockdevicemappings"], list)):
				raise EC2CloudConnectionError("<blockdevicemappings> attribute must be a list")
			kwargs[EC2_CREATE_ATTRIBUTES["blockdevicemappings"]] = args["blockdevicemappings"]

		if "iamprofile" in args:
			if not (isinstance(args["iamprofile"], str)):
				raise EC2CloudConnectionError("<iamprofile> attribute must be a string")
			kwargs[EC2_CREATE_ATTRIBUTES["iamprofile"]] = args["iamprofile"]

		if "ebs_optimized" in args:
			if not (isinstance(args["ebs_optimized"], bool)):
				raise EC2CloudConnectionError("<ebs_optimized> attribute must be a bool")
			kwargs[EC2_CREATE_ATTRIBUTES["ebs_optimized"]] = args["ebs_optimized"]

		if "subnet_id" in args and args["subnet_id"] != '':
			if not (isinstance(args["subnet_id"], str) or isinstance(args["userdata"], unicode)):
				raise EC2CloudConnectionError("<subnet_id> attribute must be a string")
			subnet = [s for s in self._subnets if s.id == args["subnet_id"]]
			if not subnet:
				raise EC2CloudConnectionError("No subnet with id %s found." % args["subnet_id"])
			kwargs[EC2_CREATE_ATTRIBUTES["subnet_id"]] = subnet[0]

		# libcloud call
		try:
			logger.debug("CREATE INSTANCE, connection:%s ARGS: %s", self.publicdata.name, kwargs)
			self._exec_libcloud(lambda: self.driver.create_node(**kwargs))
			self.set_frequency_fast_update()
		except Exception as ex:
			raise EC2CloudConnectionError("Instance could not be created: %s" % ex)

	# Execute lambda function
	def _exec_libcloud(self, func):
		try:
			return func()
		except InvalidCredsError as ex:
			self.logerror(logger, "Invalid credentials provided for connection %s: %s" % (self.publicdata.name, self.publicdata.url))
			raise EC2CloudConnectionError(_('The EC2 region returned an error for connection "%(connection)s":\n\nAuthFailure: The provided AWS access credentials could not be validated. Please ensure that you are using the correct access keys. Consult the AWS service documentation for details.'), connection=self.publicdata.name)
		except MalformedResponseError as ex:
			self.logerror(logger, "Malformed response from connection, correct endpoint specified? %s: %s; %s" % (self.publicdata.name, self.publicdata.url, str(ex)))
			raise
		except ProviderError as ex:
			self.logerror(logger, "Connection %s: %s: httpcode: %s, %s" % (self.publicdata.name, self.publicdata.url, ex.http_code, ex))
			raise
		except IdempotentParamError as ex:
			self.logerror(logger, "Connection %s: %s, same client token sent, but made different request" % (self.publicdata.name, self.publicdata.url))
			raise
		except KeyPairDoesNotExistError as ex:
			self.logerror(logger, "Connection %s: %s the requested keypair does not exist" % (self.publicdata.name, self.publicdata.url))
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
			elif hasattr(ex, 'message'):
				self.logerror(logger, "%s: %s Error: %s" % (self.publicdata.name, self.publicdata.url, ex.message))
				if "Blocked" in ex.message:
					raise EC2CloudConnectionError(_('The EC2 region returned an error for connection "%(connection)s":\n\nYour AWS account is currently blocked. If you have questions, please contact AWS Support.'), connection=self.publicdata.name)
				if "RequestExpired" in ex.message:
					raise EC2CloudConnectionError(_('The EC2 region returned an error for connection "%(connection)s":\n\nRequestExpired: Please check your system time to interact with AWS.'), connection=self.publicdata.name)
				if "UnauthorizedOperation" in ex.message:
					raise EC2CloudConnectionError(_('The EC2 region returned an error for connection "%(connection)s":\n\nUnauthorizedOperation: The provided AWS access credentials are not authorized to perform this operation. Check your IAM policies, and ensure that you are using the correct access keys. Also, the IAM user must have appropriate access rights to interact with EC2, e.g. AmazonEC2FullAccess.'), connection=self.publicdata.name)
			else:
				self.logerror(logger, "Unknown exception %s: %s, %s" % (self.publicdata.name, self.publicdata.url, dir(ex)))
			raise


if __name__ == '__main__':
	import doctest
	doctest.testmod()
