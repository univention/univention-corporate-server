from ..common import RestartService


class PhaseRestartNscd(RestartService):
	service = "nscd"
	priority = 18
