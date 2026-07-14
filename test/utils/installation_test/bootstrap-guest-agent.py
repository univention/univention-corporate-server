#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Install qemu-guest-agent on a freshly VNC-installed UCS via its console.

A UCS installed from ISO ships without qemu-guest-agent, so `ucs-proxmox-create`
cannot discover the VM's IP address and no SSH connection is possible yet. This
tool breaks that cycle out-of-band: it logs into a text console through the
(Proxmox) VNC connection, installs qemu-guest-agent and then polls the Proxmox
API until the agent answers - the deterministic signal that agent-based IP
discovery will work from now on.

Run it between `vnc-install-ucs.py` and the first SSH-based command (COPY_FILES).
"""

import logging
import ssl
import time
import urllib.error
import urllib.request
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, RawDescriptionHelpFormatter
from urllib.parse import quote

from installation import VNCInstallation, build_parser, sleep, verbose
from proxmox_vnc import load_credentials


log = logging.getLogger(__name__)

# Console keysym transposition for VMs whose QEMU VNC keymap is German while the
# installed UCS uses the US console keymap (vnc-install-ucs.py always selects
# 'us_keyboard_layout'). On such VMs every keysym passes QEMU's de keymap before
# the guest's us keymap, so the *sent* keysym must sit on the German keyboard at
# the physical position of the *intended* US character. The y/z swap, '/', '=',
# '@' and '|' entries replicate what configure_kvm_network() types manually; the
# remaining entries follow the same physical-position rule.
_DE_CONSOLE_KEYS: dict[str, str | tuple[str, str]] = {
    "y": "z", "Y": "Z",
    "z": "y", "Z": "Y",
    "/": "-",
    "=": "`",
    "-": "ß",
    ";": "ö",
    ":": "Ö",
    "_": ("shift", "ß"),
    "@": ("shift", "2"),
    "|": ("shift", "'"),
}


class _HelpFormatter(ArgumentDefaultsHelpFormatter, RawDescriptionHelpFormatter):
    """Show argument defaults and keep the epilog's raw formatting."""


def agent_ping(credentials: dict[str, str], node: str, vmid: str, port: int = 443) -> bool:
    """POST /agent/ping; return whether the QEMU guest agent answered."""
    token_id = f"{credentials['proxmox_api_user']}!{credentials['proxmox_api_token_name']}"
    url = (
        f"https://{credentials['proxmox_host']}:{port}/api2/json"
        f"/nodes/{quote(node, safe='')}/qemu/{quote(vmid, safe='')}/agent/ping"
    )
    # The URL is a fixed https:// endpoint assembled from the credentials file
    # (as in proxmox_vnc.py), so the scheme is not caller-controlled; S310 is a
    # false positive.
    req = urllib.request.Request(url, data=b"", method="POST")  # noqa: S310
    req.add_header("Authorization", f"PVEAPIToken={token_id}={credentials['proxmox_api_token_secret']}")
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, context=ssl_ctx) as resp:  # noqa: S310
            return resp.status == 200
    except urllib.error.HTTPError:
        # HTTP 500 "QEMU guest agent is not running"
        return False
    except urllib.error.URLError:
        return False


class GuestAgentBootstrap(VNCInstallation):

    @verbose("MAIN")
    def main(self) -> None:
        self.wait_for_system()
        self.open_console()
        self.login()
        self.install_agent()
        self.wait_for_agent()
        self.logout()

    @verbose("TYPE", "{1!r}")
    def console_type(self, text: str) -> None:
        """Type `text` on the console, transposing keysyms for the configured keymap."""
        if self.args.console_keymap == "us":
            self.type(text)
            return
        time.sleep(1)
        for char in text:
            key = {" ": "space", "\n": "enter"}.get(char) or _DE_CONSOLE_KEYS.get(char, char)
            if isinstance(key, tuple):
                self.client.keyDown(key[0])
                self.client.keyPress(key[1])
                self.client.keyUp(key[0])
            else:
                self.client.keyPress(key)

    @verbose("BOOT")
    def wait_for_system(self) -> None:
        """
        After vnc-install-ucs.py the appliance is booted; the screen shows either
        the graphical setup wizard or a console banner - both contain 'Univention'.
        """
        self.wait_for_text('univention', timeout=-300)

    @verbose("CONSOLE")
    def open_console(self) -> None:
        """Switch to tty2 for a getty, regardless of whether X is running on tty1."""
        self.client.keyDown('ctrl')
        self.client.keyDown('alt')
        self.client.keyPress('f2')
        self.client.keyUp('alt')
        self.client.keyUp('ctrl')
        sleep(3, "console.vt2")

    @verbose("LOGIN")
    def login(self) -> None:
        """
        Welcome to Univention Corporate Server 5.2 ...

        base login: _
        """
        self.type('\n')
        self.wait_for_text('login', timeout=-60)
        self.console_type('root\n')
        sleep(5, "login.user")
        self.console_type(self.args.password + '\n')
        sleep(5, "login.password")

    @verbose("INSTALL")
    def install_agent(self) -> None:
        if self.args.repository_server:
            self.console_type('ucr set repository/online=yes repository/online/server=%s\n' % self.args.repository_server)
            sleep(10, "install.ucr")
        # The unit is static and only started by udev when the virtio port
        # appears at boot
        self.console_type('univention-install -y qemu-guest-agent; systemctl start qemu-guest-agent\n')

    @verbose("PING")
    def wait_for_agent(self) -> None:
        """Poll the Proxmox API until the freshly installed agent answers."""
        credentials = load_credentials(self.args.proxmox_credentials)
        deadline = time.monotonic() + self.args.agent_timeout
        while time.monotonic() < deadline:
            if agent_ping(credentials, self.args.proxmox_node, self.args.proxmox_vmid, self.args.proxmox_port):
                log.info("QEMU guest agent is answering")
                return
            sleep(10, "ping.agent")
        self.screenshot('agent-timeout.png')
        raise SystemExit("qemu-guest-agent did not answer within %ss" % self.args.agent_timeout)

    @verbose("LOGOUT")
    def logout(self) -> None:
        self.console_type('exit\n')
        self.client.keyDown('ctrl')
        self.client.keyDown('alt')
        self.client.keyPress('f1')
        self.client.keyUp('alt')
        self.client.keyUp('ctrl')


def main() -> None:
    parser = ArgumentParser(
        description=__doc__,
        parents=[build_parser()],
        formatter_class=_HelpFormatter,
        epilog="""
Example (in a scenario, between vnc-install-ucs.py and COPY_FILES):
  %(prog)s --proxmox-node uni-pve-03 --proxmox-vmid 5402 \\
      --proxmox-credentials /root/.ucs-ec2-tools.json \\
      --repository-server updates-test.software-univention.de
""",
    )
    parser.add_argument(
        '--language',
        choices=['deu', 'eng', 'fra'],
        default="deu",
        help="OCR language for reading the screen",
    )
    parser.add_argument(
        '--repository-server',
        help="Set repository/online/server before installing. Required for "
             "unreleased versions, whose packages are not yet on the public "
             "updates server a fresh ISO installation points at.",
        metavar="HOST",
    )
    parser.add_argument(
        '--console-keymap',
        choices=['us', 'de'],
        default='us',
        help="QEMU VNC keymap of the host. Proxmox defaults to en-us ('us'); "
             "use 'de' if the datacenter keyboard setting is German (as on the "
             "KVM build servers, cf. configure_kvm_network in vnc-install-ucs.py).",
    )
    parser.add_argument(
        '--agent-timeout',
        default=900,
        type=int,
        help="Seconds to wait for the installed agent to answer",
        metavar="SECONDS",
    )
    args = parser.parse_args()

    if not (args.proxmox_node and args.proxmox_vmid and args.proxmox_credentials):
        parser.error("the Proxmox VNC bridge (--proxmox-node, --proxmox-vmid, "
                     "--proxmox-credentials) is required: success is detected "
                     "by polling the Proxmox API for the agent")

    inst = GuestAgentBootstrap(args=args)
    inst.run()


if __name__ == '__main__':
    main()
