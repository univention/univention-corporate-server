from univention.management.console.modules.setup.netconf.common import AddressMap, LdapChange
import univention.admin.modules as modules
from univention.admin.uexceptions import base as UniventionBaseException
from ldap import LDAPError


class PhaseLdapSSO(AddressMap, LdapChange):

	"""
	Rewrite UCS SSO host address.
	"""
	priority = 49

	def __init__(self, changeset):
		super(PhaseLdapSSO, self).__init__(changeset)
		modules.update()

	def post(self):
		try:
			if self.changeset.ucr.is_true('ucs/server/sso/autoregistraton', True):
				self.open_ldap()
				self._update_sso()
		except (LDAPError, UniventionBaseException) as ex:
			self.logger.warn("Failed LDAP: %s", ex)

	def _update_sso(self):
		forward_module = modules.get("dns/forward_zone")
		modules.init(self.ldap, self.position, forward_module)

		host_module = modules.get("dns/host_record")
		modules.init(self.ldap, self.position, host_module)

		sso_fqdn = self.changeset.ucr.get('ucs/server/sso/fqdn')
		forward_zones = forward_module.lookup(None, self.ldap, None)
		for forward_zone in forward_zones:
			zone = forward_zone.get('zone')
			if not sso_fqdn.endswith(zone):
				continue
			sso_name = sso_fqdn[:-(len(zone) + 1)]
			hosts = host_module.lookup(None, self.ldap, "relativeDomainName=%s" % sso_name, superordinate=forward_zone)
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
