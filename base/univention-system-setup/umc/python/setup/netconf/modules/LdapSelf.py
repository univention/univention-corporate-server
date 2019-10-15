from univention.management.console.modules.setup.netconf.common import AddressMap, LdapChange, convert_udm_subnet_to_network
from univention.management.console.modules.setup.netconf.conditions import Executable
import univention.admin.objects
import univention.admin.modules as modules
from univention.admin.uexceptions import base as UniventionBaseException
from ldap import LDAPError
from ldap.filter import escape_filter_chars
import os


class PhaseLdapSelf(AddressMap, LdapChange, Executable):

	"""
	Rewrite IP configuration in self LDAP object.
	"""
	priority = 40
	executable = "/usr/share/univention-directory-manager-tools/univention-dnsedit"

	def __init__(self, changeset):
		super(PhaseLdapSelf, self).__init__(changeset)
		self.module = None

	def post(self):
		try:
			self.open_ldap()
			self._get_module()
			for func in (self._find_computer_by_dn, self._find_computer_by_ipv4, self._find_computer_by_ipv6):
				try:
					computer = func()
					break
				except KeyError:
					continue
			else:
				self.logger.warn("Failed to find self in LDAP")
				return
			self._update(computer)
		except (LDAPError, UniventionBaseException) as ex:
			self.logger.warn("Failed LDAP: %s", ex, exc_info=True)

	def _get_module(self):
		modules.update()
		module_name = "computers/%(server/role)s" % self.changeset.ucr
		self.module = modules.get(module_name)
		modules.init(self.ldap, self.position, self.module)

	def _find_computer_by_dn(self):
		self_dn = self.changeset.ucr["ldap/hostdn"]
		return self._get_computer_at_dn(self_dn)

	def _find_computer_by_ipv4(self):
		ldap_filter = self._build_address_filter("aRecord", self.changeset.old_ipv4s)
		return self._search_computer(ldap_filter)

	def _find_computer_by_ipv6(self):
		ldap_filter = self._build_address_filter("aAARecord", self.changeset.old_ipv6s)
		return self._search_computer(ldap_filter)

	def _build_address_filter(self, key, addresses):
		hostname = self.changeset.ucr["hostname"]
		addresses = [
			"(%s=%s)" % (key, escape_filter_chars(str(address.ip)))
			for address in addresses
		]
		ldap_filter = "(&(cn=%s)(|%s))" % (
			escape_filter_chars(hostname),
			"".join(addresses),
		)
		return ldap_filter

	def _search_computer(self, ldap_filter):
		self.logger.debug("Searching '%s'...", ldap_filter)
		result = self.ldap.searchDn(ldap_filter)
		try:
			self_dn, = result
		except ValueError:
			raise KeyError(ldap_filter)
		return self._get_computer_at_dn(self_dn)

	def _get_computer_at_dn(self, dn):
		computer = univention.admin.objects.get(self.module, None, self.ldap, self.position, dn)
		computer.open()
		return computer

	def _update(self, computer):
		self._update_ips(computer)
		self._update_reverse_zones(computer)
		self._update_mac(computer)
		self.logger.info("Updating '%s' with '%r'...", computer.dn, computer.diff())
		if not self.changeset.no_act:
			computer.modify()

	def _update_ips(self, computer):
		all_addr = [str(addr.ip) for addr in (self.changeset.new_ipv4s + self.changeset.new_ipv6s)]
		computer.info["ip"] = list(set(all_addr))

	def _update_reverse_zones(self, computer):
		reverse_module = modules.get("dns/reverse_zone")
		modules.init(self.ldap, self.position, reverse_module)
		reverse_zones = reverse_module.lookup(None, self.ldap, None)
		for zone in reverse_zones:
			zone.open()  # may be unneeded

		computer.info["dnsEntryZoneReverse"] = [
			[zone.dn, str(addr.ip)]
			for zone in reverse_zones
			for addr in (self.changeset.new_ipv4s + self.changeset.new_ipv6s)
			if addr.ip in convert_udm_subnet_to_network(zone.info["subnet"])
		]

	def _update_mac(self, computer):
		macs = set()
		for name in self.changeset.new_names:
			filename = os.path.join("/sys/class/net", name, "address")
			try:
				with open(filename, "r") as address_file:
					mac = address_file.read().strip()
					macs.add(mac)
			except IOError as ex:
				self.logger.warn("Could not read '%s': %s", filename, ex)
		computer.info["mac"] = list(macs)
