from univention.management.console.modules.setup.netconf.common import AddressMap, LdapChange
import univention.admin.modules as modules
from univention.admin.uexceptions import base as UniventionBaseException
from ldap import LDAPError


class PhaseLdapReferences(AddressMap, LdapChange):

	"""
	Rewrite IP configuration in LDAP object.
	"""
	priority = 42
	_replace_type = {1: "complete_match", 2: "link_replace"}
	referers = (
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
		("portals/entry", "link", 2),
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
			old_values = obj[udm_property]
			if self._replace_type[replace_type] == "complete_match":
				new_values = [
					self.ip_mapping.get(value, value)
					for value in old_values
				]
			elif self._replace_type[replace_type] == "link_replace":
				new_values = []
				for old_value in old_values:
					for old_ip in self.ip_mapping.keys():
						new_ip = self.ip_mapping.get(old_ip, old_ip)
						loc, link = old_value
						link = link.replace("//%s/" % old_ip, "//%s/" % new_ip)
						new_value = [loc, link]
						if new_value not in new_values:
							new_values.append(new_value)

			new_values = [val for val in new_values if val is not None]
			if old_values == new_values:
				return
			obj[udm_property] = new_values
			self.logger.info("Updating '%s' with '%r'...", obj.dn, obj.diff())
			if not self.changeset.no_act:
				obj.modify()
		except KeyError:
			pass
