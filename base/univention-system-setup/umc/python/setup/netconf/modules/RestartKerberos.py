from univention.management.console.modules.setup.netconf.common import RestartService
from univention.management.console.modules.setup.netconf.conditions import NotNetworkOnly


class PhaseRestartKerberos(RestartService, NotNetworkOnly):
	service = "heimdal-kdc"
	priority = 28
