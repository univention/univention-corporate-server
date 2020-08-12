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

import json
import os.path
import shutil
import tempfile
import os
from imghdr import what
from StringIO import StringIO
from copy import deepcopy
from urllib import quote

import ldap

from univention.udm import UDM
from univention.udm.modules.portal import PortalsPortalEntryObject, PortalsPortalFolderObject

from univention.portal.log import get_logger

def get_dynamic_classes(klass_name):
	klasses = {
		'Portal': Portal,
		'PortalFileCache': PortalFileCache,
		'GroupFileCache': GroupFileCache,
		'PortalReloaderUDM': PortalReloaderUDM,
		'Scorer': Scorer,
		'DomainScorer': DomainScorer,
	}
	return klasses[klass_name]


class Portal(object):
	def __init__(self, scorer, portal_cache, groups_cache):
		self.scorer = scorer
		self.portal_cache = portal_cache
		self.groups_cache = groups_cache

	def get_groups(self):
		return self.groups_cache.get()

	def get_visible_content(self, username, admin_mode):
		entries = self.portal_cache.get('entries')
		folders = self.portal_cache.get('folders')
		categories = self.portal_cache.get('categories')
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
		links = self.portal_cache.get('user_links')
		links_dict = dict((link['dn'], link) for link in links)
		entry_dns = [link['dn'] for link in links]
		return [links_dict[dn] for dn in self._filter_entry_dns(entry_dns, links_dict, username, admin_mode)]

	def get_menu_links(self, username, admin_mode):
		links = self.portal_cache.get('menu_links')
		links_dict = dict((link['dn'], link) for link in links)
		entry_dns = [link['dn'] for link in links]
		return [links_dict[dn] for dn in self._filter_entry_dns(entry_dns, links_dict, username, admin_mode)]

	def get_entries(self, content):
		entries = self.portal_cache.get('entries')
		return {entry_dn: entries[entry_dn] for entry_dn in content['entry_dns']}

	def get_folders(self, content):
		folders = self.portal_cache.get('folders')
		folders = {folder_dn: folders[folder_dn] for folder_dn in content['folder_dns']}
		for folder in folders.values():
			folder['entries'] = [
				entry_dn for entry_dn in folder['entries']
				if entry_dn in content['entry_dns'] or entry_dn in content['folder_dns']
			]
		return folders

	def get_categories(self, content):
		categories = self.portal_cache.get('categories')
		categories = {category_dn: categories[category_dn] for category_dn in content['category_dns']}
		for category in categories.values():
			category['entries'] = [
				entry_dn for entry_dn in category['entries']
				if entry_dn in content['entry_dns'] or entry_dn in content['folder_dns']
			]
		return categories

	def get_meta(self, content, categories):
		portal = self.portal_cache.get('portal')
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
					checked_groups = []
					for group_dn in entry['allowedGroups']:
						group = groups.get(group_dn)
						if group is None:
							continue
						if self._recursive_search_in_groups(username, group, groups, checked_groups):
							break
					else:
						continue
			filtered_dns.append(entry_dn)
		return filtered_dns

	def _recursive_search_in_groups(self, username, group, groups, checked_groups):
		if username in group['usernames']:
			return True
		for group_dn in group['groups']:
			if group_dn in checked_groups:
				continue
			group = groups.get(group_dn)
			if group is None:
				continue
			checked_groups.append(group_dn)
			if self._recursive_search_in_groups(username, group, groups, checked_groups):
				return True
		return False

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

	def refresh_ldap_connection(self):
		self.portal_cache.refresh_ldap_connection()
		self.groups_cache.refresh_ldap_connection()

	def score(self, request):
		return self.scorer.score(request)


def make_arg(arg_definition):
	arg_type = arg_definition['type']
	if arg_type == 'static':
		return arg_definition['value']
	if arg_type == 'class':
		Klass = get_dynamic_classes(arg_definition['class'])
		args = []
		kwargs = {}
		for _arg_definition in arg_definition.get('args', []):
			args.append(make_arg(_arg_definition))
		for name, _arg_definition in arg_definition.get('kwargs', {}).items():
			kwargs[name] = make_arg(_arg_definition)
		return Klass(*args, **kwargs)
	raise TypeError('Unknown arg_definition: {!r}'.format(arg_definition))

def make_portal(portal_definition):
	return make_arg(portal_definition)


class PortalFileCache(object):
	def __init__(self, cache_file, reloader=None):
		self._cache_file = cache_file
		self._reloader = reloader
		self._cache = {}
		self.load()

	def load(self):
		self.refresh()
		get_logger('cache').info('loading portal cache file')
		self._load_portal()

	def _load_portal(self):
		with open(self._cache_file) as fd:
			self._cache = json.load(fd)

	def get(self, name):
		if self.refresh():
			get_logger('cache').info('reloading portal cache file')
			self._load_portal()
		return deepcopy(self._cache[name])

	def refresh(self, force=False):
		if self._reloader:
			return self._reloader.refresh(self._cache_file, force=force)

	def refresh_ldap_connection(self):
		if self._reloader:
			self._reloader.refresh_ldap_connection()

class GroupFileCache(object):
	def __init__(self, cache_file, reloader=None):
		self._cache_file = cache_file
		self._reloader = reloader
		self._cache = {}
		self.load()

	def load(self):
		self.refresh()
		get_logger('cache').info('loading group cache file')
		self._load_groups()

	def _load_groups(self):
		try:
			with open(self._cache_file) as fd:
				self._cache = json.load(fd)
		except EnvironmentError:
			get_logger('cache').warn('Error loading groups. Falling back to empty set')
			self._cache = {}

	def get(self):
		if self.refresh():
			get_logger('cache').info('reloading group cache file')
			self._load_groups()
		return self._cache

	def refresh(self, force=False):
		if self._reloader:
			return self._reloader.refresh(self._cache_file, force=force)

	def refresh_ldap_connection(self):
		if self._reloader:
			self._reloader.refresh_ldap_connection()


class PortalReloaderUDM(object):
	def __init__(self, portal_dn, refresh_file):
		self._portal_dn = portal_dn
		self._refresh_file = refresh_file

	@property
	def udm(self):
		if not hasattr(self, '_udm'):
			self._udm = UDM.machine().version(2)
		return self._udm

	def refresh_ldap_connection(self):
		self._udm = None

	def refresh(self, portal_cache_file, force=False):
		if force or os.path.exists(self._refresh_file):
			get_logger('cache').info('refreshing cache')
			fd = None
			try:
				try:
					fd = self._refresh()
				except (ldap.SERVER_DOWN, ldap.INSUFFICIENT_ACCESS, ldap.INVALID_CREDENTIALS):
					get_logger('server').info('Reconnecting ldap connection')
					self._udm = None
					fd = self._refresh()
			except Exception:
				get_logger('cache').exception('Error during refresh')
				# hopefully, we can still work with an older cache?
			else:
				if fd:
					try:
						os.makedirs(os.path.dirname(portal_cache_file))
					except EnvironmentError:
						pass
					shutil.move(fd.name, portal_cache_file)
					try:
						os.unlink(self._refresh_file)
					except EnvironmentError:
						pass
					return True

	def _refresh(self):
		try:
			portal = self.udm.get('portals/portal').get(self._portal_dn)
		except UDM.NoObject:
			raise ValueError('No Portal defined')  # default portal?
		content = {}
		content['portal'] = self._extract_portal(portal)
		content['user_links'] = self._extract_user_links(portal)
		content['menu_links'] = self._extract_menu_links(portal)
		content['categories'] = self._extract_categories(portal)
		content['entries'] = self._extract_entries(portal)
		content['folders'] = self._extract_folders(portal)
		with tempfile.NamedTemporaryFile(delete=False) as fd:
			json.dump(content, fd, sort_keys=True, indent=4)
		return fd

	def _extract_portal(self, portal):
		self._write_css(portal)
		ret = {}
		ret['dn'] = portal.dn
		ret['showApps'] = portal.props.showApps
		ret['fontColor'] = portal.props.fontColor
		if portal.props.logo:
			ret['logo'] = self._write_image(portal.props.name, portal.props.logo.raw, 'logos')
		else:
			ret['logo'] = None
		ret['name'] = portal.props.displayName
		ret['ensureLogin'] = portal.props.ensureLogin
		ret['anonymousEmpty'] = portal.props.anonymousEmpty
		ret['autoLayoutCategories'] = portal.props.autoLayoutCategories
		ret['defaultLinkTarget'] = portal.props.defaultLinkTarget
		ret['categories'] = portal.props.categories
		return ret

	def _extract_user_links(self, portal):
		ret = []
		for (idx, entry) in enumerate(portal.props.userLinks.objs):
			ret.append({
				'dn': entry.dn,
				'name': entry.props.displayName,
				'description': entry.props.description,
				'logo_name': self._save_image(portal, entry),
				'activated': entry.props.activated,
				'allowedGroups': entry.props.allowedGroups,
				'links': entry.props.link,
				'linkTarget': entry.props.linkTarget,
				'$priority': idx,
			})
		return ret

	def _extract_menu_links(self, portal):
		ret = []
		for (idx, entry) in enumerate(portal.props.menuLinks.objs):
			ret.append({
				'dn': entry.dn,
				'name': entry.props.displayName,
				'description': entry.props.description,
				'logo_name': self._save_image(portal, entry),
				'activated': entry.props.activated,
				'allowedGroups': entry.props.allowedGroups,
				'links': entry.props.link,
				'linkTarget': entry.props.linkTarget,
				'$priority': idx,
				# this is supposed to be the (ordered) idx of the unfiltered (no removed links due to allowdGroups etc)
				# portal.props.menuLinks, so that the frontend can display the menu links in the correct e.g.:
				# menuLinks = [
				# 	{dn: A, allowdGroups: foo, $priority: 0},
				# 	{dn: B,                    $priority: 1},
				# ]
				# visiting portal anonymously -> menu link B is rendered
				# user of group 'foo' logs in -> menu link A is rendered above B
			})
		return ret

	def _extract_categories(self, portal):
		ret = {}
		for category in portal.props.categories.objs:
			ret[category.dn] = {
				'dn': category.dn,
				'display_name': category.props.displayName,
				'entries': category.props.entries,
			}
		return ret

	def _extract_entries(self, portal):
		def _add(entry, ret):
			if entry.dn not in ret:
				ret[entry.dn] = {
					'dn': entry.dn,
					'name': entry.props.displayName,
					'description': entry.props.description,
					'logo_name': self._save_image(portal, entry),
					'activated': entry.props.activated,
					'allowedGroups': entry.props.allowedGroups,
					'links': entry.props.link,
					'linkTarget': entry.props.linkTarget,
				}

		def _add_entry(entry, ret, already_unpacked_folder_dns):
			if isinstance(entry, PortalsPortalFolderObject):
				if entry.dn not in already_unpacked_folder_dns:
					already_unpacked_folder_dns.append(entry.dn)
					for entry in entry.props.entries.objs:
						_add_entry(entry, ret, already_unpacked_folder_dns)
			elif isinstance(entry, PortalsPortalEntryObject):
				_add(entry, ret)
			else:
				pass  # TODO raise error?

		ret = {}
		already_unpacked_folder_dns = []
		for category in portal.props.categories.objs:
			for entry in category.props.entries.objs:
				_add_entry(entry, ret, already_unpacked_folder_dns)
		return ret

	def _extract_folders(self, portal):
		def _add(entry, ret):
			if entry.dn not in ret:
				ret[entry.dn] = {
					'dn': entry.dn,
					'name': entry.props.displayName,
					'entries': entry.props.entries,
				}

		def _add_entry(entry, ret, already_unpacked_folder_dns):
			if isinstance(entry, PortalsPortalFolderObject):
				if entry.dn not in already_unpacked_folder_dns:
					already_unpacked_folder_dns.append(entry.dn)
					_add(entry, ret)
					for entry in entry.props.entries.objs:
						_add_entry(entry, ret, already_unpacked_folder_dns)

		ret = {}
		already_unpacked_folder_dns = []
		for category in portal.props.categories.objs:
			for entry in category.props.entries.objs:
				_add_entry(entry, ret, already_unpacked_folder_dns)
		return ret

	def _write_css(self, portal):
		# get CSS rule for body background
		background = []
		image = portal.props.background
		bg_img = None
		if image:
			get_logger('css').info('Writing background image')
			bg_img = self._write_image(portal.props.name, image.raw, 'backgrounds')
		if bg_img:
			background.append('url("%s") no-repeat top center / cover' % (bg_img, ))
		css = portal.props.cssBackground
		if css:
			get_logger('css').info('Adding background CSS')
			background.append(css)
		background = ', '.join(background)

		# get font color
		font_color = portal.props.fontColor

		# prepare CSS code
		css_code = ''
		if background:
			css_code += '''
	body.umc.portal #contentWrapper {
		background: %s;
	}
	''' % (background, )

		if font_color == 'white':
			get_logger('css').info('Adding White Header')
			css_code += '''
	body.umc.portal .umcHeader .umcHeaderLeft h1 {
		color: white;
	}

	body.umc.portal .portalCategory h2 {
		color: white;
	}
	'''

		get_logger('css').info('No CSS code available')
		if not css_code:
			css_code = '/* no styling defined via UDM portal object */\n'

		# write CSS file
		fname = '/var/www/univention/portal/portal.css'
		get_logger('css').info('Writing CSS file %s' % fname)
		try:
			with open(fname, 'wb') as fd:
				fd.write(css_code)
		except (EnvironmentError, IOError) as err:
			get_logger('css').warn('Failed to write CSS file %s: %s' % (fname, err))

	def _write_image(self, name, img, dirname):
		try:
			name = name.replace('/', '-')  # name must not contain / and must be a path which can be accessed via the web!
			string_buffer = StringIO(img)
			suffix = what(string_buffer) or 'svg'
			fname = '/usr/share/univention-portal/icons/%s/%s.%s' % (dirname, name, suffix)
			with open(fname, 'wb') as fd:
				fd.write(img)
		except (EnvironmentError, TypeError, IOError) as err:
			get_logger('css').error(err)
		else:
			return '/univention/portal/icons/%s/%s.%s' % (quote(dirname), quote(name), quote(suffix))

	def _save_image(self, portal, entry):
		img = entry.props.icon
		if img:
			return self._write_image(entry.props.name, img.raw, 'entries')


class Scorer(object):
	def score(self, request):
		return 1


class DomainScorer(object):
	def __init__(self, domain):
		self.domain = domain

	def score(self, request):
		if request.host == self.domain:
			return 10
		return 0


