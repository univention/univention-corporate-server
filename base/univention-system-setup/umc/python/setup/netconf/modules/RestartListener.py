from univention.management.console.modules.setup.netconf.common import RestartService
from univention.management.console.modules.setup.netconf.conditions import NotNetworkOnly


class PhaseRestartListener(RestartService, NotNetworkOnly):
	service = "univention-directory-listener"
	priority = 22
