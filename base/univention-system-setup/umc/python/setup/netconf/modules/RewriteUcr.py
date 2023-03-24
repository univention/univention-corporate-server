from univention.management.console.modules.setup.netconf import SkipPhase
from univention.management.console.modules.setup.netconf.common import AddressMap


class PhaseRewriteUcr(AddressMap):
    """Rewrite IP configuration stored in UCR."""

    variables = (
        'nameserver1',
        'nameserver2',
        'nameserver3',
        'dns/forwarder1',
        'dns/forwarder2',
        'dns/forwarder3',
        'ldap/server/ip',
    )
    priority = 95

    def check(self) -> None:
        super(PhaseRewriteUcr, self).check()
        if self.old_primary is None:
            raise SkipPhase('No old primary IP')

    def pre(self) -> None:
        for key in self.variables:
            value = self.changeset.ucr.get(key, None)
            if value is None:
                continue
            try:
                new_ip = self.ip_mapping[value]
            except KeyError:
                self.logger.debug("Keeping '%s'='%s'", key, value)
                continue
            self.logger.info("Updating '%s'='%s'", key, new_ip)
            self.changeset.ucr_changes[key] = new_ip
