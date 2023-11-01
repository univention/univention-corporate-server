# SPDX-FileCopyrightText: 2014-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/

from abc import ABCMeta
from argparse import Namespace
from pathlib import Path

from ..files.raw import Raw


LICENSE = """The complete source code of Univention Corporate Server is provided
under GNU Affero General Public License (AGPL). This image contains a license key
of the UCS Core Edition. More details can be found here:
\x20
https://www.univention.com/downloads/license-models/licensing-conditions-ucs-core-edition/"""

ANNOTATION = """Univention Corporate Server (UCS) is a complete solution to provide standard
IT services (like domain management or file services for Microsoft Windows
clients) in the cloud and to integrate them with additional systems like
groupware, CRM or ECM.
\x20
Univention Corporate Server (UCS) is a reliable, pre-configured Linux server
operating system featuring:
\x20
* Active Directory like domain services compatible with Microsoft Active
Directory
\x20
* A mature and easy-to-use web-based management system for user, rights and
infrastructure management
\x20
* A scalable underlying concept suited for single server scenarios as well as
to run and manage thousands of clients and servers for thousands of users
within one single UCS domain
\x20
* An app center, providing single-click installation and integration of many
business applications from 3rd parties and Univention
\x20
* Management capabilities to manage Linux- and UNIX-based clients
\x20
* Command line, scripting interfaces and APIs for automatization and extension
\x20
Thus, Univention Corporate Server is the best fit to provide Microsoft Server
like services in the cloud or on-premises, to run and operate corporate IT
environments with Windows- and Linux-based clients and to extend those
environments with proven enterprise software, also either in the cloud or
on-premises."""


class Target(metaclass=ABCMeta):
    """represents the process for creating a complete image for a platform"""

    default = True

    def __init__(self, options: Namespace) -> None:
        self.options = options

    def __str__(self) -> str:
        return self.__doc__ or self.__class__.__name__

    @property
    def machine_name(self):
        machine_name = self.options.product
        if self.options.version is not None:
            machine_name += ' ' + self.options.version
        return machine_name

    def create(self, image: Raw) -> None:
        raise NotImplementedError()


class TargetFile(Target, metaclass=ABCMeta):
    """Target generating an output file."""

    SUFFIX = ""

    def archive_name(self) -> Path:
        path = self.options.filename  # type: Path
        if not self.options.no_target_specific_filename:
            path = path.with_name("%s-%s" % (path.name, self.SUFFIX))

        if path.exists():
            raise OSError('Output file %r exists' % (path,))

        return path
