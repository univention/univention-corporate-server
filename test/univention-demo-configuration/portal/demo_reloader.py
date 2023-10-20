from univention.portal.extensions.reloader import PortalReloaderUDM


class DemoPortalReloader(PortalReloaderUDM):
    def _check_reason(self, reason, content=None):
        return reason == 'demo'
