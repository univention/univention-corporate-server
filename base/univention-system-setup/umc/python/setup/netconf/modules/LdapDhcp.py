from univention.management.console.modules.setup.netconf.common import LdapChange
import univention.admin.modules as modules
from univention.admin.uexceptions import base as UniventionBaseException
from ldap import LDAPError


class PhaseLdapDhcp(LdapChange):

	"""
	Re-create DHCP subnet.
	"""
	priority = 48

	def post(self):
		try:
			self.open_ldap()
			self._create_subnet()
		except (LDAPError, UniventionBaseException) as ex:
			self.logger.warn("Failed LDAP: %s", ex)

	def _create_subnet(self):
		ipv4 = self.changeset.new_interfaces.get_default_ipv4_address()
		if not ipv4:
			return

		service_module = modules.get("dhcp/service")
		modules.init(self.ldap, self.position, service_module)

		subnet_module = modules.get("dhcp/subnet")
		modules.init(self.ldap, self.position, subnet_module)

		services = service_module.lookup(None, self.ldap, None)
		for service in services:
			subnet = subnet_module.object(None, self.ldap, service.position, superordinate=service)
			subnet.info["subnet"] = str(ipv4.network)
			subnet.info["subnetmask"] = str(ipv4.prefixlen)
			self.logger.info("Creating '%s' with '%r'...", subnet.position.getDn(), subnet.info)
			if not self.changeset.no_act:
				subnet.create()
