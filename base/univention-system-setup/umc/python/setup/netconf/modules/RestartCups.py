from univention.management.console.modules.setup.netconf.common import RestartService
from univention.management.console.modules.setup.netconf.conditions import NotNetworkOnly


class PhaseRestartCups(RestartService, NotNetworkOnly):
	service = "cupsys"
	priority = 14
