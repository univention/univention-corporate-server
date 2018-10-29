from univention.management.console.modules.setup.netconf import Phase


class PhaseFlushOldAddresses(Phase):

	"""
	Flush old interfaces to remove old addresses.
	"""
	priority = 55

	def pre(self):
		super(PhaseFlushOldAddresses, self).pre()
		for _name, iface in self.changeset.old_interfaces.all_interfaces:
			self.call(["ip", "addr", "flush", iface.name])
