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

import tornado.web

from univention.portal.extensions.cache_http import PortalFileCacheHTTP
from univention.portal.extensions.cache_object_storage import PortalFileCacheObjectStorage
from univention.portal.handlers.portal_resource import PortalResource
from univention.portal.log import get_logger


class PortalEntriesHandler(PortalResource):
    async def get(self, portal_name):
        portal = self.find_portal()
        if not portal:
            raise tornado.web.HTTPError(404)

        user = await portal.get_user(self)

        if isinstance(portal.portal_cache, (PortalFileCacheHTTP, PortalFileCacheObjectStorage)):
            portal.refresh()

        admin_mode = False
        if self.request.headers.get("X-Univention-Portal-Admin-Mode", "no") == "yes":
            get_logger("admin").info("Admin mode requested")
            admin_mode = user.is_admin()
            if admin_mode:
                get_logger("admin").info("Admin mode granted")
            else:
                get_logger("admin").info("Admin mode rejected")

        answer = {}
        answer["cache_id"] = portal.get_cache_id()
        visible_content = portal.get_visible_content(user, admin_mode)
        answer["user_links"] = portal.get_user_links(visible_content)
        answer["menu_links"] = portal.get_menu_links(visible_content)
        answer["entries"] = portal.get_entries(visible_content)
        answer["folders"] = portal.get_folders(visible_content)
        answer["categories"] = portal.get_categories(visible_content)
        answer["portal"] = portal.get_meta(visible_content, answer["categories"])
        if (
            not user.is_anonymous()
            and not admin_mode
            and answer["portal"].get("showUmc")
        ):
            # this is not how the portal-server is supposed to be working
            # but we need it like that...
            umc_portal = portal._get_umc_portal()
            umc_content = umc_portal.get_visible_content(user, admin_mode)
            answer["entries"].extend(umc_portal.get_entries(umc_content))
            answer["folders"].extend(umc_portal.get_folders(umc_content))
            answer["categories"].extend(umc_portal.get_categories(umc_content))
            umc_meta = umc_portal.get_meta(umc_content, answer["categories"])
            answer["portal"]["content"].extend(umc_meta["content"])
        answer["filtered"] = not admin_mode
        answer["username"] = user.username
        answer["user_displayname"] = user.display_name
        answer["auth_mode"] = portal.auth_mode(self)
        answer["may_edit_portal"] = portal.may_be_edited(user)
        answer["announcements"] = portal.get_announcements(visible_content)
        self.write(answer)
