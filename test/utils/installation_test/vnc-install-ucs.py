#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""UCS installation via VNC"""

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from os.path import dirname, join
from typing import Dict  # noqa: F401

from installation import VNCInstallation, build_parser, sleep, verbose
from vncdotool.client import VNCDoException
from yaml import safe_load


class UCSInstallation(VNCInstallation):

    def load_translation(self, language):  # type: (str) -> Dict[str, str]
        name = join(dirname(__file__), "languages.yaml")
        with open(name) as fd:
            return {
                key: values.get(self.args.language, "")
                for key, values in safe_load(fd).items()
            }

    @verbose("MAIN")
    def main(self):  # type: () -> None
        self.bootmenu()
        self.installer()
        self.setup()
        self.joinpass_ad()
        self.joinpass()
        self.hostname()
        self.ucsschool()
        self.finish()
        if self.args.second_interface:
            # TODO activate 2nd interface for ucs-kvm-create to connect to instance
            # this is done via login and setting interfaces/eth0/type, is there a better way?
            self.configure_kvm_network(self.args.second_interface)

    @verbose("GRUB")
    def bootmenu(self):  # type: () -> None
        if self.text_is_visible('Univention Corporate Server Installer'):
            if self.args.ip:
                self.client.keyPress('down')
            self.type('\n')

    @verbose("INSTALLER")
    def installer(self):  # type: () -> None
        # language
        for _ in range(3):
            self.client.waitForText('Select a language', timeout=self.timeout + 120, prevent_screen_saver=True)
            self.click_at(250, 250)
            self.type(self._['english_language_name'] + "\n")
            try:
                self.client.waitForText(self._['select_location'], timeout=self.timeout)
                break
            except VNCDoException:
                self.click_on('Go Back')

        self.click_at(250, 250)
        self.type(self._['location'] + "\n")
        self.client.waitForText(self._['select_keyboard'], timeout=self.timeout)
        self.click_at(250, 250)
        self.type(self._['us_keyboard_layout'] + "\n")

        if not self.network_setup():
            self.click_at(100, 320)
            sleep(1)

        # root
        self.client.waitForText(self._['user_and_password'], timeout=self.timeout)
        self.type("%s\t\t%s\n" % (self.args.password, self.args.password))
        if self.args.language == 'eng':
            self.client.waitForText(self._['configure_clock'], timeout=self.timeout)
            # self.type(self._['clock'])
            sleep(1)
            self.type('\n')

        # hd
        sleep(60, "disk.detect")
        self.client.waitForText(self._['partition_disks'], timeout=self.timeout)
        if self.args.role == 'applianceLVM':
            #self.click_on(self._['entire_disk_with_lvm'])
            # LVM is the default so just press enter
            self.type('\n')
            sleep(3)
            self.type('\n')
            self.click_on(self._['all_files_on_partition'])
            self.type('\n')
            sleep(3)
            self.client.keyPress('down')
            self.type('\n')
            self.client.waitForText(self._['continue_partition'], timeout=self.timeout)
            self.client.keyPress('down')
            self.type('\n')
        elif self.args.role == 'applianceEC2':
            # Manuel
            self.click_on(self._['manual'])
            self.type('\n')
            sleep(3)
            # Virtuelle Festplatte 1
            self.client.keyPress('down')
            self.client.keyPress('down')
            self.client.keyPress('down')
            self.client.keyPress('enter')
            sleep(3)
            self.client.keyPress('down')
            sleep(3)
            self.type('\n')
            sleep(3)
            self.click_on(self._['free_space'])
            self.type('\n')
            sleep(3)
            # neue partition erstellen
            self.type('\n')
            sleep(3)
            # enter: ganze festplattengröße ist eingetragen
            self.type('\n')
            sleep(3)
            # enter: primär
            self.type('\n')
            sleep(3)
            self.click_on(self._['boot_flag'])
            # enter: boot-flag aktivieren
            self.type('\n')
            sleep(3)
            self.click_on(self._['finish_create_partition'])
            self.type('\n')
            sleep(3)
            self.click_on(self._['finish_partition'])
            self.type('\n')
            sleep(3)
            # Nein (kein swap speicher)
            self.click_on(self._['no'])
            self.type('\n')
            self.client.waitForText(self._['continue_partition'], timeout=self.timeout)
            self.client.keyPress('down')
            self.type('\n\n')
        else:
            self.click_on(self._['entire_disk'])
            self.type('\n')
            sleep(3)
            self.type('\n')
            sleep(3)
            self.type('\n')
            self.click_on(self._['finish_partition'])
            self.type('\n')
            self.client.waitForText(self._['continue_partition'], timeout=self.timeout)
            self.client.keyPress('down')
            self.type('\n')

        sleep(600, "disk.partition install")
        self.client.waitForText(self._['finish_installation'], timeout=1300)
        self.type('\n')
        sleep(30, "reboot")

    @verbose("NETWORK")
    def network_setup(self):  # type: () -> bool
        sleep(60, "scan ISO and network")

        # we may not see this because the only interface is configured via dhcp
        if not self.text_is_visible(self._['configure_network']):
            return False

        self.client.waitForText(self._['configure_network'], timeout=self.timeout)
        if not self.text_is_visible(self._['ip_address']):
            # always use first interface
            self.click_on(self._['continue'])
            sleep(60, "net.detect")

        if self.args.ip:
            if self.text_is_visible(self._['not_using_dhcp']):
                self.type('\n')
                self.click_on(self._['manual_network_config'])
                self.type('\n')

            self.client.waitForText(self._['ip_address'], timeout=self.timeout)
            self.type(self.args.ip + "\n")
            self.client.waitForText(self._['netmask'], timeout=self.timeout)
            if self.args.netmask:
                self.type(self.args.netmask)

            self.type('\n')
            self.client.waitForText(self._['gateway'], timeout=self.timeout)
            if self.args.gateway:
                self.type(self.args.gateway)

            self.type('\n')
            self.client.waitForText(self._['name_server'], timeout=self.timeout)
            if self.args.dns:
                self.type(self.args.dns)

            self.type('\n')

        return True

    def _network_repo(self):
        sleep(120, "net.dns")
        if self.text_is_visible(self._['repositories_not_reachable']):
            self.type('\n')
            sleep(30, "net.dns2")

    @verbose("SETUP")
    def setup(self):  # type: () -> None
        self.client.waitForText(self._['domain_setup'], timeout=self.timeout + 900)
        sub = getattr(self, "_setup_%s" % (self.args.role,))
        sub()

    def _setup_master(self):  # type: () -> None
        self.click_on(self._['new_domain'])
        self.go_next()
        self.client.waitForText(self._['account_information'], timeout=self.timeout)
        self.type('home')
        self.go_next()

    def _setup_joined(self, role_text):  # type: (str) -> None
        self.click_on(self._['join_domain'])
        self.go_next()
        if self.text_is_visible(self._['no_dc_dns']):
            self.click_on(self._['change_settings'])
            self.click_on(self._['preferred_dns'])
            self.type(self.args.dns + "\n")
            self._network_repo()
            self.click_on(self._['join_domain'])
            self.go_next()

        self.client.waitForText(self._['role'])
        self.click_on(role_text)
        self.go_next()

    def _setup_backup(self):  # type: () -> None
        self._setup_joined('Backup Directory Node')

    def _setup_slave(self):  # type: () -> None
        self._setup_joined('Replica Directory Node')

    def _setup_member(self):  # type: () -> None
        self._setup_joined('Managed Node')

    def _setup_admember(self):  # type: () -> None
        self.click_on(self._['ad_domain'])
        self.go_next()
        self.client.waitForText(self._['no_dc_dns'], timeout=self.timeout)
        self.type('\n')
        self.click_on(self._['preferred_dns'])
        sleep(1)
        self.type(self.args.dns + "\n")
        self._network_repo()
        self.check_apipa()
        self.go_next()
        self.go_next()

    def _setup_applianceEC2(self):  # type: () -> None
        self.client.keyDown('ctrl')
        self.client.keyPress('w')  # Ctrl-Q
        self.client.keyUp('ctrl')
        """
        Close window and quit Firefox?
        [x] Confirm before quitting with Ctrl-Q
        [Cancel] [Quit Firefox]
        """
        if self.text_is_visible("Close windows and quit Firefox?", timeout=-3):
            self.type('\n')

        sleep(60, "ec2.finish")
        raise SystemExit(0)

    _setup_applianceLVM = _setup_applianceEC2

    def joinpass_ad(self):  # type: () -> None
        if self.args.role not in {'admember'}:
            return
        # join/ad password and user
        self.client.waitForText(self._['ad_account_information'], timeout=self.timeout)
        for _ in range(2):
            self.click_on(self._['address_ad'])
            self.type("\t")
            self.type(self.args.join_user + "\t", clear=True)
            self.type(self.args.join_password, clear=True)
            self.go_next()
            try:
                self.client.waitForText(self._['error'], timeout=self.timeout)
                self.type('\n')
                self.client.keyPress('caplk')
            except VNCDoException:
                break

    @verbose("JOIN")
    def joinpass(self):  # type: () -> None
        if self.args.role not in {'slave', 'backup', 'member'}:
            return
        self.client.waitForText(self._['start_join'], timeout=self.timeout)
        for _ in range(2):
            self.click_on(self._['hostname_primary'])
            sleep(5)
            self.type('\t')
            self.type(self.args.join_user + "\t", clear=True)
            self.type(self.args.join_password, clear=True)
            self.go_next()
            try:
                self.client.waitForText(self._['error'], timeout=self.timeout)
                self.type('\n')
                self.client.keyPress('caplk')
            except VNCDoException:
                break

    def hostname(self):  # type: () -> None
        # name hostname
        if self.args.role == 'master':
            self.client.waitForText(self._['host_settings'], timeout=self.timeout)
        else:
            self.client.waitForText(self._['system_name'])

        self.type(self.args.fqdn, clear=True)
        if self.args.role == 'master':
            self.type('\t')

        self.go_next()

    def ucsschool(self):  # type: () -> None
        # ucs@school role
        if not self.args.school_dep:
            return

        self.client.waitForText(self._['school_role'], timeout=self.timeout)
        self.click_on(self._['school_%s' % (self.args.school_dep,)])
        self.go_next()

    @verbose("FINISH")
    def finish(self):  # type: () -> None
        self.client.waitForText(self._['confirm_config'], timeout=self.timeout)
        self.type('\n')
        sleep(self.setup_finish_sleep, "FINISH")
        self.client.waitForText(self._['setup_successful'], timeout=2100)
        self.type('\t\n')
        sleep(10, "reboot")
        self.client.waitForText('univention', timeout=self.timeout)

    @verbose("KVM")
    def configure_kvm_network(self, iface):  # type: (str) -> None
        self.client.waitForText('corporate server')
        self.type('\n')
        sleep(3)
        self.type('root\n')
        sleep(5)
        self.type(self.args.password + "\n")
        self.type('ucr set interfaces-%s-tzpe`manual\n' % iface)
        sleep(30, "kvm.ucr")
        self.type('ip link set %s up\n' % iface)
        self.type('echo ')
        self.client.keyDown('shift')
        self.type('2')  # @
        self.client.keyUp('shift')
        self.type('reboot -sbin-ip link set %s up ' % iface)
        self.client.keyDown('shift')
        self.type("'")  # |
        self.client.keyUp('shift')
        self.type(' crontab\n')

    @verbose("NEXT")
    def go_next(self):  # type: () -> None
        self.click_at(910, 700)


def main():  # type: () -> None
    parser = ArgumentParser(
        description=__doc__,
        parents=[build_parser()],
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--language',
        choices=['deu', 'eng', 'fra'],
        default="deu",
        help="Select text language",
    )
    parser.add_argument(
        "--role",
        default="master",
        choices=["master", "backup", "slave", "member", "admember", "applianceEC2", "applianceLVM"],
        help="UCS system role",
    )
    parser.add_argument(
        "--school-dep",
        choices=["central", "edu", "adm"],
        help="Select UCS@school role",
    )

    group = parser.add_argument_group("Network settings")
    group.add_argument(
        "--ip",
        help="IPv4 address if DHCP is unavailable",
    )
    group.add_argument(
        "--netmask",
        help="Network netmask",
    )
    group.add_argument(
        "--gateway",
        help="Default router address",
        metavar="IP",
    )
    parser.add_argument(
        "--second-interface",
        help="configure second interface",
        metavar="IFACE",
    )
    args = parser.parse_args()

    if args.role in {'slave', 'backup', 'member', 'admember'}:
        assert args.dns is not None
        assert args.join_user is not None
        assert args.join_password is not None

    inst = UCSInstallation(args=args)
    inst.run()


if __name__ == '__main__':
    main()
