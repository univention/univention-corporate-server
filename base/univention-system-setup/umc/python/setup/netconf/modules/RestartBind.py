from univention.management.console.modules.setup.netconf.common import RestartService
from univention.management.console.modules.setup.netconf.conditions import NotNetworkOnly


class PhaseRestartBind(RestartService, NotNetworkOnly):

	"""
	Stop the DNS server, remove the cache, restart.
	"""
	service = "bind9"
	priority = 24

	def post(self):
		self.call(['find', '/var/cache/bind', '-type', 'f', '-delete'])
		super(PhaseRestartBind, self).post()
