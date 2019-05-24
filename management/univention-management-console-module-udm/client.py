#!/usr/bin/python3

#import argparse
#import json

import sys
import requests
from getpass import getpass
import http.client
http.client._MAXHEADERS = 1000

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

def make_request(verb, uri, credentials, data=None):
    print('{} {}'.format(verb.upper(), uri))
    if verb == 'get':
        params = data
        json = None
    else:
        params = None
        json = data
    return requests.request(verb, uri, auth=(credentials.username, credentials.password), params=params, json=json, headers={'Accept': 'application/json'})

def eval_response(response):
    if response.status_code != 200:
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

class UDM(object):
    @classmethod
    def http(cls, uri, username, password):
        return cls(uri, username, password)

    def __init__(self, uri, username, password):
        self.uri = uri
        self.username = username
        self.password = password
        self._api_version = None

    def modules(self):
        # TODO: cache - needs server side support
        resp = make_request('get', self.uri, credentials=self)
        prefix_modules = eval_response(resp)['_links']['/udm/relation/object-modules']
        for prefix_module in prefix_modules:
            resp = make_request('get', prefix_module['href'], credentials=self)
            module_infos = eval_response(resp).get('_links', {}).get('/udm/relation/object-types', [])
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

class Module(object):
    def __init__(self, udm, uri, name, title):
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
        # TODO: really wanted? there is some "uri knowledge" here.
        # but then... we should support getting a dn, right?
        obj = ShallowObject(self, dn, '{}/{}'.format(self.uri, dn))
        return obj.open()

    def get_by_id(self, dn):
        # TODO: Needed?
        raise NotImplementedError()

    def search(self, filter=None, position=None, scope='sub', hidden=False):
        # TODO: How to "fields"?
        data = {}
        if filter:
            for prop, val in filter.items():
                data['property'] = prop
                data['propertyvalue'] = val
        data['position'] = position
        data['scope'] = scope
        data['hidden'] = hidden
        resp = make_request('get', self.uri, credentials=self, data=data)
        entries = eval_response(resp)['entries']
        for entry in entries:
            yield ShallowObject(self, entry['dn'], entry['uri'])

class ShallowObject(object):
    def __init__(self, module, dn, uri):
        self.module = module
        self.dn = dn
        self.uri = uri

    def open(self):
        resp = make_request('get', self.uri, credentials=self.module)
        entry = eval_response(resp)
        return Object(self.module, entry['dn'], entry['properties'], entry['options'], entry['policies'], entry['position'], entry['superordinate'], entry['uri'])

    def __repr__(self):
        return 'ShallowObject(module={}, dn={})'.format(self.module.name, self.dn)

class Object(object):
    def __init__(self, module, dn, properties, options, policies, position, superordinate, uri):
        self.dn = dn
        self.props = properties
        self.options = options
        self.policies = policies
        self.position = position
        self.superordinate = superordinate
        self.module = module
        self.uri = uri

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
        return make_request('delete', self.uri, credentials=self.module)

    def _modify(self):
        data = {
                'properties': self.props,
                'options': self.options,
                'policies': self.policies,
                'position': self.position,
                'superordinate': self.superordinate,
                }
        resp = make_request('put', self.uri, credentials=self.module, data=data)
        entry = eval_response(resp)
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

    def _create(self):
        data = {
                'properties': self.props,
                'options': self.options,
                'policies': self.policies,
                'position': self.position,
                'superordinate': self.superordinate,
                }
        resp = make_request('post', self.module.uri, credentials=self.module, data=data)
        if resp.status_code == 200:
            uri = resp.headers['Location']
            obj = ShallowObject(self.module, None, uri).open()
            self._copy_from_obj(obj)
        else:
            eval_response(resp)

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
