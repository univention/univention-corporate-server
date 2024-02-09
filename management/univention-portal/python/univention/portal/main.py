# Univention Portal
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2019-2024 Univention GmbH
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

import json

import tornado.web

from univention.portal import config
from univention.portal.factory import make_portal
from univention.portal.handlers import LoginHandler, LogoutHandler, NavigationHandler, PortalEntriesHandler
from univention.portal.log import get_logger, setup_logger


logger = get_logger("server")


def _load_portal_definitions(portal_definitions_file):
    with open(portal_definitions_file) as fd:
        return json.load(fd)


def run_server():
    setup_logger(logfile=None, stream=True)
    portal_definitions = _load_portal_definitions(
        "/usr/share/univention-portal/portals.json",
    )
    app = make_tornado_application(portal_definitions)
    start_app(app)
    tornado.ioloop.IOLoop.current().start()


def make_tornado_application(portal_definitions):
    portals = {}
    for name, portal_definition in portal_definitions.items():
        logger.info("Building portal %s", name)
        portals[name] = make_portal(portal_definition)
    routes = build_routes(portals)
    return tornado.web.Application(routes)


def start_app(app):
    port = config.fetch("port")
    # TODO: Drop the option to configure xheaders once the portal is only
    # running as container, then it would always be expected to be "True".
    enable_xheaders = config.fetch("enable_xheaders")
    logger.info("Support for xheaders enabled: %s", enable_xheaders)
    logger.info("Firing up portal server at port %s", port)
    app.listen(port, xheaders=enable_xheaders)


def build_routes(portals):
    return [
        tornado.web.url(r"/(.+)/login/?", LoginHandler, {"portals": portals}, name='login'),
        tornado.web.url(r"/(.+)/portal.json", PortalEntriesHandler, {"portals": portals}, name='portal'),
        tornado.web.url(r"/(.+)/navigation.json", NavigationHandler, {"portals": portals}, name='navigation'),
        tornado.web.url(r"/(.+)/logout/?", LogoutHandler, {"portals": portals}, name='logout'),
        tornado.web.url(r"/(.+)/", tornado.web.RequestHandler, name='index'),
        tornado.web.url(r"/", tornado.web.RequestHandler, name='root'),
    ]
