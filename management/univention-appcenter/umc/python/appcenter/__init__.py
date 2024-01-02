#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: software management
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2011-2024 Univention GmbH
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

import json
import locale
import logging
import os
import time
from base64 import b64decode, b64encode
from contextlib import contextmanager
from json import load

import apt  # for independent apt.Cache

import univention.management.console as umc
import univention.management.console.modules as umcm
from univention.appcenter.actions import get_action
from univention.appcenter.app_cache import AppCenterCache, Apps, default_server
from univention.appcenter.exceptions import Abort, AppCenterError, NetworkError
from univention.appcenter.install_checks import check
from univention.appcenter.log import get_base_logger, log_to_logfile
from univention.appcenter.packages import LOCK_FILE, get_package_manager, package_lock, reload_package_manager
from univention.appcenter.settings import FileSetting, PasswordFileSetting
from univention.appcenter.ucr import ucr_instance, ucr_save
from univention.appcenter.udm import _update_modules
from univention.appcenter.utils import (
    app_is_running, call_process, docker_bridge_network_conflict, docker_is_running, get_local_fqdn,
    resolve_dependencies, send_information,
)
from univention.lib.package_manager import LockError, PackageManager
from univention.lib.umc import Client, ConnectionError, HTTPError
from univention.management.console.log import MODULE
from univention.management.console.modules.decorators import (
    SimpleThread, multi_response, require_password, sanitize, sanitize_list, simple_response, threaded,
)
from univention.management.console.modules.mixins import ProgressMixin
from univention.management.console.modules.sanitizers import (
    BooleanSanitizer, ChoicesSanitizer, DictSanitizer, ListSanitizer, MappingSanitizer, PatternSanitizer,
    StringSanitizer,
)
from univention.updater.tools import UniventionUpdater

from .constants import COMPONENT_BASE, DEPRECATED_PARAMS, ONLINE_BASE, PUT_PARAMETER_ERROR, PUT_SUCCESS, PUT_WRITE_ERROR
from .sanitizers import (
    AppSanitizer, add_components_sanitizer, advanced_components_sanitizer, basic_components_sanitizer, error_handling,
)
from .util import ComponentManager, create_url, install_opener, scheme_is_http, set_save_commit_load


_ = umc.Translation('univention-management-console-module-appcenter').translate


class NoneCandidate(object):
    """
    Mock object if package has no candidate
    (may happen without network connection)
    """

    def __init__(self):
        self.summary = self.version = self.description = self.priority = self.section = _('Package not found in repository')
        self.installed_size = 0


class UMCProgressHandler(logging.Handler):
    def __init__(self, progress):
        super(UMCProgressHandler, self).__init__()
        self.progress = progress

    def emit(self, record):
        msg = record.msg
        if isinstance(record.msg, Exception):
            msg = str(msg)
        detail = {'level': record.levelname, 'message': msg}
        self.progress.progress(detail=detail, message=msg)


class ProgressInfoHandler(logging.Handler):
    def __init__(self, package_manager):
        super(ProgressInfoHandler, self).__init__()
        self.state = package_manager.progress_state

    def emit(self, record):
        msg = record.msg
        if isinstance(record.msg, Exception):
            msg = str(msg)
        if record.levelno >= logging.ERROR:
            self.state.error(msg)
        else:
            self.state.info(msg)


class ProgressPercentageHandler(ProgressInfoHandler):
    def emit(self, record):
        percentage = float(record.msg)
        self.state.percentage(percentage)
        self.state._finished = percentage >= 100


def require_apps_update(func):
    def _deferred(self, *args, **kwargs):
        if not self.update_applications_done:
            self.update_applications()
        return func(self, *args, **kwargs)
    return _deferred


class Instance(umcm.Base, ProgressMixin):
    def init(self):
        os.umask(0o022)  # umc umask is too restrictive for app center as it creates a lot of files in docker containers
        self.ucr = ucr_instance()

        self.update_applications_done = False
        install_opener(self.ucr)
        self._is_working = False

        try:
            self.package_manager = PackageManager(
                info_handler=MODULE.process,
                step_handler=None,
                error_handler=MODULE.warn,
                lock=False,
            )
        except SystemError as exc:
            MODULE.error(str(exc))
            raise umcm.UMC_Error(str(exc), status=500)
        self.package_manager.set_finished()  # currently not working. accepting new tasks
        get_package_manager._package_manager = self.package_manager

        # build cache
        _update_modules()
        get_action('list').get_apps()

        # not initialize here: error prone due to network errors and also kinda slow
        self._uu = None
        self._cm = None

        # in order to set the correct locale
        locale.setlocale(locale.LC_ALL, str(self.locale))

        try:
            log_to_logfile()
        except IOError:
            pass

        # connect univention.appcenter.log to the progress-method
        handler = ProgressInfoHandler(self.package_manager)
        handler.setLevel(logging.INFO)
        get_base_logger().addHandler(handler)

        percentage = ProgressPercentageHandler(self.package_manager)
        percentage.setLevel(logging.DEBUG)
        get_base_logger().getChild('actions.install.progress').addHandler(percentage)
        get_base_logger().getChild('actions.upgrade.progress').addHandler(percentage)
        get_base_logger().getChild('actions.remove.progress').addHandler(percentage)

    def get_updater(self):
        if self._uu is None:
            self._uu = UniventionUpdater(False)
        return self._uu

    def get_component_manager(self):
        if self._cm is None:
            self._cm = ComponentManager(self.ucr, self.get_updater())
        return self._cm

    def error_handling(self, etype, exc, etraceback):
        error_handling(etype, exc, etraceback)
        return super(Instance, self).error_handling(exc, etype, etraceback)

    @simple_response
    def version(self, version=None):
        info = get_action('info')
        ret = info.get_compatibility()
        if not info.is_compatible(version):
            raise umcm.UMC_Error('The App Center version of the requesting host is not compatible with the version of %s (%s)' % (get_local_fqdn(), ret))
        return ret

    @sanitize(
        version=StringSanitizer(required=True),
        function=StringSanitizer(required=False),
    )
    @simple_response
    def version2(self, version, function=None):
        info = get_action('info')
        return {'compatible': info.is_compatible(version, function=function), 'version': info.get_ucs_version()}

    def _remote_appcenter(self, request, host, function=None):
        if host is None:
            raise ValueError('Cannot connect to None')
        if not host.endswith('.%s' % self.ucr.get('domainname')):
            raise ValueError('Only connect to FQDNs within the domain')
        info = get_action('info')
        opts = {'version': info.get_ucs_version()}
        if function is not None:
            opts['function'] = function
        try:
            client = Client(host, request.username, request.password)
            response = client.umc_command('appcenter/version2', opts)
        except (HTTPError) as exc:
            raise umcm.UMC_Error(_('Problems connecting to {0} ({1}). Please update {0}!').format(host, exc.message))
        except (ConnectionError, Exception) as exc:
            raise umcm.UMC_Error(_('Problems connecting to {} ({}).').format(host, str(exc)))
        err_msg = _('The App Center version of the this host ({}) is not compatible with the version of {} ({})').format(opts['version'], host, response.result.get('version'))
        # i guess this is kind of bad
        if response.status != 200:
            raise umcm.UMC_Error(err_msg)
        # remote says he is not compatible
        if response.result.get('compatible', True) is False:
            raise umcm.UMC_Error(err_msg)
        # i'm not compatible
        if not info.is_compatible(response.result.get('version')):
            raise umcm.UMC_Error(err_msg)
        return client

    @sanitize(
        apps=ListSanitizer(AppSanitizer(), required=True),
        action=ChoicesSanitizer(['install', 'upgrade', 'remove'], required=True),
    )
    @simple_response
    def resolve(self, apps, action):
        ret = {}
        ret['apps'] = resolve_dependencies(apps, action)
        ret['auto_installed'] = [app.id for app in ret['apps'] if app.id not in [a.id for a in apps]]
        apps = ret['apps']
        ret['errors'], ret['warnings'] = check(apps, action)
        domain = get_action('domain')
        ret['apps'] = domain.to_dict(apps)
        ret['settings'] = {}
        self.ucr.load()
        for app in apps:
            ret['settings'][app.id] = self._get_config(app, action.title())
        return ret

    @require_apps_update
    @require_password
    @sanitize(
        apps=ListSanitizer(AppSanitizer(), required=True),
        auto_installed=ListSanitizer(required=True),
        action=ChoicesSanitizer(['install', 'upgrade', 'remove'], required=True),
        hosts=DictSanitizer({}, required=True),
        settings=DictSanitizer({}, required=True),
        dry_run=BooleanSanitizer(),
    )
    @simple_response(with_progress=True, with_request=True)
    def run(self, request, progress, apps, auto_installed, action, hosts, settings, dry_run):
        localhost = get_local_fqdn()
        ret = {}
        if dry_run:
            for host in hosts:
                _apps = [next(app for app in apps if app.id == _app) for _app in hosts[host]]
                if host == localhost:
                    ret[host] = self._run_local_dry_run(_apps, action, {}, progress)
                else:
                    try:
                        ret[host] = self._run_remote_dry_run(request, host, _apps, action, auto_installed, {}, progress)
                    except umcm.UMC_Error:
                        ret[host] = {'unreachable': [app.id for app in _apps]}
        else:
            for app in apps:
                for host in hosts:
                    if app.id not in hosts[host]:
                        continue
                    host_result = ret.get(host, {})
                    ret[host] = host_result
                    _settings = {app.id: settings[app.id]}
                    if host == localhost:
                        host_result[app.id] = self._run_local(app, action, _settings, auto_installed, progress)
                    else:
                        host_result[app.id] = self._run_remote(request, host, app, action, auto_installed, _settings, progress)[app.id]
                    if not host_result[app.id]['success']:
                        break
        return ret

    def _run_local_dry_run(self, apps, action, settings, progress):
        if action == 'upgrade':
            apps = [Apps().find_candidate(app) or app for app in apps]
        if len(apps) == 1:
            progress.title = _('%s: Running tests') % apps[0].name
        else:
            progress.title = _('%d Apps: Running tests') % len(apps)
        ret = {}
        ret['errors'], ret['warnings'] = check(apps, action)
        ret['errors'].pop('must_have_no_unmet_dependencies', None)  # has to be resolved prior to this call!
        action = get_action(action)()
        ret['packages'] = {}
        for app in apps:
            args = action._build_namespace(app=[app], dry_run=True, install_master_packages_remotely=False, only_master_packages=False)
            result = action.dry_run(app, args)
            if result is not None:
                ret['packages'][app.id] = result
        return ret

    def _run_local(self, app, action, settings, auto_installed, progress):
        kwargs = {
            'noninteractive': True,
            'auto_installed': auto_installed,
            'skip_checks': ['shall_have_enough_ram', 'shall_only_be_installed_in_ad_env_with_password_service', 'must_not_have_concurrent_operation'],
        }
        if settings.get(app.id):
            kwargs['set_vars'] = settings[app.id]
        if action == 'install':
            progress.title = _('Installing %s') % (app.name,)
        elif action == 'remove':
            progress.title = _('Uninstalling %s') % (app.name,)
        elif action == 'upgrade':
            progress.title = _('Upgrading %s') % (app.name,)
        action = get_action(action)
        handler = UMCProgressHandler(progress)
        handler.setLevel(logging.INFO)
        action.logger.addHandler(handler)
        try:
            package_manager = get_package_manager()
            with package_manager.no_umc_restart():
                success = action.call(app=[app], username=self.username, password=self.password, **kwargs)
                return {'success': success}
        except AppCenterError as exc:
            raise umcm.UMC_Error(str(exc), result={
                "display_feedback": True,
                "title": '%s %s' % (exc.title, exc.info)})
        finally:
            action.logger.removeHandler(handler)

    def _run_remote_dry_run(self, request, host, apps, action, auto_installed, settings, progress):
        return self._run_remote_logic(request, host, apps, action, auto_installed, settings, progress, dry_run=True)

    def _run_remote(self, request, host, app, action, auto_installed, settings, progress):
        return self._run_remote_logic(request, host, [app], action, auto_installed, settings, progress, dry_run=False)

    def _run_remote_logic(self, request, host, apps, action, auto_installed, settings, progress, dry_run):
        if len(apps) == 1:
            progress.title = _('%s: Connecting to %s') % (apps[0].name, host)
        else:
            progress.title = _('%d Apps: Connecting to %s') % (len(apps), host)
        client = self._remote_appcenter(request, host, function='appcenter/run')
        opts = {'apps': [str(app) for app in apps], 'auto_installed': auto_installed, 'action': action, 'hosts': {host: [app.id for app in apps]}, 'settings': settings, 'dry_run': dry_run}
        progress_id = client.umc_command('appcenter/run', opts).result['id']
        while True:
            result = client.umc_command('appcenter/progress', {'progress_id': progress_id}).result
            if result['finished']:
                return result['result'][host]
            progress.title = result['title']
            progress.intermediate.extend(result['intermediate'])
            progress.message = result['message']
            time.sleep(result['retry_after'] / 1000.0)

    @simple_response
    def query(self, quick=False):
        query_cache_file = '/var/cache/univention-appcenter/umc-query.json'
        if quick:
            try:
                with open(query_cache_file) as fd:
                    return json.load(fd)
            except (EnvironmentError, ValueError) as exc:
                MODULE.error('Error returning cached query: %s' % exc)
                return []
        self.update_applications()
        self.ucr.load()
        reload_package_manager()
        list_apps = get_action('list')
        domain = get_action('domain')
        apps = list_apps.get_apps()
        if self.ucr.is_true('appcenter/docker', True):
            if not self._test_for_docker_service():
                raise umcm.UMC_Error(_('The docker service is not running! The App Center will not work properly.') + ' ' + _('Make sure docker.io is installed, try starting the service with "service docker start".'))
        info = domain.to_dict(apps)
        with open(query_cache_file, 'w') as fd:
            json.dump(info, fd)
        return info

    def update_applications(self):
        if self.ucr.is_true('appcenter/umc/update/always', True):
            update = get_action('update')
            try:
                update.call()
            except NetworkError as err:
                raise umcm.UMC_Error(str(err))
            except Abort:
                pass
            self.update_applications_done = True

    def _test_for_docker_service(self):
        if docker_bridge_network_conflict():
            msg = _('A conflict between the system network settings and the docker bridge default network has been detected.') + '\n\n'
            msg += _('Please either configure a different network for the docker bridge by setting the UCR variable docker/daemon/default/opts/bip to a different network and restart the system,') + ' '
            msg += _('or disable the docker support in the AppCenter by setting appcenter/docker to false.')
            raise umcm.UMC_Error(msg)
        if not docker_is_running():
            MODULE.warn('Docker is not running! Trying to start it now...')
            call_process(['invoke-rc.d', 'docker', 'start'])
            if not docker_is_running():
                return False
        return True

    @simple_response
    def suggestions(self, version):
        try:
            cache = AppCenterCache.build(server=default_server())
            cache_file = cache.get_cache_file('.suggestions.json')
            with open(cache_file) as fd:
                json = load(fd)
        except (EnvironmentError, ValueError):
            raise umcm.UMC_Error(_('Could not load suggestions.'))
        else:
            try:
                return json[version]
            except (KeyError, AttributeError):
                raise umcm.UMC_Error(_('Unexpected suggestions data.'))

    @simple_response
    def enable_docker(self):
        if self._test_for_docker_service():
            ucr_save({'appcenter/docker': 'enabled'})
        else:
            raise umcm.UMC_Error(_('Unable to start the docker service!') + ' ' + _('Make sure docker.io is installed, try starting the service with "service docker start".'))

    @require_apps_update
    @require_password
    @simple_response(with_progress=True, with_request=True)
    def sync_ldap(self, request):
        register = get_action('register')
        register.call(username=request.username, password=request.password)

    # used in updater-umc
    @simple_response
    def get_by_component_id(self, component_id):
        domain = get_action('domain')
        if isinstance(component_id, list):
            requested_apps = [Apps().find_by_component_id(cid) for cid in component_id]
            return domain.to_dict(requested_apps)
        else:
            app = Apps().find_by_component_id(component_id)
            if app:
                return domain.to_dict([app])[0]
            else:
                raise umcm.UMC_Error(_('Could not find an application for %s') % component_id)

    # used in updater-umc
    @simple_response
    def app_updates(self):
        upgrade = get_action('upgrade')
        domain = get_action('domain')
        return domain.to_dict(list(upgrade.iter_upgradable_apps()))

    @sanitize(application=StringSanitizer(minimum=1, required=True))
    @simple_response
    def get(self, application):
        list_apps = get_action('list')
        domain = get_action('domain')
        apps = list_apps.get_apps()
        for app in apps:
            if app.id == application:
                break
        else:
            app = None
        if app is None:
            raise umcm.UMC_Error(_('Could not find an application for %s') % (application,))
        return domain.to_dict([app])[0]

    @sanitize(app=AppSanitizer(required=True))
    @simple_response
    def config(self, app, phase):
        self.ucr.load()
        return self._get_config(app, phase)

    def _get_config(self, app, phase):
        autostart = self.ucr.get('%s/autostart' % app.id, 'yes')
        is_running = app_is_running(app)
        values = {}
        for setting in app.get_settings():
            if phase in setting.show or phase in setting.show_read_only:
                value = setting.get_value(app, phase)
                if isinstance(setting, FileSetting) and not isinstance(setting, PasswordFileSetting) and value:
                    value = b64encode(value.encode('utf-8')).decode('ascii')
                values[setting.name] = value
        return {
            'autostart': autostart,
            'is_running': is_running,
            'values': values,
        }

    @sanitize(app=AppSanitizer(required=True), values=DictSanitizer({}))
    @simple_response(with_progress=True)
    def configure(self, progress, app, values, autostart=None):
        for setting in app.get_settings():
            if isinstance(setting, FileSetting) and not isinstance(setting, PasswordFileSetting) and values.get(setting.name):
                values[setting.name] = b64decode(values[setting.name]).decode('utf-8')
        configure = get_action('configure')
        handler = UMCProgressHandler(progress)
        handler.setLevel(logging.INFO)
        configure.logger.addHandler(handler)
        try:
            return configure.call(app=app, set_vars=values, autostart=autostart)
        finally:
            configure.logger.removeHandler(handler)

    @simple_response
    def unpin_app(self, app):
        app = Apps().find(app)
        if app:
            pin = get_action('pin')
            pin.call(app=app, revert=True)

    @sanitize(app=AppSanitizer(required=True), mode=ChoicesSanitizer(['start', 'stop']))
    @simple_response
    def app_service(self, app, mode):
        service = get_action(mode)
        service.call(app=app)

    @sanitize(app=AppSanitizer(required=False), action=ChoicesSanitizer(['get', 'buy', 'search', 'vote']), value=StringSanitizer())
    @simple_response
    def track(self, app, action, value):
        send_information(action, app=app, value=value)

    @contextmanager
    def locked(self):
        try:
            if self._working():
                raise LockError()
            with package_lock():
                yield
        except LockError:
            raise umcm.UMC_Error(_('Another package operation is in progress'))

    @threaded
    def keep_alive(self, request):
        """
        Fix for Bug #30611: UMC kills appcenter module
        if no request is sent for $(ucr get umc/module/timeout).
        this happens if a user logs out during a very long installation.
        this function will be run by the frontend to always have one connection open
        to prevent killing the module.
        """
        while self._working():
            time.sleep(1)

    @simple_response
    def ping(self):
        return True

    @simple_response
    def buy(self, application):
        app = Apps().find(application)
        if not app or not app.shop_url:
            return None
        ret = {}
        ret['key_id'] = self.ucr.get('license/uuid')
        ret['ucs_version'] = self.ucr.get('version/version')
        ret['app_id'] = app.id
        ret['app_version'] = app.version
        # ret['locale'] = locale.getlocale()[0] # done by frontend
        ret['user_count'] = None  # FIXME: get users and computers from license
        ret['computer_count'] = None
        return ret

    @simple_response
    def enable_disable_app(self, application, enable=True):
        app = Apps().find(application)
        if not app:
            return
        stall = get_action('stall')
        stall.call(app=app, undo=enable)

    @simple_response
    def packages_sections(self):
        """fills the 'sections' combobox in the search form"""
        sections = set()
        cache = apt.Cache()
        for package in cache:
            sections.add(package.section)

        return sorted(sections)

    @sanitize(pattern=PatternSanitizer(required=True))
    @simple_response
    def packages_query(self, pattern, section='all', key='package'):
        """Query to fill the grid. Structure is fixed here."""
        result = []
        for package in self.package_manager.packages(reopen=True):
            if section in ('all', package.section):
                toshow = False
                if pattern.pattern == '^.*$':
                    toshow = True
                elif key == 'package' and pattern.search(package.name):
                    toshow = True
                elif key == 'description' and package.candidate and pattern.search(package.candidate.raw_description):
                    toshow = True
                if toshow:
                    result.append(self._package_to_dict(package, full=False))
        return result

    @simple_response
    def packages_get(self, package):
        """retrieves full properties of one package"""
        package = self.package_manager.get_package(package)
        if package is not None:
            return self._package_to_dict(package, full=True)
        else:
            # TODO: 404?
            return {}

    @sanitize(
        function=MappingSanitizer({
            'install': 'install',
            'upgrade': 'install',
            'uninstall': 'remove',
        }, required=True),
        packages=ListSanitizer(StringSanitizer(minimum=1), required=True),
        update=BooleanSanitizer(),
    )
    @simple_response
    def packages_invoke_dry_run(self, packages, function, update):
        if update:
            self.package_manager.update()
        packages = self.package_manager.get_packages(packages)
        kwargs = {'install': [], 'remove': [], 'dry_run': True}
        if function == 'install':
            kwargs['install'] = packages
        else:
            kwargs['remove'] = packages
        return dict(zip(['install', 'remove', 'broken'], self.package_manager.mark(**kwargs)))

    @sanitize(
        function=MappingSanitizer({
            'install': 'install',
            'upgrade': 'install',
            'uninstall': 'remove',
        }, required=True),
        packages=ListSanitizer(StringSanitizer(minimum=1), required=True),
    )
    def packages_invoke(self, request):
        """executes an installer action"""
        packages = request.options.get('packages')
        function = request.options.get('function')

        try:
            if self._working():
                # make it multi-tab safe (same session many buttons to be clicked)
                raise LockError()
            with self.package_manager.locked(reset_status=True):
                not_found = [pkg_name for pkg_name in packages if self.package_manager.get_package(pkg_name) is None]
                self.finished(request.id, {'not_found': not_found})

                if not not_found:
                    def _thread(package_manager, function, packages):
                        with package_manager.locked(set_finished=True):
                            with package_manager.no_umc_restart():
                                if function == 'install':
                                    package_manager.install(*packages)
                                else:
                                    package_manager.uninstall(*packages)

                    def _finished(thread, result):
                        if isinstance(result, BaseException):
                            MODULE.warn('Exception during %s %s: %r' % (function, packages, str(result)))
                    thread = SimpleThread('invoke', _thread, _finished)
                    thread.run(self.package_manager, function, packages)
                else:
                    self.package_manager.set_finished()  # nothing to do, ready to take new commands
        except LockError:
            # make it thread safe: another process started a package manager
            # this module instance already has a running package manager
            raise umcm.UMC_Error(_('Another package operation is in progress'))

    @contextmanager
    def is_working(self):
        self._is_working = True
        yield
        self._is_working = False

    def _working(self):
        return self._is_working or os.path.exists(LOCK_FILE) or not self.package_manager.progress_state._finished

    @simple_response
    def working(self):
        # TODO: PackageManager needs is_idle() or something
        #   preferably the package_manager can tell what is currently executed:
        #   package_manager.is_working() => False or _('Installing PKG')
        return self._working()

    @simple_response
    def custom_progress(self):
        timeout = 5
        ret = self.package_manager.poll(timeout)
        ret['finished'] = not self._working()
        return ret

    def _package_to_dict(self, package, full):
        """
        Helper that extracts properties from a 'apt_pkg.Package' object
        and stores them into a dictionary. Depending on the 'full'
        switch, stores only limited (for grid display) or full
        (for detail view) set of properties.
        """
        installed = package.installed  # may be None
        found = True
        candidate = package.candidate
        found = candidate is not None
        if not found:
            candidate = NoneCandidate()

        result = {
            'package': package.name,
            'installed': package.is_installed,
            'upgradable': package.is_upgradable and found,
            'summary': candidate.summary,
        }

        # add (and translate) a combined status field
        # *** NOTE *** we translate it here: if we would use the Custom Formatter
        #        of the grid then clicking on the sort header would not work.
        if package.is_installed:
            if package.is_upgradable:
                result['status'] = _('upgradable')
            else:
                result['status'] = _('installed')
        else:
            result['status'] = _('not installed')

        # additional fields needed for detail view
        if full:
            # Some fields differ depending on whether the package is installed or not:
            if package.is_installed:
                result['section'] = installed.section
                result['priority'] = installed.priority or ''
                result['summary'] = installed.summary   # take the current one
                result['description'] = installed.description
                result['installed_version'] = installed.version
                result['size'] = installed.installed_size
                if package.is_upgradable:
                    result['candidate_version'] = candidate.version
            else:
                del result['upgradable']  # not installed: don't show 'upgradable' at all
                result['section'] = candidate.section
                result['priority'] = candidate.priority or ''
                result['description'] = candidate.description
                result['size'] = candidate.installed_size
                result['candidate_version'] = candidate.version
            # format size to handle bytes
            size = result['size']
            byte_mods = ['B', 'kB', 'MB']
            for byte_mod in byte_mods:  # noqa: B007
                if size < 10000:
                    break
                size = float(size) / 1000  # MB, not MiB
            else:
                size = size * 1000  # once too often
            format_string = '%d %s' if size == int(size) else '%.2f %s'
            result['size'] = format_string % (size, byte_mod)

        return result

    @simple_response
    def components_query(self):
        """Returns components list for the grid in the ComponentsPage."""
        # be as current as possible.
        self.get_updater().ucr_reinit()
        self.ucr.load()

        return [
            self.get_component_manager().component(comp.name)
            for comp in self.get_updater().get_components(all=True)
        ]

    @sanitize_list(StringSanitizer())
    @multi_response(single_values=True)
    def components_get(self, iterator, component_id):
        # be as current as possible.
        self.get_updater().ucr_reinit()
        self.ucr.load()
        for component_id in iterator:
            items = self.get_component_manager().component(component_id).copy()
            items['server'] = create_url(items['server'], items['prefix'], items['username'], items['password'], items['port'])
            for deprecated in DEPRECATED_PARAMS:
                del items[deprecated]
            yield items

    @sanitize_list(DictSanitizer({'object': advanced_components_sanitizer}))
    @multi_response
    def components_put(self, iterator, object):
        """Writes back one or more component definitions."""
        # umc.widgets.Form wraps the real data into an array:
        #
        #    [
        #        {
        #            'object' : { ... a dict with the real data .. },
        #            'options': None
        #        },
        #        ... more such entries ...
        #    ]
        #
        # Current approach is to return a similarly structured array,
        # filled with elements, each one corresponding to one array
        # element of the request:
        #
        #    [
        #        {
        #            'status'    :    a number where 0 stands for success, anything else
        #                            is an error code
        #            'message'    :    a result message
        #            'object'    :    a dict of field -> error message mapping, allows
        #                            the form to show detailed error information
        #        },
        #        ... more such entries ...
        #    ]
        # check if scheme of server is correct
        for repo, in iterator:
            name = repo['name']
            named_component_base = '%s/%s' % (COMPONENT_BASE, name)
            for key, value in repo.items():
                if key.endswith("server") and not scheme_is_http(value):
                    msg = _("Invalid scheme, use http or https: %(base)r/%(key)r: %(value)r") % {'base': named_component_base, 'key': key, 'value': value}
                    yield [{'message': msg, 'status': PUT_PARAMETER_ERROR}]
                    return
        with set_save_commit_load(self.ucr) as super_ucr:
            for repo, in iterator:
                try:
                    name = repo['name']
                    named_component_base = '%s/%s' % (COMPONENT_BASE, name)
                    for deprecated in DEPRECATED_PARAMS:
                        if self.ucr.get(f'{named_component_base}/{deprecated}', ''):
                            super_ucr.set_registry_var(f'{named_component_base}/{deprecated}', None)
                except Exception as e:
                    MODULE.warn("   !! Writing UCR failed: %s" % str(e))
                    yield [{'message': str(e), 'status': PUT_WRITE_ERROR}]
                    return
                yield self.get_component_manager().put(repo, super_ucr)

        self.package_manager.update()

    # do the same as components_put (update)
    # but don't allow adding an already existing entry
    components_add = sanitize_list(DictSanitizer({'object': add_components_sanitizer}))(components_put)
    components_add.__name__ = 'components_add'

    @sanitize_list(StringSanitizer())
    @multi_response(single_values=True)
    def components_del(self, iterator, component_id):
        for component_id in iterator:
            yield self.get_component_manager().remove(component_id)
        self.package_manager.update()

    @multi_response
    def settings_get(self, iterator):
        # *** IMPORTANT *** Our UCR copy must always be current. This is not only
        #    to catch up changes made via other channels (ucr command line etc),
        #    but also to reflect the changes we have made ourselves!
        self.ucr.load()

        path = self.ucr.get(f'{ONLINE_BASE}/prefix', '')
        server = self.ucr.get(f'{ONLINE_BASE}/server', '')
        port = self.ucr.get(f'{ONLINE_BASE}/port', '')

        for _ in iterator:
            yield {
                'server': create_url(server, path, '', '', port),
            }

    @sanitize_list(
        DictSanitizer({'object': basic_components_sanitizer}),
        min_elements=1,
        max_elements=1,  # moduleStore with one element...
    )
    @multi_response
    def settings_put(self, iterator, object):
        # FIXME: returns values although it should yield (multi_response)
        # check if scheme of server is correct
        for repo, in iterator:
            for key, value in repo.items():
                if key.endswith("server") and not scheme_is_http(value):
                    msg = _("Invalid scheme, use http or https: %(base)r/%(key)r: %(value)r") % {'base': ONLINE_BASE, 'key': key, 'value': value}
                    return [{'message': msg, 'status': PUT_PARAMETER_ERROR}]
        # Set values into our UCR copy.
        try:
            with set_save_commit_load(self.ucr) as super_ucr:
                for repo, in iterator:
                    for key, value in repo.items():
                        MODULE.info("   ++ Setting new value for '%s' to '%s'" % (key, value))
                        super_ucr.set_registry_var('%s/%s' % (ONLINE_BASE, key), value)
                super_ucr.changed()
        except Exception as e:
            MODULE.warn("   !! Writing UCR failed: %s" % str(e))
            return [{'message': str(e), 'status': PUT_WRITE_ERROR}]

        # delete deprecated ucr variables if still exist.
        try:
            with set_save_commit_load(self.ucr) as super_ucr:
                for deprecated in DEPRECATED_PARAMS:
                    if self.ucr.get(f'{ONLINE_BASE}/{deprecated}', ''):
                        super_ucr.set_registry_var(f'{ONLINE_BASE}/{deprecated}', None)
                super_ucr.changed()
        except Exception as e:
            MODULE.warn("   !! Writing UCR failed: %s" % str(e))
            return [{'message': str(e), 'status': PUT_WRITE_ERROR}]

        self.package_manager.update()

        return [{'status': PUT_SUCCESS}]
