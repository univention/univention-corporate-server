from univention.management.console.modules.setup.netconf import SkipPhase
from univention.management.console.modules.setup.netconf.conditions import Dhcp
from univention.config_registry.frontend import handler_commit


class PhaseResolvConv(Dhcp):

	"""
	Commit /etc/resolv.conf if no more DHCP is used.
	"""
	priority = 75

	def check(self):
		super(PhaseResolvConv, self).check()
		if self.new_dhcps:
			raise SkipPhase("Still using DHCP")

	def post(self):
		super(PhaseResolvConv, self).post()
		self.logger.info("Committing /etc/resolv.conf...")
		if not self.changeset.no_act:
			handler_commit(["/etc/resolv.conf"])
