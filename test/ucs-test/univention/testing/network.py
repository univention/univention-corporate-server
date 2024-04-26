#
# UCS test
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2014-2024 Univention GmbH
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

"""
Networking helper that may establish connection redirection for testing
network connections/configuration of different programs (e.g. postfix).

WARNING:
The networking helper will install special iptables rules that may completely
break routing from/to the test system. Especially if the test script does
not clean up in error cases!
"""

from __future__ import annotations

import copy
import re
import subprocess
from types import TracebackType
from typing import Mapping, Sequence

from typing_extensions import Literal

import univention.config_registry


class UCSTestNetwork(Exception):
    pass


class UCSTestNetworkCannotDetermineExternalAddress(UCSTestNetwork):
    pass


class UCSTestNetworkCmdFailed(UCSTestNetwork):
    pass


class UCSTestNetworkUnknownLoop(UCSTestNetwork):
    pass


class UCSTestNetworkUnknownRedirection(UCSTestNetwork):
    pass


class UCSTestNetworkNoWithStatement(UCSTestNetwork):
    message = 'NetworkRedirector has to be used via with statement!'


class UCSTestNetworkOnlyOneLoopSupported(UCSTestNetwork):
    message = 'NetworkRedirector does support only ONE loop at a time!'


class NetworkRedirector:
    """
    The NetworkRedirector is able to establish port/connection redirections via
    iptables. It has to be used via the with-statement.

    >>> NetworkRedirector.BIN_IPTABLES = '/bin/true'  # monkey-patch for unit-testing only
    >>> with NetworkRedirector() as nethelper:  # doctest: +ELLIPSIS
    ...     nethelper.add_loop('1.2.3.4', '4.3.2.1')
    ...     nethelper.add_redirection('1.1.1.1', 25, 60025)
    ...     pass
    ...     # the following lines are optional! NetworkRedirector does automatic cleanup!
    ...     nethelper.remove_loop('1.2.3.4', '4.3.2.1')
    ...     nethelper.remove_redirection('1.1.1.1', 25, 60025)
    *** Entering with-statement of NetworkRedirector()
    ...

    It is also possible to redirect all traffic to a specific port.
    The trailing "/0" is important, otherwise the redirection won't work!

    >>> with NetworkRedirector() as nethelper:  # doctest: +ELLIPSIS
    ...     nethelper.add_redirection('0.0.0.0/0', 25, 60025)
    *** Entering with-statement of NetworkRedirector()
    ...
    """

    BIN_IPTABLES = '/sbin/iptables'
    CMD_LIST_LOOP = [
        # localhost--><addr1> ==> <addr2>-->localhost
        ["%(IPT)s", '-t', 'mangle', '%(action)s', 'OUTPUT', '-d', '%(addr1)s', '-j', 'TOS', '--set-tos', '0x04'],
        ["%(IPT)s", '-t', 'nat', '%(action)s', 'OUTPUT', '-d', '%(addr1)s', '-j', 'DNAT', '--to-destination', '%(local_external_addr)s'],
        ["%(IPT)s", '-t', 'nat', '%(action)s', 'POSTROUTING', '-m', 'tos', '--tos', '0x04', '-j', 'SNAT', '--to-source', '%(addr2)s'],

        # localhost--><addr2> ==> <addr1>-->localhost
        ["%(IPT)s", '-t', 'mangle', '%(action)s', 'OUTPUT', '-d', '%(addr2)s', '-j', 'TOS', '--set-tos', '0x08'],
        ["%(IPT)s", '-t', 'nat', '%(action)s', 'OUTPUT', '-d', '%(addr2)s', '-j', 'DNAT', '--to-destination', '%(local_external_addr)s'],
        ["%(IPT)s", '-t', 'nat', '%(action)s', 'POSTROUTING', '-m', 'tos', '--tos', '0x08', '-j', 'SNAT', '--to-source', '%(addr1)s'],
    ]

    CMD_LIST_REDIRECTION = [
        # redirect localhost-->%(remote_addr)s:%(remote_port)s ==> localhost:%(local_port)s
        ["%(IPT)s", '-t', 'nat', '%(action)s', 'OUTPUT', '-p', '%(family)s', '-d', '%(remote_addr)s', '--dport', '%(remote_port)s', '-j', 'DNAT', '--to-destination', '127.0.0.1:%(local_port)s'],
    ]

    def __init__(self) -> None:
        ucr = univention.config_registry.ConfigRegistry()
        ucr.load()
        reUCRaddr = re.compile('^interfaces/[^/]+/address$')
        for key in ucr.keys():
            if reUCRaddr.match(key):
                self._external_address = ucr.get(key)
                break
        else:
            raise UCSTestNetworkCannotDetermineExternalAddress
        self.used_by_with_statement = False
        self.cleanup_rules: list[tuple[Literal["loop"], str, str] | tuple[Literal["redirection"], str, int, int, str]] = []
        # [ ('loop', 'addr1', 'addr2'), ('redirection', 'remoteaddr', remoteport, localport), ... ]

    def __enter__(self) -> NetworkRedirector:  # FIXME Py3.9: Self
        print('*** Entering with-statement of NetworkRedirector()')
        self.used_by_with_statement = True
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> None:
        print('*** Leaving with-statement of NetworkRedirector()')
        self.revert_network_settings()

    def revert_network_settings(self) -> None:
        print('*** NetworkRedirector.revert_network_settings()')
        for entry in copy.deepcopy(self.cleanup_rules):
            if entry[0] == 'loop':
                self.remove_loop(entry[1], entry[2], ignore_errors=True)
            elif entry[0] == 'redirection':
                self.remove_redirection(entry[1], entry[2], entry[3], entry[4], ignore_errors=True)

    def run_commands(self, cmdlist: Sequence[Sequence[str]], argdict: Mapping[str, str], ignore_errors: bool = False) -> None:
        """
        Start all commands in cmdlist and replace formatstrings with arguments in argdict.

        >>> with NetworkRedirector() as nethelper:  # doctest: +ELLIPSIS
        ...     nethelper.run_commands([['/bin/echo', '%(msg)s'], ['/bin/echo', 'World']], {'msg': 'Hello'})
        *** Entering with-statement of NetworkRedirector()
        ...
        """
        for cmd in cmdlist:
            cmd = [val % dict(argdict, IPT=self.BIN_IPTABLES) for val in cmd]
            print('*** %r' % cmd)
            result = subprocess.call(cmd)
            if result and not ignore_errors:
                print('*** Exitcode: %r' % result)
                raise UCSTestNetworkCmdFailed('Command returned with non-zero exitcode: %r' % cmd)

    def add_loop(self, addr1: str, addr2: str) -> None:
        """
        Add connection loop for addr1 and addr2.
        Outgoing connections to addr1 will be redirected back to localhost. The redirected
        connection will appear as it comes from addr2. All outgoing traffic to addr2 will
        be also redirected back to localhost and will appear as it comes from addr1.

        HINT: only one loop may be established at a time!
        """
        if not self.used_by_with_statement:
            raise UCSTestNetworkNoWithStatement
        for i in self.cleanup_rules:
            if i[0] == 'loop':
                raise UCSTestNetworkOnlyOneLoopSupported

        self.cleanup_rules.append(('loop', addr1, addr2))
        args = {
            'addr1': addr1,
            'addr2': addr2,
            'local_external_addr': self._external_address,
            'action': '-A',
        }
        print(f'*** Adding network loop ({addr1} <--> {addr2})')
        self.run_commands(self.CMD_LIST_LOOP, args)

    def remove_loop(self, addr1: str, addr2: str, ignore_errors: bool = False) -> None:
        """Remove previously defined connection loop."""
        try:
            self.cleanup_rules.remove(('loop', addr1, addr2))
        except ValueError:
            raise UCSTestNetworkUnknownLoop('The given loop has not been established and cannot be removed.')

        args = {
            'addr1': addr1,
            'addr2': addr2,
            'local_external_addr': self._external_address,
            'action': '-D',
        }
        print(f'*** Removing network loop ({addr1} <--> {addr2})')
        self.run_commands(self.CMD_LIST_LOOP, args, ignore_errors)

    def add_redirection(self, remote_addr: str, remote_port: int, local_port: int, family: str = 'tcp') -> None:
        """
        Add new connection redirection.

        Outgoing connections to <remote_addr>:<remote_port> will be redirected back to localhost:<local_port>.
        """
        if not self.used_by_with_statement:
            raise UCSTestNetworkNoWithStatement

        entry: tuple[Literal["redirection"], str, int, int, str] = ('redirection', remote_addr, remote_port, local_port, family)
        if entry not in self.cleanup_rules:
            self.cleanup_rules.append(entry)
            args: dict[str, str] = {
                'remote_addr': remote_addr,
                'remote_port': str(remote_port),
                'local_port': str(local_port),
                'action': '-A',
                'family': family,
            }
            print(f'*** Adding network redirection ({remote_addr}:{remote_port} --> 127.0.0.1:{local_port} with {family})')
            self.run_commands(self.CMD_LIST_REDIRECTION, args)

    def remove_redirection(self, remote_addr: str, remote_port: int, local_port: int, family: str = 'tcp', ignore_errors: bool = False) -> None:
        """Remove previously defined connection redirection."""
        try:
            self.cleanup_rules.remove(('redirection', remote_addr, remote_port, local_port, family))
        except ValueError:
            raise UCSTestNetworkUnknownRedirection('The given redirection has not been established and cannot be removed.')

        args: dict[str, str] = {
            'remote_addr': remote_addr,
            'remote_port': str(remote_port),
            'local_port': str(local_port),
            'action': '-D',
            'family': family,
        }
        print(f'*** Removing network redirection ({remote_addr}:{remote_port} <--> 127.0.0.1:{local_port})')
        self.run_commands(self.CMD_LIST_REDIRECTION, args, ignore_errors)
