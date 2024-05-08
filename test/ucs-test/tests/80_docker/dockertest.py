#
# UCS test
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2015-2024 Univention GmbH
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

from __future__ import annotations

import shutil
import subprocess
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

import requests

from univention.config_registry import ConfigRegistry, handler_set
from univention.testing import umc
from univention.testing.debian_package import DebianPackage
from univention.testing.strings import random_name, random_version
from univention.testing.ucr import UCSTestConfigRegistry


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from types import TracebackType


BASE_DIR = Path('/var/www')
META_DIR = BASE_DIR / 'meta-inf'
REPO_DIR = BASE_DIR / 'univention-repository'


class BaseFailure(Exception):
    """Base or internal error."""


class UMCFailure(BaseFailure):
    """UMC client command failed."""


class AppFailure(BaseFailure):
    """univention-app failed."""


class DockerFailure(BaseFailure):
    """docker failed."""


def tiny_app(name: str | None = None, version: str | None = None) -> App:
    name = name or get_app_name()
    version = version or '1'
    app = App(name=name, version=version, build_package=False)
    app.set_ini_parameter(
        DockerImage='docker-test.software-univention.de/alpine:3.6',
        DockerScriptInit='/sbin/init',
        DockerScriptSetup='',
        DockerScriptStoreData='',
        DockerScriptRestoreDataBeforeSetup='',
        DockerScriptRestoreDataAfterSetup='',
        DockerScriptUpdateAvailable='',
        DockerScriptUpdatePackages='',
        DockerScriptUpdateRelease='',
        DockerScriptUpdateAppVersion='',
    )
    return app


def tiny_app_apache(name: str | None = None, version: str | None = None) -> App:
    name = name or get_app_name()
    version = version or '1'
    app = App(name=name, version=version, build_package=False)
    app.set_ini_parameter(
        DockerImage='docker-test.software-univention.de/nimmis/alpine-apache',
        DockerScriptInit='/boot.sh',
        DockerScriptSetup='',
        DockerScriptStoreData='',
        DockerScriptRestoreDataBeforeSetup='',
        DockerScriptRestoreDataAfterSetup='',
        DockerScriptUpdateAvailable='',
        DockerScriptUpdatePackages='',
        DockerScriptUpdateRelease='',
        DockerScriptUpdateAppVersion='',
    )
    return app


def get_docker_appbox_ucs() -> str:
    # should be in line with get_docker_appbox_image()
    return '4.4'


def get_docker_appbox_image() -> str:
    image_name = f'docker-test.software-univention.de/ucs-appbox-amd64:{get_docker_appbox_ucs()}-8'
    print('Using %s' % image_name)
    return image_name


def docker_login(server: str = 'docker.software-univention.de') -> None:
    cmd = ['docker', 'login', '-u', 'ucs', '-p', 'readonly', server]
    error_handling_call(cmd, exc=DockerFailure)


def docker_pull(image: str, server: str = 'docker.software-univention.de') -> None:
    cmd = ['docker', 'pull', '%s/%s' % (server, image)]
    error_handling_call(cmd, exc=DockerFailure)


def docker_image_is_present(imgname: str) -> bool:
    cmd = ['docker', 'inspect', imgname]
    return subprocess.call(cmd, stdout=subprocess.DEVNULL) == 0


def remove_docker_image(imgname: str) -> bool:
    cmd = ['docker', 'rmi', imgname]
    return subprocess.call(cmd) == 0


def pull_docker_image(imgname: str) -> bool:
    cmd = ['docker', 'pull', imgname]
    return subprocess.call(cmd) == 0


def restart_docker() -> bool:
    cmd = ['systemctl', 'restart', 'docker']
    return subprocess.call(cmd) == 0


def get_app_name() -> str:
    """returns a valid app name"""
    return random_name()


def get_app_version() -> str:
    return random_version()


def copy_package_to_appcenter(ucs_version: str, app_directory: str, package_name: str) -> None:
    comp_dir = REPO_DIR / ucs_version / 'maintained' / 'component'
    pkg_dir = comp_dir / app_directory / 'all'

    print('cp %s %s' % (package_name, pkg_dir))
    pkg_dir.mkdir(0o755, parents=True, exist_ok=True)
    shutil.copy(package_name, pkg_dir.as_posix())

    print('Creating packages in local repository:')
    pkg = pkg_dir / "Packages"
    subprocess.run(["apt-ftparchive", "packages", f"{app_directory}/all"], cwd=comp_dir, stdout=pkg.open("wb"), check=True)
    subprocess.run(["gzip", "--force", "--keep", "--no-name", pkg.as_posix()], check=True)


def error_handling_call(cmd: Sequence[str] | str, exc: type[BaseException] = BaseFailure) -> None:
    try:
        print(subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('UTF-8', 'replace'))
    except subprocess.CalledProcessError as ex:
        raise exc('%s: %s' % (ex, ex.output.decode('UTF-8', 'replace'))) from ex


class App:

    def __init__(
        self,
        name: str,
        version: str,
        container_version: str | None = None,
        app_directory_suffix: str | None = None,
        package_name: str | None = None,
        build_package: bool = True,
        call_join_scripts: bool = True,
    ) -> None:
        self.app_name = name
        self.app_version = version
        self.call_join_scripts = call_join_scripts
        self.app_directory_suffix = app_directory_suffix or random_version()
        self.app_directory = '%s_%s' % (self.app_name, self.app_directory_suffix)
        self.package_name = package_name or get_app_name()
        self.package_version = '%s.%s' % (version, get_app_version())

        self.ucr = ConfigRegistry()
        self.ucr.load()

        if build_package:
            self.package: DebianPackage | None = DebianPackage(name=self.package_name, version=self.package_version)
            self.package.build()
        else:
            self.package = None

        self.ini: dict[str, str] = {
            'ID': self.app_name,
            'Code': self.app_name[0:2],
            'Name': self.app_name,
            'Version': self.app_version,
            'NotifyVendor': "False",
            'Categories': 'System services',
            'Logo': '%s.svg' % self.app_name,
            'ServerRole': 'domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver',
        }
        if self.package:
            self.ini['DefaultPackages'] = self.package_name

        self.scripts: dict[str, str] = {}

        if not container_version:
            self.ucs_version = self.ucr.get('version/version')
        else:
            self.ucs_version = container_version
            # make sure version of default appbox image is part of SupportedUCSVersions
            self.ini['SupportedUCSVersions'] = '%s-0,4.3-0,%s-0' % (container_version, self.ucr.get('version/version'))

        self.installed = False

        self.admin_user = self.ucr.get('tests/domainadmin/account').split(',')[0][len('uid='):]
        self.admin_pwdfile = self.ucr.get('tests/domainadmin/pwdfile')

        print(repr(self))

    def __repr__(self) -> str:
        return '%s(app_name=%r, app_version=%r)' % (self.__class__.__name__, self.app_name, self.app_version)

    def set_ini_parameter(self, **kwargs: str) -> None:
        for key, value in kwargs.items():
            print('set_ini_parameter(%s=%s)' % (key, value))
            self.ini[key] = value

    def add_to_local_appcenter(self) -> None:
        self._dump_ini()
        if self.package:
            copy_package_to_appcenter(self.ucs_version, self.app_directory, self.package.get_binary_name())
        self._dump_scripts()

    def add_script(self, **kwargs: str) -> None:
        for key, value in kwargs.items():
            self.scripts[key] = value

    def install(self) -> None:
        print('App.install()')
        self._update()
        cmd = ['univention-app', 'install', '--noninteractive', '--username', self.admin_user, '--pwdfile', self.admin_pwdfile]
        if not self.call_join_scripts:
            cmd.append('--do-not-call-join-scripts')
        cmd.append('%s=%s' % (self.app_name, self.app_version))
        print(cmd)
        error_handling_call(cmd, exc=AppFailure)

        self.reload_container_id()

        self.installed = True

    def reload_container_id(self) -> None:
        self.ucr.load()
        self.container_id = self.ucr.get('appcenter/apps/%s/container' % self.app_name)

    def file(self, fname: str) -> Path:
        dirname = subprocess.check_output(['docker', 'inspect', '--format={{.GraphDriver.Data.MergedDir}}', self.container_id], text=True).strip()
        return Path(dirname) / fname.lstrip('/')

    def configure(self, args: Mapping[str, str | None]) -> None:
        set_vars = []
        unset_vars = []
        for key, value in args.items():
            if value is None:
                unset_vars.append(key)
            else:
                set_vars.append('%s=%s' % (key, value))
        cmd = ['univention-app', 'configure', '%s=%s' % (self.app_name, self.app_version)]
        if set_vars:
            cmd.extend(['--set'] + set_vars)
        if unset_vars:
            cmd.extend(['--unset'] + unset_vars)
        error_handling_call(cmd, exc=AppFailure)

    def install_via_umc(self) -> None:

        def _thread(event: threading.Event, options: dict) -> None:
            try:
                client.umc_command("appcenter/keep_alive")
            finally:
                event.set()

        print('App.umc_install()')
        client = umc.Client.get_test_connection()
        client.umc_get('session-info')

        options = {
            "function": 'install',
            "application": self.app_name,
            "app": self.app_name,
            "force": True,
        }
        resp = client.umc_command('appcenter/docker/invoke', options).result
        progress_id = resp.get('id')
        if not resp:
            raise UMCFailure(resp, None)
        errors = []
        finished = False
        progress: Any = None
        event = threading.Event()
        threading.Thread(target=_thread, args=(event, options)).start()
        while not (event.wait(3) and finished):
            options = {"progress_id": progress_id}
            progress = client.umc_command('appcenter/docker/progress', options, print_request_data=False, print_response=False).result
            progress.get('info', None)
            for i in progress.get('intermediate', []):
                if i['level'] in ['ERROR', 'CRITICAL']:
                    errors.append(i)
            finished = progress.get('finished', False)
        if not progress['result'].get('success', False) or not progress['result'].get('can_continue', False):
            raise UMCFailure(progress, errors)
        self.reload_container_id()
        self.installed = True
        if errors:
            raise UMCFailure(None, errors)

    def _update(self) -> None:
        error_handling_call(['univention-app', 'update'], exc=AppFailure)

    def register(self) -> None:
        print('App.register()')
        cmd = ['univention-app', 'register', '--app']
        print(cmd)
        error_handling_call(cmd, exc=AppFailure)

    def upgrade(self) -> None:
        print('App.upgrade()')
        self._update()
        cmd = ['univention-app', 'upgrade', '--noninteractive', '--username', self.admin_user, '--pwdfile', self.admin_pwdfile]
        if not self.call_join_scripts:
            cmd.append('--do-not-call-join-scripts')
        cmd.append('%s=%s' % (self.app_name, self.app_version))
        print(cmd)
        error_handling_call(cmd, exc=AppFailure)
        self.reload_container_id()
        self.installed = True

    def verify(self, joined: bool = True) -> None:
        print('App.verify(%r)' % (joined,))
        error_handling_call(['univention-app', 'status', '%s=%s' % (self.app_name, self.app_version)], exc=AppFailure)

        if joined:
            error_handling_call(['docker', 'exec', self.container_id, 'univention-check-join-status'], exc=AppFailure)

        if self.package:
            try:
                output = subprocess.check_output(['univention-app', 'shell', '%s=%s' % (self.app_name, self.app_version), 'dpkg-query', '-W', self.package_name], text=True)
                expected_output1 = '%s\t%s\r\n' % (self.package_name, self.package_version)
                expected_output2 = '%s\t%s\n' % (self.package_name, self.package_version)
                if output not in [expected_output1, expected_output2]:
                    raise AppFailure('%r != %r' % (output, expected_output2))
            except subprocess.CalledProcessError as exc:
                raise AppFailure('univention-app shell failed') from exc

    def uninstall(self) -> None:
        print('App.uninstall()')
        if self.installed:
            cmd = ['univention-app', 'remove', '--noninteractive', '--username', self.admin_user, '--pwdfile', self.admin_pwdfile]
            if not self.call_join_scripts:
                cmd.append('--do-not-call-join-scripts')
            cmd.append('%s=%s' % (self.app_name, self.app_version))
            print(cmd)
            error_handling_call(cmd, exc=AppFailure)

    def execute_command_in_container(self, cmd: str) -> str:
        print('Execute: %s' % cmd)
        return subprocess.check_output(['docker', 'exec', self.container_id, 'sh', '-c', cmd], stderr=subprocess.STDOUT, text=True)

    def remove(self) -> None:
        print('App.remove()')
        if self.package:
            self.package.remove()

    def _dump_ini(self) -> None:
        vdir = META_DIR / self.ucs_version
        vdir.mkdir(0o755, parents=True, exist_ok=True)
        v41dir = META_DIR / '4.1'
        if self.ucs_version == '4.2' and not v41dir.exists():
            v41dir.mkdir(0o755)

        target = vdir / f'{self.app_directory}.ini'
        with target.open("w") as f:
            print('Write ini file: %s' % target)
            f.write('[Application]\n')
            print('[Application]')
            for key, val in self.ini.items():
                f.write('%s: %s\n' % (key, val))
                print('%s: %s' % (key, val))
            print()

        svg = vdir / self.ini.get('Logo')
        svg.write_bytes(Path(__file__).with_name("dummy.svg").read_bytes())

    def _dump_scripts(self) -> None:
        for script, content in self.scripts.items():
            comp_dir = REPO_DIR / self.ucs_version / 'maintained' / 'component' / self.app_directory
            comp_dir.mkdir(0o755, parents=True, exist_ok=True)

            target = comp_dir / script
            print(f'Create {target}: {content!r}')
            target.write_text(content)

    def configure_tinyapp_modproxy(self) -> None:
        fqdn = '%(hostname)s.%(domainname)s' % self.ucr
        self.execute_command_in_container('apk update --allow-untrusted')
        self.execute_command_in_container('apk upgrade')
        self.execute_command_in_container('apk add apache2-ssl')
        self.execute_command_in_container("sed -i 's#/var/www/localhost/htdocs#/web/html#g' /etc/apache2/conf.d/ssl.conf")
        self.execute_command_in_container("sed -i 's#/var/www/localhost/cgi-bin#/web/cgi-bin#g' /etc/apache2/conf.d/ssl.conf")
        self.execute_command_in_container("sed -i 's#www.example.com#%s#g' /etc/apache2/conf.d/ssl.conf" % fqdn)
        self.execute_command_in_container('cp /etc/apache2/conf.d/ssl.conf /web/config/conf.d')
        self.execute_command_in_container('sv restart apache2')
        self.execute_command_in_container('cat  /etc/ssl/apache2/server.pem > /root/server.pem')
        self.execute_command_in_container('mkdir /web/html/%s' % self.app_name)
        self.execute_command_in_container('/bin/sh -c "echo TEST-%s > /web/html/%s/index.txt"' % (self.app_name, self.app_name))

    def verify_basic_modproxy_settings_tinyapp(self, http: bool = True, https: bool = True):
        return self.verify_basic_modproxy_settings(http=http, https=https, verify=False)

    def verify_basic_modproxy_settings(
        self,
        http: bool = True,
        https: bool = True,
        verify: str | bool = '/etc/univention/ssl/ucsCA/CAcert.pem',
    ) -> None:
        fqdn = '%(hostname)s.%(domainname)s' % self.ucr
        test_string = 'TEST-%s\n' % self.app_name
        protocols = {'http': http, 'https': https}
        for protocol, should_succeed in protocols.items():
            response = requests.get(f'{protocol}://{fqdn}/{self.app_name}/index.txt', verify=verify)
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                if should_succeed:
                    raise

            if should_succeed:
                assert response.text == test_string
            else:
                assert response.text != test_string


class Appcenter:

    def __init__(self, version: str | None = None) -> None:
        self.meta_inf_created = False
        self.univention_repository_created = False
        self.ucr = UCSTestConfigRegistry()
        self.ucr.load()
        self.apps: list[App] = []

        paths = [p for p in (META_DIR, REPO_DIR) if p.exists()]
        if paths:
            for p in paths:
                shutil.rmtree(p.as_posix(), ignore_errors=True)
            raise BaseFailure(f'{paths} already existed')

        if version:
            self.versions = [version]
            support = f'[{version}\nSupportedUCSVersions={version}\n'
        else:
            self.versions = VERSIONS
            support = SUPPORT

        for version in self.versions:
            self.add_ucs_version_to_appcenter(version)

        (META_DIR / 'ucs.ini').write_text(support)
        (META_DIR / 'suggestions.json').write_text('{"v1": []}')

        print(repr(self))

    def add_ucs_version_to_appcenter(self, version: str) -> None:
        if not META_DIR.exists():
            META_DIR.mkdir(0o755, parents=True)
            self.meta_inf_created = True

        if not REPO_DIR.exists():
            REPO_DIR.mkdir(0o755, parents=True)
            self.univention_repository_created = True

        (REPO_DIR / version / 'maintained' / 'component').mkdir(0o755, parents=True, exist_ok=True)
        (META_DIR / version).mkdir(0o755, exist_ok=True)

        categories = META_DIR / 'categories.ini'
        if not categories.exists():
            categories.write_text(CATEGORIES)

        app_categories = META_DIR / 'app-categories.ini'
        if not app_categories.exists():
            app_categories.write_text(APP_CATEGORIES)
            (META_DIR / 'rating.ini').write_text('# rating stuff\n')
            (META_DIR / 'license_types.ini').write_text('# license stuff')

        handler_set([
            'update/secure_apt=no',
            'appcenter/index/verify=false',
            'repository/app_center/server=http://%(hostname)s.%(domainname)s' % self.ucr,
        ])

    def update(self) -> None:
        fqdn = '%(hostname)s.%(domainname)s' % self.ucr
        for ver_dir in META_DIR.glob('[1-9]*.[0-9]*/'):
            ver = ver_dir.name
            print('create_appcenter_json.py for %s' % ver)
            idx_file = ver_dir / 'index.json.gz'
            tar_file = ver_dir / 'all.tar'
            subprocess.check_call([
                './create_appcenter_json.py',
                '-u', ver,
                '-d', f'{BASE_DIR}',
                '-o', f'{idx_file}',
                '-s', f'http://{fqdn}',
                '-t', f'{tar_file}',
            ])
            path = tar_file.with_suffix(f'{tar_file.suffix}.gz').relative_to(BASE_DIR)
            subprocess.check_call([
                'zsyncmake',
                '-u', f'http://{fqdn}/{path}',
                '-z',
                '-o', f'{tar_file}.zsync',
                f'{tar_file}',
            ])
        subprocess.check_call(['univention-app', 'update'])

    def cleanup(self) -> None:
        if self.meta_inf_created:
            shutil.rmtree(META_DIR.as_posix())
        if self.univention_repository_created:
            shutil.rmtree(REPO_DIR.as_posix())
        self.ucr.revert_to_original_registry()

    def __enter__(self) -> Appcenter:
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        if exc_type:
            print(f'Cleanup after exception: {exc_val}')
        try:
            for app in self.apps:
                app.uninstall()
        except Exception as ex:
            print(f'removing app {app} in __exit__ failed with: {ex}')
        finally:
            self.cleanup()


CATEGORIES = '''\
[de]
Administration=Administration
Business=Business
Collaboration=Collaboration
Education=Schule
System services=Systemdienste
UCS components=UCS-Komponenten
Virtualization=Virtualisierung
'''
APP_CATEGORIES = '''\
[de]
Backup & Archiving=Backup & Archivierung
Education=Bildung
CMS=CMS
Collaboration & Groupware=Collaboration & Groupware
CRM & ERP=CRM & ERP
Desktop=Desktop
Device Management=Device Management
File Sync & Share=File Sync & Share
Identity Management=Identity Management
Infrastructure=Infrastruktur
Mail & Messaging=Mail & Messaging
Office=Office
Printing=Drucken
Project Management=Projekt Management
Security=Sicherheit
Storage=Speicher
Telephony=Telefonie
Virtualization=Virtualisierung
'''
SUPPORT = '''\
[5.0]
SupportedUCSVersions=5.0, 4.4, 4.3
[4.4]
SupportedUCSVersions=4.4, 4.3, 4.2, 4.1
[4.3]
SupportedUCSVersions=4.3, 4.2, 4.1
'''
VERSIONS = ['4.1', '4.2', '4.3', '4.4', '5.0']
