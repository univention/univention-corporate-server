#!/usr/share/ucs-test/runner pytest-3 -s -l -vvv
## desc: Test users/contact
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import ldap.dn
import pytest

import univention.testing.strings as uts
import univention.testing.udm as udm_test
from univention.testing import utils


class TestContactCreation:

    def test_contact_creation_basic(self, udm):
        """Create users/contact and verify LDAP attributes"""
        firstname = uts.random_name()
        lastname = uts.random_name()
        dn = udm.create_object('users/contact', firstname=firstname, lastname=lastname)
        utils.verify_ldap_object(dn, {
            'sn': [lastname],
            'givenName': [firstname],
            'cn': [f'{firstname} {lastname} 1'],
        })

    def test_contact_cn_explicit(self, udm):
        """Create users/contact with an explicitly set cn"""
        firstname = uts.random_name()
        lastname = uts.random_name()
        cn = uts.random_name()
        dn = udm.create_object('users/contact', firstname=firstname, lastname=lastname, cn=cn)
        utils.verify_ldap_object(dn, {
            'sn': [lastname],
            'cn': [cn],
        })

    def test_contact_explicit_cn_raises_on_conflict(self, udm):
        """Creating a users/contact with an explicit cn that already exists raises an error"""
        container = udm.create_object('container/cn', name=uts.random_name())
        explicit_cn = uts.random_name()
        udm.create_object('users/contact', lastname=uts.random_name(), cn=explicit_cn, position=container)

        with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
            udm.create_object('users/contact', lastname=uts.random_name(), cn=explicit_cn, position=container)

    def test_contact_cn_auto_conflict_resolution(self, udm):
        """Create two users/contact with the same name in the same container; cn should be unique"""
        firstname = uts.random_name()
        lastname = uts.random_name()
        container = udm.create_object('container/cn', name=uts.random_name())

        dn1 = udm.create_object('users/contact', firstname=firstname, lastname=lastname, position=container)
        dn2 = udm.create_object('users/contact', firstname=firstname, lastname=lastname, position=container)

        assert dn1 != dn2
        pattern = f'{firstname} {lastname}'
        utils.verify_ldap_object(dn1, {'cn': [f'{pattern} 1']})
        utils.verify_ldap_object(dn2, {'cn': [f'{pattern} 2']})


class TestContactModification:

    def test_contact_cn_auto_updates_on_name_change(self, udm):
        """Auto-generated cn follows a firstname/lastname change"""
        firstname = uts.random_name()
        lastname = uts.random_name()
        dn = udm.create_object('users/contact', firstname=firstname, lastname=lastname)
        utils.verify_ldap_object(dn, {'cn': [f'{firstname} {lastname} 1']})

        new_firstname = uts.random_name()
        new_dn = udm.modify_object('users/contact', dn=dn, firstname=new_firstname)

        utils.verify_ldap_object(new_dn, {
            'givenName': [new_firstname],
            'cn': [f'{new_firstname} {lastname} 1'],
        })

    def test_contact_explicit_cn_not_auto_updated_on_name_change(self, udm):
        """Explicit cn stays unchanged when firstname/lastname change"""
        firstname = uts.random_name()
        lastname = uts.random_name()
        cn = uts.random_name()
        dn = udm.create_object('users/contact', firstname=firstname, lastname=lastname, cn=cn)

        new_firstname = uts.random_name()
        new_dn = udm.modify_object('users/contact', dn=dn, firstname=new_firstname)

        utils.verify_ldap_object(new_dn, {
            'givenName': [new_firstname],
            'cn': [cn],
        })


class TestContactMove:

    def test_contact_move(self, udm):
        """Move a users/contact to another container"""
        cn_source = udm.create_object('container/cn', name=uts.random_name())
        cn_dest = udm.create_object('container/cn', name=uts.random_name())

        firstname = uts.random_name()
        lastname = uts.random_name()
        dn = udm.create_object('users/contact', firstname=firstname, lastname=lastname, position=cn_source)

        new_dn = udm.move_object('users/contact', dn=dn, position=cn_dest)

        utils.verify_ldap_object(dn, should_exist=False)
        utils.verify_ldap_object(new_dn, {'sn': [lastname], 'givenName': [firstname]})

    def test_contact_move_cn_conflict_resolution(self, udm):
        """Move a users/contact into a container where its cn already exists; cn should auto-resolve"""
        cn_source = udm.create_object('container/cn', name=uts.random_name())
        cn_dest = udm.create_object('container/cn', name=uts.random_name())

        firstname = uts.random_name()
        lastname = uts.random_name()
        pattern = f'{firstname} {lastname}'

        # Contact A in dest gets cn="{pattern} 1"
        dn_a = udm.create_object('users/contact', firstname=firstname, lastname=lastname, position=cn_dest)
        # Contact B in source also gets cn="{pattern} 1" (different position, no conflict yet)
        dn_b = udm.create_object('users/contact', firstname=firstname, lastname=lastname, position=cn_source)

        # Move B to dest: conflicts with A's cn, auto-resolves to cn="{pattern} 2"
        udm.move_object('users/contact', dn=dn_b, position=cn_dest)

        resolved_dn_b = ldap.dn.dn2str([[('cn', f'{pattern} 2', 1)], *ldap.dn.str2dn(cn_dest)])

        # move_object computes new_dn from the old RDN, not the resolved one — fix cleanup tracking
        wrong_dn_b = ldap.dn.dn2str([*ldap.dn.str2dn(dn_b)[:1], *ldap.dn.str2dn(cn_dest)])
        if wrong_dn_b in udm._cleanup.get('users/contact', []):
            udm._cleanup['users/contact'].remove(wrong_dn_b)
            udm._cleanup['users/contact'].append(resolved_dn_b)

        utils.verify_ldap_object(dn_a)
        utils.verify_ldap_object(dn_b, should_exist=False)
        utils.verify_ldap_object(resolved_dn_b, {'cn': [f'{pattern} 2'], 'sn': [lastname]})

    def test_contact_move_explicit_cn_raises_on_conflict(self, udm):
        """Moving a contact with an explicit cn into a position where that cn exists raises an error"""
        cn_source = udm.create_object('container/cn', name=uts.random_name())
        cn_dest = udm.create_object('container/cn', name=uts.random_name())

        explicit_cn = uts.random_name()
        udm.create_object('users/contact', lastname=uts.random_name(), cn=explicit_cn, position=cn_dest)
        dn_b = udm.create_object('users/contact', lastname=uts.random_name(), cn=explicit_cn, position=cn_source)

        with pytest.raises(udm_test.UCSTestUDM_MoveUDMObjectFailed):
            udm.move_object('users/contact', dn=dn_b, position=cn_dest)
