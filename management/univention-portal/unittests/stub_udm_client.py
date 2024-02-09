#!/usr/bin/python3
#
# Univention Portal
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2020-2024 Univention GmbH
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
#

import binascii
import copy


portal_properties = {
    "showUmc": True,
    "logo": binascii.b2a_base64(b'<svg id="stub_logo" />'),
    "background": binascii.b2a_base64(b'<svg id="stub_background" />'),
    "name": "stub_name",
    "displayName": "stub_displayName",
    "defaultLinkTarget": "stub_defaultLinkTarget",
    "ensureLogin": "stub_ensureLogin",
    "categories": ["stub_category"],
    "userLinks": "stub_userLinks",
    "menuLinks": "stub_menuLinks",
}

category_properties = {
    "displayName": "stub_displayName",
    "entries": ["stub_entry"],
}

folder_properties = {
    "displayName": "stub_displayName",
    "entries": ["stub_entry"],
}

entry_properties = {
    "displayName": "stub_displayName",
    "name": "stub_name",
    "icon": binascii.b2a_base64(b'<svg id="stub_logo" />'),
    "description": "stub_description",
    "keywords": "stub_keywords",
    "activated": "stub_activated",
    "anonymous": "stub_anonymous",
    "allowedGroups": "stub_allowedGroups",
    "link": ["stub_locale", "stub_link"],
    "linkTarget": "stub_linkTarget",
    "target": "stub_target",
    "backgroundColor": "stub_backgroundColor",
}

announcement_properties = {
    "allowedGroups": "stub_allowedGroups",
    "name": "stub_name",
    "message": "stub_message",
    "title": "stub_title",
    "visibleFrom": "stub_visibleFrom",
    "visibleUntil": "stub_visibleeUntil",
    "isSticky": "stub_isSticky",
    "needsConfirmation": "stub_needsConfirmation",
    "severity": "stub_severity",
}


class StubUDMClient:

    def __init__(self, data=None):
        if data:
            self._data = data
        else:
            self._init_default_data()

    def _init_default_data(self):
        self._data = {
            "portals/portal": StubUDMModule(
                "portals/portal", parent=self, properties=copy.deepcopy(portal_properties)),
            "portals/category": StubUDMModule(
                "portals/category", parent=self, properties=copy.deepcopy(category_properties)),
            "portals/folder": StubUDMModule(
                "portals/folder", parent=self, properties=copy.deepcopy(folder_properties)),
            "portals/entry": StubUDMModule(
                "portals/entry", parent=self, properties=copy.deepcopy(entry_properties)),
            "portals/announcement": StubUDMModule(
                "portals/announcement", parent=self, properties=copy.deepcopy(announcement_properties)),
        }

    def get(self, name):
        return self._data[name]


class StubUDMModule:

    def __init__(self, name, parent, properties):
        self._name = name
        self._parent = parent
        self._properties = properties

    def get(self, name):
        return StubUDMObject(name, parent=self, properties=self._properties)

    def search(self, opened=False):
        return [StubUDMObject("stub_category", parent=self, properties=self._properties)]


class StubUDMObject:

    def __init__(self, name, parent, properties):
        self._name = name
        self._parent = parent
        self._properties = properties

    @property
    def dn(self):
        return f"cn={self._name},dc=stub,dc=test"

    @property
    def properties(self):
        return self._properties
