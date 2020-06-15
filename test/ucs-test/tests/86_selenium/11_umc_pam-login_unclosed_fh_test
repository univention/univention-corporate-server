#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium
## desc: Check for unclosed file handles after log ins and password resets
## packages:
##  - univention-management-console-module-udm
##  - univention-management-console-module-passwordchange
## roles-not:
##  - memberserver
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

import subprocess
import time

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import univention.testing.utils as utils
from univention.testing import selenium

from univention.admin import localization

import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test

translator = localization.translation("ucs-test-selenium")
_ = translator.translate


class UMCTester:
    """
    This test checks problems caused by open file descriptors.
    """

    def __init__(self, sel, hostname, domainname):

        self.hostname = hostname
        self.domainname = domainname
        self.fqdn = "%s.%s" % (hostname, domainname)

        self.selenium = sel
        self.browser = self.selenium.driver

    def test_umc(self, udm):
        """ call all tests """
        if not self.test_umc_logon(udm):
            msg = "The amount of connections in CLOSE_WAIT state are > 2 after testing UMC logon"
            return False, msg

        if not self.test_umc_logon(udm, True):
            msg = "The amount of connections in CLOSE_WAIT state are > 2 after testing UMC logon with a wrong password"
            return False, msg

        return True, ""

    def count_fhs(self):
        umc_pid = int(subprocess.check_output(
            "pidof -x univention-management-console-server".split(" ")))

        return int(subprocess.check_output(
            ["bash", "-c", "lsof -p " + str(umc_pid) + " | grep 7389 | wc -l"]))

    def take_a_screenshot(self):
        self.selenium.driver.get(
            s.base_url + "/univention/self-service/#page=passwordchange"
        )
        self.selenium.save_screenshot()

    @classmethod
    def systemd_restart(cls, service):
        """
        check_call runs a command with arguments and waits for command to
        complete. No further wait is necessary.
        """

        subprocess.check_call(["systemctl", "restart", service])

    def umc_logon(self, username, pw, try_wrong_pw):
        """
        method to log into the ucs portal with a given username and password
        """

        try:
            self.browser.get("http://" + self.fqdn + "/univention/portal/")

            WebDriverWait(self.browser, 30).until(
                expected_conditions.element_to_be_clickable(
                    (By.XPATH, '//*[@id="umcLoginButton_label"]')
                )
            ).click()
            WebDriverWait(self.browser, 30).until(
                expected_conditions.element_to_be_clickable(
                    (By.XPATH, '//*[@id="umcLoginUsername"]')
                )
            ).send_keys(username)
            WebDriverWait(self.browser, 30).until(
                expected_conditions.element_to_be_clickable(
                    (By.XPATH, '//*[@id="umcLoginPassword"]')
                )
            ).send_keys(pw)

            elem = self.browser.find_elements_by_id("umcLoginSubmit")[0]
            elem.click()

            WebDriverWait(self.browser, 30).until(
                expected_conditions.element_to_be_clickable(
                    (By.XPATH, '//*[@id="umcLoginButton_label"]')
                )
            ).click()
        except BaseException as exc:
            if not try_wrong_pw:
                self.take_a_screenshot()
        finally:
            print("UMC Logon with {} done".format(username))

    def test_umc_logon(self, udm, try_wrong_pw=False):
        """
        count the number of open file handles in the CLOSE_WAIT state after
        several logins. Code taken from `repr2.py`, attached to Bug #51047
        """
        print("\n##################################################################")
        if try_wrong_pw:
            print("  Test UMC login with correct password")
        else:
            print("  Test UMC login with false password")
        print("###################################################################\n")
        self.systemd_restart("univention-management-console-server")

        username = ""
        # this is the default password, but it is made explicit here on purpose
        login_password = password = "univention"
        if try_wrong_pw:
            login_password = "whatever"
        for i in range(0, 4):

            _, username = udm.create_user(set={"password": password})

            print(
                "Created user %d '%s' with password %s. Logging in..."
                % (i, username, password)
            )

            self.umc_logon(username, login_password, try_wrong_pw)
            print("done.\n")
            self.selenium.end_umc_session()

        # wait for timeouts
        time.sleep(60)
        self.systemd_restart("slapd")

        close_wait = self.count_fhs()
        print("> close wait: %d\n" % close_wait)
        return close_wait < 3 # the hard coded value of 3 has to be adapted later


if __name__ == "__main__":

    with selenium.UMCSeleniumTest() as s,\
         ucr_test.UCSTestConfigRegistry() as ucr,\
         udm_test.UCSTestUDM() as udm:

        umc_tester = UMCTester(s, ucr.get("hostname"), ucr.get("domainname"))

        retval, msg = umc_tester.test_umc(udm)

        if not retval:
            utils.fail(msg)

# vim: ft=python
