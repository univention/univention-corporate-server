from univention.management.console.modules.setup.netconf import SkipPhase
from univention.management.console.modules.setup.netconf.common import AddressMap
from ipaddr import IPNetwork


class PhaseRewritePackageDatabase(AddressMap):
	"""
	Rewrite IP configuration of Univention Package Database.
	"""
	priority = 95

	def __init__(self, changeset):
		super(PhaseRewritePackageDatabase, self).__init__(changeset)
		try:
			self.old_net = IPNetwork("%(pgsql/pkgdb/network)s/%(pgsql/pkgdb/netmask)s" % self.changeset.ucr)
		except (KeyError, ValueError):
			self.old_net = None
		self.new_net = None

	def check(self):
		super(PhaseRewritePackageDatabase, self).check()
		if not self.old_net:
			raise SkipPhase("Package Database not configured")
		try:
			self.new_net = self.ip_changes[self.old_net]
		except KeyError:
			raise SkipPhase("No change")

	def pre(self):
		self.changeset.ucr_changes.update({
			"pgsql/pkgdb/network": str(self.new_net.network),
			"pgsql/pkgdb/netmask": str(self.new_net.prefixlen),
		} if self.new_net else {
			"pgsql/pkgdb/network": None,
			"pgsql/pkgdb/netmask": None,
		})
