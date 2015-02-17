from ..common import RestartService
from ..conditions import NotNetworkOnly


class PhaseRestartPostgresql(RestartService, NotNetworkOnly):
	service = "postgresql"
	priority = 16
