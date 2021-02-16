#!/usr/bin/python3
#
# Univention Portal
#
# Copyright 2020-2021 Univention GmbH
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

from six import with_metaclass

from univention.portal import Plugin


class Portal(with_metaclass(Plugin)):
	"""
	Base (and maybe only) class for a Portal.
	It is the only interface exposed to the portal tools, so you could
	replace it entirely. But these methods need to be implemented:

	`get_user`: Get the user for the current request
	`login_user`: New login for a user
	`login_request`: An anonymous user wants to login
	`get_visible_content`: The content that the frontend shall present.
		Should be filtered by the "user". Also gets "admin_mode", a
		boolean indicating whether the user requested all the content
		(and is authorized to do so)
	`get_user_links`: Get the user links in the portal, filtered by "user"
		and "admin_mode"
	`get_menu_links`: Get the menu links in the portal, filtered by "user"
		and "admin_mode"
	`get_entries`: Get all entries of "content", which in turn was the
		return value of `get_visible_content`
	`get_folders`: Get all folders of "content", which in turn was the
		return value of `get_visible_content`
	`get_categories`: Get all categories of "content", which in turn was the
		return value of `get_visible_content`
	`may_be_edited`: Whether a "user" may edit this portal
	`get_meta`: Get some information about the portal itself, given
		"content" and "categories". Those were return values of
		`get_visible_content` and `get_categories`.
	`refresh`: Refresh the portal data if needed ("reason" acts as a hint).
		Thereby allows the object to cache its content.
	`score`: If multiple portals are configured, use the one with the
		highest score for a given "request".

	scorer:
		Object that does the actual scoring. Meant to get a `Scorer` object
	portal_cache:
		Object that holds the cache. Meant to get a `Cache` object
	authenticator:
		Object that does the whole auth thing. Meant to the a `Authenticator` object
	"""

	def __init__(self, scorer, portal_cache, authenticator):
		self.scorer = scorer
		self.portal_cache = portal_cache
		self.authenticator = authenticator

	def get_user(self, request):
		return self.authenticator.get_user(request)

	def login_user(self, request):
		return self.authenticator.login_user(request)

	def login_request(self, request):
		return self.authenticator.login_request(request)

	def get_visible_content(self, user, admin_mode):
		entries = self.portal_cache.get_entries()
		folders = self.portal_cache.get_folders()
		categories = self.portal_cache.get_categories()
		visible_entry_dns = self._filter_entry_dns(entries.keys(), entries, user, admin_mode)
		visible_folder_dns = [
			folder_dn
			for folder_dn in folders.keys()
			if admin_mode or len(
				[
					entry_dn
					for entry_dn in self._get_all_entries_of_folder(folder_dn, folders, entries)
					if entry_dn in visible_entry_dns
				]
			) > 0
		]
		visible_category_dns = [
			category_dn
			for category_dn in categories.keys()
			if admin_mode or len(
				[
					entry_dn
					for entry_dn in categories[category_dn]["entries"]
					if entry_dn in visible_entry_dns or entry_dn in visible_folder_dns
				]
			) > 0
		]
		return {
			"entry_dns": visible_entry_dns,
			"folder_dns": visible_folder_dns,
			"category_dns": visible_category_dns,
		}

	def get_user_links(self, user, admin_mode):
		if user is None:
			return []
		links = self.portal_cache.get_user_links()
		links_dict = dict((link["dn"], link) for link in links)
		entry_dns = [link["dn"] for link in links]
		return [
			links_dict[dn] for dn in self._filter_entry_dns(entry_dns, links_dict, user, admin_mode)
		]

	def get_menu_links(self, user, admin_mode):
		links = self.portal_cache.get_menu_links()
		links_dict = dict((link["dn"], link) for link in links)
		entry_dns = [link["dn"] for link in links]
		return [
			links_dict[dn] for dn in self._filter_entry_dns(entry_dns, links_dict, user, admin_mode)
		]

	def get_entries(self, content):
		entries = self.portal_cache.get_entries()
		return {entry_dn: entries[entry_dn] for entry_dn in content["entry_dns"]}

	def get_folders(self, content):
		folders = self.portal_cache.get_folders()
		folders = {folder_dn: folders[folder_dn] for folder_dn in content["folder_dns"]}
		for folder in folders.values():
			folder["entries"] = [
				entry_dn
				for entry_dn in folder["entries"]
				if entry_dn in content["entry_dns"] or entry_dn in content["folder_dns"]
			]
		return folders

	def get_categories(self, content):
		categories = self.portal_cache.get_categories()
		categories = {
			category_dn: categories[category_dn] for category_dn in content["category_dns"]
		}
		for category in categories.values():
			category["entries"] = [
				entry_dn
				for entry_dn in category["entries"]
				if entry_dn in content["entry_dns"] or entry_dn in content["folder_dns"]
			]
		return categories

	def may_be_edited(self, user):
		return user.is_admin()

	def get_meta(self, content, categories):
		portal = self.portal_cache.get_portal()
		portal["categories"] = [
			category_dn
			for category_dn in portal["categories"]
			if category_dn in content["category_dns"]
		]
		portal["content"] = [
			[category_dn, categories[category_dn]["entries"]]
			for category_dn in portal["categories"]
		]
		return portal

	def _filter_entry_dns(self, entry_dns, entries, user, admin_mode):
		filtered_dns = []
		for entry_dn in entry_dns:
			entry = entries.get(entry_dn)
			if entry is None:
				continue
			if not admin_mode:
				if not entry["activated"]:
					continue
				if entry["anonymous"] and not user.is_anonymous():
					continue
				if entry["allowedGroups"]:
					for group in entry["allowedGroups"]:
						if user.is_member_of(group):
							break
					else:
						continue
			filtered_dns.append(entry_dn)
		return filtered_dns

	def _get_all_entries_of_folder(self, folder_dn, folders, entries):
		def _flatten(folder_dn, folders, entries, ret, already_unpacked_folder_dns):
			for entry_dn in folders[folder_dn]["entries"]:
				if entry_dn in entries:
					if entry_dn not in ret:
						ret.append(entry_dn)
				elif entry_dn in folders:
					if entry_dn not in already_unpacked_folder_dns:
						already_unpacked_folder_dns.append(entry_dn)
						_flatten(entry_dn, folders, entries, ret, already_unpacked_folder_dns)

		ret = []
		_flatten(folder_dn, folders, entries, ret, [])
		return ret

	def refresh(self, reason=None):
		touched = self.portal_cache.refresh(reason=reason)
		touched = self.authenticator.refresh(reason=reason) or touched
		return touched

	def score(self, request):
		return self.scorer.score(request)


class UMCPortal(Portal):
	def __init__(self, scorer, authenticator):
		self.scorer = scorer
		self.authenticator = authenticator

	def may_be_edited(self, user):
		return False

	def get_visible_content(self, user, admin_mode):
		from univention.lib.umc import Client
		client = Client(None, "Administrator", "univention")
		categories = client.umc_get("categories").data["categories"]
		modules = client.umc_get("modules").data["modules"]
		return {
			"categories": categories,
			"modules": modules,
		}

	def get_user_links(self, user, admin_mode):
		return []

	def get_menu_links(self, user, admin_mode):
		return []

	def get_entries(self, content):
		entries = {}
		for module in content["modules"]:
			entries[self._entry_id(module)] = {
				"dn": self._entry_id(module),
				"name": {
					"en_US": module["name"],
					"de_DE": module["name"],
				},
				"description": {
					"en_US": module["description"],
					"de_DE": module["description"],
				},
				"linkTarget": "useportaldefault",
				"links": ["https://www.univention.com"],
			}
		return entries

	def _entry_id(self, module):
		if module.get("flavor"):
			return "{}:{}".format(module["id"], module["flavor"])
		else:
			return module["id"]

	def get_folders(self, content):
		folders = {}
		for category in content["categories"]:
			entries = [self._entry_id(module) for module in content["modules"] if category["id"] in module["categories"]]
			folders[category["id"]] = {
				"name": {
					"en_US": category["name"],
					"de_DE": category["name"],
				},
				"dn": category["id"],
				"entries": entries,
			}
		return folders

	def get_categories(self, content):
		entries = content["categories"]
		umc_category = {
			"display_name": {
				"en_US": "UMC",
				"de_DE": "UMC",
			},
			"dn": "umc",
			"entries": [cat["id"] for cat in entries]
		}
		return {"umc": umc_category}

	def get_meta(self, content, categories):
		return {
			"name": {
				"de_DE": "Univention Management Console",
				"en_US": "Univention Management Console",
			},
			"defaultLinkTarget": "embedded",
			"categories": list(categories),
			"content": [
				[category_dn, categories[category_dn]["entries"]]
				for category_dn in categories
			],
		}

	def refresh(self, reason=None):
		pass
