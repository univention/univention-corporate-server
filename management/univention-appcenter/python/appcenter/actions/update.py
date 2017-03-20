#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for updating the list of available apps
#
# Copyright 2015-2017 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.
#

import os
import os.path
import shutil
from math import ceil
from argparse import SUPPRESS
import time
from threading import Thread
from glob import glob
from gzip import open as gzip_open
from json import loads
import tarfile
from urlparse import urlsplit
from urllib2 import quote, Request, HTTPError

from univention.config_registry import handler_commit

from univention.appcenter.log import catch_stdout
from univention.appcenter.app import LOCAL_ARCHIVE_DIR
from univention.appcenter.app_cache import Apps, AppCenterCache
from univention.appcenter.actions import UniventionAppAction, Abort, possible_network_error
from univention.appcenter.utils import urlopen, get_md5_from_file, gpg_verify, container_mode, mkdir
from univention.appcenter.ucr import ucr_save, ucr_is_false


class Update(UniventionAppAction):

	'''Updates the list of all available applications by asking the App Center server'''
	help = 'Updates the list of apps'

	def __init__(self):
		super(Update, self).__init__()
		self._cache_dir = None
		self._ucs_version = None
		self._appcenter_server = None
		self._files_downloaded = {}

	def setup_parser(self, parser):
		parser.add_argument('--ucs-version', help=SUPPRESS)
		parser.add_argument('--appcenter-server', help=SUPPRESS)
		parser.add_argument('--cache-dir', help=SUPPRESS)

	def main(self, args):
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
		if something_changed:
			apps_cache = Apps()
			for app in apps_cache.get_all_locally_installed_apps():
				newest_app = apps_cache.find_candidate(app) or app
				if app < newest_app:
					ucr_save({app.ucr_upgrade_key: 'yes'})
			self._update_local_files()

	def get_app_info(self, app):
		json_apps = self._load_index_json(app.get_app_cache_obj())
		return json_apps.get(app.component_id)

	def _appcenter_caches(self, args):
		if args.appcenter_server:
			return [AppCenterCache(server=args.appcenter_server)]
		else:
			ret = []
			servers = set()
			for appcenter_cache in Apps().get_appcenter_caches():
				server = appcenter_cache.get_server()
				if server not in servers:
					servers.add(server)
					ret.append(appcenter_cache)
			return ret

	def _app_caches(self, args):
		for appcenter_cache in self._appcenter_caches(args):
			for app_cache in appcenter_cache.get_app_caches():
				if args.ucs_version:
					yield app_cache.copy(ucs_version=args.ucs_version)
					break
				else:
					yield app_cache

	def _get_etags(self, etags_file):
		ret = {}
		try:
			with open(etags_file, 'rb') as f:
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
		etags_file = os.path.join(cache.get_cache_dir(), '.etags')
		with open(etags_file, 'wb') as f:
			for fname, etag in etags.iteritems():
				f.write('%s\t%s\n' % (fname, etag))

	def _download_supra_files(self, appcenter_cache):
		return self._download_files(appcenter_cache, ['categories.ini', 'rating.ini', 'license_types.ini', 'ucs.ini'])

	def _download_files(self, cache, filenames):
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

	def _download_apps(self, app_cache):
		filenames = ['index.json.gz']
		if not ucr_is_false('appcenter/index/verify'):
			filenames.append('index.json.gz.gpg')
		self._download_files(app_cache, filenames)
		json_apps = self._load_index_json(app_cache)
		files_to_download, something_changed_remotely = self._read_index_json(app_cache.get_cache_dir(), json_apps)
		num_files_to_be_downloaded = len(files_to_download)
		self.log('%d file(s) are new' % num_files_to_be_downloaded)
		num_files_threshold = 5
		if num_files_to_be_downloaded > num_files_threshold:
			files_to_download = self._download_archive(app_cache, files_to_download)
		threads = []
		max_threads = 10
		files_per_thread = max(num_files_threshold, int(ceil(float(len(files_to_download)) / max_threads)))
		while files_to_download:
			# normally, this should be only one thread as
			# _download_archive() is used if many files are to be downloaded
			# but if all.tar.gz fails, everything needs to be downloaded
			# don't do this at once as this opens 100 connections.
			files_to_download_in_thread, files_to_download = files_to_download[:files_per_thread], files_to_download[files_per_thread:]
			self.log('Starting to download %d file(s) directly' % len(files_to_download_in_thread))
			thread = Thread(target=self._download_directly, args=(app_cache, files_to_download_in_thread,))
			thread.start()
			threads.append(thread)
			time.sleep(0.1)  # wait 100 milliseconds so that not all threads start at the same time
		for thread in threads:
			thread.join()
		return something_changed_remotely

	@possible_network_error
	def _download_file(self, base_url, filename, cache_dir, etag, ucs_version=None):
		url = os.path.join(base_url, 'meta-inf', ucs_version or '', filename)
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
		with open(os.path.join(cache_dir, '.%s' % filename), 'wb') as f:
			f.write(content)
		return etag

	@possible_network_error
	def _download_archive(self, app_cache, files_to_download):
		# a lot of files to download? Do not download them
		#   one at a time. Download the full archive!
		files_still_to_download = []
		archive_url = os.path.join(app_cache.get_server(), 'meta-inf', app_cache.get_ucs_version(), 'all.tar.gz')
		try:
			self.log('Downloading "%s"...' % archive_url)
			# for some reason saving this in memory is flawed.
			# using StringIO and GZip objects has issues
			# with "empty" files in tar.gz archives, i.e.
			# doublets like .png logos
			with open(os.path.join(app_cache.get_cache_dir(), 'all.tar.gz'), 'wb') as f:
				f.write(urlopen(archive_url).read())
			archive = tarfile.open(f.name, 'r:*')
			try:
				for filename_url, filename, remote_md5sum in files_to_download:
					self.debug('Extracting %s' % filename)
					try:
						archive.extract(filename, path=app_cache.get_cache_dir())
						absolute_filename = os.path.join(app_cache.get_cache_dir(), filename)
						os.chown(absolute_filename, 0, 0)
						os.chmod(absolute_filename, 0o664)
						local_md5sum = get_md5_from_file(absolute_filename)
						if local_md5sum != remote_md5sum:
							self.warn('Checksum for %s should be %r but was %r! Download manually' % (filename, remote_md5sum, local_md5sum))
							raise KeyError(filename)
						self._files_downloaded[filename] = remote_md5sum
					except KeyError:
						self.warn('%s not found in archive!' % filename)
						files_still_to_download.append((filename_url, filename, remote_md5sum))
			finally:
				archive.close()
				os.unlink(f.name)
			return files_still_to_download
		except Exception as exc:
			self.fatal('Could not read "%s": %s' % (archive_url, exc))
			return files_to_download

	@possible_network_error
	def _download_directly(self, app_cache, files_to_download):
		for filename_url, filename, remote_md5sum in files_to_download:
			# dont forget to quote: 'foo & bar.ini' -> 'foo%20&%20bar.ini'
			# but dont quote https:// -> https%3A//
			path = quote(urlsplit(filename_url).path)
			filename_url = '%s%s' % (app_cache.get_server(), path)

			cached_filename = os.path.join(app_cache.get_cache_dir(), filename)

			self.debug('Downloading %s' % filename_url)
			try:
				urlcontent = urlopen(filename_url)
			except Exception as e:
				self.fatal('Error downloading %s: %s' % (filename_url, e))
			else:
				with open(cached_filename, 'wb') as f:
					f.write(urlcontent.read())
				local_md5sum = get_md5_from_file(cached_filename)
				if local_md5sum != remote_md5sum:
					self.fatal('Checksum for %s should be %r but was %r! Rather removing this file...' % (filename, remote_md5sum, local_md5sum))
					os.unlink(cached_filename)
				self._files_downloaded[filename] = remote_md5sum

	def _update_local_files(self):
		self.debug('Updating app files...')

		if container_mode():
			self.debug('do not update files in container mode...')
			return
		update_files = {
			'inst': lambda x: self._get_joinscript_path(x, unjoin=False),
			'schema': lambda x: x.get_share_file('schema'),
			'univention-config-registry-variables': lambda x: x.get_share_file('univention-config-registry-variables'),
		}
		for app in Apps().get_all_locally_installed_apps():
			for file in update_files:
				src = app.get_cache_file(file)
				dest = update_files[file](app)
				if not os.path.exists(src):
					if app.docker:
						# remove files that do not exist on server anymore
						if os.path.exists(dest):
							self.log('Deleting obsolete app file %s' % dest)
							os.unlink(dest)
				else:
					# update local files if downloaded
					component_file = '%s.%s' % (app.component_id, file)
					if component_file not in self._files_downloaded:
						continue
					src_md5 = self._files_downloaded[component_file]
					dest_md5 = None
					if os.path.exists(dest):
						dest_md5 = get_md5_from_file(dest)
					if dest_md5 is None or src_md5 != dest_md5:
						self.log('Copying %s to %s' % (src, dest))
						shutil.copy2(src, dest)
						if file == 'inst':
							os.chmod(dest, 0o755)

		# some variables could change UCR templates
		# e.g. Name, Description
		self._update_conffiles()

	def _get_conffiles(self):
		return ['/usr/share/univention-portal/apps.json']

	def _update_conffiles(self):
		conffiles = self._get_conffiles()
		if conffiles:
			with catch_stdout(self.logger):
				handler_commit(conffiles)

	def _get_local_archive(self, app_cache):
		fname = os.path.join(LOCAL_ARCHIVE_DIR, app_cache.get_server_netloc(), app_cache.get_ucs_version(), 'all.tar.gz')
		if os.path.exists(fname):
			return fname

	def _extract_local_archive(self, app_cache):
		local_archive = self._get_local_archive(app_cache)
		if not local_archive:
			# Not my local_archive
			return False
		if any(not fname.startswith('.') for fname in os.listdir(app_cache.get_cache_dir())):
			# we already have a cache. our archive is just outdated...
			return False
		self.log('Filling the App Center file cache from our local archive %s!' % local_archive)
		try:
			archive = tarfile.open(local_archive, 'r:*')
		except (tarfile.TarError, IOError) as e:
			self.warn('Error while reading %s: %s' % (local_archive, e))
			return
		try:
			for member in archive.getmembers():
				filename = member.name
				if os.path.sep in filename:
					# just some paranoia
					continue
				self.debug('Extracting %s' % filename)
				archive.extract(filename, path=app_cache.get_cache_dir())
				self._files_downloaded[filename] = get_md5_from_file(os.path.join(app_cache.get_cache_dir(), filename))
		finally:
			archive.close()
		return True

	def _load_index_json(self, app_cache):
		index_json_gz_filename = os.path.join(app_cache.get_cache_dir(), '.index.json.gz')
		if not ucr_is_false('appcenter/index/verify'):
			detached_sig_path = index_json_gz_filename + '.gpg'
			(rc, gpg_error) = gpg_verify(index_json_gz_filename, detached_sig_path)
			if rc:
				if gpg_error:
					self.fatal(gpg_error)
				raise Abort('Signature verification for %s failed' % index_json_gz_filename)
		with gzip_open(index_json_gz_filename, 'rb') as fgzip:
			content = fgzip.read()
			return loads(content)

	def _read_index_json(self, cache_dir, json_apps):
		files_to_download = []
		something_changed = False
		files_in_json_file = []
		for appname, appinfo in json_apps.iteritems():
			for appfile, appfileinfo in appinfo.iteritems():
				filename = os.path.basename('%s.%s' % (appname, appfile))
				remote_md5sum = appfileinfo['md5']
				remote_url = appfileinfo['url']
				# compare with local cache
				cached_filename = os.path.join(cache_dir, filename)
				files_in_json_file.append(cached_filename)
				local_md5sum = get_md5_from_file(cached_filename)
				if remote_md5sum != local_md5sum:
					# ask to re-download this file
					files_to_download.append((remote_url, filename, remote_md5sum))
					something_changed = True
		# remove those files that apparently do not exist on server anymore
		for cached_filename in glob(os.path.join(cache_dir, '*')):
			if os.path.basename(cached_filename).startswith('.'):
				continue
			if os.path.isdir(cached_filename):
				continue
			if cached_filename not in files_in_json_file:
				self.log('Deleting obsolete %s' % cached_filename)
				something_changed = True
				os.unlink(cached_filename)
		return files_to_download, something_changed
