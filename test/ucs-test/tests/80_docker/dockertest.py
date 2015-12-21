# -*- coding: utf-8 -*-
#
# UCS test
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

from univention.testing.strings import random_name, random_version
from univention.testing.debian_package import DebianPackage
from univention.testing.ucr import UCSTestConfigRegistry
from univention.config_registry import handler_set, ConfigRegistry
import os
import shutil
import subprocess
import urllib2


class UCSTest_Docker_Exception(Exception): pass
class UCSTest_Docker_LoginFailed(Exception): pass
class UCSTest_Docker_PullFailed(Exception): pass
class AppcenterMetainfAlreadyExists(Exception): pass
class AppcenterRepositoryAlreadyExists(Exception): pass
class UCSTest_DockerApp_InstallationFailed(Exception): pass
class UCSTest_DockerApp_UpdateFailed(Exception): pass
class UCSTest_DockerApp_UpgradeFailed(Exception): pass
class UCSTest_DockerApp_VerifyFailed(Exception): pass
class UCSTest_DockerApp_RemoveFailed(Exception): pass
class UCSTest_DockerApp_ModProxyFailed(Exception): pass


def docker_login(server='docker.software-univention.de'):
	ret = subprocess.call(['docker', 'login', '-e', 'foo@bar', '-u', 'ucs', '-p', 'readonly', server])
	if ret != 0:
		raise UCSTest_Docker_LoginFailed()


def docker_pull(image, server='docker.software-univention.de'):
	ret = install_docker_image('%s/%s' % (server, image))
	if ret != 0:
		raise UCSTest_Docker_PullFailed()

def docker_image_is_present(imgname):
	cmd = ['docker', 'inspect', imgname]
	with open('/dev/null', 'w') as devnull:
		p = subprocess.Popen(cmd, close_fds=True, stdout=devnull)
		p.wait()
		return p.returncode == 0

def remove_docker_image(imgname):
	cmd = ['docker', 'rmi', imgname]
	p = subprocess.Popen(cmd, close_fds=True)
	p.wait()
	return p.returncode == 0

def pull_docker_image(imgname):
	cmd = ['docker', 'pull', imgname]
	p = subprocess.Popen(cmd, close_fds=True)
	p.wait()
	return p.returncode == 0

def restart_docker():
	cmd = ['invoke-rc.d', 'docker', 'restart']
	p = subprocess.Popen(cmd, close_fds=True)
	p.wait()
	return p.returncode == 0

def get_app_name():
	""" returns a valid app name """
	return random_name()


def get_app_version():
	return random_version()


class App:
	def __init__(self, name, version, app_directory_suffix=None, package_name=None, build_package=True):
		self.app_name = name
		self.app_version = version

		if not app_directory_suffix:
			self.app_directory_suffix = random_version()
		else:
			self.app_directory_suffix = app_directory_suffix

		self.app_directory = '%s_%s' % (self.app_name, self.app_directory_suffix)

		if package_name:
			self.package_name = package_name
		else:
			self.package_name = get_app_name()

		self.package_version = '%s.%s' % (version,get_app_version())

		self.ucr = ConfigRegistry()
		self.ucr.load()

		if build_package:
			self.package = DebianPackage(name=self.package_name, version=self.package_version)
			self.package.build()
		else:
			self.package = None

		self.ini = {}

		self.ini['ID'] = self.app_name
		self.ini['Code'] = self.app_name[0:2]
		self.ini['Name'] = self.app_name
		self.ini['Version'] = self.app_version
		self.ini['NotifyVendor'] = False
		self.ini['Categories'] = 'System services'
		self.ini['Logo'] = '%s.svg' % self.app_name
		if self.package:
			self.ini['DefaultPackages'] = self.package_name
		self.ini['ServerRole'] = 'domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver'

		self.scripts = {}

		self.ucs_version = self.ucr.get('version/version')

		self.installed = False

		self.admin_user = self.ucr.get('tests/domainadmin/account').split(',')[0][len('uid='):]
		self.admin_pwdfile = self.ucr.get('tests/domainadmin/pwdfile')

	def set_ini_parameter(self, **kwargs):
		for key, value in kwargs.iteritems():
			self.ini[key] = value
		pass

	def add_to_local_appcenter(self):
		self._dump_ini()
		if self.package:
			self._copy_package()
		self._dump_scripts()

	def add_script(self, **kwargs):
		for key, value in kwargs.iteritems():
			self.scripts[key] = value

	def install(self):
		self._update()
		admin_user = self.ucr.get('tests/domainadmin/account').split(',')[0][len('uid='):]
		# ret = subprocess.call('univention-app install --noninteractive --do-not-revert --username=%s --pwdfile=%s %s' %
		cmd = 'univention-app install --noninteractive --username=%s --pwdfile=%s %s' % (admin_user, self.ucr.get('tests/domainadmin/pwdfile'), self.app_name)
		print cmd
		ret = subprocess.call(cmd, shell=True)
		if ret != 0:
			raise UCSTest_DockerApp_InstallationFailed()

		self.ucr.load()
		self.container_id = self.ucr.get('appcenter/apps/%s/container' % self.app_name)

		self.installed = True

	def _update(self):
		ret = subprocess.call(['univention-app', 'update'])
		if ret != 0:
			raise UCSTest_DockerApp_UpdateFailed()

	def upgrade(self):
		self._update()
		ret = subprocess.call('univention-app upgrade --noninteractive --username=%s --pwdfile=%s %s' %
					(self.admin_user, self.admin_pwdfile, self.app_name), shell=True)
		if ret != 0:
			raise UCSTest_DockerApp_UpgradeFailed()
		self.ucr.load()
		self.container_id = self.ucr.get('appcenter/apps/%s/container' % self.app_name)
		self.installed = True

	def verify(self, joined=True):
		ret = subprocess.call('univention-app status %s' % (self.app_name), shell=True)
		if ret != 0:
			raise UCSTest_DockerApp_VerifyFailed()

		if joined:
			ret = subprocess.call('docker exec %s univention-check-join-status' % self.container_id, stderr=subprocess.STDOUT, shell=True)
			if ret != 0:
				raise UCSTest_DockerApp_VerifyFailed()

	def uninstall(self):
		if self.installed:
			ret = subprocess.call('univention-app remove --noninteractive --username=%s --pwdfile=%s %s' %
						(self.admin_user, self.admin_pwdfile, self.app_name), shell=True)
			if ret != 0:
				raise UCSTest_DockerApp_RemoveFailed()

	def execute_command_in_container(self, cmd):
		print 'Execute: %s' % cmd
		return subprocess.check_output('docker exec %s %s' % (self.container_id, cmd), stderr=subprocess.STDOUT, shell=True)

	def remove(self):
		if self.package:
			self.package.remove()

	def _dump_ini(self):
		if not os.path.exists('/var/www/meta-inf/%s' % self.ucs_version):
			os.makedirs('/var/www/meta-inf/%s' % self.ucs_version)

		target = os.path.join('/var/www/meta-inf/%s' % self.ucs_version, '%s.ini' % self.app_directory)
		f = open(target, 'w')
		print 'Write ini file: %s' % target
		f.write('[Application]\n')
		print '[Application]'
		for key in self.ini.keys():
			f.write('%s: %s\n' % (key, self.ini[key]))
			print '%s: %s' % (key, self.ini[key])
		print
		f.close()
		svg = os.path.join('/var/www/meta-inf/%s' % self.ucs_version, self.ini.get('Logo'))
		f = open(svg, 'w')
		f.write(get_dummy_svg())
		f.close()

	def _dump_scripts(self):
		for script in self.scripts.keys():
			comp_path = os.path.join('/var/www/univention-repository/%s/maintained/component' % self.ucs_version, '%s' % self.app_directory)
			if not os.path.exists(comp_path):
				os.makedirs(comp_path)
			target = os.path.join(comp_path, script)

			print 'Create %s' % target
			print self.scripts[script]

			f = open(target, 'w')
			f.write(self.scripts[script])
			f.close()

	def _copy_package(self):
		target = os.path.join('/var/www/univention-repository/%s/maintained/component' % self.ucs_version, '%s/all' % self.app_directory)
		os.makedirs(target)
		shutil.copy(self.package.get_binary_name(), target)
		subprocess.call('''
			cd /var/www/univention-repository/%(version)s/maintained/component;
			apt-ftparchive packages %(app)s/all >%(app)s/all/Packages;
			gzip -c %(app)s/all/Packages >%(app)s/all/Packages.gz
		''' % {'version': self.ucs_version, 'app': self.app_directory}, shell=True)

	def create_basic_modproxy_settings(self):
		self.add_script(setup='''#!/bin/bash
set -x -e
eval "$(ucr shell)"
if [ "$version_version" = 4.0 ]; then
	ucr set repository/online/server="$(echo $repository_online_server | sed -e 's|.*//\(.*\)|\\1|')"
fi
univention-install --yes univention-apache
mkdir /var/www/%(app_name)s
echo "TEST-%(app_name)s" >>/var/www/%(app_name)s/index.txt
/usr/share/univention-docker-container-mode/setup "$@"
''' % {'app_name': self.app_name})

	def verify_basic_modproxy_settings(self):
		fqdn = '%s.%s' % (self.ucr['hostname'], self.ucr['domainname'])
		test_string = 'TEST-%s\n' % self.app_name

		response = urllib2.urlopen('http://%s/%s/index.txt' % (fqdn, self.app_name))
		html = response.read()
		if html != test_string:
			raise UCSTest_DockerApp_ModProxyFailed(Exception)

		response = urllib2.urlopen('https://%s/%s/index.txt' % (fqdn, self.app_name))
		html = response.read()
		if html != test_string:
			raise UCSTest_DockerApp_ModProxyFailed(Exception)




class Appcenter:
	def __init__(self, version=None):
		self.meta_inf_created = False
		self.univention_repository_created = False

		self.ucr = UCSTestConfigRegistry()
		self.ucr.load()

		if os.path.exists('/var/www/meta-inf'):
			print 'ERROR: /var/www/meta-inf already exists'
			raise AppcenterMetainfAlreadyExists()
		if os.path.exists('/var/www/univention-repository'):
			print 'ERROR: /var/www/univention-repository already exists'
			raise AppcenterRepositoryAlreadyExists()

		if not version:
			version = self.ucr.get('version/version')

		self.add_ucs_version_to_appcenter(version)

	def add_ucs_version_to_appcenter(self, version):

		if not os.path.exists('/var/www/meta-inf'):
			os.makedirs('/var/www/meta-inf', 0755)
			self.meta_inf_created = True

		if not os.path.exists('/var/www/univention-repository'):
			os.makedirs('/var/www/univention-repository', 0755)
			self.univention_repository_created = True

		os.makedirs('/var/www/univention-repository/%s/maintained/component' % version)
		os.makedirs('/var/www/meta-inf/%s' % version)

		if not os.path.exists('/var/www/meta-inf/categories.ini'):
			f = open('/var/www/meta-inf/categories.ini', 'w')
			f.write('''[de]
Administration=Administration
Business=Business
Collaboration=Collaboration
Education=Schule
System services=Systemdienste
UCS components=UCS-Komponenten
Virtualization=Virtualisierung''')
			f.close()
			f = open('/var/www/meta-inf/rating.ini', 'w')
			f.write('# rating stuff\n')
			f.close()

		handler_set([
			'update/secure_apt=no',
			'appcenter/index/verify=false',
			'repository/app_center/server=%s.%s' % (self.ucr['hostname'], self.ucr['domainname'])
		])

	def update(self):
		for vv in os.listdir('/var/www/meta-inf/'):
			directory = os.path.join('/var/www/meta-inf/', vv)
			if not os.path.isdir(directory):
				continue
			print 'create_appcenter_json.py for %s' % vv
			subprocess.call('create_appcenter_json.py -u %(version)s -d /var/www -o /var/www/meta-inf/%(version)s/index.json.gz -s http://%(fqdn)s' %
				 {'version': vv, 'fqdn': '%s.%s' % (self.ucr['hostname'], self.ucr['domainname'])}, shell=True)

	def cleanup(self):
		if self.meta_inf_created:
			shutil.rmtree('/var/www/meta-inf')
		if self.univention_repository_created:
			shutil.rmtree('/var/www/univention-repository')
		self.ucr.revert_to_original_registry()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if exc_type:
			print 'Cleanup after exception: %s %s' % (exc_type, exc_value)
		self.cleanup()

def restore_data_script_4_1():
	return '''#!/usr/bin/python2.7
from optparse import OptionParser
import os
import shutil
import string
import univention.config_registry
import traceback

BLACKLIST_UCR_VARIABLES = [
	'version/version',
	'version/erratalevel',
	'version/patchlevel',
	'version/releasename',
]


# Helper function to copy all meta data of a file or directory
def copy_permissions(src, dest):
	s_stat = os.stat(src)
	os.chown(dest, s_stat.st_uid, s_stat.st_gid)
	shutil.copymode(src, dest)
	shutil.copystat(src, dest)
	d_stat = os.stat(dest)


def restore_files(source_dir):
	if not os.path.exists(source_dir):
		return
	for (path, dirs, files) in os.walk(source_dir):
		for d in dirs:
			r_path = string.replace(path, source_dir, '/', 1)
			dest = os.path.join(r_path, d)
			if not os.path.exists(dest):
				os.makedirs(dest)
			src = os.path.join(path, d)
			copy_permissions(src, dest)
		for i in files:
			src = os.path.join(path, i)
			dest = string.replace(src, source_dir, '', 1)
			if os.path.islink(src):
				linkto = os.readlink(src)
				if os.path.exists(dest) or os.path.islink(dest):
					print 'rm %s' % dest
					os.remove(dest)
				print 'ln -sf %s %s' % (linkto, dest)
				os.symlink(linkto, dest)
			else:
				print 'cp %s %s' % (src, dest)
				shutil.copy(src, dest)
				copy_permissions(src, dest)


def restore_ucr_layer(ucr_file, options):
	if not os.path.exists(ucr_file):
		return
	f = open(ucr_file, "r")
	vv = []
	for v in f.readlines():
		v = v.strip()
		if not v or v.startswith('#'):
			continue
		key, value = v.split(':', 1)
		if key not in BLACKLIST_UCR_VARIABLES:
			vv.append('%s=%s' % (key, value))
	if vv:
		print vv
		univention.config_registry.handler_set(vv, opts=options)

if __name__ == '__main__':
	parser = OptionParser('%prog [options]')
	parser.add_option('--app', dest='app', help='App ID')
	parser.add_option('--app-version', dest='app_version', help='Version of App')
	parser.add_option('--error-file', dest='error_file', help='Name of Error File')
	opts, args = parser.parse_args()

	conf_dir = '/var/lib/univention-appcenter/apps/%s/conf/' % opts.app
	source_dir = '/var/lib/univention-appcenter/apps/%s/conf/files' % opts.app

	try:
		restore_files(source_dir)

		print '** Restore forced UCR layer:'
		restore_ucr_layer(os.path.join(conf_dir, 'base-forced.conf'), {'force': True})
		print '** Restore ldap UCR layer'
		restore_ucr_layer(os.path.join(conf_dir, 'base-ldap.conf'), {'ldap-policy': True})
		print '** Restore normal UCR layer:'
		restore_ucr_layer(os.path.join(conf_dir, 'base.conf'), {})
	except:
		traceback.print_exc()
		if opts.error_file:
			error_file = open(opts.error_file, 'a+')
			traceback.print_exc(file=error_file)
			error_file.close()
		raise
'''

def store_data_script_4_1():
	return '''#!/usr/bin/python2.7
from optparse import OptionParser
import glob
import os
import shutil
import string
import traceback


# Helper function to copy all meta data of a file or directory
def copy_permissions(src, dest):
	s_stat = os.stat(src)
	os.chown(dest, s_stat.st_uid, s_stat.st_gid)
	shutil.copymode(src, dest)
	shutil.copystat(src, dest)
	d_stat = os.stat(dest)


# Helper function to copy the files and directory
def copy_to_persistent_storage(src, dest):
	l_src = string.split(src, '/')
	# Ignore first empty entry
	if l_src[0] == '':
		l_src = l_src[1:]
	for j in range(0, len(l_src)):
		s = os.path.join('/', string.join(l_src[0:j + 1], '/'))
		d = os.path.join(dest, string.join(l_src[0:j + 1], '/'))
		if os.path.isdir(s):
			if not os.path.exists(d):
				os.makedirs(d)
				copy_permissions(s, d)
		elif os.path.islink(s):
			linkto = os.readlink(s)
			if os.path.exists(d) or os.path.islink(d):
				print 'rm %s' % d
				os.remove(d)
			print 'ln -sf %s %s' % (linkto, d)
			os.symlink(linkto, d)
		else:
			print 'cp %s %s' % (s, d)
			shutil.copy(s, d)
			copy_permissions(s, d)


def copy_files(src, dest):
	for f in glob.glob(src):
		copy_to_persistent_storage(f, dest)


def copy_recursive(src, dest):
	if not os.path.exists(src):
		return
	copy_to_persistent_storage(src, dest)
	for root, dirs, files in os.walk(src):
		for f in files:
			fullpath = os.path.join(root, f)
			copy_to_persistent_storage(fullpath, dest)

if __name__ == '__main__':
	parser = OptionParser('%prog [options]')
	parser.add_option('--app', dest='app', help='App ID')
	parser.add_option('--app-version', dest='app_version', help='Version of App')
	parser.add_option('--error-file', dest='error_file', help='Name of Error File')
	opts, args = parser.parse_args()

	dest = '/var/lib/univention-appcenter/apps/%s/conf/' % opts.app

	# The files and directories below the files directory are restored
	# automatically after the new container has been started
	store = '/var/lib/univention-appcenter/apps/%s/conf/files' % opts.app

	try:
		for f in glob.glob('/etc/univention/base*conf'):
			print 'cp %s %s' % (f, dest)
			shutil.copy(f, dest)
		copy_files('/etc/*.secret', store)
		copy_recursive('/etc/univention/ssl', store)
		copy_recursive('/var/univention-join', store)
		copy_recursive('/var/lib/univention-ldap/', store)
		copy_recursive('/var/lib/univention-directory-listener/', store)
		copy_recursive('/etc/univention/connector', store)
	except:
		traceback.print_exc()
		if opts.error_file:
			error_file = open(opts.error_file, 'a+')
			traceback.print_exc(file=error_file)
			error_file.close()
		raise
'''

def get_dummy_svg():
	return '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!-- Created with Inkscape (http://www.inkscape.org/) -->

<svg
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:cc="http://creativecommons.org/ns#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   version="1.1"
   width="110"
   height="126.122"
   id="svg3555">
  <defs
     id="defs3557" />
  <metadata
     id="metadata3560">
    <rdf:RDF>
      <cc:Work
         rdf:about="">
        <dc:format>image/svg+xml</dc:format>
        <dc:type
           rdf:resource="http://purl.org/dc/dcmitype/StillImage" />
        <dc:title></dc:title>
      </cc:Work>
    </rdf:RDF>
  </metadata>
  <g
     transform="translate(-319.28571,-275.01547)"
     id="layer1">
    <g
       transform="matrix(1,0,0,-1,331.53071,388.89247)"
       id="g530">
      <path
         d="m 0,0 0,101.633 85.51,0 0,-66.758 C 85.51,15.552 61.655,23.293 61.655,23.293 61.655,23.293 68.958,0 50.941,0 L 0,0 z m 97.755,33.818 0,80.059 -110,0 0,-126.122 63.372,0 c 20.867,0 46.628,27.266 46.628,46.063 M 40.87,21.383 C 33.322,18.73 27.1,21.772 28.349,29.02 c 1.248,7.25 8.41,22.771 9.432,25.705 1.021,2.936 -0.937,3.74 -3.036,2.546 -1.21,-0.698 -3.009,-2.098 -4.554,-3.458 -0.427,0.862 -1.03,1.848 -1.482,2.791 2.52,2.526 6.732,5.912 11.72,7.138 5.958,1.471 15.916,-0.88 11.636,-12.269 -3.056,-8.117 -5.218,-13.719 -6.58,-17.89 -1.361,-4.173 0.256,-5.048 2.639,-3.423 1.862,1.271 3.846,3 5.299,4.342 0.673,-1.093 0.888,-1.442 1.553,-2.698 C 52.452,29.217 45.85,23.163 40.87,21.383 m 15.638,50.213 c -3.423,-2.913 -8.498,-2.85 -11.336,0.143 -2.838,2.992 -2.365,7.779 1.058,10.694 3.423,2.913 8.498,2.85 11.336,-0.141 2.838,-2.993 2.364,-7.781 -1.058,-10.696"
         id="path532"
         style="fill:#ffffff;fill-opacity:1;fill-rule:nonzero;stroke:none" />
    </g>
  </g>
</svg>'''
