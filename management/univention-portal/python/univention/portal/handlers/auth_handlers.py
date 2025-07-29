# Univention Portal
#
# SPDX-FileCopyrightText: 2019-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from univention.portal.handlers.portal_resource import PortalResource


class LoginHandler(PortalResource):
    async def post(self, portal_name):
        portal = self.find_portal()
        await portal.login_user(self)

    async def get(self, portal_name):
        portal = self.find_portal()
        await portal.login_request(self)


class LogoutHandler(PortalResource):

    async def get(self, portal_name):
        portal = self.find_portal()
        await portal.logout_user(self)
