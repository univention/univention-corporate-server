from ..common import RestartService
from ..conditions import NotNetworkOnly


class PhaseRestartKerberos(RestartService, NotNetworkOnly):
	service = "heimdal-kdc"
	priority = 28
