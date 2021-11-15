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

import importlib
import json
import os.path
import shutil
import tempfile
from imghdr import what

import ldap
from ldap.dn import str2dn
from six import BytesIO, with_metaclass
from six.moves.urllib.parse import quote
from univention.portal import Plugin
from univention.portal.log import get_logger


class Reloader(with_metaclass(Plugin)):
	"""
	Our base class for reloading

	The idea is that this class handles the reloading
	for caches.

	`refresh`: In fact the only method. Gets a "reason" so that it can
		decide that a refresh is not necessary. If it was necessary, it
		should return True

	A reason "force" should be treated as very important.
	If the reloader refreshed the content, the overlying cache will reload
	itself.
	"""

	def refresh(self, reason=None):  # pragma: no cover
		pass


class MtimeBasedLazyFileReloader(Reloader):
	"""
	Specialized class that reloads if a certain (cache) file was updated.
	So if a seconds process updated the file and this class is asked to
	reload, it just returns True. If the reason fits, it actually refreshes
	the content and writes it into the file.

	cache_file:
		Filename this object is responsible for
	"""

	def __init__(self, cache_file):
		self._cache_file = cache_file
		self._mtime = self._get_mtime()

	def _get_mtime(self):
		try:
			return os.stat(self._cache_file).st_mtime
		except (EnvironmentError, AttributeError) as exc:
			get_logger("cache").warning("Unable to get mtime for {}".format(exc))
			return 0

	def _file_was_updated(self):
		mtime = self._get_mtime()
		if mtime > self._mtime:
			self._mtime = mtime
			return True

	def _check_reason(self, reason, content=None):
		if reason is None:
			return False
		if reason == "force":
			return True

	def refresh(self, reason=None, content=None):
		if self._check_reason(reason, content=content):
			get_logger("cache").info("refreshing cache")
			fd = None
			try:
				fd = self._refresh()
			except Exception:
				get_logger("cache").exception("Error during refresh")
				# hopefully, we can still work with an older cache?
			else:
				if fd:
					try:
						os.makedirs(os.path.dirname(self._cache_file))
					except EnvironmentError:
						pass
					shutil.move(fd.name, self._cache_file)
					self._mtime = self._get_mtime()
					return True
		return self._file_was_updated()

	def _refresh(self):  # pragma: no cover
		pass


class PortalReloaderUDM(MtimeBasedLazyFileReloader):
	"""
	Specialized class that reloads a cache file with the content of a certain
	portal object using UDM. Reacts on reasons like "ldap:portal:<correct_dn>".

	portal_dn:
		DN of the portals/portal object
	cache_file:
		Filename this object is responsible for
	"""

	def __init__(self, portal_dn, cache_file):
		super(PortalReloaderUDM, self).__init__(cache_file)
		self._portal_dn = portal_dn
		self._auth_info = None
		self._keywords = None

	def _check_reason(self, reason, content=None):
		if super(PortalReloaderUDM, self)._check_reason(reason, content):
			return True
		if reason is None:
			return False
		reason_args = reason.split(":", 2)
		if len(reason_args) < 2:
			return False
		if reason_args[0] != "ldap":
			return False
		return reason_args[1] in ["portal", "category", "entry", "folder"]

	def _refresh(self):
		self._auth_info = None
		udm_lib = importlib.import_module("univention.udm")
		try:
			udm = udm_lib.UDM.machine().version(2)
			portal = udm.get("portals/portal").get(self._portal_dn)
		except udm_lib.ConnectionError:
			get_logger("cache").warning("Could not establish UDM connection. Is the LDAP server accessible?")
			return None
		except udm_lib.UnknownModuleType:
			get_logger("cache").warning("UDM not up to date? Portal module not found.")
			return None
		except udm_lib.NoObject:
			get_logger("cache").warning("Portal %s not found", self._portal_dn)
			return None
		content = {}
		content["portal"] = self._extract_portal(portal)
		content["categories"] = categories = self._extract_categories(udm, portal)
		content["folders"] = folders = self._extract_folders(udm, portal, list(categories.values()))
		content["entries"] = self._extract_entries(udm, portal, list(categories.values()), list(folders.values()))
		content["user_links"] = self._extract_user_links(portal)
		content["menu_links"] = self._extract_menu_links(portal)
		with tempfile.NamedTemporaryFile(mode="w", delete=False) as fd:
			json.dump(content, fd, sort_keys=True, indent=4)
		return fd

	def _extract_portal(self, portal):
		ret = {}
		ret["dn"] = portal.dn
		ret["showUmc"] = portal.props.showUmc
		if portal.props.logo:
			ret["logo"] = self._write_image(portal.props.name, portal.props.logo.raw, "logos")
		else:
			ret["logo"] = None
		if portal.props.background:
			ret["background"] = self._write_image(
				portal.props.name, portal.props.background.raw, "backgrounds"
			)
		else:
			ret["background"] = None
		ret["name"] = portal.props.displayName
		ret["defaultLinkTarget"] = portal.props.defaultLinkTarget
		ret["ensureLogin"] = portal.props.ensureLogin
		ret["categories"] = portal.props.categories
		return ret

	def _extract_user_links(self, portal):
		return portal.props.userLinks

	def _extract_menu_links(self, portal):
		return portal.props.menuLinks

	def _extract_categories(self, udm, portal):
		ret = {}
		for category in udm.get("portals/category").search():
			in_portal = category.dn in portal.props.categories
			ret[category.dn] = {
				"dn": category.dn,
				"in_portal": in_portal,
				"display_name": category.props.displayName,
				"entries": category.props.entries,
			}
		return ret

	def _extract_entries(self, udm, portal, categories, folders):
		ret = {}

		def add(entry, ret, in_portal):
			if entry.dn not in ret:
				ret[entry.dn] = {
					"dn": entry.dn,
					"in_portal": in_portal,
					"name": entry.props.displayName,
					"description": entry.props.description,
					"logo_name": self._save_image(portal, entry),
					"activated": entry.props.activated,
					"anonymous": entry.props.anonymous,
					"allowedGroups": entry.props.allowedGroups,
					"links": entry.props.link,
					"linkTarget": entry.props.linkTarget,
					"backgroundColor": entry.props.backgroundColor,
					"auth_info": self._get_authorization_info(entry),
					'keywords': self._get_keywords(entry),
				}

		for obj in udm.get("portals/entry").search():
			if obj.dn in portal.props.menuLinks:
				add(obj, ret, True)
				continue
			if obj.dn in portal.props.userLinks:
				add(obj, ret, True)
				continue
			if any(obj.dn in category["entries"] for category in categories if category["in_portal"]):
				add(obj, ret, True)
				continue
			if any(obj.dn in folder["entries"] for folder in folders if folder["in_portal"]):
				add(obj, ret, True)
				continue
			add(obj, ret, False)

		return ret

	def _get_authorization_info(self, entry):
		if self._auth_info is None:
			try:
				with open('/var/cache/univention-portal/portal_authinfo.json') as fd:
					self._auth_info = json.load(fd)
			except (ValueError, EnvironmentError):
				self._auth_info = {}
		return self._auth_info.get(entry.dn, {})

	def _get_keywords(self, entry):
		if self._keywords is None:
			try:
				with open('/var/cache/univention-portal/portal_keywords.json') as fd:
					self._keywords = json.load(fd)
			except (ValueError, EnvironmentError):
				self._keywords = {}
		return self._keywords.get(entry.dn, {})

	def _extract_folders(self, udm, portal, categories):
		ret = {}

		def add(folder, ret, in_portal):
			ret[folder.dn] = {
				"dn": folder.dn,
				"in_portal": in_portal,
				"name": folder.props.displayName,
				"entries": folder.props.entries,
			}

		for obj in udm.get("portals/folder").search():
			if obj.dn in portal.props.menuLinks:
				add(obj, ret, True)
				continue
			if obj.dn in portal.props.userLinks:
				add(obj, ret, True)
				continue
			if any(obj.dn in category["entries"] for category in categories if category["in_portal"]):
				add(obj, ret, True)
				continue
			add(obj, ret, False)

		return ret

	def _write_image(self, name, img, dirname):
		try:
			name = name.replace(
				"/", "-"
			)  # name must not contain / and must be a path which can be accessed via the web!
			string_buffer = BytesIO(img)
			suffix = what(string_buffer) or "svg"
			fname = "/usr/share/univention-portal/icons/%s/%s.%s" % (dirname, name, suffix)
			with open(fname, "wb") as fd:
				fd.write(img)
		except (EnvironmentError, TypeError, IOError):
			get_logger("img").exception("Error saving image for %s" % name)
		else:
			return "./icons/%s/%s.%s" % (
				quote(dirname),
				quote(name),
				quote(suffix),
			)

	def _save_image(self, portal, entry):
		img = entry.props.icon
		if img:
			return self._write_image(entry.props.name, img.raw, "entries")


class GroupsReloaderLDAP(MtimeBasedLazyFileReloader):
	"""
	Specialized class that reloads a cache file with the content of group object
	in LDAP. Reacts on the reason "ldap:group"

	ldap_uri:
		URI for the LDAP connection, e.g. "ldap://ucs:7369"
	binddn:
		The bind dn for the connection, e.g. "cn=ucs,cn=computers,..."
	password_file:
		Filename that holds the password for the binddn, e.g. "/etc/machine.secret"
	ldap_base:
		Base in which the groups are searched in. E.g., "dc=base,dc=com" or "cn=groups,ou=OU1,dc=base,dc=com"
	cache_file:
		Filename this object is responsible for
	"""

	def __init__(self, ldap_uri, binddn, password_file, ldap_base, cache_file):
		super(GroupsReloaderLDAP, self).__init__(cache_file)
		self._ldap_uri = ldap_uri
		self._bind_dn = binddn
		self._password_file = password_file
		self._ldap_base = ldap_base

	def _check_reason(self, reason, content=None):
		if super(GroupsReloaderLDAP, self)._check_reason(reason, content):
			return True
		if reason is None:
			return False
		if reason.startswith("ldap:group"):
			return True

	def _refresh(self):
		try:
			with open(self._password_file) as fd:
				password = fd.read().rstrip("\n")
		except EnvironmentError:
			get_logger("cache").warning("Unable to read {}".format(self._password_file))
			return None
		con = ldap.initialize(self._ldap_uri)
		con.simple_bind_s(self._bind_dn, password)
		ldap_content = {}
		users = {}
		groups = con.search_s(self._ldap_base, ldap.SCOPE_SUBTREE, u"(objectClass=posixGroup)")
		for dn, attrs in groups:
			usernames = []
			groups = []
			member_uids = [member.decode("utf-8").lower() for member in attrs.get("memberUid", [])]
			unique_members = [
				member.decode("utf-8").lower() for member in attrs.get("uniqueMember", [])
			]
			for member in member_uids:
				if not member.endswith("$"):
					usernames.append(member.lower())
			for member in unique_members:
				if member.startswith("cn="):
					member_uid = str2dn(member)[0][0][1]
					if "{}$".format(member_uid) not in member_uids:
						groups.append(member)
			ldap_content[dn.lower()] = {"usernames": usernames, "groups": groups}
		groups_with_nested_groups = {}
		for group_dn in ldap_content:
			self._nested_groups(group_dn, ldap_content, groups_with_nested_groups)
		for group_dn, attrs in ldap_content.items():
			for user in attrs["usernames"]:
				groups = users.setdefault(user, set())
				groups.update(groups_with_nested_groups[group_dn])
		users = dict((user, list(groups)) for user, groups in users.items())
		with tempfile.NamedTemporaryFile(mode="w", delete=False) as fd:
			json.dump(users, fd, sort_keys=True, indent=4)
		return fd

	def _nested_groups(self, dn, ldap_content, nested_groups_cache):
		if dn in nested_groups_cache:
			return nested_groups_cache[dn]
		ret = set([dn])
		for group_dn in ldap_content.get(dn, {}).get("groups", []):
			ret.update(self._nested_groups(group_dn, ldap_content, nested_groups_cache))
		nested_groups_cache[dn] = ret
		return ret
