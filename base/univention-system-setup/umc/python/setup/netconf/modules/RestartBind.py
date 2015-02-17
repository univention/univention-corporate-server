from ..common import RestartService
from ..conditions import NotNetworkOnly


class PhaseRestartBind(RestartService, NotNetworkOnly):
	"""
	Stop the DNS server, remove the cache, restart.
	"""
	service = "univention-bind"
	priority = 24

	def post(self):
		self.call(['find', '/var/cache/bind', '-type', 'f', '-delete'])
		super(PhaseRestartBind, self).post()
