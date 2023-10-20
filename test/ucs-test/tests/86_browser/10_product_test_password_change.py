#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Change password via User Settings
## packages:
##  - univention-management-console-module-udm
##  - univention-management-console-module-passwordchange
## roles-not:
##  - memberserver
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import time
from enum import Enum

import pytest
from ldap.filter import filter_format
from playwright.sync_api import Locator, Page, expect

import univention.admin.modules as udm_modules
import univention.testing.strings as uts
import univention.testing.ucr as ucr_test
from univention.lib.i18n import Translation
from univention.testing.browser import logger
from univention.testing.browser.generic_udm_module import UserModule
from univention.testing.browser.lib import UMCBrowserTest
from univention.testing.browser.sidemenu import SideMenu, SideMenuUser
from univention.testing.browser.udm_users import User, Users
from univention.testing.ucs_samba import wait_for_drs_replication
from univention.testing.utils import get_ldap_connection


_ = Translation("ucs-test-browser").translate


class PasswordTooShortError(Exception):
    pass


class UDMRetryException(BaseException):
    pass


class PasswordChangeExpectedOutcome(Enum):
    SUCCESS = 1
    TOO_SHORT = 2
    REUSE = 3

    def __str__(self) -> str:
        if self == PasswordChangeExpectedOutcome.SUCCESS:
            return _("The password has been changed successfully.")
        elif self == PasswordChangeExpectedOutcome.TOO_SHORT:
            return _("password is too short")
        elif self == PasswordChangeExpectedOutcome.REUSE:
            return _("password was already used")
        return ""


@pytest.fixture()
def random_password():
    return uts.random_string()


def create_testusers_container(udm, ldap_base,):
    container_dn = udm.create_object(
        "container/cn",
        name="testusers",
        position=f"cn=users,{ldap_base}",
        wait_for=True,)

    # create the pwhistory policy
    pwhistory_dn = udm.create_object(
        "policies/pwhistory",
        name="ucs_test_pw_policy",
        length=3,
        pw_length=8,
        position=f"cn=pwhistory,cn=users,cn=policies,{ldap_base}",
        wait_for=True,)

    # set the password policy as the password policy for the testusers cn container
    udm.modify_object(
        "container/cn",
        dn=f"cn=testusers,cn=users,{ldap_base}",
        policy_reference=pwhistory_dn,
        wait_for=True,)

    return container_dn


def create_regular_user(udm, lo, container_dn,):
    regular_dn, regular_username = udm.create_user(password="univention", position=container_dn, wait_for=True,)

    regular_user = lo.get(regular_dn, required=True,)

    return User(regular_username, regular_user["sn"][0].decode("UTF-8"), password="univention", has_popup_after_login=True,)


def create_admin_user(udm, lo, container_dn, ldap_base,):
    admin_dn, admin_username = udm.create_user(password="univention", position=container_dn, primaryGroup=f"cn=Domain Admins,cn=groups,{ldap_base}", wait_for=True,)

    admin_user = lo.get(admin_dn, required=True,)
    return User(admin_username, admin_user["sn"][0].decode("UTF-8"), password="univention",)


@pytest.fixture(scope="module")
def admin_user(test_users: Users,) -> User:
    return test_users.admin_user


@pytest.fixture(scope="module")
def regular_user(test_users: Users,) -> User:
    return test_users.regular_user


@pytest.fixture(scope="module")
def test_users(udm_module_scope, ldap_base, lo,) -> Users:
    container_dn = create_testusers_container(udm_module_scope, ldap_base,)
    regular_user = create_regular_user(udm_module_scope, lo, container_dn,)
    admin_user = create_admin_user(udm_module_scope, lo, container_dn, ldap_base,)
    return Users(regular_user, admin_user,)


def logout(umc_browser_test: UMCBrowserTest,):
    side_menu = SideMenu(umc_browser_test)
    side_menu.navigate(do_login=False)
    side_menu.logout()


@pytest.mark.parametrize("role", ["admin", "regular"],)
def test_change_user_password(role: str, random_password: str, test_users: Users, side_menu_user: SideMenuUser,):
    user = test_users.regular_user if role == "regular" else test_users.admin_user

    change_own_password(user, random_password, side_menu_user, check_for_no_module_available_popup=user.has_popup_after_login,)
    logout(side_menu_user.tester)

    side_menu_user.tester.login(user.username, user.password, check_for_no_module_available_popup=user.has_popup_after_login,)
    logout(side_menu_user.tester)


def change_own_password(
    user: User,
    new_password: str,
    side_menu: SideMenuUser,
    outcome: PasswordChangeExpectedOutcome = PasswordChangeExpectedOutcome.SUCCESS,
    cancel_password_change_dialog_after_failure: bool = False,
    do_login: bool = True,
    check_for_no_module_available_popup: bool = False,**kwargs,
):
    # When chaning the password for the admin, sometimes the password change is faster than the request to command/udm/license
    side_menu.navigate(user.username, user.password, do_login=do_login, check_for_no_module_available_popup=check_for_no_module_available_popup, **kwargs,)
    side_menu.change_password(user.password, new_password,)

    check_password_change_outcome(outcome, side_menu.page,)

    logger.info("Ok button click")
    side_menu.page.get_by_role("button", name=_("Ok"),).click()

    # If the outcome is NOT success we will just go back again to the password change prompt.
    if outcome == PasswordChangeExpectedOutcome.SUCCESS:
        user.password = new_password
    elif cancel_password_change_dialog_after_failure:
        change_password_dialog = side_menu.page.get_by_role("dialog", name=_("Change password"),)
        change_password_dialog.get_by_text("Cancel").click()


def check_password_change_outcome(outcome: PasswordChangeExpectedOutcome, page: Page,):
    logger.info("checking password change outcome")
    result_text = page.get_by_text(str(outcome))
    dialog_text = ""
    success_dialog = page.get_by_role("dialog", name=_("Notification"),)
    error_dialog = page.get_by_role("dialog", name=_("Error changing password"),)
    logger.info("checking for success or failure dialog")
    expect(success_dialog.or_(error_dialog)).to_be_visible()
    if success_dialog.is_visible():
        dialog_text = success_dialog.inner_text()
    else:
        dialog_text = error_dialog.inner_text()

    expect(result_text, f"expected the outcome to be '{outcome}' but found:\n'{dialog_text}'",).to_be_visible(
        timeout=30 * 1000,
    )
    logger.info("passed password outcome check")
    return False


# FIXME: admins can somehow always reuse passwords in a samba domain; testing with regular user
def test_for_password_reuse_error(regular_user: User, side_menu_user: SideMenuUser,):
    change_own_password(
        regular_user,
        regular_user.password,
        side_menu_user,
        PasswordChangeExpectedOutcome.REUSE,
        cancel_password_change_dialog_after_failure=True,
        check_for_no_module_available_popup=regular_user.has_popup_after_login,)
    logout(side_menu_user.tester)


def test_for_short_password_error(admin_user: User, side_menu_user: SideMenuUser,):
    change_own_password(
        admin_user,
        "a",
        side_menu_user,
        outcome=PasswordChangeExpectedOutcome.TOO_SHORT,
        cancel_password_change_dialog_after_failure=True,
        check_for_no_module_available_popup=admin_user.has_popup_after_login,)
    logout(side_menu_user.tester)


def test_usability_of_a_module_after_password_change(admin_user: User, random_password, umc_browser_test: UMCBrowserTest,):
    user_module = UserModule(umc_browser_test)
    side_menu = SideMenuUser(umc_browser_test)
    user_module.navigate(admin_user.username, admin_user.password,)
    expect(user_module.page.get_by_role("gridcell").first).to_be_visible(timeout=2 * 60 * 1000)

    change_own_password(admin_user, random_password, side_menu, do_login=False,)

    user_module.open_details(admin_user.username)
    heading = umc_browser_test.page.get_by_role("heading", name=_("Basic settings"),)
    expect(heading).to_be_visible()
    logout(umc_browser_test)


def test_login_while_changing_password(admin_user: User, random_password: str, umc_browser_test: UMCBrowserTest,):
    set_change_password_on_login_flag(admin_user, umc_browser_test,)
    umc_browser_test.end_umc_session()

    umc_browser_test.login(admin_user.username, admin_user.password, "/univention/management", expect_password_change_prompt=True,)
    password_expired_text: Locator = umc_browser_test.page.get_by_text(_("The password has expired and must be renewed."))
    expect(password_expired_text).to_be_visible()

    umc_browser_test.page.get_by_label(_("New password"), exact=True,).type(random_password)
    time.sleep(0.5)

    retype_input = umc_browser_test.page.get_by_label(_("New Password (retype)"))
    retype_input.fill(random_password)
    time.sleep(0.5)

    retype_input.press("Enter")

    expect(umc_browser_test.page.get_by_role("button", name=_("Favorites"),)).to_be_visible()
    admin_user.password = random_password

    logout(umc_browser_test)

    favorite_button: Locator = umc_browser_test.page.get_by_role("button", name=_("Favorites"),)

    # retrying logging in three times here because sometimes when logging immediately after chaning the password at login
    # the password expiry prompt is still there
    for i in range(3):
        umc_browser_test.login(admin_user.username, admin_user.password, "/univention/management",)
        expect(favorite_button.or_(password_expired_text)).to_be_visible(timeout=15 * 1000)
        if favorite_button.is_visible():
            return

        time.sleep(10)

    pytest.fail("'Pasword expired' notice still displayed after three login attempts")


def set_change_password_on_login_flag(user: User, tester: UMCBrowserTest,):
    user_module = UserModule(tester)
    user_module.navigate(user.username, user.password,)
    details = user_module.open_details(user.username)
    details.open_tab(_("Account"))
    details.check_checkbox(_("User has to change password on next login"))
    details.save()

    # sleep, must be synced to samba
    time.sleep(3)
    wait_for_drs_replication(filter_format("(&(cn=%s)(pwdLastSet=0))", (user.username,),))


def get_samba_settings():
    obj = _get_samba_obj()
    return {
        "passwordHistory": obj["passwordHistory"],
        "domainPasswordComplex": obj["domainPasswordComplex"],
    }


def set_samba_settings(settings,):
    obj = _get_samba_obj()
    for key, value in settings.items():
        obj[key] = value
    obj.modify()


def _get_samba_obj():
    ucr = ucr_test.UCSTestConfigRegistry()
    ucr.load()
    lo = get_ldap_connection()
    udm_modules.update()
    samba_module = udm_modules.get("settings/sambadomain")
    obj = samba_module.object(None, lo, None, "sambaDomainName=%s,cn=samba,%s" % (ucr.get("windows/domain"), ucr.get("ldap/base")),)
    obj.open()
    return obj


@pytest.fixture(autouse=True, scope="module",)
def backup_samba_settings():
    old_samba_settings = get_samba_settings()
    set_samba_settings(
        {
            "passwordHistory": "3",
            "domainPasswordComplex": "0",
        },
    )

    yield

    set_samba_settings(old_samba_settings)
