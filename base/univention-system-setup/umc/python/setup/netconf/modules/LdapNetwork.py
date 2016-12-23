from univention.management.console.modules.setup.netconf import SkipPhase
from univention.management.console.modules.setup.netconf.common import LdapChange, convert_udm_subnet_to_network
import univention.admin.objects
import univention.admin.uldap as uldap
import univention.admin.modules as modules
from univention.admin.uexceptions import base as UniventionBaseException, noObject
from ldap import LDAPError


class PhaseLdapNetwork(LdapChange):

	"""
	Rewrite default network.
	This must run after LdapDhcp[48], which might created the new DHCP subnet.
	This must run after LdapDns[44], which might created the new reverse DNS zone.
	"""
	priority = 44

	def check(self):
		super(PhaseLdapNetwork, self).check()
		self._check_role()
		self._check_network()

	def _check_role(self):
		role = self.changeset.ucr.get("server/role")
		if role != "domaincontroller_master":
			raise SkipPhase("Wrong server/role")

	def _check_network(self):
		old_default = self.changeset.old_interfaces.get_default_ipv4_address()
		new_default = self.changeset.new_interfaces.get_default_ipv4_address()
		if not new_default:
			raise SkipPhase("No new default network")
		if old_default == new_default:
			raise SkipPhase("No change in default network")

	def post(self):
		try:
			self.open_ldap()
			# PMH: the original shell version first updates univentionNetwork,
			# then deletes the network and re-creates it again. I'll skip the
			# first part.
			# self._update_network()
			self._recreate_network()
		except (LDAPError, UniventionBaseException) as ex:
			self.logger.warn("Failed LDAP: %s", ex)

	def _update_network(self):
		network_dn = "cn=default,cn=networks,%(ldap/base)s" % self.changeset.ucr
		new_default = str(self.changeset.new_interfaces.get_default_ipv4_address().network)
		changes = [("univentionNetwork", "UNKNOWN", new_default)]
		self.logger.info("Updating '%s' with '%r'...", network_dn, changes)
		if not self.changeset.no_act:
			try:
				self.ldap.modify(network_dn, changes)
			except (LDAPError, UniventionBaseException) as ex:
				self.logger.warn("Failed to update default network '%s': %s", network_dn, ex)

	def _recreate_network(self):
		self._remove_old_network()
		forward_zone = self._find_forward_zone()
		reverse_zone = self._find_reverse_zone()
		dhcp_service = self._find_dhcp_service()
		self._create_new_network(forward_zone, reverse_zone, dhcp_service)

	def _remove_old_network(self):
		network_dn = "cn=default,cn=networks,%(ldap/base)s" % self.changeset.ucr
		network_module = modules.get("networks/network")
		modules.init(self.ldap, self.position, network_module)
		try:
			network = univention.admin.objects.get(network_module, None, self.ldap, self.position, network_dn)
		except noObject:
			return
		self.logger.info("Removing '%s'...", network_dn)
		if not self.changeset.no_act:
			network.remove()

	def _find_forward_zone(self):
		forward_module = modules.get("dns/forward_zone")
		modules.init(self.ldap, self.position, forward_module)
		forward_zones = forward_module.lookup(None, self.ldap, "zone=%(domainname)s" % self.changeset.ucr)
		if forward_zones:
			return forward_zones[0].dn

	def _find_reverse_zone(self):
		new_default = self.changeset.new_interfaces.get_default_ipv4_address()
		reverse_module = modules.get("dns/reverse_zone")
		modules.init(self.ldap, self.position, reverse_module)
		reverse_zones = reverse_module.lookup(None, self.ldap, None)
		for zone in reverse_zones:
			zone.open()  # may be unneeded
			network = convert_udm_subnet_to_network(zone.info["subnet"])
			if new_default in network:
				return zone.dn

	def _find_dhcp_service(self):
		dhcp_module = modules.get("dhcp/service")
		modules.init(self.ldap, self.position, dhcp_module)
		dhcp_services = dhcp_module.lookup(None, self.ldap, None)
		if dhcp_services:
			return dhcp_services[0].dn

	def _create_new_network(self, forward_zone, reverse_zone, dhcp_service):
		ipv4 = self.changeset.new_interfaces.get_default_ipv4_address()

		network_position = uldap.position(self.position.getDn())
		network_position.setDn("cn=networks,%(ldap/base)s" % self.changeset.ucr)

		network_module = modules.get("networks/network")
		modules.init(self.ldap, self.position, network_module)
		network = network_module.object(None, self.ldap, network_position)
		network.info["name"] = "default"
		network.info["network"] = str(ipv4.network)
		network.info["netmask"] = str(ipv4.netmask)
		if forward_zone:
			network.info["dnsEntryZoneForward"] = forward_zone
		if reverse_zone:
			network.info["dnsEntryZoneReverse"] = reverse_zone
		if dhcp_service:
			network.info["dhcpEntryZone"] = dhcp_service
		self.logger.info("Creating '%s' with '%r'...", network.position.getDn(), network.info)
		if not self.changeset.no_act:
			network.create()
