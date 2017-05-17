from univention.management.console.modules.setup.netconf.common import AddressMap, LdapChange
import univention.admin.modules as modules
from univention.admin.uexceptions import base as UniventionBaseException
from ldap import LDAPError


class PhaseLdapReferences(AddressMap, LdapChange):

	"""
	Rewrite IP configuration in LDAP object.
	"""
	priority = 42
	_replace_type = {1: "complete_match"}
	referers = (
		("policies/thinclient", "fileServer", 1),
		("policies/thinclient", "authServer", 1),
		("policies/thinclient", "linuxTerminalServer", 1),
		("policies/ldapserver", "ldapServer", 1),
		("policies/dhcp_boot", "boot_server", 1),
		("policies/dhcp_dns", "domain_name_servers", 1),
		("policies/dhcp_netbios", "netbios_name_servers", 1),
		("policies/dhcp_routing", "routers", 1),
		("policies/printserver", "printServer", 1),
		("policies/repositoryserver", "repositoryServer", 1),
		("shares/share", "host", 1),
		("shares/printer", "spoolHost", 1),
		("dns/forward_zone", "a", 1),
		("settings/portal_entry", "link", "//%s/"),
	)

	def __init__(self, changeset):
		super(PhaseLdapReferences, self).__init__(changeset)
		modules.update()

	def post(self):
		try:
			self.open_ldap()
			for module, udm_property, replace_type in self._iterate_objects():
				# ldap_attribute = module.mapping.mapName(udm_property)
				# force = not module.property_descriptions[udm_property].multivalue
				objects = module.lookup(None, self.ldap, None)
				for obj in objects:
					self._rewrite_object(obj, udm_property, replace_type)
		except (LDAPError, UniventionBaseException) as ex:
			self.logger.warn("Failed LDAP: %s", ex, exc_info=True)

	def _iterate_objects(self):
		for module_name, udm_property, replace_type in self.referers:
			module = modules.get(module_name)
			if not module:
				self.logger.debug("Unknown module '%s", module_name)
				continue
			self.logger.info("Processing %s", module_name)
			modules.init(self.ldap, self.position, module)
			yield module, udm_property, replace_type

	def _rewrite_object(self, obj, udm_property, replace_type):
		obj.open()
		try:
			old_values = set(obj.info[udm_property])
			if replace_type in self._replace_type and self._replace_type[replace_type] == "complete_match":
				new_values = set((
					self.ip_mapping.get(value, value)
					for value in old_values
				))
			else:
				# substring match and replace the value of replace_type
				new_values = set()
				for old_ip in self.ip_mapping.keys():
					new_ip = self.ip_mapping.get(old_ip, old_ip)
					for item in list(value.replace(replace_type % old_ip, replace_type % new_ip) for value in old_values):
						new_values.add(item)

			new_values.discard(None)
			if old_values == new_values:
				return
			obj.info[udm_property] = list(new_values)
			self.logger.info("Updating '%s' with '%r'...", obj.dn, obj.diff())
			if not self.changeset.no_act:
				obj.modify()
		except KeyError:
			pass
