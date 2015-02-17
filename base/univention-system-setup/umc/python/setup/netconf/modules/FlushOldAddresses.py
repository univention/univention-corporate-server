from univention.management.console.modules.setup.netconf import Phase, SkipPhase


class PhaseFlushOldAddresses(Phase):
	"""
	Flush old interfaces to remove old addresses.
	"""
	priority = 55

	def check(self):
		super(PhaseFlushOldAddresses, self).check()
		if self.changeset.options.appliance_mode:
			raise SkipPhase("Skipping flush in appliance-mode")

	def pre(self):
		super(PhaseFlushOldAddresses, self).pre()
		for _name, iface in self.changeset.old_interfaces.all_interfaces:
			self.call(["ip", "addr", "flush", iface.name])
