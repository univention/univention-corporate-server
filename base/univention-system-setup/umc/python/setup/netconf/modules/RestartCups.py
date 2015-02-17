from ..common import RestartService
from ..conditions import NotNetworkOnly


class PhaseRestartCups(RestartService, NotNetworkOnly):
	service = "cupsys"
	priority = 14
