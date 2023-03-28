from univention.management.console.modules.setup.netconf.common import RestartService
from univention.management.console.modules.setup.netconf.conditions import NotNetworkOnly


class PhaseRestartBind(RestartService, NotNetworkOnly):
    """Stop the DNS server, remove the cache, restart."""

    service = "named"
    priority = 24

    def post(self) -> None:
        self.call(['find', '/var/cache/bind', '-type', 'f', '-delete'])
        super(PhaseRestartBind, self).post()
