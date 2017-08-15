from selenium import webdriver
from selenium.webdriver.support import expected_conditions
import logging

logger = logging.getLogger(__name__)


class ChecksAndWaits(object):
	def wait_for_text(self, text, timeout=60):
		logger.info("Waiting for text: %r", text)
		xpath = '//*[contains(text(), "%s")]' % (text,)
		webdriver.support.ui.WebDriverWait([xpath], timeout).until(
			self.get_all_visible_elements
		)

	def wait_for_any_text_in_list(self, texts, timeout=60):
		logger.info("Waiting until any of those texts is visible: %r", texts)
		xpaths = ['//*[contains(text(), "%s")]' % (text,) for text in texts]
		webdriver.support.ui.WebDriverWait(xpaths, timeout).until(
			self.get_all_visible_elements
		)

	def wait_until_all_dialogues_closed(self):
		logger.info("Waiting for all dialogues to close.")
		xpath = '//*[contains(concat(" ", normalize-space(@class), " "), " dijitDialogUnderlay ")]'
		webdriver.support.ui.WebDriverWait(xpath, timeout=60).until(
			self.elements_invisible
		)

	def wait_until_all_standby_animations_disappeared(self):
		logger.info("Waiting for all standby animations to disappear.")
		xpath = '//*[starts-with(@id, "dojox_widget_Standby_")]/img'
		webdriver.support.ui.WebDriverWait(xpath, timeout=60).until(
			self.elements_invisible
		)

	def wait_until_element_visible(self, xpath):
		logger.info('Waiting for the element with the xpath %r to be visible.' % (xpath,))
		self.wait_until(
			expected_conditions.visibility_of_element_located(
				(webdriver.common.by.By.XPATH, xpath)
			)
		)

	def wait_until(self, check_function, timeout=60):
		webdriver.support.ui.WebDriverWait(self.driver, timeout).until(
			check_function
		)

	def get_all_visible_elements(self, xpaths):
		visible_elems = []
		for xpath in xpaths:
			elems = self.driver.find_elements_by_xpath(xpath)
			[visible_elems.append(elem) for elem in elems if elem.is_displayed()]
		if len(visible_elems) > 0:
			return visible_elems
		return False

	def elements_invisible(self, xpath):
		elems = self.driver.find_elements_by_xpath(xpath)
		visible_elems = [elem for elem in elems if elem.is_displayed()]
		if len(visible_elems) is 0:
			return True
		return False
