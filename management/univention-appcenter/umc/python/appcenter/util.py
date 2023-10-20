#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  module: software management
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2011-2023 Univention GmbH
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

import os.path
import ssl
from contextlib import contextmanager
from hashlib import md5
from urllib.parse import ParseResult, urlparse

# import psutil # our psutil is outdated. re-enable when methods are supported
from six.moves import http_client, urllib_request

import univention.management.console as umc
from univention.admin.handlers.computers import (
    domaincontroller_backup, domaincontroller_master, domaincontroller_slave, memberserver,
)
from univention.config_registry.frontend import ucr_update
from univention.management.console.ldap import get_machine_connection
from univention.management.console.log import MODULE

from .constants import COMP_PARAMS, COMPONENT_BASE, DEFAULT_ICON, PUT_PROCESSING_ERROR, PUT_SUCCESS, STATUS_ICONS


_ = umc.Translation('univention-management-console-module-appcenter').translate


def rename_app(old_id, new_id, component_manager, package_manager):
    from univention.management.console.modules.appcenter.app_center import Application
    app = Application.find(old_id)
    if not app:
        app = Application.find(new_id)
    if not app:
        MODULE.error('Found neither OLD_ID nor NEW_ID.\n')
        raise ValueError([old_id, new_id])

    if not app.is_installed(package_manager, strict=False):
        MODULE.process(f'{app.name} is not installed. Fine, nothing to do.\n')
        return

    app.set_id(old_id)
    app.unregister_all_and_register(None, component_manager, package_manager)
    app.tell_ldap(component_manager.ucr, package_manager, inform_about_error=False)

    app.set_id(new_id)
    app.register(component_manager, package_manager)
    app.tell_ldap(component_manager.ucr, package_manager, inform_about_error=False)


def get_hosts(module, lo, ucr=None):
    _hosts = module.lookup(None, lo, None)
    hosts = []
    local_hostname = ucr.get('hostname') if ucr is not None else None
    for host in _hosts:
        host.open()  # needed for fqdn. it may be enough to return 'name'
        hostname = host.info.get('name')
        if hostname == local_hostname:
            MODULE.process(f'{host.dn} is me. Skipping')
            continue
        if 'fqdn' not in host.info:
            MODULE.warn(f'{host.dn} does not have an FQDN. Skipping')
            continue
        hosts.append(host)
    MODULE.process('Found hosts: %r' % [host.info.get('name') for host in hosts])
    return hosts


def get_master(lo):
    MODULE.process('Searching Primary Directory Node')
    return get_hosts(domaincontroller_master, lo)[0].info['fqdn']


def get_all_backups(lo, ucr=None):
    MODULE.process('Searching Backup Directory Node')
    return [host.info['fqdn'] for host in get_hosts(domaincontroller_backup, lo, ucr)]


def get_all_hosts(lo=None, ucr=None):
    if lo is None:
        lo = get_machine_connection(write=False)[0]
        if lo is None:
            return []
    return get_hosts(domaincontroller_master, lo, ucr) + \
        get_hosts(domaincontroller_backup, lo, ucr) + \
        get_hosts(domaincontroller_slave, lo, ucr) + \
        get_hosts(memberserver, lo, ucr)


def get_md5(filename):
    m = md5()
    if os.path.exists(filename):
        with open(filename) as f:
            m.update(f.read())
            return m.hexdigest()


def scheme_is_http(server: str) -> bool:
    surl = urlparse(server)
    return surl.scheme in ['http', 'https']


def create_url(server: str, prefix: str, username: str, password: str, port: str) -> str:
    surl = urlparse(server)
    if all([surl.scheme, surl.netloc]):
        netloc = surl.netloc
        path = surl.path or prefix
        scheme = surl.scheme
    else:
        scheme = 'https' if port.strip() == '443' else 'http'
        netloc = server
        path = prefix
    if not surl.username and username:
        _, _, hostport = netloc.rpartition('@')
        netloc = f"{username}:{password}@{hostport}"
    if not surl.port and port.strip() not in ['80', '443', '']:
        netloc = f'{netloc}:{port}'
    return ParseResult(scheme=scheme, netloc=netloc, path=path, params='', query='', fragment='').geturl()


class HTTPSConnection(http_client.HTTPSConnection):
    """Verified HTTP Connection, Bug #30620"""

    def __init__(self, *args, **kwargs):
        ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ssl_context.set_alpn_protocols(['http/1.1'])
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.load_verify_locations("/etc/ssl/certs/ca-certificates.crt")
        super(HTTPSConnection, self).__init__(*args, context=ssl_context, **kwargs)


class HTTPSHandler(urllib_request.HTTPSHandler):

    def https_open(self, req):
        return self.do_open(HTTPSConnection, req)

# TODO: this should probably go into univention-lib
# and hide urllib/urllib2 completely
# i.e. it should be unnecessary to import them directly
# in a module


def install_opener(ucr):
    handler = []
    proxy_http = ucr.get('proxy/http')
    if proxy_http:
        handler.append(urllib_request.ProxyHandler({'http': proxy_http, 'https': proxy_http}))
    handler.append(HTTPSHandler())
    opener = urllib_request.build_opener(*handler)
    urllib_request.install_opener(opener)


def urlopen(request):
    # use this in __init__ and app_center
    # to have the proxy handler installed globally
    return urllib_request.urlopen(request, timeout=60)


def get_current_ram_available():
    """Returns RAM currently available in MB, excluding Swap"""
    # return (psutil.avail_phymem() + psutil.phymem_buffers() + psutil.cached_phymem()) / (1024*1024) # psutil is outdated. re-enable when methods are supported
    # implement here. see http://code.google.com/p/psutil/source/diff?spec=svn550&r=550&format=side&path=/trunk/psutil/_pslinux.py
    with open('/proc/meminfo') as f:
        splitlines = map(lambda line: line.split(), f.readlines())
        meminfo = {line[0]: int(line[1]) * 1024 for line in splitlines}  # bytes
    avail_phymem = meminfo['MemFree:']  # at least MemFree is required

    # see also http://code.google.com/p/psutil/issues/detail?id=313
    phymem_buffers = meminfo.get('Buffers:', 0)  # OpenVZ does not have Buffers, calculation still correct, see Bug #30659
    cached_phymem = meminfo.get('Cached:', 0)  # OpenVZ might not even have Cached? Don't know if calculation is still correct but it is better than raising KeyError
    return (avail_phymem + phymem_buffers + cached_phymem) / (1024 * 1024)


def component_registered(component_id, ucr):
    """
    Checks if a component is registered (enabled or disabled).
    Moved outside of ComponentManager to avoid dependencies for
    UniventionUpdater when just using Application.all()
    """
    return f'{COMPONENT_BASE}/{component_id}' in ucr


def component_current(component_id, ucr):
    """
    Checks if a component is enabled (not disabled!).
    Moved outside of ComponentManager to avoid dependencies for
    UniventionUpdater
    """
    return ucr.get(f'{COMPONENT_BASE}/{component_id}/version') == 'current'


class Changes(object):

    def __init__(self, ucr):
        self.ucr = ucr
        self._changes = {}

    def changed(self):
        return bool(self._changes)

    def _bool_string(self, variable, value):
        """
        Returns a boolean string representation for a boolean UCR variable. We need
        this as long as we don't really know that all consumers of our variables
        transparently use the ucr.is_true() method to process the values. So we
        write the strings that we think are most suitable for the given variable.

        *** NOTE *** I would like to see such function in the UCR base class
                     so we could call
                     `ucr.set_bool(variable, boolvalue)`
                     and the ucr itself would know which string representation to write.
        """
        yesno = ['no', 'yes']
        # truefalse = ['False', 'True']
        enabled = ['disabled', 'enabled']
        # enable = ['disable', 'enable']
        onoff = ['off', 'on']
        # onezero = ['0', '1']  # strings here! UCR doesn't know about integers

        # array of strings to match against the variable name, associated with the
        # corresponding bool representation to use. The first match is used.
        # 'yesno' is default if nothing matches.
        #
        # *** NOTE *** Currently these strings are matched as substrings, not regexp.

        setup = [
            ['repository/online/component', enabled],
            ['repository/online', onoff],
        ]

        intval = int(bool(value))  # speak C:  intval = value ? 1 : 0;

        for s in setup:
            if s[0] in variable:
                return s[1][intval]
        return yesno[intval]

    def set_registry_var(self, name, value):
        """
        Sets a registry variable and tracks changedness in a private variable.
        This enables the set_save_commit_load() method to commit the files being affected
        by the changes we have made.

        Function handles boolean values properly.
        """
        try:
            oldval = self.ucr.get(name)
            if isinstance(value, bool):
                value = self._bool_string(name, value)

            # Possibly useful: if the value is the empty string -> try to unset this variable.
            # FIXME Someone please confirm that there are no UCR variables that need
            #        to be set to an empty string!
            if value == '':
                value = None

            # Don't do anything if the value being set is the same as
            # the value already found.
            if value == oldval:
                return
            MODULE.info('Setting registry variable %r to %r' % (name, value))

            self._changes[name] = value
        except Exception as e:
            MODULE.warn(f"set_registry_var('{name}', '{value}') ERROR {str(e)}")

    def commit(self):
        ucr_update(self.ucr, self._changes)


@contextmanager
def set_save_commit_load(ucr):
    ucr.load()
    changes = Changes(ucr)
    yield changes
    if changes.changed():
        changes.commit()


class ComponentManager(object):

    def __init__(self, ucr, updater):
        self.ucr = ucr
        self.uu = updater

    def component(self, component_id):
        """Returns a dict of properties for the component with this id."""
        comp = self.uu.component(component_id)
        entry = {
            'name': component_id,
            'enabled': bool(comp),
            'defaultpackages': list(comp.default_packages),
            # Explicitly enable unmaintained component
            'unmaintained': self.ucr.is_true(comp.ucrv("unmaintained"), False),
            # Component status as a symbolic string
            'status': comp.status(),
            'installed': comp.defaultpackage_installed(),
        }
        # Most values that can be fetched unchanged
        for attr in COMP_PARAMS:
            entry[attr] = self.ucr.get(comp.ucrv(attr), '')

        # correct the status to 'installed' if (1) status is 'available' and (2) installed is true
        if entry['status'] == 'available' and entry['installed']:
            entry['status'] = 'installed'

        # Possibly this makes sense? add an 'icon' column so the 'status' column can decorated...
        entry['icon'] = STATUS_ICONS.get(entry['status'], DEFAULT_ICON)

        # Allowance for an 'install' button: if a package is available, not installed, and there's a default package specified
        entry['installable'] = entry['status'] == 'available' and bool(entry['defaultpackages']) and not entry['installed']

        return entry

    def is_registered(self, component_id):
        return component_registered(component_id, self.ucr)

    def put_app(self, app, super_ucr=None):
        if super_ucr is None:
            with set_save_commit_load(self.ucr) as super_ucr:
                return self.put_app(app, super_ucr)
        app_data = {
            'server': app.get_server(),
            'prefix': '',
            'unmaintained': False,
            'enabled': True,
            'name': app.component_id,
            'description': app.name,
            'username': '',
            'password': '',
            'localmirror': 'false',
        }
        if not self.is_registered(app_data['name']):
            # do not overwrite version when registering apps
            # (like in univention-register-apps which is called
            # in a join script)
            # it may have been changed intentionally, see EndOfLife
            app_data['version'] = 'current'
        self.put(app_data, super_ucr)

    def remove_app(self, app, super_ucr=None):
        if super_ucr is None:
            with set_save_commit_load(self.ucr) as super_ucr:
                return self.remove_app(app, super_ucr)
        self._remove(app.component_id, super_ucr)

    def put(self, data, super_ucr):
        """
        Does the real work of writing one component definition back.
        Will be called for each element in the request array of
        a 'put' call, returns one element that has to go into
        the result of the 'put' call.
        Function does not throw exceptions or print log messages.
        """
        result = {
            'status': PUT_SUCCESS,
            'message': '',
            'object': {},
        }
        try:
            name = data.pop('name')
            named_component_base = f'{COMPONENT_BASE}/{name}'
            for key, val in data.items():
                if val is None:
                    # was not given, so don't update
                    continue
                if key in COMP_PARAMS:
                    super_ucr.set_registry_var(f'{named_component_base}/{key}', val)
                elif key == 'enabled':
                    super_ucr.set_registry_var(named_component_base, val)
        except Exception as e:
            result['status'] = PUT_PROCESSING_ERROR
            result['message'] = f"Parameter error: {str(e)}"

        # Saving the registry and invoking all commit handlers is deferred until
        # the end of the loop over all request elements.

        return result

    def remove(self, component_id):
        """
        Removes one component. Note that this does not remove
        entries below repository/online/component/<id> that
        are not part of a regular component definition.
        """
        result = {}
        result['status'] = PUT_SUCCESS

        try:
            with set_save_commit_load(self.ucr) as super_ucr:
                self._remove(component_id, super_ucr)

        except Exception as e:
            result['status'] = PUT_PROCESSING_ERROR
            result['message'] = f"Parameter error: {str(e)}"

        return result

    def currentify(self, component_id, super_ucr):
        self.put({'name': component_id, 'version': 'current'}, super_ucr)
        return super_ucr.changed()

    def uncurrentify(self, component_id, super_ucr):
        self.put({'name': component_id, 'version': ''}, super_ucr)
        return super_ucr.changed()

    def _remove(self, component_id, super_ucr):
        named_component_base = f'{COMPONENT_BASE}/{component_id}'
        for var in COMP_PARAMS:
            super_ucr.set_registry_var(f'{named_component_base}/{var}', '')

        super_ucr.set_registry_var(named_component_base, '')
