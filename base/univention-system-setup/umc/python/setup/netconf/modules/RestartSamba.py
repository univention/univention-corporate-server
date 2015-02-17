from ..common import RestartService
from ..conditions import NotNetworkOnly


class PhaseRestartSamba(RestartService, NotNetworkOnly):
	service = "samba"
	priority = 30
