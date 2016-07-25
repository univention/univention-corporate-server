#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention App Center
#  univention-app module for working with the Univention Test App Center
#
# Copyright 2016 Univention GmbH
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

import json
import re
import os.path
from subprocess import Popen, PIPE
from argparse import SUPPRESS, REMAINDER
from tempfile import NamedTemporaryFile
from urllib2 import HTTPError, URLError

from univention.appcenter.actions import UniventionAppAction, get_action, Abort
from univention.appcenter.actions.credentials import CredentialsAction
from univention.appcenter.ucr import ucr_save
from univention.appcenter.utils import urlopen


class DevUseTestAppcenter(UniventionAppAction):
	'''Use the Test App Center'''
	help = 'Uses the Apps in the Test App Center. Used for testing Apps not yet published.'

	def setup_parser(self, parser):
		super(DevUseTestAppcenter, self).setup_parser(parser)
		host_group = parser.add_mutually_exclusive_group()
		host_group.add_argument('--appcenter-host', default='appcenter-test.software-univention.de', help='The hostname of the new App Center. Default: %(default)s')
		revert_group = parser.add_mutually_exclusive_group()
		revert_group.add_argument('--revert', action='store_true', help='Reverts the changes of a previous dev-use-test-appcenter')

	def main(self, args):
		if args.revert:
			ucr_save({'repository/app_center/server': 'appcenter.software-univention.de', 'update/secure_apt': 'yes', 'appcenter/index/verify': 'yes'})
		else:
			ucr_save({'repository/app_center/server': args.appcenter_host, 'update/secure_apt': 'no', 'appcenter/index/verify': 'no'})
		update = get_action('update')
		update.call()


class SelfserviceAction(CredentialsAction):
	API_LEVEL = 1

	def __init__(self):
		super(SelfserviceAction, self).__init__()
		self._cookiejar = None

	def setup_parser(self, parser):
		try:
			with open(os.path.expanduser('~/univention-appcenter-user')) as f:
				username = f.read().strip()
		except EnvironmentError:
			username = None
		pwdfile = os.path.expanduser('~/univention-appcenter-pwd')
		if not os.path.exists(pwdfile):
			pwdfile = None
		parser.add_argument('--noninteractive', action='store_true', help='Do not prompt for anything, just agree or skip')
		parser.add_argument('--username', default=username, help='The username used for registering the app. Default: %(default)s')
		parser.add_argument('--pwdfile', default=pwdfile, help='Filename containing the password for registering the app. See --username')
		parser.add_argument('--password', help=SUPPRESS)
		parser.add_argument('--server', default='selfservice.software-univention.de', help='The server to talk to')

	def _get_result(self, result):
		try:
			if result['status'] != 200:
				raise KeyError('result')
			return result['result']
		except KeyError:
			raise Abort('Unrecoverable result: %r' % result)

	def _login(self, args):
		username = self._get_username(args)
		password = self._get_password(args)
		self._cookiejar = NamedTemporaryFile()
		result = self.curl(args, 'auth', username=username, password=password)
		self._get_result(result)
		result = self.command(args, 'api')
		remote_api_level = self._get_result(result)
		if remote_api_level != self.API_LEVEL:
			raise Abort('The Self Service has been updated (LEVEL=%s). Please update your script (LEVEL=%s)' % (remote_api_level, self.API_LEVEL))

	def curl(self, args, path, _command=False, **kwargs):
		uri = 'https://%s/univention-management-console/%s' % (args.server, path)
		args = []
		for key, value in kwargs.iteritems():
			if _command:
				args.append('-d')
			else:
				args.append('-F')
			args.append('%s=%s' % (key, value))
		self.log('Curling %s' % uri)
		args = ['curl', '--cookie', self._cookiejar.name, '--cookie-jar', self._cookiejar.name, '-H', 'X-Requested-With: XmlHttpRequest', '-H', 'Accept: application/json; q=1'] + args + [uri]
		process = Popen(args, stdout=PIPE, stderr=PIPE)
		out, err = process.communicate()
		try:
			return json.loads(out)
		except ValueError:
			self.fatal('No JSON found. This looks like a server error (e.g., Apache in front of Univention Management Console)')
			self.log(out)
			raise Abort('Unrecoverable Response')

	def command(self, args, command, **kwargs):
		if not self._cookiejar:
			self._login(args)
		return self.curl(args, 'command/appcenter-selfservice/%s' % command, _command=True, **kwargs)

	def upload(self, args, **kwargs):
		if not self._cookiejar:
			self._login(args)
		return self.curl(args, 'upload/appcenter-selfservice/upload', **kwargs)


class SelfserviceAppAction(SelfserviceAction):
	def setup_parser(self, parser):
		super(SelfserviceAppAction, self).setup_parser(parser)
		parser.add_argument('ucs_version', help='UCS version of the App')
		parser.add_argument('app', help='The App ID')

	def _find_all_app_versions(self, args):
		return self._get_result(self.command(args, 'expand', app_id=args.app))

	def _find_app_versions(self, args):
		versions = self._find_all_app_versions(args)
		return [version for version in versions if version['ucs_version'] == args.ucs_version]


class SelfserviceComponentAction(SelfserviceAction):
	def setup_parser(self, parser):
		super(SelfserviceComponentAction, self).setup_parser(parser)
		parser.add_argument('ucs_version', help='UCS version of the App version')
		parser.add_argument('component', help='The component ID of the App version. Find out with univention-app dev-test-appcenter-status $appid')


class DevList(SelfserviceAction):
	'''List all Apps'''
	help = 'Lists all Apps'

	def main(self, args):
		result = self._get_result(self.command(args, 'query'))
		vendor_ids = set([app['vendor_id'] for app in result])
		for vendor_id in sorted(vendor_ids):
			self.log('')
			self.log(vendor_id)
			apps = [app for app in result if app['vendor_id'] == vendor_id]
			for app in apps:
				self.log('  %s' % app['id'])


class DevStatus(SelfserviceAppAction):
	'''Fetch status of an App'''
	help = 'Lists available versions, their status, etc. in the Selfservice'

	def setup_parser(self, parser):
		super(SelfserviceAppAction, self).setup_parser(parser)
		#parser.add_argument('ucs_version', help='UCS version of the App')
		parser.add_argument('app', help='The App ID')

	def main(self, args):
		apps = self._find_all_app_versions(args)
		for app_version in apps:
			self.log('')
			testappcenter_status = 'Out'
			if app_version.get('in_test_appcenter'):
				testappcenter_status = 'In'
			appcenter_status = 'Out'
			if app_version.get('in_appcenter'):
				appcenter_status = 'In'
			self.log('Version %s' % app_version['version'])
			self.log('            UCS: %s' % app_version['ucs_version'])
			self.log('      COMPONENT: %s' % app_version['component_id'])
			self.log('  TESTAPPCENTER: %s' % testappcenter_status)
			self.log('       └── DIFF: %r' % app_version.get('local_changes_test_appcenter'))
			self.log('      APPCENTER: %s' % appcenter_status)
			self.log('       └── DIFF: %r' % app_version.get('local_changes_appcenter'))


class DevDownload(SelfserviceComponentAction):
	'''Download archive'''
	help = 'Downloads a full archive as found in the Test App Center. Already in a re-uploadable format.'

	def setup_parser(self, parser):
		super(DevDownload, self).setup_parser(parser)
		parser.add_argument('--include-packages', action='store_true', help='Also downloads all packages')

	def main(self, args):
		result = self.command(args, 'download_archive', ucs_version=args.ucs_version, component_id=args.component, include_packages=args.include_packages)
		tarname = self._get_result(result)['tarname']
		url = 'https://%s/univention-management-console/appcenter-selfservice/%s' % (args.server, tarname)
		self.log('Downloading "%s"...' % url)
		try:
			response = urlopen(url)
		except (URLError, HTTPError) as exc:
			raise Abort('Unable to download: %s' % exc)
		else:
			fname = '%s.tar.gz' % args.component
			with open(fname, 'wb') as f:
				f.write(response.read())
			self.log('Saved the archive to %s' % fname)
			self.log('We recommend using this archive for future uploads. Update the ini file (Version!), replace the existing packages with your newest ones all within this archive and do: "univention-app dev-new-version-upload-publish %s APPID %s"' % (args.ucs_version, fname))
			self.log('Do not forget to re-download the archive each time you are about to upload a new version to not miss possible changes made by your co-workers or Univention!')


class _DevNewVersion(object):
	def new_version(self, args):
		app = self._find_app_versions(args)[-1]
		new_ucs_version = args.new_ucs_version or args.ucs_version
		new_app_version = args.new_app_version or app['version']
		if new_ucs_version == args.ucs_version and new_app_version == app['version']:
			match = re.search(r'(.*) ucs-(\d+)$', new_app_version)
			if match:
				plain_version, ucs_part = match.groups()
				new_app_version = '%s ucs-%d' % (plain_version, int(ucs_part) + 1)
			else:
				new_app_version += ' ucs-1'
		self.log('Copying UCS %s\'s %s to UCS %s as Version=%s. (Version can be changed later)' % (app['ucs_version'], app['component_id'], new_ucs_version, new_app_version))
		result = self.command(args, 'copy', ucs_version=app['ucs_version'], component_id=app['component_id'], new_ucs_version=new_ucs_version, new_app_version=new_app_version)
		new_component_id = self._get_result(result)
		self.log('New component for UCS %s:' % new_ucs_version)
		self.log('  %s' % (new_component_id))
		return new_component_id


class DevNewVersion(SelfserviceAppAction, _DevNewVersion):
	'''Copy an existing App to a new UCS version or to become a new App version.'''
	help = 'Copy an App'

	def setup_parser(self, parser):
		super(DevNewVersion, self).setup_parser(parser)
		parser.add_argument('--new-ucs-version', help='If given, the App is copied to another UCS version.')
		parser.add_argument('--new-app-version', help='If given, the App is copied and forms a new version within the same UCS release.')

	def main(self, args):
		return self.new_version(args)


class _DevUpload(object):
	def upload_files(self, args):
		clear = str(args.clear).lower()
		for upload in args.uploads:
			try:
				ftype, fname = upload.split('=', 1)
			except ValueError:
				fname = upload
				ftype = upload
				basename, ext = os.path.splitext(upload)
				if ext:
					ftype = ext[1:]
					if ftype == 'tgz':
						ftype = 'tar.gz'
					if ext == '.gz':
						basename, ext = os.path.splitext(basename)
						if ext == '.tar':
							ftype = 'tar.gz'
			fname = os.path.abspath(fname)
			if not os.path.exists(fname):
				self.warn('%s does not exist! Skipping...' % fname)
				continue
			self.log('Uploading %s: %s' % (ftype, fname))
			result = self.upload(args, ucs_version=args.ucs_version, component_id=args.component, type=ftype, clear=clear, filename='@%s' % fname)
			self._get_result(result)
		self.log('Finished uploading. You may want to call \'univention-app dev-publish "%s" "%s"\' now.' % (args.ucs_version, args.component))


class DevUpload(SelfserviceComponentAction, _DevUpload):
	'''Upload an App'''
	help = 'Uploads an App to the Univention Test App Center'

	def setup_parser(self, parser):
		super(DevUpload, self).setup_parser(parser)
		parser.add_argument('--clear', action='store_true', help='Clears all packages with the same name (but a different version) as the uploaded packages. Only works for "deb" and "tar.gz" uploads')
		parser.add_argument('uploads', nargs=REMAINDER, help='List of files to upload. They need to be named after their type, or have it as extension or be preceeded by the file type. Example: "README_EN"; "myapp.ini"; "app.tar.gz"; "screenshot=my-screenshot.png"')

	def main(self, args):
		return self.upload_files(args)


class _DevPublish(object):
	def publish(self, args):
		self._get_result(self.command(args, 'publish_test_appcenter', ucs_version=args.ucs_version, component_id=args.component))
		self.log('Published %s in UCS %s' % (args.component, args.ucs_version))
		self.log('You may now test the App using "univention-app dev-use-test-appcenter"')
		self.log('After your successful tests, please inform us at appcenter@univention.de. We will run our test suite. Note that we only test UCS services and whether they are negatively impacted by the App; we do not test the functionality of the App itself!')


class DevPublish(SelfserviceComponentAction, _DevPublish):
	'''Publish an App'''
	help = 'Publishes an App to the Univention Test App Center'

	def main(self, args):
		return self.publish(args)


class DevNewVersionUploadPublish(SelfserviceAppAction, _DevNewVersion, _DevUpload, _DevPublish):
	'''Add a new version, upload files to it, publish it'''
	help = 'All-in-one solution for consecutively calling univention dev-new-version; univention-app dev-upload; univention-app dev-publish'

	def setup_parser(self, parser):
		super(DevNewVersionUploadPublish, self).setup_parser(parser)
		parser.add_argument('--new-ucs-version', help='If given, the App is copied to another UCS version.')
		parser.add_argument('--new-app-version', help='If given, the App is copied and forms a new version within the same UCS release.')
		parser.add_argument('--clear', action='store_true', help='Clears all packages with the same name (but a different version) as the uploaded packages. Only works for "deb" and "tar.gz" uploads')
		parser.add_argument('uploads', nargs=REMAINDER, help='List of files to upload. They need to be named after their type, or have it as extension or be preceeded by the file type. Example: "README_EN"; "myapp.ini"; "app.tar.gz"; "screenshot=my-screenshot.png"')

	def main(self, args):
		new_component_id = self.new_version(args)
		args.component = new_component_id
		self.upload_files(args)
		self.publish(args)
