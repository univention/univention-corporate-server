from ..common import RestartService
from ..conditions import NotNetworkOnly


class PhaseRestartDhcp(RestartService, NotNetworkOnly):
	service = "univention-dhcp"
	priority = 26
