#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Check delegated administration in UMC
## bugs: [58113]
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous

import pytest

from univention.config_registry import ucr as _ucr


pytestmark = pytest.mark.skipif(not _ucr.is_true('directory/manager/rest/delegative-administration/enabled'), reason='authz not activated')


def test_get_property_filtering(setup_role, udm, ldap_base):
    """
    Test property filtering for
        normal property - guardianRoles and lastname
        lazy loading property - guardianInheritedRoles
        and property set by open - primaryGroup
    """
    role = 'udm:test_roles:test_property_filter'
    acl = '''
access by role="%s"
  to objecttype="users/user" position.subtree="{ldap/base}"
    grant actions="search,read"
    grant properties="*" permission="read"
    grant properties="guardianRoles" permission="none"
    grant properties="guardianInheritedRoles" permission="none"
    grant properties="primaryGroup" permission="none"
    grant properties="lastname" permission="none"
''' % role
    rest, umc = setup_role(acl, role)
    group_dn, _ = udm.create_group(guardianMemberRoles=['foo:bar:grouprole'])
    dn, _ = udm.create_user(guardianRoles=['foo:bar:test'], groups=[group_dn])
    # umc
    obj = umc.get_object('users/user', dn)
    assert 'guardianRoles' not in obj
    assert 'guardianInheritedRoles' not in obj
    assert 'primaryGroup' not in obj
    assert 'lastname' not in obj
    # udm rest
    obj = rest.get_user(dn, properties=['*', 'guardianInheritedRoles'])
    assert not obj.properties.get('guardianRoles'), obj.properties.get('guardianRoles')
    assert not obj.properties.get('lastname'), obj.properties.get('lastname')
    assert not obj.properties.get('guardianInheritedRoles'), obj.properties.get('guardianInheritedRoles')
    assert not obj.properties.get('primaryGroup'), obj.properties.get('primaryGroup')
