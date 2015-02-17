from ..common import RestartService
from ..conditions import NotNetworkOnly


class PhaseRestartSamba4(RestartService, NotNetworkOnly):
	service = "samba-ad-dc"
	priority = 30
