#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
# -*- coding: utf-8 -*-
## desc: Test uploading new license
## roles:
##  - domaincontroller_master
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import subprocess
import tempfile
from pathlib import Path
from subprocess import CalledProcessError
from typing import IO

import pytest
from playwright.sync_api import expect

from univention.lib.i18n import Translation
from univention.testing.browser import logger
from univention.testing.browser.sidemenu import SideMenuLicense


_ = Translation("ucs-test-browser").translate

dir_name = Path(__file__).parent
core_edition_license_path = Path(dir_name, "FreeForPersonalUseTest.license")


@pytest.fixture()
def license_file_path(side_menu_license: SideMenuLicense, ucr, ldap_base):
    ucr.save()

    license_temp_file = tempfile.NamedTemporaryFile("w+")
    license_dn = f"cn=admin,cn=license,cn=univention,{ldap_base}"

    modify_free_license_template(license_dn)
    dump_current_license_to_file(license_temp_file, license_dn)

    yield core_edition_license_path

    ucr.revert_to_original_registry()
    side_menu_license.navigate(do_login=False)
    side_menu_license.import_license(Path(license_temp_file.name), False)
    license_temp_file.close()


@pytest.mark.skipif(not core_edition_license_path.is_file(), reason="FreeForPersonalUseTest.license file not found")
@pytest.mark.parametrize("as_text", [True, False])
def test_upload_license(side_menu_license: SideMenuLicense, license_file_path: Path, as_text: bool):
    logger.info("Using %s as test license" % core_edition_license_path)
    side_menu_license.tester.restart_umc()

    side_menu_license.navigate()
    side_menu_license.import_license(license_file_path, as_text)
    check_license_information(side_menu_license, license_file_path)


def check_license_information(side_menu_license: SideMenuLicense, license_file_path: Path):
    side_menu_license.navigate(do_login=False)
    side_menu_license.open_license_information()

    page = side_menu_license.page

    with open(license_file_path) as license_file:
        expected_license_type = next((line for line in license_file if line.startswith("univentionLicenseBaseDN: ")), None)
        assert expected_license_type is not None
        expected_license_type = expected_license_type.split(":")[1].strip()
        expect(page.get_by_text(expected_license_type), f"expected license type to be {expected_license_type}").to_be_visible()
        page.get_by_role("button", name=_("Close")).click()


def modify_free_license_template(license_dn: str):
    try:
        with core_edition_license_path.open("r+") as fd:
            lines = fd.readlines()
            fd.seek(0)
            for line in lines:
                if line.startswith("dn: "):
                    line = f"dn: {license_dn}\n"
                fd.write(line)
    except (OSError, ValueError):
        logger.exception("Error while modifying FreeForPersonalUseTest")
        raise


def dump_current_license_to_file(license_file: IO[str], license_dn: str):
    """
    Opens a given 'license_file' for writing and puts in the output of
    launched 'univention-ldapsearch' with self.license_dn argument
    """
    logger.info("Saving original license to file: '%s'" % license_file.name)
    try:
        subprocess.run(["univention-ldapsearch", "-LLLb", license_dn], stdout=license_file, check=True)
    except (ValueError, OSError, CalledProcessError):
        logger.exception("An error occurred backing up the old license")
        raise
