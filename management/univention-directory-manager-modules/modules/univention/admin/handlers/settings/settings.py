# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2024 Univention GmbH
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

"""|UDM| module for all setting objects"""

from typing import TYPE_CHECKING

import univention.admin.filter
import univention.admin.handlers
import univention.admin.handlers.settings.default
import univention.admin.handlers.settings.directory
import univention.admin.handlers.settings.license
import univention.admin.handlers.settings.usertemplate
import univention.admin.localization


if TYPE_CHECKING:
    import univention.admin
    import univention.admin.uldap


translation = univention.admin.localization.translation('univention.admin.handlers.settings')
_ = translation.translate

module = 'settings/settings'
superordinate = 'settings/cn'
childs = False
short_description = _('Preferences')
object_name = _('Preference')
object_name_plural = _('Preferences')
long_description = ''
operations = ['search']
virtual = True
options = {}  # type: dict[str, univention.admin.option]
property_descriptions = {}  # type: dict[str, univention.admin.property]

mapping = univention.admin.mapping.mapping()


class object(univention.admin.handlers.simpleLdap):
    module = module


def lookup(co, lo, filter_s, base='', superordinate=None, scope='sub', unique=False, required=False, timeout=-1, sizelimit=0):
    # type: (None, univention.admin.uldap.access, str, str, univention.admin.handlers.simpleLdap | None, str, bool, bool, int, int) -> list[univention.admin.handlers.simpleLdap]
    return [
        obj
        for mod in (univention.admin.handlers.settings.directory, univention.admin.handlers.settings.default, univention.admin.handlers.settings.usertemplate, univention.admin.handlers.settings.license)
        for obj in mod.lookup(co, lo, filter_s, base, superordinate, scope, unique, required, timeout, sizelimit)
    ]


def identify(dn, attr, canonical=False):
    # type: (str, univention.admin.handlers._Attributes, bool) -> None
    pass
