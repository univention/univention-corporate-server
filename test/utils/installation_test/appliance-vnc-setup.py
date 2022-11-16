#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""Setup via UMC"""

import time
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from installation import VNCInstallation, build_parser, sleep, verbose
from vncdotool.client import VNCDoException


class UCSSetup(VNCInstallation):

    @verbose("MAIN")
    def main(self):  # type: () -> None
        self.language('English')
        self.network()
        self.domain(self.args.role)
        if self.args.role == 'master':
            self.orga(self.args.organisation, self.args.password)
        if self.args.role != "fast":
            self.hostname()
        self.start()
        self.finish()

    def language(self, language):  # type: (str) -> None
        if self.text_is_visible('Notification', timeout=self.timeout):
            self.screenshot('notification.png')
            self.client.mouseClickOnText('OK')

        try:
            self.client.waitForText('English', timeout=self.timeout, prevent_screen_saver=True)
        except VNCDoException:
            self.connect()

        self.screenshot('language-setup.png')
        self.go_next(tabs=2)
        self.client.waitForText('Localization', timeout=self.timeout)
        self.go_next(tabs=4)

    @verbose("NETWORK")
    def network(self):  # type: () -> None
        try:
            self.client.waitForText('IP address', timeout=self.timeout)
        except VNCDoException:
            self.connect()
            self.client.waitForText('Domain and network', timeout=self.timeout)

        self.screenshot('network-setup.png')
        if self.args.role in {'admember', 'slave'}:
            self.click_on('Preferred')
            self.client.enterText(self.args.dns)
            time.sleep(0.5)

        self.client.keyPress('enter')

        sleep(60, "net.apipa")
        self.check_apipa()
        try:
            self.client.waitForText('No gateway has been', timeout=self.timeout)
            self.client.keyPress('enter')
            sleep(60, "net.gateway")
        except VNCDoException:
            self.connect()

        try:
            self.client.waitForText('continue without access', timeout=self.timeout)
            self.client.keyPress('enter')
            sleep(60, "net.unconnected")
        except VNCDoException:
            self.connect()

        sleep(120, "net.finish")

    def domain(self, role):  # type: (str) -> None
        if role == 'admember':
            text = 'Join into an existing Microsoft Active'
        elif role in {'join', 'slave'}:
            text = 'Join into an existing UCS domain'
        elif role == 'fast':
            text = 'Fast demo'
        elif self.args.ucs:
            text = 'Create a new UCS domain'
        else:
            text = 'Manage users and permissions'

        self.client.waitForText(text, timeout=self.timeout)
        self.client.mouseClickOnText(text, timeout=self.timeout)
        self.screenshot('domain-setup.png')
        self.go_next(tabs=2)

        sleep(10, "ucs.role")
        if role == 'slave':
            # self.client.keyPress('down')
            self.client.waitForText('Replica Directory Node', timeout=self.timeout)
            self.client.mouseClickOnText('Replica Directory Node', timeout=self.timeout)
            self.go_next(tabs=2)
            self.click_on('Username')
            self.client.enterText(self.args.join_user)
            self.click_on('Password')
            self.client.enterText(self.args.join_password)
            self.go_next(tabs=2)
        elif role == 'admember':
            self.client.waitForText('Active Directory join', timeout=self.timeout)
            self.click_on('Username')
            self.client.enterText(self.args.join_user)
            self.click_on('Password')
            self.client.enterText(self.args.join_password)
            self.go_next(tabs=2)

    def orga(self, orga, password):  # type: (str, str) -> None
        self.client.waitForText('Account information', timeout=self.timeout)
        self.screenshot('organisation-setup.png')
        self.client.enterText('home\t\t\t%s\t%s' % (password, password))
        self.go_next(tabs=2)

    def hostname(self):  # type: () -> None
        self.client.waitForText('Host settings', timeout=self.timeout)
        self.screenshot('hostname-setup.png')
        self.clear_input()
        self.client.enterText(self.args.fqdn + "\t")
        if self.args.role in {'admember', 'slave'}:
            self.client.enterText("%s\t%s" % (self.args.password, self.args.password))

        self.go_next(tabs=2)

    def start(self):  # type: () -> None
        self.client.waitForText('confirm configuration', timeout=self.timeout)
        self.screenshot('start-setup.png')
        for _ in range(3):
            self.client.keyPress('down')
        try:
            self.client.mouseClickOnText('configuresystem')
        except VNCDoException:
            self.connect()
            self.client.mouseClickOnText('configure system')

    @verbose("FINISH")
    def finish(self):  # type: () -> None
        sleep(600, "install")
        self.client.waitForText('Setup successful', timeout=3000, prevent_screen_saver=True)
        self.screenshot('finished-setup.png')
        self.client.keyPress('tab')
        self.client.keyPress('enter')
        # except welcome screen
        try:
            self.client.waitForText('www', timeout=self.timeout)
        except VNCDoException:
            self.connect()
            self.client.waitForText('press any key', timeout=self.timeout)
        self.screenshot('welcome-screen.png')

    def _go_next_search(self):  # type: () -> None
        self.client.waitForText('NEXT', timeout=self.timeout)
        self.client.mouseClickOnText('NEXT')

    def _go_next_tab(self, tabs):  # type: (int) -> None
        for _ in range(tabs):
            self.client.keyPress('tab')
            time.sleep(0.5)
        self.client.keyPress('enter')

    def go_next(self, tabs=0):  # type: (int) -> None
        self._go_next_tab(tabs)


def main():  # type: () -> None
    parser = ArgumentParser(description=__doc__, parents=[build_parser()])
    parser = ArgumentParser(
        description=__doc__,
        parents=[build_parser()],
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--role",
        default="master",
        choices=["master", "admember", "fast", "slave"],
        help="UCS system role",
    )
    parser.add_argument(
        "--ucs",
        action="store_true",
        help="UCS appliance",
    )
    parser.set_defaults(language="eng")
    args = parser.parse_args()

    if args.role in {'admember', 'slave'}:
        assert args.dns is not None
        assert args.join_user is not None
        assert args.join_password is not None

    setup = UCSSetup(args=args)
    setup.run()


if __name__ == '__main__':
    main()
