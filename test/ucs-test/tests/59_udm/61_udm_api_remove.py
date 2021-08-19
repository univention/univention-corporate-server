#!/usr/share/ucs-test/runner /usr/bin/py.test -s -lvvx
# -*- coding: utf-8 -*-
## desc: Test 'remove' operation in UDM API
## exposure: dangerous
## roles: [domaincontroller_master]
## tags: [udm_api, skip_admember]
## packages: [python-univention-directory-manager]
## bugs: [53620]

import pytest

import univention.debug as ud
from univention.testing.strings import random_username
from univention.udm.exceptions import DeleteError, NoObject


ud.init('/var/log/univention/directory-manager-cmd.log', ud.FLUSH, ud.NO_FUNCTION)
ud.set_level(ud.ADMIN, ud.ALL)


def test_remove_children(ldap_base, schedule_delete_udm_obj, simple_udm):
	cn_mod = simple_udm.get("container/cn")
	cn_obj = cn_mod.new(ldap_base)
	cn_obj.props.name = random_username()
	cn_obj.save()
	schedule_delete_udm_obj(cn_obj.dn, "container/cn")
	cn_obj_dn = cn_obj.dn
	assert cn_mod.get(cn_obj_dn)

	users_mod = simple_udm.get("users/ldap")
	user_obj = users_mod.new()
	user_obj.position = cn_obj.dn
	user_obj.props.username = random_username()
	user_obj.props.password = random_username()
	user_obj.save()
	schedule_delete_udm_obj(user_obj.dn, "users/user")
	user_obj_dn = user_obj.dn

	user_obj2 = users_mod.get(user_obj_dn)
	assert user_obj2
	assert user_obj2.position == cn_obj_dn

	cn_obj.delete(remove_childs=True)

	with pytest.raises(NoObject):
		cn_mod.get(cn_obj_dn)

	with pytest.raises(NoObject):
		users_mod.get(user_obj_dn)


def test_remove_children_missing(ldap_base, schedule_delete_udm_obj, simple_udm):
	cn_mod = simple_udm.get("container/cn")
	cn_obj = cn_mod.new(ldap_base)
	cn_obj.props.name = random_username()
	cn_obj.save()
	schedule_delete_udm_obj(cn_obj.dn, "container/cn")
	cn_obj_dn = cn_obj.dn
	assert cn_mod.get(cn_obj_dn)

	users_mod = simple_udm.get("users/ldap")
	user_obj = users_mod.new()
	user_obj.position = cn_obj.dn
	user_obj.props.username = random_username()
	user_obj.props.password = random_username()
	user_obj.save()
	schedule_delete_udm_obj(user_obj.dn, "users/user")
	user_obj_dn = user_obj.dn

	user_obj2 = users_mod.get(user_obj_dn)
	assert user_obj2
	assert user_obj2.position == cn_obj_dn

	with pytest.raises(DeleteError) as excinfo:
		cn_obj.delete()  # default: remove_childs=False
	assert "Operation not allowed on non-leaf" in str(excinfo.value)

	assert cn_mod.get(cn_obj_dn)
	assert users_mod.get(user_obj_dn)
