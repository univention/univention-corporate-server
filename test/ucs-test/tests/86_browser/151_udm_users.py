#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
# -*- coding: utf-8 -*-
## desc: Various test for UDM users/user
## packages:
##  - univention-management-console-module-udm
## roles-not:
##  - memberserver
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import time

import pytest
from playwright.sync_api import expect

import univention.testing.strings as uts
from univention.lib.i18n import Translation
from univention.testing.browser.generic_udm_module import UserModule
from univention.testing.browser.udm_users import User, create_test_user


_ = Translation("ucs-test-browser").translate


@pytest.fixture()
def test_user(lo, udm):
    return create_test_user(udm, lo)


def test_move_user_into_container_and_out_again(user_module: UserModule, test_user: User, udm, ucr, ldap_base):
    position = ucr.get("ldap/base")
    cn_name = uts.random_string()
    udm.create_object("container/cn", position=position, name=cn_name)
    ou_name = uts.random_string()
    udm.create_object("container/ou", position=position, name=ou_name)

    user_module.navigate()
    assert move_user(user_module, test_user, cn_name, udm) == f"uid={test_user.username},cn={cn_name},{ldap_base}"
    assert move_user(user_module, test_user, ou_name, udm) == f"uid={test_user.username},ou={ou_name},{ldap_base}"
    assert move_user(user_module, test_user, "users", udm) == f"uid={test_user.username},cn=users,{ldap_base}"


def move_user(user_module: UserModule, test_user: User, container_name: str, udm) -> str:
    user_module.tester.check_checkbox_in_grid_by_name(test_user.username)
    user_module.page.get_by_role("button", name=_("More")).click()
    user_module.page.get_by_role("cell", name=_("Move to...")).click()
    user_module.page.get_by_role("gridcell", name=container_name, exact=True).click()
    user_module.page.get_by_role("button", name=_("Move User")).click()
    time.sleep(3)
    props = udm.list_objects("users/user", filter=f"username={test_user.username}")[0]

    return next(prop for prop in props if prop.startswith("uid="))


def test_user_templates_description(user_module: UserModule, udm):
    description_template = uts.random_string()
    udm.create_object(
        "settings/usertemplate",
        position=f"cn=templates,cn=univention,{user_module.tester.ldap_base}",
        name=description_template,
        description="<firstname:lower,umlauts>.<lastname>[0:2]@test.com",
    )
    user_module.navigate()
    created_item = user_module.create_object(name="template_description", first_name="Bärbel", last_name="Edison", template=description_template)
    details = user_module.open_details(created_item.identifying_name)

    heading = user_module.page.get_by_role("heading", name=_("Basic settings"))
    expect(heading).to_be_visible()

    description = user_module.page.get_by_label(_("Description")).last.input_value()
    try:
        assert description == "baerbel.Ed@test.com"
    finally:
        details.save()
        user_module.delete(created_item)


def test_user_templates_group(user_module: UserModule, udm):
    secondary_group_template = uts.random_string()
    udm.create_object(
        "settings/usertemplate",
        position=f"cn=templates,cn=univention,{user_module.tester.ldap_base}",
        name=secondary_group_template,
        groups=f"cn=Domain Admins,cn=groups,{user_module.tester.ldap_base}",
    )

    user_module.navigate()
    created_item = user_module.create_object(name="template_group", first_name="Thomas", last_name="Edison", template=secondary_group_template)
    details_view = user_module.open_details(created_item.identifying_name)
    details_view.open_tab(_("Groups"))
    try:
        loc = user_module.page.get_by_text(_("Domain Admins"))
        expect(loc).to_be_visible()
    finally:
        details_view.save()
        user_module.delete(created_item)
