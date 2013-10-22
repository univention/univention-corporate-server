from time import sleep
from univention.management.console.modules.setup.netconf.conditions import Executable, NotNetworkOnly


class PhaseRestartApache(Executable, NotNetworkOnly):
	"""
	Restart Apache after IP change.
	"""
	executable = "/usr/sbin/apache2ctl"
	priority = 20

	def post(self):
		super(PhaseRestartApache, self).post()
		self.call([self.executable, "stop"])
		for _count in xrange(20):
			if self.call(["/bin/pidof", "apache2"]):
				break
			sleep(1)
		else:
			self.logger.warn("Apache2 failed to stop")
		self.call([self.executable, "start"])
