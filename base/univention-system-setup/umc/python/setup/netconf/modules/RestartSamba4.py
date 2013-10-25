from univention.management.console.modules.setup.netconf.common import RestartService
from univention.management.console.modules.setup.netconf.conditions import NotNetworkOnly


class PhaseRestartSamba4(RestartService, NotNetworkOnly):
	service = "samba-ad-dc"
	priority = 30
