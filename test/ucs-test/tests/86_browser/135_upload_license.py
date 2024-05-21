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
from pathlib import Path
from typing import Iterator

import pytest
from playwright.sync_api import expect

from univention.lib.i18n import Translation
from univention.testing.browser import logger
from univention.testing.browser.sidemenu import SideMenuLicense


_ = Translation('ucs-test-browser').translate

FFPUT = Path(__file__).with_name('FreeForPersonalUseTest.license')

pytestmark = pytest.mark.skipif(not FFPUT.is_file(), reason=f'{FFPUT} not found')


@pytest.fixture()
def license_file_path(side_menu_license: SideMenuLicense, ucr, ldap_base, tmp_path) -> Iterator[Path]:
    ucr.save()

    license_dn = f'cn=admin,cn=license,cn=univention,{ldap_base}'

    orig = dump_current_license_to_file(license_dn, tmp_path)
    mod = modify_free_license_template(license_dn, tmp_path)

    try:
        yield mod
    finally:
        side_menu_license.navigate(do_login=False)
        side_menu_license.import_license(orig, False)
        ucr.revert_to_original_registry()


@pytest.mark.parametrize('as_text', [True, False])
def test_upload_license(side_menu_license: SideMenuLicense, license_file_path: Path, as_text: bool):
    logger.info('Using %s as test license' % license_file_path)
    side_menu_license.tester.restart_umc()

    side_menu_license.navigate()
    side_menu_license.import_license(license_file_path, as_text)
    check_license_information(side_menu_license, license_file_path)


def check_license_information(side_menu_license: SideMenuLicense, license_file_path: Path):
    side_menu_license.navigate(do_login=False)
    side_menu_license.open_license_information()

    page = side_menu_license.page

    with license_file_path.open() as license_file:
        expected_license_type = next((line for line in license_file if line.startswith('univentionLicenseBaseDN: ')), None)
    assert expected_license_type is not None
    expected_license_type = expected_license_type.split(':')[1].strip()
    expect(page.get_by_text(expected_license_type), f'expected license type to be {expected_license_type}').to_be_visible()
    page.get_by_role('button', name=_('Close')).click()


def modify_free_license_template(license_dn: str, tmp: Path) -> Path:
    path = tmp / 'Modified.license'
    with FFPUT.open('r') as fd, path.open("w") as out:
        for line in fd:
            key, sep, val = line.rstrip("\n").partition(": ")
            out.write(f"{key}{sep}{license_dn if key == 'dn' else val}\n")
    return path


def dump_current_license_to_file(license_dn: str, tmp: Path) -> Path:
    """
    Opens a given 'license_file' for writing and puts in the output of
    launched 'univention-ldapsearch' with self.license_dn argument
    """
    path = tmp / 'InitiallyInstalled.license'
    logger.info("Saving original license to file: %s", path)
    with path.open("w") as fd:
        subprocess.run(['univention-ldapsearch', '-LLLb', license_dn], stdout=fd, check=True)
    return path
