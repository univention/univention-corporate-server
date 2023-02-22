# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2013-2023 Univention GmbH
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

import time
from types import SimpleNamespace

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def wait_for(driver: WebDriver, by: By, element: str, timeout: int = 60) -> None:
    element_present = EC.presence_of_element_located((by, element))
    WebDriverWait(driver, timeout).until(element_present)
    WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((by, element)))
    time.sleep(1)


def wait_for_id(driver: WebDriver, element_id: str, timeout: int = 10) -> WebElement:
    wait_for(driver, By.ID, element_id, timeout)
    return driver.find_element_by_id(element_id)


def wait_for_class(driver: WebDriver, element_class: str, timeout: int = 10) -> WebElement:
    wait_for(driver, By.CLASS_NAME, element_class, timeout)
    return driver.find_elements_by_class_name(element_class)


def get_portal_tile(driver: WebDriver, text: str, portal_config: SimpleNamespace) -> WebElement:
    for tile in driver.find_elements_by_class_name(portal_config.tile_name_class):
        if tile.text == text:
            return tile
