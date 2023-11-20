# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2004-2023 Univention GmbH
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

"""Univention Setup: network configuration abstract base classes"""

import logging
import subprocess
from ipaddress import IPv4Interface, IPv6Interface
from typing import Dict, List, Optional, Sequence, Set, Type

from univention.config_registry import ConfigRegistry
from univention.config_registry.interfaces import Interfaces


class ChangeSet(object):

    def __init__(self, ucr: ConfigRegistry, profile: Dict[str, str], options):
        self.ucr = ucr
        self.profile = profile
        self.options = options
        self.ucr_changes: Dict[str, Optional[str]] = {}
        self.old_interfaces = Interfaces(ucr)
        self.logger = logging.getLogger("uss.network.change")

        self.update_config(self.only_network_config(profile))

    @staticmethod
    def only_network_config(profile: Dict[str, str]) -> Dict[str, Optional[str]]:
        config: Dict[str, Optional[str]] = {}
        for key, value in profile.items():
            if key.startswith("interfaces/"):
                config[key] = value or None
        return config

    def update_config(self, changes: Dict[str, Optional[str]]) -> None:
        self.ucr_changes.update(changes)
        new_ucr = dict(self.ucr.items())  # Bug #33101
        new_ucr.update(changes)
        self.new_interfaces = Interfaces(new_ucr)

    @property
    def no_act(self) -> bool:
        return self.options.no_act

    @property
    def old_names(self) -> Set[str]:
        return {name for name, _iface in self.old_interfaces.all_interfaces}

    @property
    def new_names(self) -> Set[str]:
        return {name for name, _iface in self.new_interfaces.all_interfaces}

    @property
    def old_ipv4s(self) -> List[IPv4Interface]:
        return [iface.ipv4_address() for _name, iface in self.old_interfaces.ipv4_interfaces]

    @property
    def new_ipv4s(self) -> List[IPv4Interface]:
        return [iface.ipv4_address() for _name, iface in self.new_interfaces.ipv4_interfaces]

    @property
    def old_ipv6s(self) -> List[IPv6Interface]:
        return [iface.ipv6_address(name) for iface, name in self.old_interfaces.ipv6_interfaces]

    @property
    def new_ipv6s(self) -> List[IPv6Interface]:
        return [iface.ipv6_address(name) for iface, name in self.new_interfaces.ipv6_interfaces]


class SkipPhase(Exception):
    pass


class Phase:
    """Base-class for all phases."""

    priority = 0

    def __init__(self, changeset: ChangeSet) -> None:
        self.changeset = changeset
        self.logger = logging.getLogger("uss.network.phase.%s" % (self,))

    def __lt__(self, other: object) -> object:
        """
        Order phases by priority.

        >>> Phase(None) < Phase(None)
        False
        >>> Phase(None) <= Phase(None)
        True
        >>> Phase(None) == Phase(None)
        True
        >>> Phase(None) != Phase(None)
        False
        >>> Phase(None) >= Phase(None)
        True
        >>> Phase(None) > Phase(None)
        False
        """
        if isinstance(other, Phase):
            return (self.priority, str(self)) < (other.priority, str(other))
        raise TypeError(type(self).__name__)

    def __le__(self, other: object) -> object:
        if isinstance(other, Phase):
            return (self.priority, str(self)) <= (other.priority, str(other))
        raise TypeError(type(self).__name__)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Phase) and (self.priority, str(self)) == (other.priority, str(other))

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __ge__(self, other: object) -> object:
        if isinstance(other, Phase):
            return (self.priority, str(self)) >= (other.priority, str(other))
        raise TypeError(type(self).__name__)

    def __gt__(self, other: object) -> object:
        if isinstance(other, Phase):
            return (self.priority, str(self)) > (other.priority, str(other))
        raise TypeError(type(self).__name__)

    def __str__(self) -> str:
        name = self.__class__.__name__
        if name.startswith("Phase"):
            name = name[len("Phase"):]
        return name

    @classmethod
    def _check_valid(cls, other: Type["Phase"]) -> None:
        try:
            if not issubclass(other, cls):
                raise SkipPhase('Invalid super-class')
            if not other.priority:
                raise SkipPhase('Missing priority')
            # if type(other) is ABCMeta:
            #    raise SkipPhase('Abstract class')
        except TypeError:
            raise SkipPhase('Not a class')

    def check(self) -> None:
        """
        Check if the phase should be activated.
        Throw SkipPhase to skip this phase.
        """

    def pre(self) -> None:
        """Called before the changes are applied to UCR."""

    def post(self) -> None:
        """Called after the changes have been applied to UCR."""

    def call(self, command: Sequence[str]) -> int:
        """Call external command using subprocess.call(shell=False)."""
        self.logger.debug("Running %r", command)
        if self.changeset.no_act:
            ret = 0
        else:
            ret = subprocess.call(command)
            self.logger.debug("%r returned %d", command, ret)
        return ret
