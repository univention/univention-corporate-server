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

from univention.portal.factory import make_portal
from univention.portal.handlers import LoginHandler, LogoutHandler, NavigationHandler, PortalEntriesHandler
from univention.portal.log import get_logger


def make_app(portal_definitions,):
    portals = {}
    for name, portal_definition in portal_definitions.items():
        get_logger("server").info("Building portal {}".format(name))
        portals[name] = make_portal(portal_definition)

    routes = build_routes(portals)

    return tornado.web.Application(routes)


def build_routes(portals,):
    return [
        tornado.web.url(r"/(.+)/login/?", LoginHandler, {"portals": portals}, name='login',),
        tornado.web.url(r"/(.+)/portal.json", PortalEntriesHandler, {"portals": portals}, name='portal',),
        tornado.web.url(r"/(.+)/navigation.json", NavigationHandler, {"portals": portals}, name='navigation',),
        tornado.web.url(r"/(.+)/logout/?", LogoutHandler, {"portals": portals}, name='logout',),
        tornado.web.url(r"/(.+)/", tornado.web.RequestHandler, name='index',),
        tornado.web.url(r"/", tornado.web.RequestHandler, name='root',),
    ]
