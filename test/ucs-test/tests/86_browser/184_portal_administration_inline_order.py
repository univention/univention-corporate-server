#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
# -*- coding: utf-8 -*-
## desc: Test changing the order of portal categories/entries from within the portal
## roles:
##  - domaincontroller_master
## tags:
##  - SKIP
##  - skip_admember
## join: true
## exposure: dangerous

import logging

from selenium.webdriver.common.by import By

import univention.testing.strings as uts
import univention.testing.ucr as ucr_test
from univention.lib.i18n import Translation
from univention.testing import selenium
from univention.testing.selenium.utils import expand_path
from univention.testing.udm import UCSTestUDM
from univention.udm import UDM


logger = logging.getLogger(__name__)

_ = Translation('ucs-test-selenium').translate


class UMCTester(object):

    def test_umc(self):
        try:
            self.init()
            self.do_test()
        finally:
            self.cleanup()

    def init(self):
        logger.info('Creating dummy portal entries and categories')
        self.entry_a_1_dname = f"entry_a_1__{uts.random_string()}"
        entry_a_1_dn = self.udm_test.create_object(
            'portals/entry',
            name=self.entry_a_1_dname,
            displayName=['en_US ' + self.entry_a_1_dname],
            description=['en_US foo'],
            link=['en_US foo'],
        )
        self.entry_a_2_dname = f"entry_a_2__{uts.random_string()}"
        entry_a_2_dn = self.udm_test.create_object(
            'portals/entry',
            name=self.entry_a_2_dname,
            displayName=['en_US ' + self.entry_a_2_dname],
            description=['en_US foo'],
            link=['en_US foo'],
        )
        self.cat_a_dname = f"category_a__{uts.random_string()}"
        cat_a_dn = self.udm_test.create_object(
            'portals/category',
            name=self.cat_a_dname,
            displayName=['en_US ' + self.cat_a_dname],
            entries=[entry_a_1_dn, entry_a_2_dn],
        )
        self.entry_b_dname = f"entry_b__{uts.random_string()}"
        entry_b_dn = self.udm_test.create_object(
            'portals/entry',
            name=self.entry_b_dname,
            displayName=['en_US ' + self.entry_b_dname],
            description=['en_US foo'],
            link=['en_US foo'],
        )
        self.cat_b_dname = f"category_b__{uts.random_string()}"
        cat_b_dn = self.udm_test.create_object(
            'portals/category',
            name=self.cat_b_dname,
            displayName=['en_US ' + self.cat_b_dname],
            entries=[entry_b_dn],
        )

        logger.info('Creating dummy portal')
        self.dummy_portal_title = uts.random_string()
        self.dummy_portal_dn = self.udm_test.create_object(
            'portals/portal',
            name=uts.random_string(),
            displayName=['en_US ' + self.dummy_portal_title],
            categories=[cat_a_dn, cat_b_dn],
            portalComputers=[ucr.get('ldap/hostdn')],
        )

        logger.info('Saving previously set portalComputers of main portal')
        udm = UDM.admin().version(1)
        portal = udm.obj_by_dn(f'cn=domain,cn=portal,cn=portals,cn=univention,{ucr.get("ldap/base")}')
        self.prev_comps = portal.props.portalComputers
        portal.props.portalComputers = []
        portal.save()

    def do_test(self):
        self.selenium.do_login()

        logger.info('Visiting dummy portal')
        self.selenium.driver.get(self.selenium.base_url)
        self.selenium.wait_for_text(self.dummy_portal_title)

        logger.info('Enter edit mode')
        self.selenium.click_element(expand_path('//*[@containsClass="iconMenu"]'))
        self.selenium.click_button(_('Edit Portal'))

        self.selenium.wait_for_text('Add category')

        logger.info('Check order before dnd')
        # Category_B is after Category_A
        self.selenium.driver.find_element(By.XPATH, f'//h2[text()="{self.cat_a_dname}"]/following::h2[text()="{self.cat_b_dname}"]')
        # Entry_A is in Category_A
        self.selenium.driver.find_element(By.XPATH, expand_path(f'//h2[text()="{self.cat_a_dname}"]/following-sibling::*//*[@containsClass="tile__name"][text()="{self.entry_a_1_dname}"]'))
        self.selenium.driver.find_element(By.XPATH, expand_path(f'//h2[text()="{self.cat_a_dname}"]/following-sibling::*//*[@containsClass="tile__name"][text()="{self.entry_a_2_dname}"]'))
        self.selenium.driver.find_element(By.XPATH, expand_path(f'//h2[text()="{self.cat_a_dname}"]/following-sibling::*//*[@containsClass="tile__name"][text()="{self.entry_a_1_dname}"]/following::*[@containsClass="tile__name"][text()="{self.entry_a_2_dname}"]'))
        # Entry_B is in Category_B
        self.selenium.driver.find_element(By.XPATH, expand_path(f'//h2[text()="{self.cat_b_dname}"]/following-sibling::*//*[@containsClass="tile__name"][text()="{self.entry_b_dname}"]'))

        logger.info('Drag category b above category a')
        self.selenium.drag_and_drop(
            expand_path(f'//*[@containsClass="dojoDndHandle"][text()="{(self.cat_b_dname)}"]'),
            expand_path(f'//*[@containsClass="dojoDndHandle"][text()="{(self.cat_a_dname)}"]'),
        )
        self.selenium.wait_for_text('Order saved')
        self.selenium.wait_for_text_to_disappear('Order saved')

        logger.info('Check order after category dnd')
        # Category_A is after Category_B
        self.selenium.driver.find_element(By.XPATH, expand_path(f'//h2[text()="{self.cat_b_dname}"]/following::h2[text()="{self.cat_a_dname}"]'))
        # Entry_A is in Category_A
        self.selenium.driver.find_element(By.XPATH, expand_path(f'//h2[text()="{self.cat_a_dname}"]/following-sibling::*//*[@containsClass="tile__name"][text()="{self.entry_a_1_dname}"]'))
        self.selenium.driver.find_element(By.XPATH, expand_path(f'//h2[text()="{self.cat_a_dname}"]/following-sibling::*//*[@containsClass="tile__name"][text()="{self.entry_a_2_dname}"]'))
        self.selenium.driver.find_element(By.XPATH, expand_path(f'//h2[text()="{self.cat_a_dname}"]/following-sibling::*//*[@containsClass="tile__name"][text()="{self.entry_a_1_dname}"]/following::*[@containsClass="tile__name"][text()="{self.entry_a_2_dname}"]'))
        # Entry_B is in Category_B
        self.selenium.driver.find_element(By.XPATH, expand_path(f'//h2[text()="{self.cat_b_dname}"]/following-sibling::*//*[@containsClass="tile__name"][text()="{self.entry_b_dname}"]'))

        # TODO dragging entries across categories does not work in selenium for some reason
        self.selenium.drag_and_drop(
            expand_path(f'//*[@containsClass="dojoDndItem"]//*[@containsClass="tile__name"][text()="{(self.entry_a_1_dname)}"]'),
            expand_path(f'//*[@containsClass="dojoDndItem"]//*[@containsClass="tile__name"][text()="{(self.entry_a_2_dname)}"]'),
        )
        self.selenium.wait_for_text('Order saved')
        self.selenium.wait_for_text_to_disappear('Order saved')

        logger.info('Check order after entry dnd')
        # Category_A is after Category_B
        self.selenium.driver.find_element(By.XPATH, f'//h2[text()="{self.cat_b_dname}"]/following::h2[text()="{self.cat_a_dname}"]')
        # Entry_A is in Category_A
        self.selenium.driver.find_element(By.XPATH, expand_path(f'//h2[text()="{self.cat_a_dname}"]/following-sibling::*//*[@containsClass="tile__name"][text()="{self.entry_a_1_dname}"]'))
        self.selenium.driver.find_element(By.XPATH, expand_path(f'//h2[text()="{self.cat_a_dname}"]/following-sibling::*//*[@containsClass="tile__name"][text()="{self.entry_a_2_dname}"]'))
        self.selenium.driver.find_element(By.XPATH, expand_path(f'//h2[text()="{self.cat_a_dname}"]/following-sibling::*//*[@containsClass="tile__name"][text()="{self.entry_a_2_dname}"]/following::*[@containsClass="tile__name"][text()="{self.entry_a_1_dname}"]'))
        # Entry_B is in Category_B
        self.selenium.driver.find_element(By.XPATH, expand_path(f'//h2[text()="{self.cat_b_dname}"]/following-sibling::*//*[@containsClass="tile__name"][text()="{self.entry_b_dname}"]'))

        logger.info('Reload dummy portal')
        self.selenium.driver.get(self.selenium.base_url)
        self.selenium.wait_until_standby_animation_appears_and_disappears()

        logger.info('Check order after reload')
        # Category_A is after Category_B
        self.selenium.driver.find_element(By.XPATH, f'//h2[text()="{self.cat_b_dname}"]/following::h2[text()="{self.cat_a_dname}"]')
        # Entry_A is in Category_A
        self.selenium.driver.find_element(By.XPATH, expand_path(f'//h2[text()="{self.cat_a_dname}"]/following-sibling::*//*[@containsClass="tile__name"][text()="{self.entry_a_1_dname}"]'))
        self.selenium.driver.find_element(By.XPATH, expand_path(f'//h2[text()="{self.cat_a_dname}"]/following-sibling::*//*[@containsClass="tile__name"][text()="{self.entry_a_2_dname}"]'))
        self.selenium.driver.find_element(By.XPATH, expand_path(f'//h2[text()="{self.cat_a_dname}"]/following-sibling::*//*[@containsClass="tile__name"][text()="{self.entry_a_2_dname}"]/following::*[@containsClass="tile__name"][text()="{self.entry_a_1_dname}"]'))
        # Entry_B is in Category_B
        self.selenium.driver.find_element(By.XPATH, expand_path(f'//h2[text()="{self.cat_b_dname}"]/following-sibling::*//*[@containsClass="tile__name"][text()="{self.entry_b_dname}"]'))

    def cleanup(self):
        logger.info('Cleanup')
        if hasattr(self, 'prev_comps'):
            logger.info('Restore previously set portalComputers on main portal')
            udm = UDM.admin().version(1)
            portal = udm.obj_by_dn(f'cn=domain,cn=portal,cn=portals,cn=univention,{ucr.get("ldap/base")}')
            portal.props.portalComputers = self.prev_comps
            portal.save()


if __name__ == '__main__':
    with ucr_test.UCSTestConfigRegistry() as ucr, UCSTestUDM() as udm_test, selenium.UMCSeleniumTest(suppress_notifications=False) as s:
        umc_tester = UMCTester()
        umc_tester.ucr = ucr
        umc_tester.udm_test = udm_test
        umc_tester.selenium = s

        umc_tester.test_umc()
