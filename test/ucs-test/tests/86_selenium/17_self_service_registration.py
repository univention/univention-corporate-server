#!/usr/share/ucs-test/runner /usr/bin/py.test
# -*- coding: utf-8 -*-
## desc: test self registration
## packages:
##  - univention-mail-server
##  - univention-self-service
##  - univention-self-service-master
##  - univention-self-service-passwordreset-umc
## roles-not:
##  - memberserver
##  - basesystem
## join: true
## exposure: dangerous

import pytest

import time

from univention.testing import selenium as sel
from univention.testing.ucr import UCSTestConfigRegistry
from univention.config_registry import handler_set
from test_self_service import capture_mails
import selenium.common.exceptions as selenium_exceptions


@pytest.fixture
def selenium():
    with sel.UMCSeleniumTest() as s:
        yield s

@pytest.fixture
def ucr():
    with UCSTestConfigRegistry() as ucr:
        yield ucr

@pytest.fixture
def mails():
    with capture_mails(timeout=5) as mails:
        yield mails

# test the umc/self-service/registration/enabled ucr variable
def test_registration_enabled(ucr, selenium):
    handler_set(['umc/self-service/registration/enabled=false'])
    selenium.driver.get(selenium.base_url + 'univention/self-service')
    with pytest.raises(selenium_exceptions.TimeoutException) as excinfo:
        selenium.wait_for_text('Create an account', 2)
    handler_set(['umc/self-service/registration/enabled=true'])
    selenium.driver.get(selenium.base_url + 'univention/self-service')
    selenium.wait_for_text('Create an account', 2)

# tests existence of all attributes umc/self-service/registration/udm_attributes
def test_udm_attributes(ucr, selenium):
    selenium.driver.get(selenium.base_url + 'univention/self-service/#page=createaccount')
    selenium.wait_until_element_visible('//h2[text()="Create an account"]')
    selenium.wait_until_element_visible('//label[text()="Email *"]')
    selenium.wait_until_element_visible('//label[text()="Password *"]')
    selenium.wait_until_element_visible('//label[text()="Password (retype) *"]')
    selenium.wait_until_element_visible('//label[text()="First name"]')
    selenium.wait_until_element_visible('//label[text()="Last name *"]')
    selenium.wait_until_element_visible('//label[text()="User name *"]')

# tests whether a user is created and put into the right container
def test_user_creation(mails, selenium):
    selenium.driver.get(selenium.base_url + 'univention/self-service/#page=createaccount')
    selenium.enter_input('PasswordRecoveryEmail', 'testuser@example.com')
    selenium.enter_input('password_1', 'univention')
    selenium.enter_input('password_2', 'univention')
    selenium.enter_input('lastname', 'user')
    selenium.enter_input('username', 'user')
    selenium.click_button('Create account')
    selenium.wait_until_standby_animation_appears_and_disappears()


