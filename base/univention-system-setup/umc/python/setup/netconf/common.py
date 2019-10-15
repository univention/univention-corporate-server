"""
Univention Setup: network configuration abstract common classes
"""
# Copyright 2004-2019 Univention GmbH
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

import os
from abc import ABCMeta
from univention.management.console.modules.setup.netconf.conditions import Executable, AddressChange, Ldap
import univention.admin.uldap as uldap
from ipaddr import IPv4Network, IPv6Network


class RestartService(Executable):

	"""
	Helper to restart a single service.
	"""
	__metaclass__ = ABCMeta
	service = None
	PREFIX = "/etc/init.d"

	@property
	def executable(self):
		return os.path.join(self.PREFIX, self.service)

	def pre(self):
		super(RestartService, self).pre()
		self.call(["invoke-rc.d", self.service, "stop"])

	def post(self):
		super(RestartService, self).pre()
		self.call(["invoke-rc.d", self.service, "start"])


class AddressMap(AddressChange):

	"""
	Helper to provide a mapping from old addresses to new addresses.
	"""
	__metaclass__ = ABCMeta

	def __init__(self, changeset):
		super(AddressMap, self).__init__(changeset)
		self.old_primary, self.new_primary = [
			iface.get_default_ip_address()
			for iface in (
				self.changeset.old_interfaces,
				self.changeset.new_interfaces,
			)
		]
		self.net_changes = self._map_ip()
		self.ip_mapping = self._get_address_mapping()

	def _map_ip(self):
		ipv4_changes = self.ipv4_changes()
		ipv6_changes = self.ipv6_changes()
		net_changes = {}
		net_changes.update(ipv4_changes)
		net_changes.update(ipv6_changes)
		return net_changes

	def ipv4_changes(self):
		ipv4s = dict((
			(name, iface.ipv4_address())
			for name, iface in self.changeset.new_interfaces.ipv4_interfaces
		))
		default = self.changeset.new_interfaces.get_default_ipv4_address()
		mapping = {}
		for name, iface in self.changeset.old_interfaces.ipv4_interfaces:
			old_addr = iface.ipv4_address()
			new_addr = ipv4s.get(name, default)
			if new_addr is None or old_addr.ip != new_addr.ip:
				mapping[old_addr] = new_addr
		return mapping

	def ipv6_changes(self):
		ipv6s = dict((
			((iface.name, name), iface.ipv6_address(name))
			for (iface, name) in self.changeset.new_interfaces.ipv6_interfaces
		))
		default = self.changeset.new_interfaces.get_default_ipv6_address()
		mapping = {}
		for iface, name in self.changeset.old_interfaces.ipv6_interfaces:
			old_addr = iface.ipv6_address(name)
			new_addr = ipv6s.get((iface.name, name), default)
			if new_addr is None or old_addr.ip != new_addr.ip:
				mapping[old_addr] = new_addr
		return mapping

	def _get_address_mapping(self):
		mapping = dict((
			(str(old_ip.ip), str(new_ip.ip) if new_ip else None)
			for (old_ip, new_ip) in self.net_changes.items()
		))
		return mapping


class LdapChange(AddressChange, Ldap):

	"""
	Helper to provide access to LDAP through UDM.
	"""
	__metaclass__ = ABCMeta

	def __init__(self, changeset):
		super(LdapChange, self).__init__(changeset)
		self.ldap = None
		self.position = None

	def open_ldap(self):
		ldap_host = self.changeset.ucr["ldap/master"]
		ldap_base = self.changeset.ucr["ldap/base"]
		self.ldap = uldap.access(
			host=ldap_host,
			base=ldap_base,
			binddn=self.binddn,
			bindpw=self.bindpwd,
		)
		self.position = uldap.position(ldap_base)


def convert_udm_subnet_to_network(subnet):
	if ":" in subnet:
		return convert_udm_subnet_to_ipv6_network(subnet)
	else:
		return convert_udm_subnet_to_ipv4_network(subnet)


def convert_udm_subnet_to_ipv4_network(subnet):
	octets = subnet.split('.')
	count = len(octets)
	assert 1 <= count <= 4
	prefix_length = 8 * count
	octets += ["0"] * (4 - count)
	address = '.'.join(octets)
	return IPv4Network("%s/%d" % (address, prefix_length))


def convert_udm_subnet_to_ipv6_network(subnet):
	prefix = subnet.replace(":", "")
	count = len(prefix)
	assert 1 <= count <= 32
	prefix_length = 4 * count
	address = subnet
	if count <= 28:
		address += "::"
	return IPv6Network("%s/%d" % (address, prefix_length))
