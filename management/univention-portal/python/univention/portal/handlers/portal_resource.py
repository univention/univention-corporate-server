# Univention Portal
#
# SPDX-FileCopyrightText: 2019-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import tornado.web

from univention.portal.log import get_logger


class PortalResource(tornado.web.RequestHandler):

    def initialize(self, portals):
        self.portals = portals

    def prepare(self, *args, **kwargs):
        super().prepare(*args, **kwargs)
        if self.request.headers.get('X-UMC-HTTPS') == 'on':
            self.request.protocol = 'https'

    def write_error(self, status_code, **kwargs):
        if "exc_info" in kwargs:
            get_logger("server").exception("Error during service")
        return super().write_error(status_code, **kwargs)

    def find_portal(self):
        best_score = 0
        best_portal = None
        for portal in self.portals.values():
            score = portal.score(self.request)
            if score > best_score:
                best_score = score
                best_portal = portal
        return best_portal

    def reverse_abs_url(self, name, args=None):
        if args is None:
            args = self.path_args
        return self.request.protocol + "://" + self.request.host + self.reverse_url(name, *args)
