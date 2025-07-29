#!/usr/bin/python3
#
# Univention App Center
#  univention-app module for getting app meta information
#
# SPDX-FileCopyrightText: 2015-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

import re
from argparse import Action
from configparser import NoOptionError, NoSectionError
from fnmatch import translate
from shlex import quote

from univention.appcenter.actions import StoreAppAction, UniventionAppAction
from univention.appcenter.app import CaseSensitiveConfigParser
from univention.appcenter.app_cache import Apps
from univention.appcenter.ucr import ucr_get
from univention.appcenter.utils import shell_safe


class StoreKeysAction(Action):

    def __call__(self, parser, namespace, value, option_string=None):
        keys = []
        for val in value:
            try:
                section, key = val.rsplit(':', 1)
            except ValueError:
                section, key = None, val
            keys.append((section, key))
        setattr(namespace, self.dest, keys)


def _match(value, pattern):
    regex = re.compile(translate(pattern), re.I)
    return regex.match(value)


class Get(UniventionAppAction):
    """Fetches meta information about the app."""

    help = 'Query an app'

    def setup_parser(self, parser):
        parser.add_argument('app', action=StoreAppAction, help='The ID of the App that shall be queried')
        parser.add_argument('--shell', action='store_true', help='Print the information so that it can be evaluated in shell scripts. Example: %(prog)s app Vendor UseShop -> vendor="Vendor Inc."\\nuse_shop="1"')
        parser.add_argument('--values-only', action='store_true', help='Only print the value of KEY, not KEY itself')
        parser.add_argument('keys', action=StoreKeysAction, metavar='KEY', nargs='+', help='The key of the meta information')

    def main(self, args):
        for section, key, value in self.get_values(args.app, args.keys):
            if args.shell:
                if isinstance(value, list):
                    value = ' '.join(value)
                if isinstance(value, bool):
                    value = int(value)
                if value is None:
                    value = ''
                value = str(value)
                if args.values_only:
                    self.log(value)
                else:
                    if section is not None:
                        key = '%s__%s' % (section, key)
                    self.log('%s=%s' % (shell_safe(key), quote(value)))
            else:
                if isinstance(value, list):
                    value = ', '.join(value)
                if section is not None:
                    key = '%s/%s' % (section, key)
                if args.values_only:
                    self.log(value)
                else:
                    self.log('%s: %s' % (key, value))

    @classmethod
    def to_dict(cls, app):
        ret = app.attrs_dict()
        ret['logo_name'] = app.logo_name
        ret['logo_detail_page_name'] = app.logo_detail_page_name
        ret['license_description'] = app.license_description
        ret['thumbnails'] = app.get_thumbnail_urls()
        ret['is_installed'] = app.is_installed()
        ret['is_current'] = app.without_repository or ucr_get('repository/online/component/%s' % app.component_id) == 'enabled'
        ret['local_role'] = ucr_get('server/role')
        ret['is_master'] = ret['local_role'] == 'domaincontroller_master'
        ret['host_master'] = ucr_get('ldap/master')
        ret['is_ucs_component'] = app.is_ucs_component()
        ret.update(cls._candidate_dict(app))
        return ret

    @classmethod
    def _candidate_dict(cls, app):
        ret = {}
        candidate = Apps().find_candidate(app) if app.is_installed() else None
        if candidate:
            ret['update_available'] = True
            ret['candidate_docker'] = candidate.docker
            ret['candidate_version'] = candidate.version
            ret['candidate_component_id'] = candidate.component_id
            ret['candidate_readme_update'] = candidate.readme_update
            ret['candidate_readme_post_update'] = candidate.readme_post_update
            ret['candidate_needs_install_permissions'] = not candidate.install_permissions_exist()
            ret['candidate_install_permissions_message'] = candidate.install_permissions_message
        else:
            ret['update_available'] = False  # TODO: ucr.is_true(app.ucr_upgrade_key); Bug#39916
            ret['candidate_needs_install_permissions'] = not app.install_permissions_exist()
            ret['candidate_install_permissions_message'] = app.install_permissions_message
        return ret

    @classmethod
    def raw_value(cls, app, section, option):
        config_parser = CaseSensitiveConfigParser()
        with open(app.get_ini_file()) as f:
            config_parser.read_file(f)
        try:
            return config_parser.get(section, option)
        except (NoSectionError, NoOptionError):
            return None

    def get_values(self, app, keys, warn=True):
        config_parser = CaseSensitiveConfigParser()
        with open(app.get_ini_file()) as f:
            config_parser.read_file(f)
        for section, key in keys:
            search_section = section or 'Application'
            found = False
            for config_section in config_parser.sections():
                if _match(config_section, search_section):
                    for name, value in config_parser.items(config_section):
                        if _match(name, key):
                            for attr in app._attrs:
                                ini_attr_name = attr.name.replace('_', '')
                                if ini_attr_name == name.lower():
                                    value = attr.get(value, app.get_ini_file())
                            found = True
                            result_section = section and config_section
                            yield result_section, name, value
            if not found:
                try:
                    value = getattr(app, key)
                    if callable(value):
                        raise AttributeError(key)
                except AttributeError:
                    if warn:
                        self.warn('Could not find option %s:%s' % (search_section, key))
                else:
                    yield None, key, value
