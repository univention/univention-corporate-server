#!/usr/bin/python3
#
# Copyright 2020-2021 Univention GmbH
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
Prune no longer required Linux kernel packages.
"""

from argparse import ArgumentParser, Namespace
from typing import List, Optional
from os import uname

from apt import Cache

PREFIX = "linux-image-"


def main() -> None:
    opt = parse_args()
    prune(opt)


def parse_args(argv: Optional[List[str]] = None) -> Namespace:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", "-v", action="count", help="Increase verbosity")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Only show what would be done")
    return parser.parse_args(argv)


def prune(opt: Namespace) -> None:
    cache = Cache()

    cur = {PREFIX + uname()[2] + suffix for suffix in {"", "-signed"}}
    top = {
        "univention-kernel-image",
        PREFIX + "amd64",
        PREFIX + "rt-amd64",
        PREFIX + "686-pae",
        PREFIX + "686",
        PREFIX + "rt-686-pae",
    }
    meta = [
        pkg.installed
        for pkg in (cache[pkg] for pkg in top if pkg in cache)
        if pkg.is_installed
    ]
    if opt.verbose:
        print("Installed kernel meta packages:\n %s" % ("\n ".join(sorted(str(pkg) for pkg in meta)),))

    keep = (
        {
            dep.name
            for pkg in meta
            for alt in pkg.dependencies
            for dep in alt
            if dep.name.startswith(PREFIX)
        }
        | cur
        | top
    )
    if opt.verbose:
        print("Exception list for kernel packages:\n %s" % ("\n ".join(sorted(keep)),))

    cache.clear()
    for pkg in cache:
        if pkg.name.startswith(PREFIX) and pkg.is_installed:
            if pkg.name not in keep:
                if opt.verbose:
                    print("Purging kernel package: %s" % (pkg.name,))
                if not opt.dry_run:
                    pkg.mark_delete(purge=True)
            else:
                if opt.verbose:
                    print("Keeping kernel package: %s" % (pkg.name, ))

    cache.commit()


if __name__ == "__main__":
    main()
