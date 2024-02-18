# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# SPDX-FileCopyrightText: 2024 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from univention.portal.extensions.reloader import PortalReloaderUDM


class DemoPortalReloader(PortalReloaderUDM):
    def _check_reason(self, reason, content=None):
        return reason == 'demo'
