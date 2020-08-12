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

import shutil
import tempfile
import os.path
import json
from imghdr import what
from StringIO import StringIO
from urllib import quote

import ldap

from univention.udm import UDM
from univention.udm.modules.portal import PortalsPortalEntryObject, PortalsPortalFolderObject

from univention.portal.log import get_logger
from univention.portal import Plugin

from six import with_metaclass


class Reloader(with_metaclass(Plugin)):
	def refresh(self, cache_file, force=False):
		pass

	def refresh_ldap_connection(self):
		pass


class PortalReloaderUDM(Reloader):
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


