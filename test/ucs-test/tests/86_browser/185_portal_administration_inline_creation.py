#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
## desc: Test adding portal categories and entries from within the portal
## roles:
##  - domaincontroller_master
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import time

import pytest
from playwright.sync_api import Page, expect

from univention.testing.browser.lib import UMCBrowserTest
from univention.testing.browser.portal import UCSPortalEditMode
from univention.testing.conftest import locale_available
from univention.udm import UDM


created_modules = []


@pytest.fixture(autouse=True)
def delete_created_portal_entries():
    yield

    for module in created_modules:
        module.delete()


def add_category(edit_mode: UCSPortalEditMode, udm):
    edit_mode.navigate()
    category_name = "internal-name-for-category"
    category_display_name = "Category Name"
    edit_mode.add_category(category_name, category_display_name)

    category = search_for_udm_object("portals/category", category_name, udm)
    created_modules.append(category)

    assert category is not None
    assert category.props.name == category_name
    assert category.props.entries == []
    assert category.props.displayName == {"en_US": f"{category_display_name} US", "de_DE": f"{category_display_name} DE"}

    return category


def add_entry(edit_mode: UCSPortalEditMode, udm, category: str):
    internal_name = "internal-name-for-entry"
    entry_display_name = "Entry Name"
    description = "Entry Description"
    keyword = "Keyword"
    link = "https://example.com"

    edit_mode.navigate()
    edit_mode.add_entry(internal_name, entry_display_name, description, keyword, link, category)
    wait_for_dialog_to_disappear(edit_mode.page)

    entry = search_for_udm_object("portals/entry", internal_name, udm)
    created_modules.append(entry)

    assert entry is not None
    assert entry.props.name == internal_name
    assert entry.props.description == {"de_DE": f"{description} DE", "en_US": f"{description} US"}
    assert entry.props.displayName == {"en_US": f"{entry_display_name} US", "de_DE": f"{entry_display_name} DE"}
    assert entry.props.keywords == {"de_DE": f"{keyword} DE", "en_US": f"{keyword} US"}
    assert entry.props.link == [{"locale": str(edit_mode.tester.lang).replace("-", "_"), "value": link}]
    assert entry.props.allowedGroups == []
    assert entry.props.anonymous is False
    assert entry.props.backgroundColor is None
    assert entry.props.icon is None
    assert entry.props.linkTarget == "useportaldefault"
    assert entry.props.target is None
    return entry


def add_folder(edit_mode: UCSPortalEditMode, udm, category: str):
    internal_Name = "internal-name-for-folder"
    folder_display_name = "Folder Name"

    edit_mode.navigate()
    edit_mode.add_folder(internal_Name, folder_display_name, category)
    wait_for_dialog_to_disappear(edit_mode.page)

    folder = search_for_udm_object("portals/folder", internal_Name, udm)
    created_modules.append(folder)

    assert folder is not None
    assert folder.props.name == internal_Name
    assert folder.props.displayName == {"en_US": f"{folder_display_name} US", "de_DE": f"{folder_display_name} DE"}
    assert folder.props.entries == []
    return folder


def wait_for_dialog_to_disappear(page: Page):
    expect(page.get_by_role("dialog")).to_be_hidden()


@locale_available()
def test_inline_creation(umc_browser_test: UMCBrowserTest):
    udm = UDM.admin().version(2)
    edit_mode = UCSPortalEditMode(umc_browser_test)

    category = add_category(edit_mode, udm)
    category_name = category.props.displayName[str(umc_browser_test.lang).replace("-", "_")]

    add_entry(edit_mode, udm, category_name)
    add_folder(edit_mode, udm, category_name)


def search_for_udm_object(module: str, name: str, udm, timeout: int = 10):
    udm_module = udm.get(module)

    end = time.time() + timeout
    while time.time() < end:
        entries = list(udm_module.search(f"name={name}"))
        if len(entries) != 0:
            return entries[0]

        time.sleep(0.2)

    pytest.fail(f"Failed to find {name} in {module} after {timeout} seconds")
