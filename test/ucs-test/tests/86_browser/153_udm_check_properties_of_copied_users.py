#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: check properties of copied users/user
## tags: [udm]
## roles: [domaincontroller_master]
## bugs: [49823]
## exposure: dangerous
## tags:
##  - skip_admember
## packages:
## - univention-management-console-module-udm

import pytest
from playwright.sync_api import expect

from univention.testing.browser.generic_udm_module import UserModule
from univention.testing.browser.lib import UMCBrowserTest
from univention.udm import UDM


JPEG = """
/9j/4AAQSkZJRgABAQAAAQABAAD/4QBiRXhpZgAATU0AKgAAAAgABQESAAMAAAABAAEAAAEaAAUAAAABAAAASgEbAA
UAAAABAAAAUgEoAAMAAAABAAEAAAITAAMAAAABAAEAAAAAAAAAAAABAAAAAQAAAAEAAAAB/9sAQwADAgICAgIDAgIC
AwMDAwQGBAQEBAQIBgYFBgkICgoJCAkJCgwPDAoLDgsJCQ0RDQ4PEBAREAoMEhMSEBMPEBAQ/9sAQwEDAwMEAwQIBA
QIEAsJCxAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQ/8AAEQgAAQABAwER
AAIRAQMRAf/EABQAAQAAAAAAAAAAAAAAAAAAAAX/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFAEBAAAAAAAAAAAAAA
AAAAAACP/EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAMAwEAAhEDEQA/ADBHP1//2Q==""".strip().replace("\n", "",)

CERT = """
MIICEjCCAXsCAg36MA0GCSqGSIb3DQEBBQUAMIGbMQswCQYDVQQGEwJKUDEOMAwGA1UECBMFVG9reW8xEDAOBgNVBA
cTB0NodW8ta3UxETAPBgNVBAoTCEZyYW5rNEREMRgwFgYDVQQLEw9XZWJDZXJ0IFN1cHBvcnQxGDAWBgNVBAMTD0Zy
YW5rNEREIFdlYiBDQTEjMCEGCSqGSIb3DQEJARYUc3VwcG9ydEBmcmFuazRkZC5jb20wHhcNMTIwODIyMDUyNjU0Wh
cNMTcwODIxMDUyNjU0WjBKMQswCQYDVQQGEwJKUDEOMAwGA1UECAwFVG9reW8xETAPBgNVBAoMCEZyYW5rNEREMRgw
FgYDVQQDDA93d3cuZXhhbXBsZS5jb20wXDANBgkqhkiG9w0BAQEFAANLADBIAkEAm/xmkHmEQrurE/0re/jeFRLl8Z
PjBop7uLHhnia7lQG/5zDtZIUC3RVpqDSwBuw/NTweGyuP+o8AG98HxqxTBwIDAQABMA0GCSqGSIb3DQEBBQUAA4GB
ABS2TLuBeTPmcaTaUW/LCB2NYOy8GMdzR1mx8iBIu2H6/E2tiY3RIevV2OW61qY2/XRQg7YPxx3ffeUugX9F4J/iPn
nu1zAxxyBy2VguKv4SWjRFoRkIfIlHX0qVviMhSlNy2ioFLy7JcPZb+v3ftDGywUqcBiVDoea0Hn+GmxZACg==""".strip().replace("\n", "",)


@pytest.fixture()
def user_info(udm,):
    """The created user will have all properties set that were removed from being copyable (Bug 49823)"""
    dn, username = udm.create_user(
        gecos="",
        displayName="",
        title="Univ",
        initials="U.U.",
        preferredDeliveryMethod="any",
        pwdChangeNextLogin="1",
        employeeNumber="42",
        homePostalAddress="Mary-Somervile 28359 Bremen",
        mobileTelephoneNumber="+49 421 12345-0",
        pagerTelephoneNumber="+49 421 23456-0",
        birthday="2000-01-01",
        jpegPhoto=JPEG,
        unixhome="/home/username",
        userCertificate=CERT,)
    copied_username = f"testcopy_{username}"
    yield {
        "orig_dn": dn,
        "orig_username": username,
        "copied_username": copied_username,
    }
    for user in UDM.admin().version(1).get("users/user").search(f"username={copied_username}"):
        user.delete()


def test_properties_of_copied_users(umc_browser_test: UMCBrowserTest, user_info,):
    orig_dn = user_info["orig_dn"]
    orig_username = user_info["orig_username"]
    copied_username = user_info["copied_username"]

    user_module = UserModule(umc_browser_test)
    user_module.navigate()
    user_module.copy_user(orig_username, copied_username, "testuser",)

    copied_username_in_grid = umc_browser_test.page.get_by_role("gridcell").filter(has_text=copied_username)
    expect(copied_username_in_grid).to_be_visible()

    # verify copying worked
    attribute_list = [
        "title",
        "initials",
        "preferredDeliveryMethod",
        "pwdChangeNextLogin",
        "employeeNumber",
        "homePostalAddress",
        "mobileTelephoneNumber",
        "pagerTelephoneNumber",
        "birthday",
        "jpegPhoto",
        "unixhome",
        "userCertificate",
        "certificateIssuerCountry",
        "certificateIssuerState",
        "certificateIssuerLocation",
        "certificateIssuerOrganisation",
        "certificateIssuerMail",
        "certificateSubjectCountry",
        "certificateSubjectState",
        "certificateSubjectLocation",
        "certificateSubjectOrganisation",
        "certificateSubjectOrganisationalUnit",
        "certificateSubjectCommonName",
        "certificateSubjectMail",
        "certificateDateNotBefore",
        "certificateDateNotAfter",
        "certificateVersion",
        "certificateSerial",
    ]

    udm_user_module = UDM.admin().version(2).get("users/user")
    orig_user = udm_user_module.get(orig_dn)
    copied_user = udm_user_module.get_by_id(copied_username)

    orig_user_props = orig_user.props.__dict__
    copied_user_props = copied_user.props.__dict__
    for attribute in attribute_list:
        if attribute == "jpegPhoto":
            assert copied_user_props[attribute] is None
        else:
            assert orig_user_props[attribute] != copied_user_props[attribute]
