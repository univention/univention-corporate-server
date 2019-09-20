"""
Univention Setup: network configuration conditions
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
from univention.management.console.modules.setup.netconf import SkipPhase, Phase
from univention.uldap import getMachineConnection
from ldap import LDAPError
from ldap.filter import filter_format


class AddressChange(Phase):

	"""
	Check for at least one removed or added address.
	"""
	__metaclass__ = ABCMeta

	def check(self):
		super(AddressChange, self).check()
		old_ipv4s = set((_.ip for _ in self.changeset.old_ipv4s))
		new_ipv4s = set((_.ip for _ in self.changeset.new_ipv4s))
		old_ipv6s = set((_.ip for _ in self.changeset.old_ipv6s))
		new_ipv6s = set((_.ip for _ in self.changeset.new_ipv6s))
		if old_ipv4s == new_ipv4s and old_ipv6s == new_ipv6s:
			raise SkipPhase("No address change")


class Server(Phase):

	"""
	Check server role for being a UCS server.
	"""
	__metaclass__ = ABCMeta

	def check(self):
		super(Server, self).check()
		role = self.changeset.ucr.get("server/role")
		if role not in (
			"domaincontroller_master",
			"domaincontroller_backup",
			"domaincontroller_slave",
			"memberserver",
		):
			raise SkipPhase("Wrong server/role")


class Executable(Phase):

	"""
	Check executable exists.
	"""
	__metaclass__ = ABCMeta
	executable = None

	def check(self):
		super(Executable, self).check()
		if not os.path.exists(self.executable):
			raise SkipPhase("Missing executable %s" % (self.executable,))


class Dhcp(Phase):

	"""
	Check for interfaces using DHCP.
	"""
	__metaclass__ = ABCMeta

	@property
	def old_dhcps(self):
		return set(self._find_dhcp_interfaces(self.changeset.old_interfaces))

	@property
	def new_dhcps(self):
		return set(self._find_dhcp_interfaces(self.changeset.new_interfaces))

	@staticmethod
	def _find_dhcp_interfaces(interfaces):
		for name, iface in interfaces.ipv4_interfaces:
			if iface.type in ("dhcp", "dynamic"):
				yield name


class NotNetworkOnly(Phase):

	"""
	Skip when not in network only mode.
	"""
	__metaclass__ = ABCMeta

	def check(self):
		super(NotNetworkOnly, self).check()
		if self.changeset.options.network_only:
			raise SkipPhase("Network only mode")


class Ldap(Phase):

	"""
	Check LDAP server is available.
	"""
	__metaclass__ = ABCMeta
	binddn = None
	bindpwd = None
	available = None

	def check(self):
		super(Ldap, self).check()
		if self.available is None:
			self.load_state()
		if not self.available:
			raise SkipPhase("Missing LDAP")

	def load_state(self):
		self.check_available()
		if self.available:
			self.load_credentials()

	def check_available(self):
		try:
			with open("/var/run/univention-system-setup.ldap", "r") as state_file:
				line = state_file.readline()
				self.available = line.strip() != "no-ldap"
		except IOError:
			self.available = True

	def load_credentials(self):
		if self.is_master_or_backup():
			self.load_admin_credentials()
		else:
			self.load_remote_credentials()

	def is_master(self):
		role = self.changeset.ucr.get("server/role")
		return role == "domaincontroller_master"

	def is_master_or_backup(self):
		role = self.changeset.ucr.get("server/role")
		return role in (
			"domaincontroller_master",
			"domaincontroller_backup",
		)

	def load_admin_credentials(self):
		self.binddn = "cn=admin,%(ldap/base)s" % self.changeset.ucr
		try:
			self.bindpwd = open("/etc/ldap.secret", "r").read()
		except IOError:
			self.available = False

	def load_remote_credentials(self):
		try:
			username = self.changeset.profile["ldap_username"]
			self.bindpwd = self.changeset.profile["ldap_password"]
			self.lookup_user(username)
		except KeyError:
			self.available = False

	def lookup_user(self, username):
		try:
			ldap = getMachineConnection(ldap_master=True)
			ldap_filter = filter_format(
				"(&(objectClass=person)(uid=%s))",
				(username,)
			)
			result = ldap.searchDn(ldap_filter)
			self.binddn = result[0]
		except LDAPError as ex:
			self.logger.warn("Failed LDAP search for '%s': %s", username, ex)
			self.available = False
