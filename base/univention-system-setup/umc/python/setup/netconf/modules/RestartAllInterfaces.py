from univention.config_registry.interfaces import Interfaces, _Iface
from univention.management.console.modules.setup.netconf import Phase


class PhaseRestartAllInterfaces(Phase):
    """Stop and restart all interfaces."""

    priority = 50

    def pre(self) -> None:
        super(PhaseRestartAllInterfaces, self,).pre()
        self.call(["ifdown", "--all", "--exclude", "lo"])

    def post(self) -> None:
        super(PhaseRestartAllInterfaces, self,).post()
        self.call(["ifup", "--all"])

    def _stop_old_interfaces(self, config: Interfaces,) -> None:  # FIXME: unused
        interfaces = [
            iface.name
            for _name, iface in config.all_interfaces
            if self._is_auto(iface)
        ]
        if interfaces:
            interfaces.reverse()
            self.call(["ifdown"] + interfaces)

    def _start_new_interfaces(self, config: Interfaces,) -> None:  # FIXME: unused
        interfaces = [
            iface.name
            for _name, iface in config.all_interfaces
            if self._is_auto(iface)
        ]
        if interfaces:
            self.call(["ifup"] + interfaces)

    @staticmethod
    def _is_auto(iface: _Iface,) -> bool:
        if iface.type in ("dhcp", "manual"):
            return True
        if not iface.start:
            return False
        if iface.ipv4_address():
            return True
        if any(iface.ipv6_address(name) for name in iface.ipv6_names):
            return True
        return False
