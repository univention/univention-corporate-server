from univention.management.console.modules.setup.netconf.common import RestartService


class PhaseRestartNscd(RestartService):
	service = "nscd"
	priority = 18
