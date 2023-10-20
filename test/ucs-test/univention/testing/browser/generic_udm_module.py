#!/usr/bin/python3
#
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2023 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

from dataclasses import dataclass
from typing import Union

from playwright.sync_api import Locator, Page, expect

from univention.lib.i18n import Translation
from univention.testing.browser.lib import UMCBrowserTest


_ = Translation("ucs-test-framework").translate


@dataclass
class CreatedItem:
    identifying_name: str


class AddObjectDialog:
    """
    Use this class when pressing the "Add" button opens a dialog

    :param tester: The UMCBrowserTest instance to use
    :param locator: The locator of the dialog
    """

    def __init__(self, tester: UMCBrowserTest, locator: Locator,):
        self.tester = tester
        self.locator: Locator = locator
        self.page: Page = tester.page

    def fill_field(self, label: str, value: str, exact: bool = False,**kwargs):
        self.locator.get_by_role("textbox", name=label, exact=exact, **kwargs,).fill(value)

    def finish(self, label: str,):
        self.locator.get_by_role("button", name=label,).click()
        self.locator.get_by_role("button", name=_("Cancel"),).last.click()
        expect(self.locator).to_be_hidden()

    def next(self, label: str = _("Next"),):
        self.locator.get_by_role("button", name=label,).click()


class DetailsView:
    def __init__(self, tester: UMCBrowserTest,):
        self.tester = tester
        self.page = tester.page

    def fill_field(self, label: str, value: str,):
        self.page.get_by_label(label).fill(value)

    def check_checkbox(self, label: str,):
        self.page.get_by_role("checkbox", name=label,).check()

    def save(self, label: str = _("Save"),):
        self.page.get_by_role("button", name=label,).click()

    def open_tab(self, name: str,):
        self.page.get_by_role("tab", name=name,).click()

    def click_button(self, name: str,):
        self.page.get_by_role("button", name=name,).click()

    def upload_picture(self, img_path: str,) -> Locator:
        # for some reason this button is a textbox and not a button
        upload_profile_picture_button = self.page.get_by_role("textbox", name=_("Upload profile image"),)
        expect(upload_profile_picture_button).to_be_visible()

        self.page.screenshot(path=img_path)

        with self.page.expect_file_chooser() as file_chooser_info:
            upload_profile_picture_button.click()

        file_chooser = file_chooser_info.value
        file_chooser.set_files(img_path)

        # very ugly locator for this but the image isn't even in an <img> tag
        image_locator = self.page.locator(".umcUDMUsersModule__jpegPhoto .umcImage__img")
        expect(image_locator).to_be_visible()

        return image_locator

    def remove_picture(self):
        # for some reason this locator resolves to two buttons
        remove_button = self.page.get_by_role("button", name="Remove",).first
        expect(remove_button).to_be_visible()

        remove_button.click()


class GenericUDMModule(object):
    """
    The GenericUmcModule is the base class for a bunch of UMC Modules which are all structured similarly
    This class provides a bunch of methods for functionality that is similar/common in the modules.

    :param tester: The base tester
    :param module_name: The module name to be opened by navigate
    """

    def __init__(self, tester: UMCBrowserTest, module_name: str,):
        self.tester: UMCBrowserTest = tester
        self.page: Page = tester.page
        self.module_name: str = module_name

    def navigate(self, username="Administrator", password="univention",):
        self.tester.login(username, password,)
        self.tester.open_module(self.module_name)

    def add_object_dialog(self) -> AddObjectDialog:
        """
        Will add an object by clicking the `Add` button which is visible for all modules inheriting from this class
        The way how objects are added is however different between the classes. Some open a dialog to fill in information,
        others open a full page view and others do both. This function should be used when a dialog is opened by clicking the add button.
        If there is a full page view being opened `add_object_detail_view` should be used
        """
        self.page.get_by_role("button", name=_("Add"),).click()

        return AddObjectDialog(self.tester, self.page.get_by_role("dialog"),)

    def add_object_detail_view(self) -> DetailsView:
        """See `add_object_dialog` for details"""
        self.page.get_by_role("button", name=_("Add"),).click()
        return DetailsView(self.tester)

    def open_details(self, name: str,) -> DetailsView:
        """Click on the `name` of a <tr> entry to open it's DetailsView"""
        self.page.get_by_role("gridcell").get_by_text(name).click()
        return DetailsView(self.tester)

    def delete(self, name: str,):
        """Checks the checkbox of the row containing `name` and then press the delete button"""
        self.tester.check_checkbox_in_grid_by_name(name)
        self.page.get_by_role("button", name=_("Delete"),).click()
        self.page.get_by_role("dialog").get_by_role("button", name=_("Delete"),).click()

    def modify_text_field(self, name: Union[str, CreatedItem], label: str = _("Description"), value: str = "description",):
        """
        Shortcut method to open the details of an object, fill a field with a value and save

        :param name: the name of the object to modify
        :param label: the label of the textbox to fill the text into
        :param value: the value to fill into the textbox
        """
        if isinstance(name, CreatedItem,):
            name = name.identifying_name

        modify_object = self.open_details(name)
        modify_object.fill_field(label, value,)
        modify_object.save()


class PortalModule(GenericUDMModule):
    def __init__(self, tester: UMCBrowserTest,):
        super().__init__(tester, _("Portal"),)

    def add(
        self,
        name: str = "portal_name",
        lang_code: str = "English/USA",
        display_name: str = "Portal Display Name",) -> CreatedItem:
        add_object = self.add_object_dialog()
        add_object.tester.fill_combobox("Type", "Portal: Portal",)
        add_object.next()
        add_object = DetailsView(self.tester)
        add_object.fill_field(_("Internal name"), name,)
        add_object.tester.fill_combobox("Language code", lang_code,)
        add_object.fill_field(_("Display Name"), display_name,)
        add_object.save(_("Create Portal"))

        return CreatedItem(name)


class UserModule(GenericUDMModule):
    def __init__(self, tester: UMCBrowserTest,) -> None:
        super().__init__(tester, _("Users"),)

    def handle_comboboxes(self, add_object: AddObjectDialog, template: Union[str, None],):
        combobox_filled = False

        # in some cases there might be a dialog with a combobox pop-up where none is expected
        # here we make sure that either a detail view or add dialog is displayed
        # before checking if a combobox is visible
        dialog = add_object.locator.get_by_text(_("Add a new user"))
        detail = self.page.get_by_role("heading", name=_("Basic settings"),)

        expect(dialog.or_(detail)).to_be_visible()
        # in case there is a different user container we want to select the default one here
        filter = self.page.get_by_label(_("Container"))
        container_combobox = self.page.get_by_role("combobox").filter(has=filter)
        if container_combobox.is_visible():
            add_object.tester.fill_combobox(_("Container"), f"{self.tester.domainname}:/users",)
            combobox_filled = True

        # in case there is a template when none is expected
        filter = self.page.get_by_label(_("User template"))
        template_combobox = self.page.get_by_role("combobox").filter(has=filter)

        if template is None and template_combobox.is_visible():
            add_object.tester.fill_combobox(_("User template"), _("None"),)
            combobox_filled = True

        if template is not None:
            add_object.tester.fill_combobox(_("User template"), template,)
            combobox_filled = True

        if combobox_filled:
            add_object.next()

    def create_object(
        self,
        name: str = "user_name",
        first_name: str = "first_name",
        last_name: str = "last_name",
        password: str = "univention",
        template: Union[str, None] = None,) -> CreatedItem:
        """
        Add a new user with the given information

        :return: CreatedItem which can be passed to subsequent methods of this class to modify the added user
        """
        add_object = self.add_object_dialog()
        self.handle_comboboxes(add_object, template,)

        add_object.fill_field(_("First name"), first_name,)
        add_object.fill_field(_("Last name"), last_name,)
        add_object.fill_field(_("User name"), name,)
        add_object.next()
        add_object.fill_field(f"{_('Password')} *", password, exact=True,)
        add_object.fill_field(f"{_('Password (retype)')} *", password, exact=True,)
        add_object.finish("Create User")

        return CreatedItem(name)

    def copy_user(self, original_name: str, name: str, last_name: str = "last_name", password: str = "univention",):
        self.tester.check_checkbox_in_grid_by_name(original_name)

        self.page.get_by_role("button", name=_("more"),).click()
        self.page.get_by_role("cell", name=_("copy"),).click()
        add_object = AddObjectDialog(self.tester, self.page.get_by_role("dialog"),)
        self.handle_comboboxes(add_object, None,)

        detail_view = DetailsView(self.tester)
        detail_view.fill_field(f"{_('Last name')} *", last_name,)
        detail_view.fill_field(f"{_('User name')} *", name,)
        detail_view.fill_field(f"{_('Password')} *", password,)
        detail_view.fill_field(f"{_('Password (retype)')} *", password,)
        detail_view.save(_("Create User"))

    def delete(self, created_item: CreatedItem,):
        super().delete(created_item.identifying_name)


class GroupModule(GenericUDMModule):
    def __init__(self, tester: UMCBrowserTest,):
        super().__init__(tester, _("Groups"),)

    def create_object(self, group_name: str = "group_name",) -> CreatedItem:
        """
        Add a new group with the given information

        :return: CreatedItem which can be passed to subsequent methods of this class to modify the added group
        """
        detail_view = self.add_object_detail_view()
        detail_view.fill_field("name", group_name,)
        detail_view.save(_("Create Group"))
        expect(self.page.get_by_role("gridcell").filter(has_text=group_name).first, "expect created group to be visible in grid",).to_be_visible()
        return CreatedItem(group_name)

    def delete(self, created_item: CreatedItem,):
        return super().delete(created_item.identifying_name)


class PoliciesModule(GenericUDMModule):
    def __init__(self, tester: UMCBrowserTest,):
        super().__init__(tester, _("Policies"),)

    def create_object(self, policy_name: str = "policy_name",) -> CreatedItem:
        """
        Add a new policy with the given information

        :return: CreatedItem which can be passed to subsequent methods of this class to modify the added policy
        """
        add_dialog = self.add_object_dialog()
        add_dialog.next()
        add_dialog = DetailsView(self.tester)
        add_dialog.fill_field(f"{_('Name')} *", policy_name,)
        add_dialog.save(_("Create Policy"))
        expect(self.page.get_by_role("gridcell").filter(has_text=policy_name).first, "expect created group to be visible in grid",).to_be_visible()
        return CreatedItem(policy_name)

    def modify_text_field(self, created_item: CreatedItem, label: str = _("Update to this UCS version"), value: str = "4.0",):
        super().modify_text_field(created_item.identifying_name, label, value,)

    def delete(self, created_item: CreatedItem,):
        super().delete(created_item.identifying_name)


class ComputerModule(GenericUDMModule):
    def __init__(self, tester: UMCBrowserTest,):
        super().__init__(tester, _("Computers"),)

    def create_object(self, computer_name: str = "computer_name_8",) -> CreatedItem:
        """
        Add a new computer with the given information

        :return: CreatedItem which can be passed to subsequent methods of this class to modify the added computer
        """
        add_dialog = self.add_object_dialog()
        add_dialog.next()
        add_dialog.fill_field(f"{_('Windows workstation/server name')} *", computer_name,)
        add_dialog.finish(_("Create Computer"))
        return CreatedItem(computer_name)

    def delete(self, created_item: CreatedItem,):
        return super().delete(created_item.identifying_name)
