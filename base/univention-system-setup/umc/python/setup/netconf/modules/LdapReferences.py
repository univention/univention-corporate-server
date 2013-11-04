from univention.management.console.modules.setup.netconf.common import AddressMap, LdapChange
import univention.admin.objects
import univention.admin.modules as modules
from univention.admin.uexceptions import base as UniventionBaseException
from ldap import LDAPError


class PhaseLdapReferences(AddressMap, LdapChange):
	"""
	Rewrite IP configuration in LDAP object.
	"""
	priority = 42
	referers = (
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
		super(PhaseLdapReferences, self).__init__(changeset)
		modules.update()

	def post(self):
		try:
			self.open_ldap()
			for module, udm_property in self._iterate_objects():
				#ldap_attribute = module.mapping.mapName(udm_property)
				#force = not module.property_descriptions[udm_property].multivalue
				objects = module.lookup(None, self.ldap, None)
				for obj in objects:
					self._rewrite_object(obj, udm_property)
		except (LDAPError, UniventionBaseException) as ex:
			self.logger.warn("Failed LDAP: %s", ex, exc_info=True)

	def _iterate_objects(self):
		for module_name, udm_property in self.referers:
			module = modules.get(module_name)
			if not module:
				self.logger.debug("Unknown module '%s", module_name)
				continue
			self.logger.info("Processing %s", module_name)
			modules.init(self.ldap, self.position, module)
			yield module, udm_property

	def _rewrite_object(self, obj, udm_property):
		obj.open()
		try:
			old_values = set(obj.info[udm_property])
			new_values = set((
				self.ip_mapping.get(value, value)
				for value in old_values
			))
			new_values.discard(None)
			if old_values == new_values:
				return
			obj.info[udm_property] = list(new_values)
			self.logger.info("Updating '%s' with '%r'...", obj.dn, obj.diff())
			if not self.changeset.no_act:
				obj.modify()
		except KeyError:
			pass
