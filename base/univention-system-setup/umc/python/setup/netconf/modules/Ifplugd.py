from .. import SkipPhase
from ..common import RestartService
from ..conditions import Server, Dhcp


class PhaseIfplugd(RestartService, Server, Dhcp):
	"""
	Stop and restart ifplugd if DHCP is used.
	"""
	service = "ifplugd"
	priority = 20

	def check(self):
		super(PhaseIfplugd, self).check()
		if self.old_dhcps == self.new_dhcps:
			raise SkipPhase("No type changes")
