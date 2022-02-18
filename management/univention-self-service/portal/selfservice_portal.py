#!/usr/bin/python3
#
# Copyright 2022 Univention GmbH
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


import time


from univention.portal.extensions.portal import Portal
from univention.portal.log import get_logger


class SelfServicePortal(Portal):
	def __init__(self, scorer, portal_cache, authenticator):
		self.scorer = scorer
		self.portal_cache = portal_cache
		self.authenticator = authenticator

	def may_be_edited(self, user):
		return False

	def get_visible_content(self, user, admin_mode):
		entries = self.portal_cache.get_entries()
		selfservice_entries = {}
		for dn, entry in entries.items():
			if dn.startswith("cn=self-service-"):
				entry["in_portal"] = True
				selfservice_entries[dn] = entry
		visible_entry_dns = self._filter_entry_dns(selfservice_entries.keys(), selfservice_entries, user, admin_mode)
		return {
			"selfservice-entries": selfservice_entries,
		}

	def get_user_links(self, content):
		return []

	def get_menu_links(self, content):
		return []

	def get_entries(self, content):
		return list(content["selfservice-entries"].values())

	def get_folders(self, content):
		return []

	def get_categories(self, content):
		ret = []
		entries = content["selfservice-entries"]
		ret.append({
			"display_name": {
				"en_US": "Self Service",
			},
			"dn": "selfservice:category:main",
			"entries": sorted(entries),
		})
		return ret

	def get_meta(self, content, categories):
		category_dns = ["selfservice:category:main"]
		content = []
		for category_dn in category_dns:
			category = next(cat for cat in categories if cat["dn"] == category_dn)
			content.append([category_dn, category["entries"]])
		return {
			"name": {
				"en_US": "Self Service",
			},
			"defaultLinkTarget": "samewindow",
			"ensureLogin": False,
			"categories": category_dns,
			"content": content
		}

	def refresh(self, reason=None):
		pass

	def get_cache_id(self):
		return str(time.time())
