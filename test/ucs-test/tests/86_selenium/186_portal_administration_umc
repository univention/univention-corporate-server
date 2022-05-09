#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
# -*- coding: utf-8 -*-
## desc: Test creating a portal via UMC
## roles:
##  - domaincontroller_master
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import logging
import subprocess

import univention.config_registry
from univention.testing import selenium
import univention.testing.ucr as ucr_test
from univention.testing.udm import UCSTestUDM
from univention.admin import localization
from univention.udm import UDM
from selenium.common.exceptions import TimeoutException
import univention.testing.selenium.udm as selenium_udm

logger = logging.getLogger(__name__)

translator = localization.translation('ucs-test-selenium')
_ = translator.translate


class PortalNotSetException(Exception):
	pass


class UMCTester(object):

	def test_umc(self):
		try:
			self.do_test()
		finally:
			self.cleanup()

	def do_test(self):
		self.udm = UDM.admin().version(1)
		self.selenium.do_login()

		logger.info('Create portal via UMC and set this host as server')
		self.portals = selenium_udm.Portals(self.selenium)
		self.selenium.open_module('Portal')
		self.portal_name = self.portals.add()
		portal = list(self.udm.get('portals/portal').search('name={}'.format(self.portal_name)))[0]
		portal_dname = portal.props.displayName['en_US']
		univention.config_registry.handler_set(['portal/default-dn=%s' % portal.dn])
		subprocess.call(['univention-portal', 'update'])
		logger.info('Visiting portal')
		self.selenium.driver.get(self.selenium.base_url)
		try:
			self.selenium.wait_for_text(portal_dname)
		except TimeoutException:
			raise PortalNotSetException('The portal added via UMC is not visible')

	def cleanup(self):
		logger.info('Cleanup')
		if hasattr(self, 'portal_name'):
			logger.info('Delete portal created via UMC')
			try:
				self.udm.obj_by_dn('cn=%s,cn=portal,cn=portals,cn=univention,%s' % (self.portal_name, self.ucr.get('ldap/base'))).delete()
			except Exception:
				pass


if __name__ == '__main__':
	with ucr_test.UCSTestConfigRegistry() as ucr, UCSTestUDM() as udm_test, selenium.UMCSeleniumTest() as s:
		umc_tester = UMCTester()
		umc_tester.ucr = ucr
		umc_tester.udm_test = udm_test
		umc_tester.selenium = s

		umc_tester.test_umc()
	subprocess.call(['univention-portal', 'update'])
