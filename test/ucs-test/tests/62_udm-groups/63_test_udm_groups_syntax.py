#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: test udm module admin syntax
## versions:
##  5.0-2: fixed
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: safe


import pytest

from univention.admin import syntax as udm_syntax
from univention.admin.handlers.groups import group


def test_group_attributes_syntax():
    properties = group.property_descriptions
    assert isinstance(properties.get("name").syntax, udm_syntax.gid)
    assert isinstance(properties.get("gidNumber").syntax, udm_syntax.integer)
    assert isinstance(properties.get("sambaRID").syntax, udm_syntax.integer)
    assert isinstance(properties.get("sambaGroupType").syntax, udm_syntax.sambaGroupType)
    assert isinstance(properties.get("sambaPrivileges").syntax, udm_syntax.SambaPrivileges)
    assert isinstance(properties.get("adGroupType").syntax, udm_syntax.adGroupType)
    assert isinstance(properties.get("description").syntax, udm_syntax.string)
    assert isinstance(properties.get("users").syntax, udm_syntax.UserDN)
    assert isinstance(properties.get("hosts").syntax, udm_syntax.HostDN)
    assert isinstance(properties.get("mailAddress").syntax, udm_syntax.emailAddressValidDomain)
    assert isinstance(properties.get("memberOf").syntax, udm_syntax.GroupDN)
    assert isinstance(properties.get("nestedGroup").syntax, udm_syntax.GroupDN)
    assert isinstance(properties.get("allowedEmailUsers").syntax, udm_syntax.UserDN)
    assert isinstance(properties.get("allowedEmailGroups").syntax, udm_syntax.GroupDN)
