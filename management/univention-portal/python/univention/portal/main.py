# Univention Portal
#
# SPDX-FileCopyrightText: 2019-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import tornado.web

from univention.portal.factory import make_portal
from univention.portal.handlers import LoginHandler, LogoutHandler, NavigationHandler, PortalEntriesHandler
from univention.portal.log import get_logger


def make_app(portal_definitions):
    portals = {}
    for name, portal_definition in portal_definitions.items():
        get_logger("server").info(f"Building portal {name}")
        portals[name] = make_portal(portal_definition)

    routes = build_routes(portals)

    return tornado.web.Application(routes)


def build_routes(portals):
    return [
        tornado.web.url(r"/(.+)/login/?", LoginHandler, {"portals": portals}, name='login'),
        tornado.web.url(r"/(.+)/portal.json", PortalEntriesHandler, {"portals": portals}, name='portal'),
        tornado.web.url(r"/(.+)/navigation.json", NavigationHandler, {"portals": portals}, name='navigation'),
        tornado.web.url(r"/(.+)/logout/?", LogoutHandler, {"portals": portals}, name='logout'),
        tornado.web.url(r"/(.+)/", tornado.web.RequestHandler, name='index'),
        tornado.web.url(r"/", tornado.web.RequestHandler, name='root'),
    ]
