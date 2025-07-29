#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2020-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#

from copy import deepcopy
from unittest.mock import MagicMock

from univentionunittests.udm_filter import make_filter


def get_domain():
    return 'dc=intranet,dc=example,dc=de'


class MockedAccess(MagicMock):
    def search(self, filter='(objectClass=*)', base='', scope='sub', attr=[], unique=False, required=False, timeout=-1, sizelimit=0, serverctrls=None, response=None):
        if base is None:
            base = get_domain()
        res = []
        ldap_filter = make_filter(filter)
        for obj in self.database:
            if not obj.dn.endswith(base):
                continue
            if not ldap_filter.matches(obj):
                continue
            if attr:
                attrs = {}
                for att in attr:
                    if att in obj.attrs:
                        attrs[att] = deepcopy(obj.attrs[att])
            else:
                attrs = deepcopy(obj.attrs)
            result = obj.dn, attrs
            res.append(result)
        return res

    def searchDn(self, filter='(objectClass=*)', base='', scope='sub', unique=False, required=False, timeout=-1, sizelimit=0, serverctrls=None, response=None):
        res = []
        for dn, _attrs in self.search(filter, base):
            res.append(dn)
        return res

    def modify(self, dn, changes, exceptions=False, ignore_license=0, serverctrls=None, response=None, rename_callback=None):
        self.database.modify(dn, changes)

    def get(self, dn, attr=[], required=False, exceptions=False):
        return self.database.get(dn)

    def parentDn(self, dn):
        idx = dn.find(',')
        return dn[idx + 1:]

    @classmethod
    def compare_dn(cls, a, b):
        return a.lower() == b.lower()

    def getAttr(self, dn, attr, required=False, exceptions=False):
        obj = self.database.objs.get(dn)
        if obj:
            return obj.attrs.get(attr)


class MockedPosition:
    def __init__(self):
        self.dn = get_domain()

    def getDn(self):
        return self.dn

    def getDomain(self):
        return get_domain()

    def getDomainConfigBase(self):
        return 'cn=univention,%s' % self.getDomain()

    def getBase(self):
        return 'cn=univention,%s' % self.getDomain()
