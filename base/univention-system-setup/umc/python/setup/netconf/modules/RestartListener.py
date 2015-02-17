from ..common import RestartService
from ..conditions import NotNetworkOnly


class PhaseRestartListener(RestartService, NotNetworkOnly):
	service = "univention-directory-listener"
	priority = 22
