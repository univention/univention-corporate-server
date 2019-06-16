#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Univention Directory Manager Module
#
# Copyright 2019 Univention GmbH
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

#import argparse
#import json

import sys
import requests
from getpass import getpass

if sys.version_info.major > 2:
    import http.client
    http.client._MAXHEADERS = 1000
else:
    import httplib
    httplib._MAXHEADERS = 1000


#def main():
#    return
#    description = '%(prog)s: command line interface for managing UCS'
#    epilog = '%(prog)s is a tool to handle the configuration for UCS on command line level. Use "%(prog)s modules" for a list of available modules.'
#    parser = argparse.ArgumentParser(description=description, epilog=epilog)
#    parser.add_argument('module', help='UDM type, e.g. users/user or computers/memberserver')
#    parser.add_argument('--binddn', help='bind DN')
#    parser.add_argument('--bindpwd', help='bind password')
#    parser.add_argument('--bindpwdfile', help='file containing bind password')
#    parser.add_argument('--logfile', help='path and name of the logfile to be used')
#    parser.add_argument('--tls', help='0 (no); 1 (try); 2 (must)')
#
#    subparsers = parser.add_subparsers(description='type %(prog)s <module> <action> --help for further help and possible arguments', metavar='action')
#
#    # CREATE
#    create_parser = subparsers.add_parser('create', help='Create a new UDM object')
#    create_parser.add_argument('--position', help='Set position in tree')
#    create_parser.add_argument('--set', help='Set variable to value, e.g. foo=bar')
#    create_parser.add_argument('--superordinate', help='Use superordinate module')
#    create_parser.add_argument('--option', help='Use only given module options')
#    create_parser.add_argument('--append-option', help='Append the module option')
#    create_parser.add_argument('--remove-option', help='Remove the module option')
#    create_parser.add_argument('--policy-reference', help='Reference to policy given by DN')
#    create_parser.add_argument('--ignore_exists')
#
#    # MODIFY
#    modify_parser = subparsers.add_parser('modify', help='Modify an existing UDM object')
#    modify_parser.add_argument('--dn', help='Edit object with DN')
#    modify_parser.add_argument('--set', help='Set variable to value, e.g. foo=bar')
#    modify_parser.add_argument('--append', help='Append value to variable, e.g. foo=bar')
#    modify_parser.add_argument('--remove', help='Remove value from variable, e.g. foo=bar')
#    modify_parser.add_argument('--option', help='Use only given module options')
#    modify_parser.add_argument('--append-option', help='Append the module option')
#    modify_parser.add_argument('--remove-option', help='Remove the module option')
#    modify_parser.add_argument('--policy-reference', help='Reference to policy given by DN')
#    modify_parser.add_argument('--policy-dereference', help='Remove reference to policy given by DN')
#
#    # REMOVE
#    remove_parser = subparsers.add_parser('remove', help='Remove a UDM object')
#    remove_parser.add_argument('--dn', help='Remove object with DN')
#    remove_parser.add_argument('--superordinate', help='Use superordinate module')
#    remove_parser.add_argument('--filter', help='Lookup filter e.g. foo=bar')
#    remove_parser.add_argument('--remove_referring', help='remove referring objects')
#    remove_parser.add_argument('--ignore_not_exists')
#
#    # LIST
#    list_parser = subparsers.add_parser('list', help='Search and list UDM objects')
#    list_parser.add_argument('--filter', help='Lookup filter e.g. foo=bar')
#    list_parser.add_argument('--position', help='Search underneath of position in tree')
#    list_parser.add_argument('--policies', choices=['0', '1'], help='List policy-based settings: 0:short, 1:long (with policy-DN)')
#
#    # MOVE
#    move_parser = subparsers.add_parser('move', help='Move a UDM object to a different position in tree')
#    move_parser.add_argument('--dn', help='Move object with DN')
#    move_parser.add_argument('--position', help='Move to position in tree')
#
#    #args = parser.parse_args()


class UdmError(Exception):
    pass


class Client(object):

    def __init__(self, language='en-US'):
        self.language = language

    def make_request(self, method, uri, credentials, data=None, **headers):
        print('{} {}'.format(method.upper(), uri))
        if method in ('get', 'head'):
            params = data
            json = None
        else:
            params = None
            json = data
        return requests.request(method, uri, auth=(credentials.username, credentials.password), params=params, json=json, headers=dict({'Accept': 'application/json; q=1; text/html; q=0.2, */*; q=0.1', 'Accept-Language': self.language}, **headers))

    def eval_response(self, response):
        if response.status_code >= 299:
            msg = '{} {}: {}'.format(response.request.method, response.url, response.status_code)
            try:
                json = response.json()
            except ValueError:
                pass
            else:
                if isinstance(json, dict):
                    if 'error' in json:
                        server_message = json['error'].get('message')
                        # traceback = json['error'].get('traceback')
                        if server_message:
                            msg += '\n{}'.format(server_message)
            raise UdmError(msg)
        return response.json()


class UDM(Client):

    @classmethod
    def http(cls, uri, username, password):
        return cls(uri, username, password)

    def __init__(self, uri, username, password, *args, **kwargs):
        super(UDM, self).__init__(*args, **kwargs)
        self.uri = uri
        self.username = username
        self.password = password
        self._api_version = None

    def modules(self):
        # TODO: cache - needs server side support
        resp = self.make_request('get', self.uri, credentials=self)
        prefix_modules = self.eval_response(resp)['_links']['udm/relation/object-modules']
        for prefix_module in prefix_modules:
            resp = self.make_request('get', prefix_module['href'], credentials=self)
            module_infos = self.eval_response(resp).get('_links', {}).get('udm/relation/object-types', [])
            for module_info in module_infos:
                yield Module(self, module_info['href'], module_info['name'], module_info['title'])

    def version(self, api_version):
        self._api_version = api_version
        return self

    def obj_by_dn(self, dn):
        # TODO: Needed?
        raise NotImplementedError()

    def get(self, name):
        for module in self.modules():
            if module.name == name:
                return module

    def __repr__(self):
        return 'UDM(uri={}, username={}, password=****, version={})'.format(self.uri, self.username, self._api_version)


class Module(Client):

    def __init__(self, udm, uri, name, title, *args, **kwargs):
        super(Module, self).__init__(*args, **kwargs)
        self.uri = uri
        self.username = udm.username
        self.password = udm.password
        self.name = name
        self.title = title

    def __repr__(self):
        return 'Module(uri={}, name={})'.format(self.uri, self.name)

    def new(self, superordinate=None):
        return Object(self, None, {}, [], {}, None, superordinate, None)

    def get(self, dn):
        for obj in self.search(position=dn, scope='base'):
            return obj.open()

    def get_by_entry_uuid(self, uuid):
        for obj in self.search(filter={'entryUUID': uuid}, scope='base'):
            return obj.open()

    def get_by_id(self, dn):
        # TODO: Needed?
        raise NotImplementedError()

    def search(self, filter=None, position=None, scope='sub', hidden=False, opened=False):
        data = {}
        if filter:
            for prop, val in filter.items():
                data['property'] = prop
                data['propertyvalue'] = val
        data['position'] = position
        data['scope'] = scope
        data['hidden'] = '1' if hidden else ''
        if opened:
            data['properties'] = '*'
        resp = self.make_request('get', self.uri, credentials=self, data=data)
        entries = self.eval_response(resp)['entries']
        for entry in entries:
            if opened:
                yield Object(self, entry['dn'], entry['properties'], entry['options'], entry['policies'], entry['position'], entry['superordinate'], entry['uri'])  # NOTE: this is missing last-modified, therefore no conditional request is done on modification!
            else:
                yield ShallowObject(self, entry['dn'], entry['uri'])

    def create(self, properties, options, policies, position, superordinate=None):
        obj = Object(self, None, properties, options, policies, position, superordinate, self.uri)
        obj.save()
        return obj


class ShallowObject(Client):

    def __init__(self, module, dn, uri, *args, **kwargs):
        super(ShallowObject, self).__init__(*args, **kwargs)
        self.module = module
        self.dn = dn
        self.uri = uri

    def open(self):
        resp = self.make_request('get', self.uri, credentials=self.module)
        entry = self.eval_response(resp)
        return Object(self.module, entry['dn'], entry['properties'], entry['options'], entry['policies'], entry['position'], entry['superordinate'], entry['uri'], etag=resp.headers.get('Etag'), last_modified=resp.headers.get('Last-Modified'))

    def __repr__(self):
        return 'ShallowObject(module={}, dn={})'.format(self.module.name, self.dn)


class Object(Client):

    def __init__(self, module, dn, properties, options, policies, position, superordinate, uri, etag=None, last_modified=None, *args, **kwargs):
        super(Object, self).__init__(*args, **kwargs)
        self.dn = dn
        self.props = properties
        self.options = options
        self.policies = policies
        self.position = position
        self.superordinate = superordinate
        self.module = module
        self.uri = uri
        self.etag = etag
        self.last_modified = last_modified

    def __repr__(self):
        return 'Object(module={}, dn={}, uri={})'.format(self.module.name, self.dn, self.uri)

    def reload(self):
        obj = self.module.get(self.dn)
        self._copy_from_obj(obj)

    def save(self):
        if self.dn:
            return self._modify()
        else:
            return self._create()

    def delete(self):
        return self.make_request('delete', self.uri, credentials=self.module)

    def _modify(self):
        data = {
            'properties': self.props,
            'options': self.options,
            'policies': self.policies,
            'position': self.position,
            'superordinate': self.superordinate,
        }
        headers = dict((key, value) for key, value in {
            'If-Unmodified-Since': self.last_modified,
            'If-None-Match': self.etag,
        }.items() if value)
        resp = self.make_request('put', self.uri, credentials=self.module, data=data, **headers)
        entry = self.eval_response(resp)
        self.dn = entry['dn']
        self.reload()

    def _copy_from_obj(self, obj):
        self.dn = obj.dn
        self.props = obj.props
        self.options = obj.options
        self.policies = obj.policies
        self.position = obj.position
        self.superordinate = obj.superordinate
        self.module = obj.module
        self.uri = obj.uri
        self.etag = obj.etag
        self.last_modified = obj.last_modified

    def _create(self):
        data = {
            'properties': self.props,
            'options': self.options,
            'policies': self.policies,
            'position': self.position,
            'superordinate': self.superordinate,
        }
        resp = self.make_request('post', self.module.uri, credentials=self.module, data=data)
        if resp.status_code == 200:
            uri = resp.headers['Location']
            obj = ShallowObject(self.module, None, uri).open()
            self._copy_from_obj(obj)
        else:
            self.eval_response(resp)


if __name__ == '__main__':
    if sys.argv[1:]:
        username = input('Username: ')
        password = getpass()
        uri = sys.argv[1]
        module = sys.argv[2]
        action = sys.argv[3]
    else:
        username = 'Administrator'
        password = 'univention'
        uri = 'http://10.200.27.100/univention/udm/'
        module = 'mail/domain'
        action = 'search'
    udm = UDM.http(uri, username, password).version(1)
    module = udm.get(module)
    print('Found {}'.format(module))
    print('Now performing {}'.format(action))
    if action == 'search':
        for entry in module.search():
            print(entry)
    else:
        print('Not supported...')
