from univention.management.console.modules.setup.netconf.common import AddressMap, LdapChange
import univention.admin.objects
import univention.admin.modules as modules
from univention.admin.uexceptions import base as UniventionBaseException
from ldap import LDAPError


class PhaseLdapPolicies(AddressMap, LdapChange):
	"""
	Rewrite IP configuration in LDAP object.
	"""
	priority = 42
	policies = (
		("policies/thinclient", "fileServer"),
		("policies/thinclient", "authServer"),
		("policies/thinclient", "linuxTerminalServer"),
		("policies/ldapserver", "ldapServer"),
		("policies/dhcp_boot", "boot_server"),
		("policies/dhcp_dns", "domain_name_servers"),
		("policies/dhcp_netbios", "netbios_name_servers"),
		("policies/dhcp_routing", "routers"),
		("policies/printserver", "printServer"),
		("policies/repositoryserver", "repositoryServer"),
		("shares/share", "host"),
		("shares/printer", "spoolHost"),
		("dns/forward_zone", "a"),
   )

	def __init__(self, changeset):
		super(PhaseLdapPolicies, self).__init__(changeset)
		modules.update()

	def post(self):
		try:
			self.open_ldap()
			for module, udm_property in self._iterate_policies():
				#ldap_attribute = module.mapping.mapName(udm_property)
				#force = not module.property_descriptions[udm_property].multivalue
				policies = module.lookup(None, self.ldap, None)
				for policy in policies:
					self._rewrite_policy(policy, udm_property)
		except (LDAPError, UniventionBaseException) as ex:
			self.logger.warn("Failed LDAP: %s", ex, exc_info=True)

	def _iterate_policies(self):
		for module_name, udm_property in self.policies:
			module = modules.get(module_name)
			if not module:
				self.logger.debug("Unknown module '%s", module_name)
				continue
			self.logger.info("Processing %s", module_name)
			modules.init(self.ldap, self.position, module)
			yield module, udm_property

	def _rewrite_policy(self, policy, udm_property):
		try:
			old_values = set(policy.info[udm_property])
			new_values = set((
				self.ip_mapping.get(value, value)
				for value in old_values
			))
			if old_values == new_values:
				return
			policy.info[udm_property] = list(new_values)
			if self.changeset.no_act:
				self.logger.info("Would update '%r'", policy.diff())
			else:
				policy.modify()
		except KeyError:
			pass
