# Univention Portal
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2019-2023 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

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
        return super(PortalResource, self).write_error(status_code, **kwargs)

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
