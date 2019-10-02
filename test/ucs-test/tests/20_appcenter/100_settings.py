#!/usr/share/ucs-test/runner /usr/bin/py.test
## desc: App Settings
## tags: [basic, coverage, skip_admember]
## packages:
##   - univention-appcenter-dev
## exposure: dangerous

import os
import os.path
import re
import stat
from shutil import rmtree
import subprocess
from contextlib import contextmanager

import pytest

from univention.appcenter.actions import get_action, Abort
from univention.appcenter.app_cache import Apps
from univention.appcenter.settings import SettingValueError
from univention.appcenter.ucr import ucr_get, ucr_save
from univention.appcenter.log import log_to_logfile, log_to_stream
from univention.appcenter.docker import Docker


log_to_logfile()
log_to_stream()


class Configuring(object):
	def __init__(self, app, revert='configure'):
		self.settings = set()
		self.app = app
		self.revert = revert

	def __enter__(self):
		return self

	def set(self, config):
		self.settings.update(config)
		configure = get_action('configure')
		configure.call(app=self.app, set_vars=config, run_script='no')

	def __exit__(self, exc_type, exc_val, exc_tb):
		if self.revert == 'configure':
			config = dict((key, None) for key in self.settings)
			configure = get_action('configure')
			configure.call(app=self.app, set_vars=config, run_script='no')
			for setting in self.settings:
				assert ucr_get(setting) is None
		elif self.revert == 'ucr':
			config = dict((key, None) for key in self.settings)
			ucr_save(config)


def fresh_settings(content, app, num):
	settings = get_settings(content, app)
	assert len(settings) == num
	return Apps().find(app.id), settings


def docker_shell(app, command):
	container = ucr_get(app.ucr_container_key)
	return subprocess.check_output(['docker', 'exec', container, '/bin/bash', '-c', command], stderr=subprocess.STDOUT)


@contextmanager
def install_app(app):
	username = re.match('uid=([^,]*),.*', ucr_get('tests/domainadmin/account')).groups()[0]
	install = get_action('install')
	install.call(app=app, username=username, password=ucr_get('tests/domainadmin/pwd'), noninteractive=True)
	yield app
	remove = get_action('remove')
	remove.call(app=app, username=username, password=ucr_get('tests/domainadmin/pwd'), noninteractive=True)


@pytest.yield_fixture(scope='module')
def local_appcenter():
	setup_appcenter = get_action('dev-setup-local-appcenter')
	setup_appcenter.call()
	yield
	test_appcenter = get_action('dev-use-test-appcenter')
	test_appcenter.call(revert=True)
	rmtree('/var/www/meta-inf')
	rmtree('/var/www/univention-repository')


@pytest.yield_fixture(scope='module')
def installed_component_app(local_appcenter):
	ini_file = '''[Application]
ID = ucs-test
Code = TE
Name = UCS Test App
Logo = logo.svg
Version = 1.0
License = free
WithoutRepository = True
DefaultPackages = libcurl4-doc'''
	with open('/tmp/app.ini', 'wb') as fd:
		fd.write(ini_file)
	with open('/tmp/app.logo', 'wb') as fd:
		fd.write('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><rect x="10" y="10" height="100" width="100" style="stroke:#ff0000; fill: #0000ff"/></svg>')
	populate = get_action('dev-populate-appcenter')
	populate.call(new=True, ini='/tmp/app.ini', logo='/tmp/app.logo')
	app = Apps().find('ucs-test')
	with install_app(app) as app:
		yield app


@pytest.fixture(scope='module')
def apache_docker_app(local_appcenter):
	ini_file = '''[Application]
ID = apache
Code = AP
Name = Apache
Version = 2.4
DockerImage = httpd:2.4.23-alpine
DockerScriptInit = httpd-foreground
DockerScriptStoreData =
DockerScriptRestoreDataBeforeSetup =
DockerScriptRestoreDataAfterSetup =
DockerScriptSetup =
DockerScriptUpdateAvailable =
PortsRedirection = 8080:80
Webinterface = /
WebInterfacePortHTTP = 8080
WebInterfacePortHTTPS = 0
AutoModProxy = False
UCSOverviewCategory = False'''
	with open('/tmp/app.ini', 'wb') as fd:
		fd.write(ini_file)
	populate = get_action('dev-populate-appcenter')
	populate.call(new=True, ini='/tmp/app.ini')
	return Apps().find('apache')


@pytest.yield_fixture
def installed_apache_docker_app(apache_docker_app):
	with install_app(apache_docker_app) as app:
		yield app


def get_settings(content, app):
	fname = '/tmp/app.settings'
	with open(fname, 'wb') as fd:
		fd.write(content)
	populate = get_action('dev-populate-appcenter')
	populate.call(component_id=app.component_id, ini=app.get_ini_file(), settings='/tmp/app.settings')

	app = Apps().find(app.id)
	settings = app.get_settings()

	return settings


def test_string_setting(installed_component_app):
	content = '''[test/setting]
Type = String
Description = My Description
InitialValue = Default: @%@ldap/base@%@
'''

	app, settings = fresh_settings(content, installed_component_app, 1)
	setting, = settings
	assert repr(setting) == "StringSetting(name='test/setting')"

	assert setting.is_inside(app) is False
	assert setting.is_outside(app) is True

	assert setting.get_initial_value(app) == 'Default: %s' % ucr_get('ldap/base')

	assert setting.get_value(app) is None

	with Configuring(app, revert='ucr') as config:
		config.set({setting.name: 'My value'})
		assert setting.get_value(app) == 'My value'
		config.set({setting.name: None})
		assert setting.get_value(app) is None
		config.set({setting.name: ''})
		assert setting.get_value(app) is None


def test_string_setting_docker(installed_apache_docker_app):
	content = '''[test/setting]
Type = String
Description = My Description
InitialValue = Default: @%@ldap/base@%@
Scope = inside, outside
'''

	app, settings = fresh_settings(content, installed_apache_docker_app, 1)
	setting, = settings
	assert repr(setting) == "StringSetting(name='test/setting')"

	assert setting.is_inside(app) is True
	assert setting.is_outside(app) is True

	assert setting.get_initial_value(app) == 'Default: %s' % ucr_get('ldap/base')

	assert setting.get_value(app) is None

	with Configuring(app, revert='ucr') as config:
		config.set({setting.name: 'My value'})
		assert setting.get_value(app) == 'My value'
		assert ucr_get(setting.name) == 'My value'
		assert docker_shell(app, 'grep "test/setting: " /etc/univention/base.conf') == 'test/setting: My value\n'

		stop = get_action('stop')
		stop.call(app=app)
		config.set({setting.name: 'My new value'})

		start = get_action('start')
		start.call(app=app)
		assert ucr_get(setting.name) == 'My new value'


def test_int_setting(installed_component_app):
	content = '''[test/setting2]
Type = Int
Description = My Description 2
InitialValue = 123
Show = Install, Settings
Required = Yes
'''

	app, settings = fresh_settings(content, installed_component_app, 1)
	setting, = settings
	assert repr(setting) == "IntSetting(name='test/setting2')"

	# FIXME: This should be int(123), right?
	assert setting.get_initial_value(app) == '123'
	assert setting.get_value(app, phase='Install') == '123'
	assert setting.get_value(app, phase='Settings') is None

	assert setting.should_go_into_image_configuration(app) is False

	with pytest.raises(SettingValueError):
		setting.sanitize_value(app, None)

	with Configuring(app, revert='ucr') as config:
		config.set({setting.name: '3000'})
		assert setting.get_value(app) == 3000
		with pytest.raises(Abort):
			config.set({setting.name: 'invalid'})
		assert setting.get_value(app) == 3000


def test_status_and_file_setting(installed_component_app):
	content = '''[test/setting3]
Type = Status
Description = My Description 3

[test/setting4]
Type = File
Filename = /tmp/settingdir/setting4.test
Description = My Description 4

[test/setting4/2]
Type = File
Filename = /tmp/%s
Description = My Description 4.2
''' % (300 * 'X')

	app, settings = fresh_settings(content, installed_component_app, 3)
	status_setting, file_setting, file_setting2 = settings
	assert repr(status_setting) == "StatusSetting(name='test/setting3')"
	assert repr(file_setting) == "FileSetting(name='test/setting4')"
	assert repr(file_setting2) == "FileSetting(name='test/setting4/2')"

	try:
		with Configuring(app, revert='ucr') as config:
			ucr_save({status_setting.name: 'My Status'})
			assert status_setting.get_value(app) == 'My Status'
			assert not os.path.exists(file_setting.filename)
			assert file_setting.get_value(app) is None

			config.set({status_setting.name: 'My new Status', file_setting.name: 'File content'})

			assert status_setting.get_value(app) == 'My Status'
			assert os.path.exists(file_setting.filename)
			assert open(file_setting.filename, 'rb').read() == 'File content'
			assert file_setting.get_value(app) == 'File content'

			config.set({file_setting.name: None})
			assert not os.path.exists(file_setting.filename)
			assert file_setting.get_value(app) is None

			assert file_setting2.get_value(app) is None
			config.set({file_setting2.name: 'File content 2'})
			assert file_setting2.get_value(app) is None
	finally:
		try:
			os.unlink(file_setting.filename)
		except EnvironmentError:
			pass


def test_file_setting_docker(installed_apache_docker_app):
	content = '''[test/setting4]
Type = File
Filename = /tmp/settingdir/setting4.test
Description = My Description 4
'''

	app, settings = fresh_settings(content, installed_apache_docker_app, 1)
	setting, = settings
	assert repr(setting) == "FileSetting(name='test/setting4')"

	docker_file = Docker(app).path(setting.filename)

	try:
		with Configuring(app, revert='configure') as config:
			assert not os.path.exists(docker_file)
			assert setting.get_value(app) is None

			config.set({setting.name: 'Docker file content'})
			assert os.path.exists(docker_file)
			assert open(docker_file, 'rb').read() == 'Docker file content'
			assert setting.get_value(app) == 'Docker file content'

			config.set({setting.name: None})
			assert not os.path.exists(docker_file)
			assert setting.get_value(app) is None
	finally:
		try:
			os.unlink(setting.filename)
		except EnvironmentError:
			pass


def test_password_setting(installed_component_app):
	content = '''[test/setting5]
Type = Password

[test/setting6]
Type = PasswordFile
Filename = /tmp/settingdir/setting6.password
'''

	app, settings = fresh_settings(content, installed_component_app, 2)
	password_setting, password_file_setting = settings

	assert repr(password_setting) == "PasswordSetting(name='test/setting5')"
	assert repr(password_file_setting) == "PasswordFileSetting(name='test/setting6')"

	assert password_setting.should_go_into_image_configuration(app) is False
	assert password_file_setting.should_go_into_image_configuration(app) is False

	assert password_setting.get_value(app) is None
	assert not os.path.exists(password_file_setting.filename)

	try:
		with Configuring(app, revert='ucr') as config:
			config.set({password_setting.name: 'MyPassword', password_file_setting.name: 'FilePassword'})

			assert password_setting.get_value(app) == 'MyPassword'
			assert os.path.exists(password_file_setting.filename)
			assert open(password_file_setting.filename, 'rb').read() == 'FilePassword'
			assert stat.S_IMODE(os.stat(password_file_setting.filename).st_mode) == 0600
	finally:
		try:
			os.unlink(password_file_setting.filename)
		except EnvironmentError:
			pass


def test_password_setting_docker(installed_apache_docker_app):
	content = '''[test/setting5]
Type = Password

[test/setting6]
Type = PasswordFile
Filename = /tmp/settingdir/setting6.password
'''

	app, settings = fresh_settings(content, installed_apache_docker_app, 2)
	password_setting, password_file_setting = settings

	assert repr(password_setting) == "PasswordSetting(name='test/setting5')"
	assert repr(password_file_setting) == "PasswordFileSetting(name='test/setting6')"

	assert password_setting.should_go_into_image_configuration(app) is False
	assert password_file_setting.should_go_into_image_configuration(app) is False

	password_file = Docker(app).path(password_file_setting.filename)

	assert password_setting.is_inside(app) is True
	assert password_file_setting.is_inside(app) is True

	assert not os.path.exists(password_file)

	with Configuring(app, revert='ucr') as config:
		config.set({password_setting.name: 'MyPassword', password_file_setting.name: 'FilePassword'})

		assert password_setting.get_value(app) == 'MyPassword'
		assert os.path.exists(password_file)
		assert open(password_file, 'rb').read() == 'FilePassword'
		assert stat.S_IMODE(os.stat(password_file).st_mode) == 0600

		stop = get_action('stop')
		stop.call(app=app)
		config.set({password_setting.name: 'MyNewPassword2', password_file_setting.name: 'NewFilePassword2'})
		assert password_setting.get_value(app) is None
		assert password_file_setting.get_value(app) is None

		start = get_action('start')
		start.call(app=app)
		assert password_setting.get_value(app) == 'MyPassword'
		assert open(password_file, 'rb').read() == 'FilePassword'


def test_bool_setting(installed_component_app):
	content = '''[test/setting7]
Type = Bool
Description = My Description 7
InitialValue = False
'''

	app, settings = fresh_settings(content, installed_component_app, 1)
	setting, = settings
	assert repr(setting) == "BoolSetting(name='test/setting7')"

	# FIXME: This should be bool(False), right?
	assert setting.get_initial_value(app) == 'False'
	assert setting.get_value(app) is False

	with Configuring(app, revert='ucr') as config:
		config.set({setting.name: 'yes'})
		assert setting.get_value(app) is True
		config.set({setting.name: 'false'})
		assert setting.get_value(app) is False
		config.set({setting.name: True})
		assert setting.get_value(app) is True


def test_list_setting(installed_component_app):
	content = '''[test/setting8]
Type = List
Values = v1, v2, v3
Labels = Label 1, Label 2\, among others, Label 3
Description = My Description 8
'''

	app, settings = fresh_settings(content, installed_component_app, 1)
	setting, = settings
	assert repr(setting) == "ListSetting(name='test/setting8')"

	with Configuring(app, revert='ucr') as config:
		with pytest.raises(Abort):
			config.set({setting.name: 'v4'})
		assert setting.get_value(app) is None
		config.set({setting.name: 'v1'})
		assert setting.get_value(app) == 'v1'
