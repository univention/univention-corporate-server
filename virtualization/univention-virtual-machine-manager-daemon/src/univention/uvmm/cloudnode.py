# -*- coding: utf-8 -*-
#
# UCS Virtual Machine Manager Daemon
#  cloud connection and instance handler
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
"""UVMM cloud node handler.

This module implements functions to handle cloud connections and instances. This is independent from the on-wire-format.
"""

from __future__ import absolute_import
import logging
import fnmatch
import re

from .cloudconnection import CloudConnectionError
from .openstackcloud import OpenStackCloudConnection
from .ec2cloud import EC2CloudConnection
import univention.config_registry as ucr
try:
	from typing import Dict, List, Optional  # noqa
	from .cloudconnection import CloudConnection  # noqa
except ImportError:
	pass

configRegistry = ucr.ConfigRegistry()
configRegistry.load()

logger = logging.getLogger('uvmmd.cloudconnection')

STATES = ('NOSTATE', 'RUNNING', 'IDLE', 'PAUSED', 'SHUTDOWN', 'SHUTOFF', 'CRASHED')


class CloudConnectionMananger(dict):

	"""
	Dictionary which holds all connections
	key is the cloud name, value the CloudConnection
	"""

	def __init__(self):
		# type: () -> None
		super(CloudConnectionMananger, self).__init__()

	def __delitem__(self, cloudname):
		# type: (str) -> None
		"""x.__delitem__(i) <==> del x[i]"""
		self[cloudname].unregister(wait=True)
		super(CloudConnectionMananger, self).__delitem__(cloudname)

	def _parse_cloud_info(self, cloud):
		# type: (Dict[str, str]) -> None
		if "name" not in cloud:
			raise CloudConnectionError("Field 'name' is required for adding a connection")
		if "type" not in cloud:
			raise CloudConnectionError("Field 'type' is required for adding a connection")

	def _check_if_connection_exists(self, conn_name):
		# type: (str) -> None
		if conn_name not in self:
			raise CloudConnectionError("No connection named %s available" % conn_name)

	def _get_connections(self, conn_name="*"):
		# type: (str) -> List[CloudConnection]
		connection_list = []  # type: List[CloudConnection]
		if conn_name in ("*", ""):
			connection_list = self.values()
		else:
			self._check_if_connection_exists(conn_name)
			connection_list = [self[conn_name]]
		return connection_list

	def set_cache(self, cache):
		# type: (str) -> None
		self.cache_dir = cache

	def list(self, pattern="*"):
		# type: (str) -> List[CloudConnection]
		connection_list = []  # type: List[CloudConnection]

		regex = re.compile(fnmatch.translate(pattern), re.IGNORECASE)
		for conn in self.values():
			if regex.match(conn.publicdata.name) is not None:
				# publicdata => class Cloud_Data_Connection
				connection_list.append(conn.publicdata)

		return connection_list

	def set_poll_frequency(self, freq, name=None):
		# type: (int, Optional[str]) -> None
		if name:
			try:
				self[name].set_frequency(freq)
			except KeyError:
				raise CloudConnectionError("No connection to %s" % name)
		else:
			for connection in self.values():
				connection.set_frequency(freq)

	def add_connection(self, cloud, testconnection=True):
		# type: (Dict[str, str], bool) -> None
		"""
		Add a new cloud connection
		cloud: dict with cloud name, type, credentials, urls, ...
		"""
		self._parse_cloud_info(cloud)

		if cloud["name"] in self:
			raise CloudConnectionError("Connection to %s already established" % cloud["name"])

		newconnection = None
		try:
			newconnection = create_cloud_connection(cloud, self.cache_dir)
			newconnection.connect(cloud, testconnection)
		except:
			logger.error("Error while establishing connection %s" % cloud["name"])
			if newconnection:
				newconnection.unregister(wait=True)
			raise

		self[cloud["name"]] = newconnection
		logger.info("Added connection to %s" % cloud["name"])

	def remove_connection(self, cloudname):
		# type: (str) -> None
		"""Remove connection; cloudname = ldap name attribute"""
		try:
			del self[cloudname]
		except KeyError:
			raise CloudConnectionError("No Connection to %s present" % cloudname)
		logger.info("Removed connection to %s" % cloudname)

	def list_conn_instances(self, conn_name, pattern="*"):
		# type: (str, str) -> Dict[str, List[CloudConnection]]
		"""
		List instances available through connection identified by conn_name,
		matching the pattern. If conn_name = "*", list all connections
		"""
		connection_list = self._get_connections(conn_name)

		instances = {}
		for connection in connection_list:
			instances[connection.publicdata.name] = connection.list_instances(pattern)

		return instances

	def list_conn_images(self, conn_name="*"):
		connection_list = self._get_connections(conn_name)

		images = {}
		for connection in connection_list:
			images[connection.publicdata.name] = connection.list_images()

		return images

	def list_conn_sizes(self, conn_name="*"):
		connection_list = self._get_connections(conn_name)

		sizes = {}
		for connection in connection_list:
			sizes[connection.publicdata.name] = connection.list_sizes()

		return sizes

	def list_conn_locations(self, conn_name="*"):
		connection_list = self._get_connections(conn_name)

		regions = {}
		for connection in connection_list:
			regions[connection.publicdata.name] = connection.list_locations()

		return regions

	def list_conn_keypairs(self, conn_name="*"):
		connection_list = self._get_connections(conn_name)

		keypairs = {}
		for connection in connection_list:
			keypairs[connection.publicdata.name] = connection.list_keypairs()

		return keypairs

	def list_conn_secgroups(self, conn_name="*"):
		connection_list = self._get_connections(conn_name)

		secgroups = {}
		for connection in connection_list:
			secgroups[connection.publicdata.name] = connection.list_secgroups()

		return secgroups

	def list_conn_networks(self, conn_name="*"):
		connection_list = self._get_connections(conn_name)

		networks = {}
		for connection in connection_list:
			networks[connection.publicdata.name] = connection.list_networks()

		return networks

	def list_conn_subnets(self, conn_name="*"):
		connection_list = self._get_connections(conn_name)

		subnets = {}
		for connection in connection_list:
			subnets[connection.publicdata.name] = connection.list_subnets()

		return subnets

	def instance_state(self, conn_name, instance_id, state):
		# type: (str, str, str) -> None
		self._check_if_connection_exists(conn_name)
		self[conn_name].instance_state(instance_id, state)

	def instance_terminate(self, conn_name, instance_id):
		# type: (str, str) -> None
		self._check_if_connection_exists(conn_name)
		self[conn_name].instance_terminate(instance_id)

	def instance_create(self, conn_name, args):
		# type: (str, str) -> None
		self._check_if_connection_exists(conn_name)
		self[conn_name].instance_create(args)


def create_cloud_connection(cloud, cache_dir):
	# type: (Dict[str, str], str) -> CloudConnection
	if cloud["type"] == "OpenStack":
		return OpenStackCloudConnection(cloud, cache_dir)
	elif cloud["type"] == "EC2":
		return EC2CloudConnection(cloud, cache_dir)
	else:
		raise CloudConnectionError("Unknown cloud type %s" % cloud["type"])


cloudconnections = CloudConnectionMananger()

if __name__ == '__main__':
	import doctest
	doctest.testmod()
