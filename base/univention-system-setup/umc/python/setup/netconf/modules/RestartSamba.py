from univention.management.console.modules.setup.netconf.common import RestartService
from univention.management.console.modules.setup.netconf.conditions import NotNetworkOnly


class PhaseRestartSamba(RestartService, NotNetworkOnly):
	service = "samba"
	priority = 30
