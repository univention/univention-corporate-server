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
from argparse import SUPPRESS
import zlib
from urlparse import urljoin
from glob import glob
from gzip import open as gzip_open
from json import loads
from urllib2 import Request, HTTPError

from univention.appcenter.app import AppManager, CACHE_DIR, LOCAL_ARCHIVE
from univention.appcenter.actions import UniventionAppAction, Abort, possible_network_error
from univention.appcenter.utils import urlopen, get_md5_from_file, gpg_verify, container_mode
from univention.appcenter.ucr import ucr_get, ucr_save, ucr_is_false


class Update(UniventionAppAction):

	'''Updates the list of all available applications by asking the App Center server'''
	help = 'Updates the list of apps'

	def __init__(self):
		super(Update, self).__init__()
		self._cache_dir = None
		self._ucs_version = None
		self._appcenter_server = None
		self._files_downloaded = dict()

	def setup_parser(self, parser):
		parser.add_argument('--ucs-version', help=SUPPRESS)
		parser.add_argument('--appcenter-server', help=SUPPRESS)
		parser.add_argument('--cache-dir', help=SUPPRESS)

	def main(self, args):
		self._cache_dir = args.cache_dir
		self._ucs_version = args.ucs_version
		self._appcenter_server = args.appcenter_server
		something_changed_locally = self._extract_local_archive()
		self._download_supra_files()
		something_changed_remotely = self._extract_remote_archive()
		if something_changed_locally or something_changed_remotely:
			AppManager.clear_cache()
			for app in AppManager.get_all_locally_installed_apps():
				if AppManager.find_candidate(app):
					ucr_save({app.ucr_upgrade_key: 'yes'})
			self._update_local_files()

	@possible_network_error
	def _download_supra_files(self):
		present_etags = {}
		etags_file = os.path.join(self._get_cache_dir(), '.etags')
		if os.path.exists(etags_file):
			with open(etags_file, 'rb') as f:
				for line in f:
					try:
						fname, etag = line.split('\t')
					except ValueError:
						pass
					else:
						present_etags[fname] = etag.rstrip('\n')

		def _download_supra_file(filename, version_specific):
			if version_specific:
				url = urljoin('%s/' % self._get_metainf_url(), '%s' % filename)
			else:
				url = urljoin('%s/' % self._get_metainf_url(), '../%s' % filename)
			self.log('Downloading "%s"...' % url)
			headers = {}
			if filename in present_etags:
				headers['If-None-Match'] = present_etags[filename]
			request = Request(url, headers=headers)
			try:
				response = urlopen(request)
			except HTTPError as exc:
				if exc.getcode() == 304:
					self.debug('  ... Not Modified')
					return
				raise
			etag = response.headers.get('etag')
			present_etags[filename] = etag
			content = response.read()
			with open(os.path.join(self._get_cache_dir(), '.%s' % filename), 'wb') as f:
				f.write(content)
			AppManager.clear_cache()

		_download_supra_file('index.json.gz', version_specific=True)
		if not ucr_is_false('appcenter/index/verify'):
			_download_supra_file('index.json.gz.gpg', version_specific=True)
			_download_supra_file('all.tar.gpg', version_specific=True)
		_download_supra_file('categories.ini', version_specific=False)
		_download_supra_file('rating.ini', version_specific=False)
		_download_supra_file('license_types.ini', version_specific=False)
		with open(etags_file, 'wb') as f:
			for fname, etag in present_etags.iteritems():
				f.write('%s\t%s\n' % (fname, etag))

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
		for app in AppManager.get_all_locally_installed_apps():
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

	def _extract_local_archive(self):
		if any(not fname.startswith('.') for fname in os.listdir(self._get_cache_dir())):
			# we already have a cache. our archive is just outdated...
			return False
		if not os.path.exists(LOCAL_ARCHIVE):
			# for some reason the archive is not there. should only happen when deleted intentionally...
			return False
		self.log('Filling the App Center file cache from our local archive!')
		try:
			with gzip_open(LOCAL_ARCHIVE) as zipped_file:
				archive_content = zipped_file.read()
				with open(os.path.join(self._get_cache_dir(), '.all.tar'), 'wb') as extracted_file:
					extracted_file.write(archive_content)
		except (zlib.error, EnvironmentError) as exc:
			self.warn('Error while reading %s: %s' % (LOCAL_ARCHIVE, exc))
			return
		else:
			self._extract_archive()
		return True

	def _extract_remote_archive(self):
		all_tar_file = os.path.join(self._get_cache_dir(), '.all.tar')
		old_md5 = get_md5_from_file(all_tar_file)
		url = urljoin('%s/' % self._get_metainf_url(), 'all.tar.zsync')
		if url.startswith('https'):
			url = 'http://%s' % url[8:]
		self.log('Downloading "%s"...' % url)
		if self._subprocess(['zsync', url, '-q', '-o', all_tar_file]).returncode:
			raise Abort('Failed to download "%s"' % url)
		self._verify_file(all_tar_file)
		new_md5 = get_md5_from_file(all_tar_file)
		if old_md5 != new_md5:
			self._extract_archive()
			return True

	def _extract_archive(self):
		for fname in glob(os.path.join(self._get_cache_dir(), '*')):
			try:
				os.unlink(fname)
			except EnvironmentError as exc:
				self.warn('Cannot delete %s: %s' % (fname, exc))
		all_tar_file = os.path.join(self._get_cache_dir(), '.all.tar')
		if self._subprocess(['tar', '-C', self._get_cache_dir(), '-xf', all_tar_file]).returncode:
			raise Abort('Failed to unpack "%s"' % all_tar_file)

	def _verify_file(self, fname):
		if not ucr_is_false('appcenter/index/verify'):
			detached_sig_path = fname + '.gpg'
			(rc, gpg_error) = gpg_verify(fname, detached_sig_path)
			if rc:
				if gpg_error:
					self.fatal(gpg_error)
				raise Abort('Signature verification for %s failed' % fname)

	def _get_metainf_url(self):
		return '%s/meta-inf/%s' % (self._get_server(), self._get_ucs_version())

	def _get_cache_dir(self):
		if self._cache_dir is None:
			self._cache_dir = CACHE_DIR
		return self._cache_dir

	def _get_server(self):
		if self._appcenter_server is None:
			server = ucr_get('repository/app_center/server', 'appcenter.software-univention.de')
			self._appcenter_server = server
		if not self._appcenter_server.startswith('http'):
			self._appcenter_server = 'https://%s' % self._appcenter_server
		return self._appcenter_server

	# needed in docker.py
	def _load_index_json(self):
		index_json_gz_filename = os.path.join(self._get_cache_dir(), '.index.json.gz')
		self._verify_file(index_json_gz_filename)
		with gzip_open(index_json_gz_filename, 'rb') as fgzip:
			content = fgzip.read()
			return loads(content)

	def _get_ucs_version(self):
		'''Returns the current UCS version (ucr get version/version).
		During a release update of UCS, returns the target version instead
		because the new ini files should now be used in any script'''
		if self._ucs_version is None:
			version = None
			try:
				still_running = False
				next_version = None
				status_file = '/var/lib/univention-updater/univention-updater.status'
				if os.path.exists(status_file):
					with open(status_file, 'r') as status:
						for line in status:
							line = line.strip()
							key, value = line.split('=', 1)
							if key == 'status':
								still_running = value == 'RUNNING'
							elif key == 'next_version':
								next_version = value.split('-')[0]
						if still_running and next_version:
							version = next_version
			except (IOError, ValueError) as exc:
				self.warn('Could not parse univention-updater.status: %s' % exc)
			if version is None:
				version = ucr_get('version/version', '')
			self.debug('UCS Version is %r' % version)
			self._ucs_version = version
		return self._ucs_version
