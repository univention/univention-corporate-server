#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for updating the list of available apps
#
# Copyright 2015 Univention GmbH
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
from math import ceil
from argparse import SUPPRESS
import time
from threading import Thread
from urlparse import urljoin
from glob import glob
from StringIO import StringIO
from gzip import GzipFile
from json import loads
import tarfile
from urlparse import urlsplit
import urllib2

from univention.config_registry import ConfigRegistry
from univention.config_registry.frontend import ucr_update

from univention.appcenter.app import AppManager, CACHE_DIR, LOCAL_ARCHIVE
from univention.appcenter.actions import UniventionAppAction, possible_network_error
from univention.appcenter.utils import urlopen, get_md5_from_file, gpg_verify


class Update(UniventionAppAction):
	'''Updates the list of all available applications by asking the App Center server'''
	help = 'Updates the list of apps'

	def __init__(self):
		super(Update, self).__init__()
		self._ucs_version = None

	def setup_parser(self, parser):
		parser.add_argument('--ucs-version', help=SUPPRESS)
		parser.add_argument('--appcenter-server', help=SUPPRESS)

	def main(self, args):
		self._ucs_version = args.ucs_version
		self._appcenter_server = args.appcenter_server
		something_changed_locally = self._extract_local_archive()
		self._download_supra_files()
		json_apps = self._load_index_json()
		files_to_download, something_changed_remotely = self._read_index_json(json_apps)
		num_files_to_be_downloaded = len(files_to_download)
		self.log('%d file(s) are new' % num_files_to_be_downloaded)
		num_files_threshold = 5
		if num_files_to_be_downloaded > num_files_threshold:
			files_to_download = self._download_archive(files_to_download)
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
			thread = Thread(target=self._download_directly, args=(files_to_download_in_thread,))
			thread.start()
			threads.append(thread)
			time.sleep(0.1)  # wait 100 milliseconds so that not all threads start at the same time
		for thread in threads:
			thread.join()
		if something_changed_locally or something_changed_remotely:
			ucr = ConfigRegistry()
			AppManager.clear_cache()
			for app in AppManager.get_all_locally_installed_apps():
				if AppManager.find(app.id, latest=True) > app:
					ucr_update(ucr, {app.ucr_upgrade_key: 'yes'})
			self._update_local_files()

	@possible_network_error
	def _download_supra_files(self):
		def _download_supra_file(filename):
			url = urljoin('%s/' % self._get_metainf_url(), '../%s' % filename)
			self.log('Downloading "%s"...' % url)
			categories = urlopen(url).read()
			with open(os.path.join(CACHE_DIR, '.%s' % filename), 'wb') as f:
				f.write(categories)
		_download_supra_file('categories.ini')
		_download_supra_file('rating.ini')

	@possible_network_error
	def _download_archive(self, files_to_download):
		# a lot of files to download? Do not download them
		#   one at a time. Download the full archive!
		files_still_to_download = []
		archive_url = urljoin('%s/' % self._get_metainf_url(), 'all.tar.gz')
		try:
			self.log('Downloading "%s"...' % archive_url)
			# for some reason saving this in memory is flawed.
			# using StringIO and GZip objects has issues
			# with "empty" files in tar.gz archives, i.e.
			# doublets like .png logos
			with open(os.path.join(CACHE_DIR, 'all.tar.gz'), 'wb') as f:
				f.write(urlopen(archive_url).read())
			archive = tarfile.open(f.name, 'r:*')
			try:
				for filename_url, filename, remote_md5sum in files_to_download:
					self.debug('Extracting %s' % filename)
					try:
						archive.extract(filename, path=CACHE_DIR)
						local_md5sum = get_md5_from_file(os.path.join(CACHE_DIR, filename))
						if local_md5sum != remote_md5sum:
							self.warn('Checksum for %s should be %r but was %r! Download manually' % (filename, remote_md5sum, local_md5sum))
							raise KeyError(filename)
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
	def _download_directly(self, files_to_download):
		for filename_url, filename, remote_md5sum in files_to_download:
			# dont forget to quote: 'foo & bar.ini' -> 'foo%20&%20bar.ini'
			# but dont quote https:// -> https%3A//
			path = urllib2.quote(urlsplit(filename_url).path)
			filename_url = '%s%s' % (self._get_server(), path)

			cached_filename = os.path.join(CACHE_DIR, filename)

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

	#def _process_new_file(self, filename):
	#	self.log('Installing %s' % os.path.basename(filename))
	#	component, ext = os.path.splitext(os.path.basename(filename))
	#	ret = None
	#	if hasattr(self, '_process_new_file_%s' % ext):
	#		ini_file = os.path.join(CACHE_DIR, '%s.ini' % component)
	#		try:
	#			local_app = App.from_ini(ini_file)
	#		except IOError:
	#			self.log('Could not find a previously existing app with component %s' % component)
	#		else:
	#			ret = self.getattr('_process_new_file_%s' % ext)(filename, local_app)
	#	if ret != 'reject':
	#		shutil.copy2(filename, CACHE_DIR)
	#	return ret

	#def _process_new_file_ini(self, filename, local_app):
	#	if local_app.is_installed():
	#		new_app = App.from_ini(filename)
	#		if new_app:
	#			if new_app.component_id == local_app.component_id:
	#				pass
	#				#register = get_action('register')()
	#				#register._register_app(new_app)
	#		else:
	#			return 'reject'
	#	else:
	#		new_app = App.from_ini(filename)
	#		if new_app:
	#			local_app = AppManager.find(new_app.id)
	#			if local_app.is_installed() and local_app < new_app:
	#				ucr = ConfigRegistry()
	#				ucr_update(ucr, {local_app.ucr_upgrade_key: 'yes'})
	#		else:
	#			return 'reject'

	#def _process_new_file_inst(self, filename, local_app):
	#	if local_app.is_installed():
	#		shutil.copy2(filename, JOINSCRIPT_DIR)

	#def _process_new_file_uinst(self, filename, local_app):
	#	uinst_filename = self._get_joinscript_path(local_app, unjoin=True)
	#	if os.path.exists(uinst_filename):
	#		shutil.copy2(filename, uinst_filename)

	def _update_local_files(self):
		# overwritten when UMC is installed
		pass

	def _extract_local_archive(self):
		if os.listdir(CACHE_DIR):
			# we already have a cache. our archive is just outdated...
			return False
		if not os.path.exists(LOCAL_ARCHIVE):
			# for some reason the archive is not there. should only happen when deleted intentionally...
			return False
		self.log('Filling the App Center file cache from our local archive!')
		try:
			archive = tarfile.open(LOCAL_ARCHIVE, 'r:*')
		except (tarfile.TarError, IOError) as e:
			self.warn('Error while reading %s: %s' % (LOCAL_ARCHIVE, e))
			return
		try:
			for member in archive.getmembers():
				filename = member.name
				if os.path.sep in filename:
					# just some paranoia
					continue
				self.debug('Extracting %s' % filename)
				archive.extract(filename, path=CACHE_DIR)
		finally:
			self._update_local_files()
			archive.close()
		return True

	def _get_metainf_url(self):
		return '%s/meta-inf/%s' % (self._get_server(), self._get_ucs_version())

	def _get_server(self):
		if self._appcenter_server is None:
			ucr = ConfigRegistry()
			ucr.load()
			server = ucr.get('repository/app_center/server', 'appcenter.software-univention.de')
			self._appcenter_server = server
		if not self._appcenter_server.startswith('http'):
			self._appcenter_server = 'https://%s' % self._appcenter_server
		return self._appcenter_server

	@possible_network_error
	def _load_index_json(self):
		index_json_gz_filename = 'index.json.gz'
		detached_sig_filename = None

		ucr = ConfigRegistry()
		ucr.load()
		if not ucr.is_false('appcenter/index/verify'):
			detached_sig_filename = index_json_gz_filename + '.gpg'

			sig_url = urljoin('%s/' % self._get_metainf_url(), detached_sig_filename)
			self.log('Downloading "%s"...' % sig_url)
			detached_sig = urlopen(sig_url).read()
			detached_sig_path = os.path.join(CACHE_DIR, detached_sig_filename)
			with open(detached_sig_path, 'wb') as f:
				f.write(detached_sig)

		json_url = urljoin('%s/' % self._get_metainf_url(), index_json_gz_filename)
		self.log('Downloading "%s"...' % json_url)
		index_json_gz = urlopen(json_url).read()

		if detached_sig_filename:
			(rc, gpg_error) = gpg_verify("-", detached_sig_path, content=index_json_gz)
			if rc:
				self.fatal('Signature verification for %s failed' % (index_json_gz_filename,))
				if gpg_error:
					self.fatal(gpg_error)

		index_json_gz_path = os.path.join(CACHE_DIR, index_json_gz_filename)
		with open(index_json_gz_path, 'wb') as f:
			f.write(index_json_gz)

		zipped = StringIO(index_json_gz)
		content = GzipFile(mode='rb', fileobj=zipped).read()
		return loads(content)

	def _read_index_json(self, json_apps):
		files_to_download = []
		something_changed = False
		files_in_json_file = []
		for appname, appinfo in json_apps.iteritems():
			for appfile, appfileinfo in appinfo.iteritems():
				filename = os.path.basename('%s.%s' % (appname, appfile))
				remote_md5sum = appfileinfo['md5']
				remote_url = appfileinfo['url']
				# compare with local cache
				cached_filename = os.path.join(CACHE_DIR, filename)
				files_in_json_file.append(cached_filename)
				local_md5sum = get_md5_from_file(cached_filename)
				if remote_md5sum != local_md5sum:
					# ask to re-download this file
					files_to_download.append((remote_url, filename, remote_md5sum))
					something_changed = True
		for index_filename in ('index.json.gz', 'index.json.gz.gpg'):
			files_in_json_file.append(os.path.join(CACHE_DIR, index_filename))
		# remove those files that apparently do not exist on server anymore
		for cached_filename in glob(os.path.join(CACHE_DIR, '*')):
			if cached_filename not in files_in_json_file:
				self.log('Deleting obsolete %s' % cached_filename)
				something_changed = True
				os.unlink(cached_filename)
		return files_to_download, something_changed

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
				ucr = ConfigRegistry()
				ucr.load()
				version = ucr.get('version/version', '')
			self.debug('UCS Version is %r' % version)
			self._ucs_version = version
		return self._ucs_version
