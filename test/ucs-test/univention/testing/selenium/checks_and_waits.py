#!/usr/bin/python3
#
# Selenium Tests
#
# SPDX-FileCopyrightText: 2017-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import logging
from collections.abc import Callable, Iterable
from typing import Any

import selenium.common.exceptions as selenium_exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from univention.testing.selenium.utils import expand_path


logger = logging.getLogger(__name__)


class ChecksAndWaits:

    def wait_for_text(self, text: str, timeout: int = 60) -> None:
        logger.info("Waiting for text: %r", text)
        xpath = f'//*[contains(text(), "{text}")]'
        WebDriverWait([xpath], timeout).until(
            self.get_all_visible_elements, f'waited {timeout} seconds for text {text!r}',
        )

    def wait_for_any_text_in_list(self, texts: Iterable[str], timeout: int = 60) -> None:
        logger.info("Waiting until any of those texts is visible: %r", texts)
        xpaths = [f'//*[contains(text(), "{text}")]' for text in texts]
        WebDriverWait(xpaths, timeout).until(
            self.get_all_visible_elements, f'waited {timeout} seconds for texts {texts!r}',
        )

    def wait_for_text_to_disappear(self, text: object, timeout: int = 60) -> None:
        xpath = f'//*[contains(text(), "{text}")]'
        WebDriverWait(xpath, timeout).until(
            self.elements_invisible, f'waited {timeout} seconds for text {text!r} to disappear',
        )

    def wait_for_button(self, button_text: str, **kwargs: Any) -> None:
        logger.info("Waiting for the button %r", button_text)
        self.click_element(
            expand_path('//*[@containsClass="dijitButtonText"][text() = "%s"]')
            % (button_text,),
            **kwargs,
        )

    def wait_until_all_dialogues_closed(self) -> None:
        logger.info("Waiting for all dialogues to close.")
        xpath = '//*[contains(concat(" ", normalize-space(@class), " "), " dijitDialogUnderlay ")]'
        WebDriverWait(xpath, timeout=60).until(
            self.elements_invisible, 'wait_until_all_dialogues_closed() timeout=60',
        )

    def wait_until_all_standby_animations_disappeared(self, timeout: int = 60) -> None:
        logger.info("Waiting for all standby animations to disappear.")
        xpath = expand_path('//*[contains(@id, "_Standby_")]//*[@containsClass="umcStandbySvgWrapper"]')
        WebDriverWait(xpath, timeout).until(
            self.elements_invisible, f'wait_until_all_standby_animations_disappeared(timeout={timeout!r})',
        )

    def wait_until_standby_animation_appears(self, timeout: int = 5) -> None:
        logger.info("Waiting for standby animation to appear.")
        xpath = expand_path('//*[contains(@id, "_Standby_")]//*[@containsClass="umcStandbySvgWrapper"]')
        try:
            WebDriverWait(xpath, timeout).until(
                self.elements_visible, f'wait_until_standby_animation_appears(timeout={timeout!r})',
            )
        except selenium_exceptions.TimeoutException:
            logger.info("No standby animation appeared during timeout. Ignoring")
        else:
            logger.info("Found standby animation")

    def wait_until_standby_animation_appears_and_disappears(self, appear_timeout: int = 5, disappear_timeout: int = 60) -> None:
        self.wait_until_standby_animation_appears(timeout=appear_timeout)
        self.wait_until_all_standby_animations_disappeared(timeout=disappear_timeout)

    def wait_until_progress_bar_finishes(self, timeout: int = 300) -> None:
        logger.info("Waiting for all progress bars to disappear.")
        xpath = '//*[contains(concat(" ", normalize-space(@class), " "), " umcProgressBar ")]'
        WebDriverWait(xpath, timeout=timeout).until(
            self.elements_invisible, f'waited {timeout} seconds for progress bar',
        )

    def wait_until_element_visible(self, xpath: str, timeout: int = 60) -> None:
        logger.info("Waiting for the element with the xpath %r to be visible.", xpath)
        self.wait_until(
            expected_conditions.visibility_of_element_located(
                (By.XPATH, xpath),
            ),
            timeout=timeout,
        )

    def wait_until(self, check_function: Callable[..., Any], timeout: int = 60) -> None:
        WebDriverWait(self.driver, timeout).until(
            check_function, f'wait_until({check_function!r}, timeout={timeout!r})',
        )

    def get_gallery_items(self) -> list[str]:
        items = self.get_all_visible_elements(['//div[contains(concat(" ", normalize-space(@class), " "), " umcGalleryName ")]'])
        return [item.text for item in items]

    def get_all_visible_elements(self, xpaths: Iterable[str]) -> list[Any]:
        try:
            return [
                elem
                for xpath in xpaths
                for elem in self.driver.find_elements(By.XPATH, xpath)
                if elem.is_displayed()
            ]
        except selenium_exceptions.StaleElementReferenceException:
            pass
        return []

    def elements_invisible(self, xpath: Iterable[str]) -> bool:
        elems = self.driver.find_elements(By.XPATH, xpath)
        try:
            return all(not elem.is_displayed() for elem in elems)
        except selenium_exceptions.StaleElementReferenceException:
            pass
        return False

    def elements_visible(self, xpath: Iterable[str]) -> bool:
        elems = self.driver.find_elements(By.XPATH, xpath)
        try:
            return any(elem.is_displayed() for elem in elems)
        except selenium_exceptions.StaleElementReferenceException:
            pass
        return False

    def wait_for_element_by_css_selector(self, css_selector: str, message: str = '', timeout: int = 60) -> Any:
        return WebDriverWait(self.driver, timeout).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, css_selector)),
            message,
        )
