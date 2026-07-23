#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Check delegated administration in UMC
## bugs: [58113]
## packages:
##  - univention-management-console-module-udm
## roles:
##  - domaincontroller_master
##  - domaincontroller_backup
## exposure: dangerous


import pytest
from playwright.sync_api import expect

from univention.config_registry import ucr as _ucr
from univention.lib.i18n import Translation


pytestmark = pytest.mark.skipif(not _ucr.is_true('directory/manager/web/delegative-administration/enabled'), reason='authz not activated')

_ = Translation('ucs-test-browser').translate


def test_helpdesk_operator_set_description(user_module, ou, ldap_base, random_username):
    """Helpdesk operator can't change description"""
    user_module.navigate(username=ou.helpdesk_operator_username, password='univention')
    details = user_module.open_details(ou.user_username)
    details.fill_field(_('Description'), random_username())
    details.save()
    expect(details.page.get_by_text(_("The LDAP object could not be saved: Permission denied."))).to_be_visible()


def test_helpdesk_operator_set_password(user_module, ou, ldap_base, Client, random_username, udm):
    """Helpdesk operator can set password"""
    username = f"a{random_username()}"
    password = random_username()
    description = random_username()
    # also set description, a propery the helpdesk role can not read, and check if it still set after modification
    dn, username = udm.create_user(position=ou.user_default_container, description=description, username=username)
    user_module.navigate(username=ou.helpdesk_operator_username, password='univention')
    details = user_module.open_details(username)
    details.fill_field(_("Password"), password, exact=True)
    details.fill_field(_("Password (retype)"), password)
    details.save()
    umc_client = Client()
    # correct password?
    assert umc_client.authenticate(username, password).status == 200
    # description still set?
    udm.verify_udm_object("users/user", dn, {"description": description})
