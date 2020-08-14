#!/usr/bin/python2.7
#
# Univention Portal
#
# Copyright 2020 Univention GmbH
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

from univention.portal import Plugin

from six import with_metaclass


class Portal(with_metaclass(Plugin)):
	def __init__(self, scorer, portal_cache, groups_cache):
		self.scorer = scorer
		self.portal_cache = portal_cache
		self.groups_cache = groups_cache

	def get_visible_content(self, username, admin_mode):
		entries = self.portal_cache.get_entries()
		folders = self.portal_cache.get_folders()
		categories = self.portal_cache.get_categories()
		visible_entry_dns = self._filter_entry_dns(entries.keys(), entries, username, admin_mode)
		visible_folder_dns = [
			folder_dn for folder_dn in folders.keys()
			if len(
				[
					entry_dn for entry_dn in self._get_all_entries_of_folder(folder_dn, folders, entries)
					if entry_dn in visible_entry_dns
				]
			) > 0
		]
		visible_category_dns = [
			category_dn for category_dn in categories.keys()
			if len(
				[
					entry_dn for entry_dn in categories[category_dn]['entries']
					if entry_dn in visible_entry_dns or entry_dn in visible_folder_dns
				]
			) > 0
		]
		return {
			'entry_dns': visible_entry_dns,
			'folder_dns': visible_folder_dns,
			'category_dns': visible_category_dns,
		}

	def get_user_links(self, username, admin_mode):
		if username is None:
			return []
		links = self.portal_cache.get_user_links()
		links_dict = dict((link['dn'], link) for link in links)
		entry_dns = [link['dn'] for link in links]
		return [links_dict[dn] for dn in self._filter_entry_dns(entry_dns, links_dict, username, admin_mode)]

	def get_menu_links(self, username, admin_mode):
		links = self.portal_cache.get_menu_links()
		links_dict = dict((link['dn'], link) for link in links)
		entry_dns = [link['dn'] for link in links]
		return [links_dict[dn] for dn in self._filter_entry_dns(entry_dns, links_dict, username, admin_mode)]

	def get_entries(self, content):
		entries = self.portal_cache.get_entries()
		return {entry_dn: entries[entry_dn] for entry_dn in content['entry_dns']}

	def get_folders(self, content):
		folders = self.portal_cache.get_folders()
		folders = {folder_dn: folders[folder_dn] for folder_dn in content['folder_dns']}
		for folder in folders.values():
			folder['entries'] = [
				entry_dn for entry_dn in folder['entries']
				if entry_dn in content['entry_dns'] or entry_dn in content['folder_dns']
			]
		return folders

	def get_categories(self, content):
		categories = self.portal_cache.get_categories()
		categories = {category_dn: categories[category_dn] for category_dn in content['category_dns']}
		for category in categories.values():
			category['entries'] = [
				entry_dn for entry_dn in category['entries']
				if entry_dn in content['entry_dns'] or entry_dn in content['folder_dns']
			]
		return categories

	def get_meta(self, content, categories):
		portal = self.portal_cache.get_portal()
		portal['categories'] = [category_dn for category_dn in portal['categories'] if category_dn in content['category_dns']]
		portal['content'] = [
			[category_dn, categories[category_dn]['entries']]
			for category_dn in portal['categories']
		]
		return portal

	def _filter_entry_dns(self, entry_dns, entries, username, admin_mode):
		groups = self.groups_cache.get()
		filtered_dns = []
		for entry_dn in entry_dns:
			entry = entries.get(entry_dn)
			if entry is None:
				continue
			if not admin_mode:
				if not entry['activated']:
					continue
				if entry['allowedGroups']:
					for group_dn in entry['allowedGroups']:
						if group_dn in groups.get(username, []):
							break
					else:
						continue
			filtered_dns.append(entry_dn)
		return filtered_dns

	def _get_all_entries_of_folder(self, folder_dn, folders, entries):
		def _flatten(folder_dn, folders, entries, ret, already_unpacked_folder_dns):
			for entry_dn in folders[folder_dn]['entries']:
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

	def refresh_cache(self):
		self.portal_cache.refresh()
		self.groups_cache.refresh()

	def score(self, request):
		return self.scorer.score(request)
