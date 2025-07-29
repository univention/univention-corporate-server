#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

from collections import OrderedDict


class LDAPObject:
    def __init__(self, dn, attrs):
        self.dn = dn
        self.attrs = attrs
        self.changed = {}

    def __repr__(self):
        return f'Object({self.dn!r}, {self.attrs!r})'


def make_obj(obj):
    dn = obj.pop('dn')[0].decode('utf-8')
    return LDAPObject(dn, obj)


def parse_ldif(ldif):
    ret = []
    obj = {}
    for line in ldif.splitlines():
        if not line.strip():
            if obj:
                ret.append(make_obj(obj))
            obj = {}
            continue
        k, v = line.split(': ', 1)
        obj.setdefault(k, [])
        obj[k].append(v.encode('utf-8'))
    if obj:
        ret.append(make_obj(obj))
    return ret


class Database:
    def __init__(self):
        self.objs = OrderedDict()

    def fill(self, fname):
        with open(fname) as fd:
            objs = parse_ldif(fd.read())
            for obj in objs:
                self.add(obj)

    def __iter__(self):
        yield from self.objs.values()

    def __repr__(self):
        return f'Database({self.objs!r})'

    def __getitem__(self, dn):
        return self.objs[dn].attrs

    def get(self, dn):
        obj = self.objs.get(dn)
        if obj:
            return obj.attrs

    def add(self, obj):
        self.objs[obj.dn] = obj
        return obj.dn

    def delete(self, dn):
        del self.objs[dn]

    def modify(self, dn, ml):
        obj = self.objs[dn]
        for attr, _old, new in ml:
            if new:
                if not isinstance(new, list | tuple):
                    new = [new]
                obj.attrs[attr] = new
            else:
                obj.attrs.pop(attr, None)


# def make_univention_object(object_type, attrs, parent=None):
#     if parent is None:
#         parent = get_domain()
#     id_attr = 'cn'
#     id_value = attrs[id_attr][0]
#     attrs['univentionObjectType'] = [object_type]
#     attrs['objectClass'].append('univentionObject')
#     dn = '{}={},{}'.format(id_attr, id_value, parent)
#     return LDAPObject(dn, attrs)
