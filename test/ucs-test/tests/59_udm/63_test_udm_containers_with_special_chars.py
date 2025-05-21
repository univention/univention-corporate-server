#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Create container/ou
## tags: [udm,apptest,udm-containers]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

from univention.testing import utils
from univention.udm import UDM


class Test_ContainerOUWithSpecialChars:

    def test_create_plus1_container(self, udm):
        ou = udm.create_object('container/ou', name='+1')
        utils.verify_ldap_object(ou)
        _udm = UDM.admin().version(2)
        ou_obj = _udm.get("container/ou").get(ou)
        assert ou_obj.dn == "ou=\\2B1,%s" % udm.LDAP_BASE

    def test_create_user_in_plus1_container(self, udm):
        ou = udm.create_object('container/ou', name='+1')
        user_dn, user_name = udm.create_user(position=ou)
        utils.verify_ldap_object(user_dn)
        _udm = UDM.admin().version(2)
        user_obj = _udm.get("users/user").get(user_dn)
        assert user_obj.dn == "uid=%s,ou=\\2B1,%s" % (user_name, udm.LDAP_BASE)

    def test_create_group_and_user_in_plus1_container(self, udm):
        ou = udm.create_object('container/ou', name='+1')
        group_dn, group_name = udm.create_group(position=ou)
        user_dn, user_name = udm.create_user(position=ou, primaryGroup=group_dn)
        _udm = UDM.admin().version(2)
        user_obj = _udm.get("users/user").get(user_dn)
        group_obj = _udm.get("groups/group").get(group_dn)
        assert user_obj.props.primaryGroup == "cn=%s,ou=\\2B1,%s" % (group_name, udm.LDAP_BASE)
        assert "uid=%s,ou=\\2B1,%s" % (user_name, udm.LDAP_BASE) in group_obj.props.users
