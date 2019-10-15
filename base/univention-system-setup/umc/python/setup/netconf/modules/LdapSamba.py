from univention.management.console.modules.setup.netconf.common import AddressMap, LdapChange
import univention.admin.modules as modules
from univention.admin.uexceptions import base as UniventionBaseException
from ldap import LDAPError


class PhaseLdapSamba(AddressMap, LdapChange):

	"""
	Rewrite Samba gc._msdcs host address.
	"""
	priority = 44

	def __init__(self, changeset):
		super(PhaseLdapSamba, self).__init__(changeset)
		modules.update()

	def post(self):
		try:
			self.open_ldap()
			self._update_samba()
		except (LDAPError, UniventionBaseException) as ex:
			self.logger.warn("Failed LDAP: %s", ex)

	def _update_samba(self):
		forward_module = modules.get("dns/forward_zone")
		modules.init(self.ldap, self.position, forward_module)

		host_module = modules.get("dns/host_record")
		modules.init(self.ldap, self.position, host_module)

		forward_zones = forward_module.lookup(None, self.ldap, None)
		for zone in forward_zones:
			hosts = host_module.lookup(None, self.ldap, "name=gc._msdcs", superordinate=zone)
			for host in hosts:
				self._update_host(host)

	def _update_host(self, obj):
		obj.open()
		try:
			old_values = set(obj.info["a"])
			new_values = set((
				self.ip_mapping.get(value, value)
				for value in old_values
			))
			new_values.discard(None)
			if old_values == new_values:
				return
			obj.info["a"] = list(new_values)
			self.logger.info("Updating '%s' with '%r'...", obj.dn, obj.diff())
			if not self.changeset.no_act:
				obj.modify()
		except KeyError:
			pass
