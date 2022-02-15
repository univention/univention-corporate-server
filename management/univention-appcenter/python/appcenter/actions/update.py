#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for updating the list of available apps
#
# Copyright 2015-2021 Univention GmbH
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

import os
import os.path
from argparse import SUPPRESS, ArgumentParser, Namespace  # noqa F401
from glob import glob
from gzip import open as gzip_open
import zlib
from typing import Dict, Iterable, Iterator, List, Mapping, Optional  # noqa F401

from six.moves.urllib_request import Request
from six.moves.urllib_error import HTTPError

from univention.config_registry import handler_commit

from univention.appcenter.log import catch_stdout
from univention.appcenter.app import LOCAL_ARCHIVE_DIR
from univention.appcenter.app_cache import Apps, AppCenterCache
from univention.appcenter.actions import UniventionAppAction, possible_network_error
from univention.appcenter.exceptions import UpdateUnpackArchiveFailed, UpdateSignatureVerificationFailed
from univention.appcenter.utils import urlopen, gpg_verify, mkdir
from univention.appcenter.ucr import ucr_save, ucr_is_false


class Update(UniventionAppAction):

	'''Updates the list of all available applications by asking the App Center server'''
	help = 'Updates the list of apps'

	def setup_parser(self, parser):
		# type: (ArgumentParser) -> None
		parser.add_argument('--ucs-version', help=SUPPRESS)
		parser.add_argument('--appcenter-server', help=SUPPRESS)
		parser.add_argument('--cache-dir', help=SUPPRESS)
		parser.add_argument('--just-get-cache', action='store_true', default=False, help=SUPPRESS)

	def main(self, args):
		# type: (Namespace) -> None
		something_changed = False
		for app_cache in self._app_caches(args):
			# first of all, set up local cache
			mkdir(app_cache.get_cache_dir())
			if self._extract_local_archive(app_cache):
				something_changed = True
		for appcenter_cache in self._appcenter_caches(args):
			# download meta files like index.json
			mkdir(appcenter_cache.get_cache_dir())
			if self._download_supra_files(appcenter_cache):
				appcenter_cache.clear_cache()
				something_changed = True
		for app_cache in self._app_caches(args):
			# try it one more time (ucs.ini may have changed)
			mkdir(app_cache.get_cache_dir())
			if self._extract_local_archive(app_cache):
				something_changed = True
			# download apps based on meta files
			if self._download_apps(app_cache):
				app_cache.clear_cache()
				something_changed = True
		if something_changed and not args.just_get_cache:
			apps_cache = Apps()
			for app in apps_cache.get_all_locally_installed_apps():
				newest_app = apps_cache.find_candidate(app) or app
				if app < newest_app:
					ucr_save({app.ucr_upgrade_key: 'yes'})
			self._update_local_files()

		# remove cache files to force a rebuild with the next access to the cache.
		for appcenter_cache in self._appcenter_caches(args):
			appcenter_cache.clear_cache()

	def _appcenter_caches(self, args):
		# type: (Namespace) -> List[AppCenterCache]
		if args.appcenter_server:
			return [AppCenterCache(server=args.appcenter_server)]

		ret = []
		servers = set()
		for appcenter_cache in Apps().get_appcenter_caches():
			server = appcenter_cache.get_server()
			if server not in servers:
				servers.add(server)
				ret.append(appcenter_cache)
		return ret

	def _app_caches(self, args):
		# type: (Namespace) -> Iterator[AppCenterCache]
		for appcenter_cache in self._appcenter_caches(args):
			for app_cache in appcenter_cache.get_app_caches():
				if args.ucs_version:
					yield app_cache.copy(ucs_version=args.ucs_version, cache_dir=args.cache_dir)
					break
				else:
					yield app_cache.copy(cache_dir=args.cache_dir)

	def _get_etags(self, etags_file):
		# type: (str) -> Dict[str, str]
		ret = {}
		try:
			with open(etags_file, 'r') as f:
				for line in f:
					try:
						fname, etag = line.split('\t')
					except ValueError:
						pass
					else:
						ret[fname] = etag.rstrip('\n')
		except EnvironmentError:
			pass
		return ret

	def _save_etags(self, cache, etags):
		# type: (AppCenterCache, Mapping[str, str]) -> None
		etags_file = os.path.join(cache.get_cache_dir(), '.etags')
		with open(etags_file, 'w') as f:
			for fname, etag in etags.items():
				f.write('%s\t%s\n' % (fname, etag))

	def _download_supra_files(self, appcenter_cache):
		# type: (AppCenterCache) -> bool
		return self._download_files(appcenter_cache, ['app-categories.ini', 'rating.ini', 'license_types.ini', 'ucs.ini', 'suggestions.json'])

	def _download_files(self, cache, filenames):
		# type: (AppCenterCache, Iterable[str]) -> bool
		updated = False
		server = cache.get_server()
		cache_dir = cache.get_cache_dir()
		etags_file = os.path.join(cache_dir, '.etags')
		present_etags = self._get_etags(etags_file)
		ucs_version = None
		if hasattr(cache, 'get_ucs_version'):
			ucs_version = cache.get_ucs_version()
		for filename in filenames:
			etag = present_etags.get(filename)
			new_etag = self._download_file(server, filename, cache_dir, etag, ucs_version)
			if new_etag:
				present_etags[filename] = new_etag
				updated = True
		self._save_etags(cache, present_etags)
		return updated

	def _verify_file(self, cache_dir):
		# type: (str) -> None
		if ucr_is_false('appcenter/index/verify'):
			return

		fname = os.path.join(cache_dir, ".tmp.tar")
		sname = os.path.join(cache_dir, ".all.tar.gpg")

		(rc, gpg_error) = gpg_verify(fname, sname)
		if not rc:
			return

		if gpg_error:
			self.fatal(gpg_error)

		os.unlink(fname)
		os.unlink(sname)

		raise UpdateSignatureVerificationFailed(fname)

	def _download_apps(self, app_cache):
		# type: (AppCenterCache) -> bool
		filenames = [] if ucr_is_false('appcenter/index/verify') else ['all.tar.gpg']
		if filenames and not self._download_files(app_cache, filenames):
			return False

		appcenter_host = app_cache.get_server()
		if appcenter_host.startswith('https'):
			appcenter_host = 'http://%s' % appcenter_host[8:]

		cache_dir = app_cache.get_cache_dir()
		tmp_file = os.path.join(cache_dir, '.tmp.tar')
		all_tar_file = os.path.join(cache_dir, '.all.tar')
		all_tar_url = '%s/meta-inf/%s/all.tar.zsync' % (appcenter_host, app_cache.get_ucs_version())
		self.log('Downloading "%s"...' % all_tar_url)
		if self._subprocess(['zsync', all_tar_url, '-q', '-o', tmp_file, '-i', all_tar_file], cwd=cache_dir).returncode:
			# fallback: download all.tar.gz without zsync. some proxys have difficulties with it, including:
			#   * Range requests are not supported
			#   * HTTP requests are altered
			self.warn('Downloading the App archive via zsync failed. Falling back to download it directly.')
			self.warn('For better performance, try to make zsync work for "%s". The error may be caused by a proxy altering HTTP requests' % all_tar_url)
			self._download_files(app_cache, ['all.tar.gz'])
			# files are always downloaded with their filename prepended by '.'
			tgz_file = os.path.join(cache_dir, '.all.tar.gz')
			self._uncompress_archive(app_cache, tgz_file)

		self._verify_file(cache_dir)

		self._extract_archive(app_cache)
		return True

	@possible_network_error
	def _download_file(self, base_url, filename, cache_dir, etag, ucs_version=None):
		# type: (str, str, str, Optional[str], Optional[str]) -> Optional[str]
		url = os.path.join(base_url, 'meta-inf', ucs_version or '', filename)
		target = os.path.join(cache_dir, '.%s' % filename)
		if not os.path.exists(target):
			etag = None
		self.log('Downloading "%s"...' % url)
		headers = {}
		if etag:
			headers['If-None-Match'] = etag
		request = Request(url, headers=headers)
		try:
			response = urlopen(request)
		except HTTPError as exc:
			if exc.getcode() == 304:
				self.debug('  ... Not Modified')
				return None
			raise
		etag = response.headers.get('etag')
		content = response.read()
		with open(target, 'wb') as f:
			f.write(content)
		return etag

	def _update_local_files(self):
		# type: () -> None
		self.debug('Updating app files...')
		# some variables could change UCR templates
		# e.g. Name, Description
		self._update_conffiles()

	def _get_conffiles(self):
		# type: () -> List[str]
		return []

	def _update_conffiles(self):
		# type: () -> None
		conffiles = self._get_conffiles()
		if conffiles:
			with catch_stdout(self.logger):
				handler_commit(conffiles)

	def _get_local_archive(self, app_cache):
		# type: (AppCenterCache) -> Optional[str]
		fname = os.path.join(LOCAL_ARCHIVE_DIR, app_cache.get_server_netloc(), app_cache.get_ucs_version(), 'all.tar.gz')
		if os.path.exists(fname):
			return fname

	def _extract_local_archive(self, app_cache):
		# type: (AppCenterCache) -> bool
		local_archive = self._get_local_archive(app_cache)
		if not local_archive:
			# Not my local_archive
			return False
		if any(not fname.startswith('.') for fname in os.listdir(app_cache.get_cache_dir())):
			# we already have a cache. our archive is just outdated...
			return False
		self.log('Filling the App Center file cache from our local archive %s!' % local_archive)
		if not self._uncompress_archive(app_cache, local_archive):
			return False
		return self._extract_archive(app_cache)

	def _uncompress_archive(self, app_cache, local_archive):
		# type: (AppCenterCache, str) -> bool
		"""`gunzip` in Python"""
		try:
			with gzip_open(local_archive, 'rb') as zipped_file:
				archive_content = zipped_file.read()
			with open(os.path.join(app_cache.get_cache_dir(), '.tmp.tar'), 'wb') as extracted_file:
				extracted_file.write(archive_content)
		except (zlib.error, EnvironmentError) as exc:
			self.warn('Error while reading %s: %s' % (local_archive, exc))
			return False
		else:
			return True

	def _extract_archive(self, app_cache):
		# type: (AppCenterCache) -> None
		"""`tar xf` in "Python" """
		cache_dir = app_cache.get_cache_dir()
		self.debug('Extracting archive in %s' % cache_dir)
		self._purge_old_cache(cache_dir)
		tmp_file = os.path.join(cache_dir, '.tmp.tar')
		self.debug('Unpacking %s...' % tmp_file)
		if self._subprocess(['tar', '-C', cache_dir, '-x', '-f', tmp_file]).returncode:
			raise UpdateUnpackArchiveFailed(tmp_file)
		# make sure cache dir is available for everybody
		os.chmod(cache_dir, 0o755)
		# `touch tmp_file` to get a new cache in case it was created in between extraction
		os.utime(tmp_file, None)
		# Rename temporary to final file name
		all_tar_file = os.path.join(cache_dir, '.all.tar')
		os.rename(tmp_file, all_tar_file)

	def _purge_old_cache(self, cache_dir):
		# type: (str) -> None
		self.debug('Removing old files...')
		for fname in glob(os.path.join(cache_dir, '*')):
			try:
				os.unlink(fname)
			except EnvironmentError as exc:
				self.warn('Cannot delete %s: %s' % (fname, exc))
