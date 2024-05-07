#!/usr/share/ucs-test/runner pytest-3
## desc: App Settings
## tags: [basic, coverage, skip_admember]
## packages:
##   - univention-appcenter-dev
## exposure: dangerous

from __future__ import annotations

import re
import stat
import subprocess
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Iterable

import pytest

import univention.config_registry
from univention.appcenter.actions import Abort, get_action
from univention.appcenter.app_cache import Apps
from univention.appcenter.docker import Docker
from univention.appcenter.log import log_to_logfile, log_to_stream
from univention.appcenter.settings import SettingValueError
from univention.appcenter.ucr import ucr_get, ucr_save
from univention.testing.conftest import has_license

import appcentertest as app_test


if TYPE_CHECKING:
    from collections.abc import Iterator
    from types import TracebackType

    from univention.appcenter.app import App
    from univention.appcenter.settings import Setting


log_to_logfile()
log_to_stream()


class Configuring:
    def __init__(self, app: App, revert='configure') -> None:
        self.settings: set[str] = set()
        self.app = app
        self.revert = revert

    def __enter__(self) -> Configuring:
        return self

    def set(self, config: Iterable[str]) -> None:
        self.settings.update(config)
        configure = get_action('configure')
        configure.call(app=self.app, set_vars=config, run_script='no')

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        config = dict.fromkeys(self.settings)
        if self.revert == 'configure':
            configure = get_action('configure')
            configure.call(app=self.app, set_vars=config, run_script='no')
            for setting in self.settings:
                assert ucr_get(setting) is None
        elif self.revert == 'ucr':
            ucr_save(config)


def fresh_settings(content: str, app: App, num: int) -> tuple[App | None, Setting]:
    settings = get_settings(content, app)
    assert len(settings) == num
    return Apps().find(app.id), settings


def docker_shell(app: App, command: str) -> str:
    container = ucr_get(app.ucr_container_key)
    return subprocess.check_output(['docker', 'exec', container, '/bin/bash', '-c', command], stderr=subprocess.STDOUT, text=True)


@contextmanager
def install_app(app: App, set_vars: Setting | None = None) -> Iterator[App]:
    m = re.match('uid=([^,]*),.*', ucr_get('tests/domainadmin/account'))
    assert m is not None
    username = m.group(1)
    install = get_action('install')
    subprocess.run(['apt-get', 'update', '-q'], check=True)
    install.call(app=[app], username=username, password=ucr_get('tests/domainadmin/pwd'), noninteractive=True, set_vars=set_vars)
    yield app
    remove = get_action('remove')
    remove.call(app=[app], username=username, password=ucr_get('tests/domainadmin/pwd'), noninteractive=True)


@contextmanager
def add_custom_settings(app: App, custom_settings_content: str) -> Iterator[None]:
    custom_settings_file = Path("/var/lib/univention-appcenter/apps") / app.id / "custom.settings"
    custom_settings_file.write_text(custom_settings_content)
    try:
        yield
    finally:
        custom_settings_file.unlink()


@pytest.fixture(scope='module')
def local_appcenter() -> Iterator[None]:
    with app_test.local_appcenter():
        yield


@pytest.fixture(scope='module')
def installed_component_app(local_appcenter, tmp_path_factory) -> Iterator[App]:
    ini_file = '''[Application]
ID = ucs-test
Code = TE
Name = UCS Test App
Logo = logo.svg
Version = 1.0
License = free
WithoutRepository = True
DefaultPackages = libcurl4-doc'''
    tmp = tmp_path_factory.mktemp("installed_component_app")
    ini = tmp / "app.ini"
    ini.write_text(ini_file)
    logo = tmp / "app.logo"
    logo.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect x="10" y="10" height="100" width="100" style="stroke:#ff0000; fill: #0000ff"/></svg>')
    populate = get_action('dev-populate-appcenter')
    populate.call(new=True, ini=ini.as_posix(), logo=logo.as_posix())
    app = Apps().find('ucs-test')
    with install_app(app) as app:
        yield app


@pytest.fixture(scope='module')
def apache_docker_app(local_appcenter, tmp_path_factory) -> App:
    ini_file = '''[Application]
ID = apache
Code = AP
Name = Apache
Version = 2.4
DockerImage = docker-test.software-univention.de/httpd:2.4.23-alpine
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
    tmp = tmp_path_factory.mktemp("apache_docker_app")
    ini = tmp / "app.ini"
    ini.write_text(ini_file)
    populate = get_action('dev-populate-appcenter')
    populate.call(new=True, ini=ini.as_posix())
    return Apps().find('apache')


@pytest.fixture()
def installed_apache_docker_app(apache_docker_app: App) -> Iterator[App]:
    with install_app(apache_docker_app) as app:
        yield app


def get_settings(content: str, app: App) -> list[Setting]:
    with NamedTemporaryFile("w+") as fd:
        fd.write(content)
        fd.flush()
        populate = get_action('dev-populate-appcenter')
        populate.call(component_id=app.component_id, ini=app.get_ini_file(), settings=fd.name)

    app = Apps().find(app.id)
    settings = app.get_settings()

    return settings


def test_string_setting(installed_component_app: App) -> None:
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


@has_license()
def test_string_setting_docker(installed_apache_docker_app: App) -> None:
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


@has_license()
@pytest.mark.parametrize('scope', ['inside, outside', 'outside', 'inside'])
def test_string_custom_setting_docker(installed_apache_docker_app: App, scope: str) -> None:
    content_custom = f'''[test1/setting]
Type = String
Description = My Description
InitialValue = Default: @%@hostname@%@
Scope = {scope}
'''
    content = '''[test/setting]
Type = String
Description = My Description
InitialValue = Default: @%@ldap/base@%@
Scope = inside, outside
'''
    with add_custom_settings(installed_apache_docker_app, content_custom):
        app, settings = fresh_settings(content, installed_apache_docker_app, 2)
        setting1, setting2 = settings
        for c, setting in [(content, setting1), (content_custom, setting2)]:
            assert repr(setting) == "StringSetting(name='{}')".format(setting.name)
            assert setting.is_inside(app) is ("inside" in c)
            assert setting.is_outside(app) is ("outside" in c)
            m = re.search('@%@(.*?)@%@', c)
            assert m is not None
            ucr_var_name = m.group(1)
            assert setting.get_initial_value(app) == 'Default: %s' % ucr_get(ucr_var_name)
            assert setting.get_value(app) is None

        with Configuring(app, revert='ucr') as config:
            config.set({setting1.name: 'My value', setting2.name: 'My value2'})

            assert setting1.get_value(app) == 'My value'
            assert setting2.get_value(app) == 'My value2'

            assert ucr_get(setting1.name) == 'My value'
            if setting2.is_outside(app):
                assert ucr_get(setting2.name) == 'My value2'
            assert docker_shell(app, f'grep "{setting1.name}: " /etc/univention/base.conf') == f'{setting1.name}: My value\n'
            if setting2.is_inside(app):
                assert docker_shell(app, f'grep "{setting2.name}: " /etc/univention/base.conf') == f'{setting2.name}: My value2\n'

            config.set({setting1.name: 'My new value', setting2.name: 'My new value2'})

            stop = get_action('stop')
            stop.call(app=app)

            start = get_action('start')
            start.call(app=app)

            assert ucr_get(setting1.name) == 'My new value'
            if setting2.is_outside(app):
                assert ucr_get(setting2.name) == 'My new value2'

            assert docker_shell(app, f'grep "{setting1.name}: " /etc/univention/base.conf') == f'{setting1.name}: My new value\n'
            if setting2.is_inside(app):
                assert docker_shell(app, f'grep "{setting2.name}: " /etc/univention/base.conf') == f'{setting2.name}: My new value2\n'


def test_int_setting(installed_component_app: App) -> None:
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


def test_status_and_file_setting(installed_component_app: App, tmp_path: Path) -> None:
    short = tmp_path / "setting4.test"
    long = tmp_path / (300 * 'X')
    content = f'''[test/setting3]
Type = Status
Description = My Description 3

[test/setting4]
Type = File
Filename = {short.as_posix()}
Description = My Description 4

[test/setting4/2]
Type = File
Filename = {long.as_posix()}
Description = My Description 4.2
'''

    app, settings = fresh_settings(content, installed_component_app, 3)
    status_setting, file_setting, file_setting2 = settings
    assert repr(status_setting) == "StatusSetting(name='test/setting3')"
    assert repr(file_setting) == "FileSetting(name='test/setting4')"
    assert repr(file_setting2) == "FileSetting(name='test/setting4/2')"

    with Configuring(app, revert='ucr') as config:
        ucr_save({status_setting.name: 'My Status'})
        assert status_setting.get_value(app) == 'My Status'
        assert not Path(file_setting.filename).exists()
        assert file_setting.get_value(app) is None

        config.set({status_setting.name: 'My new Status', file_setting.name: 'File content'})

        assert status_setting.get_value(app) == 'My Status'
        assert Path(file_setting.filename).exists()
        assert Path(file_setting.filename).read_text() == 'File content'
        assert file_setting.get_value(app) == 'File content'

        config.set({file_setting.name: None})
        assert not Path(file_setting.filename).exists()
        assert file_setting.get_value(app) is None

        assert file_setting2.get_value(app) is None
        config.set({file_setting2.name: 'File content 2'})
        assert file_setting2.get_value(app) is None


@has_license()
def test_file_setting_docker(installed_apache_docker_app: App, tmp_path: Path) -> None:
    fname = tmp_path / "setting4.test"
    content = f'''[test/setting4]
Type = File
Filename = {fname.as_posix()}
Description = My Description 4
'''

    app, settings = fresh_settings(content, installed_apache_docker_app, 1)
    setting, = settings
    assert repr(setting) == "FileSetting(name='test/setting4')"

    docker_file = Docker(app).path(setting.filename)

    with Configuring(app, revert='configure') as config:
        assert not Path(docker_file).exists()
        assert setting.get_value(app) is None

        config.set({setting.name: 'Docker file content'})
        assert Path(docker_file).exists()
        assert Path(docker_file).read_text() == 'Docker file content'
        assert setting.get_value(app) == 'Docker file content'

        config.set({setting.name: None})
        assert not Path(docker_file).exists()
        assert setting.get_value(app) is None


def test_password_setting(installed_component_app: App, tmp_path: Path) -> None:
    fname = tmp_path / "setting6.password"
    content = f'''[test/setting5]
Type = Password

[test/setting6]
Type = PasswordFile
Filename = {fname.as_posix()}
'''

    app, settings = fresh_settings(content, installed_component_app, 2)
    password_setting, password_file_setting = settings

    assert repr(password_setting) == "PasswordSetting(name='test/setting5')"
    assert repr(password_file_setting) == "PasswordFileSetting(name='test/setting6')"

    assert password_setting.should_go_into_image_configuration(app) is False
    assert password_file_setting.should_go_into_image_configuration(app) is False

    assert password_setting.get_value(app) is None
    assert not Path(password_file_setting.filename).exists()

    with Configuring(app, revert='ucr') as config:
        config.set({password_setting.name: 'MyPassword', password_file_setting.name: 'FilePassword'})

        assert password_setting.get_value(app) == 'MyPassword'
        assert Path(password_file_setting.filename).exists()
        assert Path(password_file_setting.filename).read_text() == 'FilePassword'
        assert stat.S_IMODE(Path(password_file_setting.filename).stat().st_mode) == 0o600


@has_license()
def test_password_setting_docker(installed_apache_docker_app: App, tmp_path: Path) -> None:
    fname = tmp_path / "settings6.password"
    content = f'''[test/setting5]
Type = Password

[test/setting6]
Type = PasswordFile
Filename = {fname.as_posix()}
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

    assert not Path(password_file).exists()

    with Configuring(app, revert='ucr') as config:
        config.set({password_setting.name: 'MyPassword', password_file_setting.name: 'FilePassword'})

        assert password_setting.get_value(app) == 'MyPassword'
        assert Path(password_file).exists()
        assert Path(password_file).read_text() == 'FilePassword'
        assert stat.S_IMODE(Path(password_file).stat().st_mode) == 0o600

        stop = get_action('stop')
        stop.call(app=app)
        config.set({password_setting.name: 'MyNewPassword2', password_file_setting.name: 'NewFilePassword2'})
        assert password_setting.get_value(app) is None
        assert password_file_setting.get_value(app) is None

        start = get_action('start')
        start.call(app=app)
        assert password_setting.get_value(app) == 'MyPassword'
        assert Path(password_file).read_text() == 'FilePassword'


def test_bool_setting(installed_component_app: App) -> None:
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


def test_list_setting(installed_component_app: App) -> None:
    content = '''[test/setting8]
Type = List
Values = v1, v2, v3
Labels = Label 1, Label 2\\, among others, Label 3
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


@pytest.fixture(scope='module')
def outside_test_settings() -> str:
    return '''[test_settings/outside]
Type = String
Required = True
Show = Install, Settings
Scope = outside
Description = setting1
InitialValue = initValue

[test_settings/inside]
Type = String
Show = Install
Scope = inside
Description = setting2

[test_settings/not_given]
Type = String
Show = Install
Scope = outside
InitialValue = initValue
Description = setting3

[test_settings/list]
Show = Install
Values = value1, value2, value3
Labels = Label 1, Label 2, Label 3
InitialValue = initValue
Scope = outside
Description = setting4

[test_settings/bool]
Type = Bool
Required = True
Show = Install, Settings
Scope = outside
InitialValue = false
Description = setting5
'''


@pytest.fixture(scope='module')
def outside_test_preinst() -> str:
    return '''#!/bin/sh
eval "$(ucr shell)"
set -x -e
test "$test_settings_outside" = "123"
test "$test_settings_list" = "value2"
test -z "$test_settings_inside"
test -z "$test_settings_not_exists"
test "$test_settings_not_given" = "initValue"
test "$test_settings_bool" = "true"
exit 0'''


def docker_app_ini() -> tuple[str, str]:
    return '''[Application]
ID = alpine
Code = AP
Name = Alpine
Version = 3.6
DockerImage = docker-test.software-univention.de/alpine:3.6
DockerScriptInit = /sbin/init
DockerScriptStoreData =
DockerScriptRestoreDataBeforeSetup =
DockerScriptRestoreDataAfterSetup =
DockerScriptSetup =
DockerScriptUpdateAvailable =
AutoModProxy = False
UCSOverviewCategory = False''', 'alpine'


def package_app_ini() -> tuple[str, str]:
    return '''[Application]
ID = ucstest
Code = TE
Name = UCS Test App
Logo = logo.svg
Version = 1.0
License = free
WithoutRepository = True
DefaultPackages = libcurl4-doc''', 'ucstest'


@pytest.fixture(scope='module', params=[package_app_ini, docker_app_ini])
def outside_test_app(request, local_appcenter, outside_test_preinst, outside_test_settings, tmp_path_factory) -> App:
    ini_file, app_id = request.param()

    tmp = tmp_path_factory.mktemp("outside_test_app")
    ini = tmp / "app.ini"
    ini.write_text(ini_file)
    settings = tmp / "app.settings"
    settings.write_text(outside_test_settings)
    preinst = tmp / "app.preinst"
    preinst.write_text(outside_test_preinst)

    populate = get_action('dev-populate-appcenter')
    populate.call(new=True, settings=settings.as_posix(), preinst=preinst.as_posix(), ini=ini.as_posix())
    return Apps().find(app_id)


@has_license()
def test_outside_settings_in_preinst(outside_test_app) -> None:
    settings_unset = [
        'test_settings/outside',
        'test_settings/inside',
        'test_settings/not_given',
        'test_settings/list',
        'test_settings/bool',
    ]
    univention.config_registry.handler_unset(settings_unset)
    settings = {
        'test_settings/outside': '123',
        'test_settings/inside': '123',
        'test_settings/not_exists': 123,
        'test_settings/list': 'value2',
        'test_settings/bool': True,
    }
    is_installed = False
    with install_app(outside_test_app, settings) as app:
        is_installed = app.is_installed()
    univention.config_registry.handler_unset(settings_unset)
    assert is_installed
