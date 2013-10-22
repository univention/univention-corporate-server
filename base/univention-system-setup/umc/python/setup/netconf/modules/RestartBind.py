import os
from univention.management.console.modules.setup.netconf.conditions import Executable, NotNetworkOnly


class PhaseRestartBind(Executable, NotNetworkOnly):
	"""
	Stop the DNS server, remove the cache, restart.
	"""
	executable = "/etc/init.d/univention-bind"
	priority = 22

	PREFIX = "/etc/init.d"
	SERVICES = (
		"univention-directory-listener",
		"univention-bind-proxy",
		"univention-bind",
		"univention-dhcp",
		"univention-kdc",
		"samba4",
		"samba",
	)

	def post(self):
		super(PhaseRestartBind, self).post()
		self._call(self.SERVICES, "stop")
		self.call(['find', '/var/cache/bind', '-type', 'f', '-delete'])
		self._call(reversed(self.SERVICES), "start")

	def _call(self, services, arg):
		for service in services:
			cmd = os.path.join(self.PREFIX, service)
			if not os.path.exists(cmd):
				continue
			self.call(["invoke-rc.d", service, arg])
