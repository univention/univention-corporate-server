#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Create JSON app center index file
#
# Copyright 2013-2019 Univention GmbH
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

import sys
import gzip
import tarfile
import os
import os.path
import urllib2
import base64
import socket
from hashlib import md5, sha256
from optparse import OptionParser
from json import dumps
from difflib import unified_diff
from glob import glob
from ConfigParser import ConfigParser

DOCKER_READ_USER_CRED = {
	'username': 'ucs',
	'password': 'readonly',
}


class FileInfo(object):

	def __init__(self, app, name, url, filename):
		self.name = name
		self.url = url
		self.filename = filename
		self.md5 = md5sum(filename)
		self.sha256 = sha256sum(filename)
		self.archive_filename = '%s.%s' % (app.name, name)


class DockerImageInfo(object):

	def __init__(self, name, url, content):
		self.name = name
		self.url = url
		self.sha256 = sha256(content).hexdigest()


class App(object):

	def __init__(self, name, ucs_version, meta_inf_dir, components_dir, server):
		self.name = name
		self.ucs_version = ucs_version
		self.meta_inf_dir = meta_inf_dir
		self.components_dir = components_dir
		if server.endswith('/'):
			server = server[:-1]
		self.server = server

	def get_metainf_url(self):
		return '%s/meta-inf/%s/' % (self.server, self.ucs_version)

	def get_repository_url(self):
		return '%s/univention-repository/%s/maintained/component/%s/' % (self.server, self.ucs_version, self.name)

	def _meta_url(self, filename):
		return urllib2.urlparse.urljoin(self.get_metainf_url(), filename)

	def _repository_url(self, filename):
		return urllib2.urlparse.urljoin(self.get_repository_url(), filename)

	def _components_dir(self, filename):
		return os.path.join(self.components_dir, self.name, filename)

	def _meta_inf_dir(self, filename):
		return os.path.join(self.meta_inf_dir, filename)

	def get_ini_file(self):
		return self._meta_inf_dir('%s.ini' % self.name)

	def get_ini_url(self):
		return self._meta_url('%s.ini' % self.name)

	def get_png_file(self):
		return self._meta_inf_dir('%s.png' % self.name)

	def get_png_url(self):
		return self._meta_url('%s.png' % self.name)

	def file_info(self, name, url, filename):
		return FileInfo(self, name, url, filename)

	def docker_image_info(self, name, url, content):
		return DockerImageInfo(name, url, content)

	def important_files(self):
		# Adding "special ini and png file
		for special_file in ['ini', 'png']:
			get_file_method = getattr(self, 'get_%s_file' % special_file.lower())
			get_url_method = getattr(self, 'get_%s_url' % special_file.lower())
			filename = get_file_method()
			url = get_url_method()
			if os.path.exists(filename):
				yield self.file_info(special_file, url, filename)

		# Adding files for docker
		for docker_file in [
			'attributes',
			'settings',
			'configure',
			'configure_host',
			'update_certificates',
			'setup',
			'store_data',
			'restore_data_before_setup',
			'restore_data_after_setup',
			'update_available',
			'update_packages',
			'update_release',
			'update_app_version',
			'univention-config-registry-variables',
			'schema',
			'preinst',
			'inst',
			'init',
			'prerm',
			'uinst',
			'env',
			'compose',
			'listener_trigger',
		]:
			for filename in glob(self._components_dir(docker_file)):
				basename = os.path.basename(filename)
				url = self._repository_url(basename)
				yield self.file_info(basename, url, filename)

		# Adding logo file
		config = ConfigParser()
		config.read(self.get_ini_file())
		if config.has_option('Application', 'Logo'):
			basename = config.get('Application', 'Logo')
			filename = self._meta_inf_dir(basename)
			url = self._meta_url(basename)
			yield self.file_info(basename, url, filename)

		# Adding LICENSE_AGREEMENT and localised versions like LICENSE_AGREEMENT_DE
		for readme_filename in glob(self._components_dir('LICENSE_AGREEMENT*')):
			basename = os.path.basename(readme_filename)
			url = self._repository_url(basename)
			yield self.file_info(basename, url, readme_filename)

		# Adding README, README_UPDATE, README_INSTALL, REAME_POST_UPDATE, README_POST_INSTALL
		#   and all the localised versions like README_DE and README_POST_INSTALL_EN (and even *_FR)
		for readme_filename in glob(self._components_dir('README*')):
			basename = os.path.basename(readme_filename)
			url = self._repository_url(basename)
			yield self.file_info(basename, url, readme_filename)

	def docker_images(self):
		# Adding manifest signature for docker
		config = ConfigParser()
		config.read(self.get_ini_file())
		if config.has_option('Application', 'DockerImage'):
			docker_image = config.get('Application', 'DockerImage')
			try:
				registry, image_name = docker_image.split('/', 1)
				try:
					socket.gethostbyname(registry)
				except socket.gaierror:
					registry = None
			except ValueError:
				image_name = docker_image
				registry = None

			if registry:
				docker_image_name_parts = image_name.split(':', 1)
				docker_image_repo = docker_image_name_parts[0]
				if len(docker_image_name_parts) > 1:
					docker_image_tag = docker_image_name_parts[1]
				else:
					docker_image_tag = 'latest'

				docker_url = 'https://%s/v2/%s/manifests/%s' % (registry, docker_image_repo, docker_image_tag)
				request = urllib2.Request(docker_url)
				base64string = base64.b64encode(DOCKER_READ_USER_CRED['username'] + ':' + DOCKER_READ_USER_CRED['password'])
				request.add_header("Authorization", "Basic %s" % base64string)
				try:
					response = urllib2.urlopen(request)
				except (urllib2.HTTPError, urllib2.URLError) as exc:
					print >> sys.stderr, 'Error fetching DockerImage manifest for %s' % (self.name,)
					print >> sys.stderr, 'from %s' % (docker_url,)
					print >> sys.stderr, str(exc)
					sys.exit(1)

				name = 'DockerImageManifestV2S1'
				docker_image_manifest = response.read()
				yield self.docker_image_info(name, docker_url, docker_image_manifest)

	def tar_files(self):
		for file_info in self.important_files():
			yield file_info.filename, file_info.archive_filename

	def to_index(self):
		index = {}
		for file_info in self.important_files():
			index[file_info.name] = {
				'url': file_info.url,
			}
			for hash_type in ('md5', 'sha256'):
				try:
					hash_value = getattr(file_info, hash_type)
					index[file_info.name][hash_type] = hash_value
				except AttributeError:
					pass
		for docker_image_info in self.docker_images():
			index['ini'][docker_image_info.name] = {
				'url': docker_image_info.url,
				'sha256': docker_image_info.sha256,
			}
		return index


def check_ini_file(filename):
	name, ext = os.path.splitext(os.path.basename(filename))
	if ext == '.ini':
		return name


def md5sum(filename):
	m = md5()
	with open(filename, 'r') as f:
		m.update(f.read())
		return m.hexdigest()


def sha256sum(filename):
	m = sha256()
	with open(filename, 'r') as f:
		m.update(f.read())
		return m.hexdigest()


if __name__ == '__main__':
	parser = OptionParser()
	parser.add_option("-u", "--ucs-version", dest="version", default="3.1",
			help="use UCS version VERSION (e.g. (and default) %default)", metavar="VERSION")
	parser.add_option("-d", "--directory", dest="directory", default=".",
			help="root directory where meta-inf and univention-repository lie", metavar="DIR")
	parser.add_option("-o", "--output", dest="output", default=None,
			help="write output to OUTPUTFILE. Defaults to stdout. If specified and not ending with .gz, .gz is added", metavar="OUTPUTFILE")
	parser.add_option("-t", "--tar", dest="archive", default=None,
			help="additionally add all files to tar archive TARFILE (not compressed)", metavar="TARFILE")
	parser.add_option("-a", "--ask", action="store_true", dest="ask", default=False,
			help="Diff between existing OUTPUTFILE and buffer. Overwrites if changes are confirmed (interactive! ... if any diff)")
	parser.add_option("-s", "--server", dest="appcenter", default="https://appcenter.software-univention.de/",
			help="external Univention App Center Server (defaults to %default. Another possibility may be https://appcenter-test.software-univention.de/ or http://appcenter.knut.univention.de/)", metavar="APPCENTER")

	(options, args) = parser.parse_args()
	root = options.directory
	ucs_version = options.version
	meta_inf_dir = os.path.join(root, 'meta-inf', ucs_version)
	components_dir = os.path.join(root, 'univention-repository', ucs_version, 'maintained', 'component')
	apps = {}
	archive = None
	if options.archive:
		archive = tarfile.open(options.archive, 'w')
	for root, dirs, files in os.walk(meta_inf_dir):
		for filename in files:
			appname = check_ini_file(filename)
			if not appname:
				continue
			app = App(appname, ucs_version, meta_inf_dir, components_dir, options.appcenter)
			apps[app.name] = app.to_index()
			if archive is not None:
				for filename_in_directory, filename_in_archive in app.tar_files():
					archive.add(filename_in_directory, filename_in_archive)
	if archive is not None:
		archive.close()
	out = dumps(apps, sort_keys=True, indent=4)
	if options.output:
		if not options.output.endswith('.gz'):
			options.output += '.gz'
		if options.ask:
			if os.path.exists(options.output):
				# with gzip.open() as f: is new in 2.7
				f = gzip.open(options.output, 'rb')
				old = f.read()
				f.close()
			else:
				old = ''
			old_format = ['%s\n' % line for line in old.splitlines()]
			out_format = ['%s\n' % line for line in out.splitlines()]
			if old_format != out_format:
				for line in unified_diff(old_format, out_format, fromfile=options.output, tofile='NEW'):
					sys.stdout.write(line)
				yes = raw_input('Overwrite [y/N]? ')
			else:
				yes = 'y'
		else:
			yes = 'y'
		if yes and yes[0].lower() == 'y':
			f = gzip.open(options.output, 'wb')
			f.write(out)
			f.close()
	else:
		print out
