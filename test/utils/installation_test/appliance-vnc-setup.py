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
        if self.text_is_visible('Notification'):
            self.screenshot('notification.png')
            self.click_on('OK')

        """
        # UCS setup
        Welcome to Univention Corporate Server (UCS). A few questions are needed to complete the configuration process.
        Choose your language
          [English]
        Enter a city nearby to preconfigure settings such as timezone, system language, keyboard layout.
          [...]

        [Next]
        """
        try:
            self.client.waitForText('English', timeout=self.timeout, prevent_screen_saver=True)
        except VNCDoException:
            pass

        self.screenshot('language-setup.png')
        self.go_next(tabs=2)
        """
        # Localization settings
        Choose your system's localization settings.

        Default system locale
          [English (United States)]
        Time zone
          [America/New_York]
        Keyboard layout
          [English (US)]

        [Back] [Next]
        """
        self.client.waitForText('Localization', timeout=self.timeout)
        self.go_next(tabs=4)

    @verbose("NETWORK")
    def network(self):  # type: () -> None
        """
        # Domain and network configuration
        Specify the network settings for this system.

        [x] Obtain IP address automatically (DHCP)
        (Request address again)
        IPv4/IPv6 address  IPv4 net mask/IPv6 prefix
          [...]              [...]
        Gateway
          [...]
        Preferred DNS server  Alternate DNS server
          [...]                 [...]
        (configure proxy settings)

        [Back] [Next]
        """
        try:
            self.client.waitForText('IP address', timeout=self.timeout)
        except VNCDoException:
            self.client.waitForText('Domain and network', timeout=self.timeout)

        self.screenshot('network-setup.png')
        if self.args.role in {'admember', 'slave'}:
            self.click_on('Preferred')
            self.type(self.args.dns)
            time.sleep(0.5)

        self.type('\n')

        sleep(60, "net.apipa")
        self.check_apipa()
        try:
            self.client.waitForText('No gateway has been', timeout=self.timeout)
            self.type('\n')
            sleep(60, "net.gateway")
        except VNCDoException:
            pass

        try:
            self.client.waitForText('continue without access', timeout=self.timeout)
            self.type('\n')
            sleep(60, "net.unconnected")
        except VNCDoException:
            pass

        sleep(120, "net.finish")

    def domain(self, role):  # type: (str) -> None
        """
        # Domain setup
        Please select your domain settings.

          Create a new UCS domain (Recommended)
            Configure this system as first system for the new domain. Additional systems can join the domain later.
          Join into an existing UCS domain
            Use this option if you already have one ore more UCS systems.
          Join into an existing Microsoft Active Directory domain
            This system will become part of an existing non-UCS Active Directory domain.

        [Back] [Next]
        """
        if role == 'admember':
            text = 'Join into an existing Microsoft Active'
        elif role in {'join', 'slave'}:
            text = 'Join into an existing UCS domain'
        elif role == 'fast':
            text = 'Fast demo'  # FIXME
        elif self.args.ucs:
            text = 'Create a new UCS domain'
        else:
            text = 'Manage users and permissions'  # FIXME

        self.click_on(text)
        self.screenshot('domain-setup.png')
        self.go_next(tabs=2)

        sleep(10, "ucs.role")
        if role == 'slave':
            """
            # System role
            Specify the type of this system.

              Backup Directory Node
                ...
              Replica Directory Node
                ...
              Managed Node
                ...

            [Back] [Next]
            """
            # self.client.keyPress('down')
            self.click_on('Replica Directory Node')
            self.go_next(tabs=2)
            """
            # Domain join information
            Enter name and password of a user account which is authorised to join a system into this domain.

            [x] Start join at the end of the installation
            [x] Search Primary Directory Node in DNS
            Hostname of the Primary Directory Node *
              [...]
            Username*
              [...]
            Password*
              [...]

            [Back] [Next]
            """
            self.click_on('Username')
            self.type(self.args.join_user)
            self.click_on('Password')
            self.type(self.args.join_password)
            self.go_next(tabs=2)
        elif role == 'admember':
            """
            # Active Directory join

            [Back] [Next]
            """
            self.client.waitForText('Active Directory join', timeout=self.timeout)
            self.click_on('Username')
            self.type(self.args.join_user)
            self.click_on('Password')
            self.type(self.args.join_password)
            self.go_next(tabs=2)

    def orga(self, orga, password):  # type: (str, str) -> None
        """
        # Account information
        Enter the name of your organization, an e-mail address to activate UCS and a password for your /Administrator/ account.
        The password is mandatory, it will be used for the domain Administrator as well as for the local superuser /root/.

          Organization name
            [...]
          E-mail address to activate UCS (more information)
            [...]
          Fill in the password for the system administrator user *root* and the domain administrative user account *Administrator*.
          Password*  Password (retype) *
            [...]      [...]

        [Back] [Next]
        """
        self.client.waitForText('Account information', timeout=self.timeout)
        self.screenshot('organisation-setup.png')
        self.type('home\t\t\t%s\t%s' % (password, password))
        self.go_next(tabs=2)

    def hostname(self):  # type: () -> None
        """
        # Host settings
        Specify the name of this system

        Fully qualified domain name*  LDAP base*
          [...]                         [...]

        [Back] [Next]
        """
        self.client.waitForText('Host settings', timeout=self.timeout)
        self.screenshot('hostname-setup.png')
        self.type(self.args.fqdn + "\t", clear=True)
        if self.args.role in {'admember', 'slave'}:
            self.type("%s\t%s" % (self.args.password, self.args.password))

        self.go_next(tabs=2)

    def start(self):  # type: () -> None
        """
        # Confirm configuration settings
        Please confirm the chosen configuration settings which are summarized in the following.

          UCS configuration: A new UCS domain will be created.
          Localization settings
          * Default system locale: English (United States)
          * Time zone: America/New_York
          * Keyboard layout: English (US)
          Domain and host configuration
          * Fully qualified domain name: ...
          * LDAP base: ...
          * Address configuration: IP address is obtained dynamically via DHCP
          * DNS server: ...
          [x] Update system after setup (more information)
          Without the activation of UCS you agree to our privacy statement.

        [Back] [Configure System]
        """
        self.client.waitForText('confirm configuration', timeout=self.timeout)
        self.screenshot('start-setup.png')
        for _ in range(3):
            self.client.keyPress('down')
        try:
            self.click_on('configuresystem')
        except VNCDoException:
            self.click_on('configure system')

    @verbose("FINISH")
    def finish(self):  # type: () -> None
        sleep(600, "install")
        self.client.waitForText('Setup successful', timeout=3000, prevent_screen_saver=True)
        self.screenshot('finished-setup.png')
        self.type('\t\n')
        # except welcome screen
        try:
            self.client.waitForText('www', timeout=self.timeout)
        except VNCDoException:
            self.client.waitForText('press any key', timeout=self.timeout)
        self.screenshot('welcome-screen.png')

    def _go_next_search(self):  # type: () -> None
        self.click_on('NEXT')

    def _go_next_tab(self, tabs):  # type: (int) -> None
        self.type("\t" * tabs + "\n")

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
