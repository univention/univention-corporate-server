#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2020-2022 Univention GmbH
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
Univention Corporate Server localization tool to extract, update, and compile
GNU gettext Portable Objects (PO files) to Message Objects (MO files).
"""

import argparse
import os
import sys

from . import l10n as tlh


def main():  # type: () -> None
    cmd = os.path.basename(sys.argv[0])
    parse_args(cmd)


def main_build():  # type: () -> None
    parse_args("univention-l10n-build")


def main_install():  # type: () -> None
    parse_args("univention-l10n-install")


def parse_args(cmd):  # type: (str) -> None
    parser_common = argparse.ArgumentParser(add_help=False)
    group = parser_common.add_argument_group("debhelper", "Common debhelper options")
    # group.add_argument("--verbose", "-v", action="store_true", help="Verbose mode: show all commands that modify the package build directory.")
    # group.add_argument("--no-act", action="store_true", help="Do not really do anything.")
    group.add_argument("--arch", "-a", action="store_true", help="Act on all architecture dependent packages.")
    group.add_argument("--indep", "-i", action="store_true", help="Act on all architecture independent packages.")
    # group.add_argument("--package", "-p", metavar="package", action="append", help="Act on the package named 'package'.")
    # group.add_argument("--same-arch", "-s", acction="store_true", help="Act on all architecture dependent packages having the same architecture.")
    # group.add_argument("--no-package", "-N", metavar="package", action="append", help="Do not act on the specified package.")
    # group.add_argument("--ignore", metavar="file", action="append", help="Ignore the specified file.")
    # group.add_argument("--tmpdir", "-P", metavar="tmpdir", help="Use 'tmpdir' for package build directory.")
    # group.add_argument("--mainpackage", metavar="package", help="Changes the package which debhelper considers the 'main package',")
    # group.add_argument("--mainpackage", metavar="package", help="Changes the package which debhelper considers the 'main package',")
    group.add_argument("--option", "-O", action="append", help="Additional debhelper options.")

    parser = argparse.ArgumentParser(description=__doc__, prog="univention-l10n", formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(help="sub-command help", dest="subcmd")  # required=True

    parser_build = subparsers.add_parser("build", description=build.__doc__, prog="univention-l10n-build", parents=[parser_common], formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_build.add_argument("--pot", "-t", action="store_true", help="Keep template file")
    parser_build.add_argument("language_code", default="de", nargs="?", help="ISO language code.")
    parser_build.set_defaults(func=build)

    parser_install = subparsers.add_parser("install", description=install.__doc__, prog="univention-l10n-install", parents=[parser_common], formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_install.add_argument("language_code", default="de", nargs="?", help="ISO language code.")
    parser_install.set_defaults(func=install)

    parsers = {
        "univention-l10n-build": parser_build,
        "univention-l10n-install": parser_install,
        "univention-l10n": parser,
    }
    parser = parsers.get(cmd, parser)
    args = parser.parse_args()
    args.func(args)


def build(args):  # type: (argparse.Namespace) -> None
    """
    Generate GNU gettext Portable Objects (PO files) from debian/\\*.univention-l10n files

    This script reads :file:`debian/*.univention-l10n` files inside the current working
    directory and creates gettext Portable Objects defined within. It intends to
    facilitate and homogenize the translation build process.

    Add it to the build target inside :file:`debian/rules` to build the POs for a certain
    language or use it manually inside source packages to update the translation
    catalog.

    Example :file:`debian/rules` override::

        %:
            dh --with univention-l10n

    or alternatively::

        override_dh_auto_build:
            univention-l10n-build fr
            dh_auto_build
    """
    cwd = os.getcwd()

    for scase in tlh.get_special_cases_from_srcpkg(cwd, args.language_code):
        pot_path = scase.create_po_template()
        if os.path.isfile(scase.new_po_path):
            tlh.message_catalogs.merge_po(pot_path, scase.new_po_path)
        else:
            os.link(pot_path, scase.new_po_path)

        if not args.pot:
            os.unlink(pot_path)

        tlh.message_catalogs.univention_location_lines(scase.new_po_path, scase.package_dir)

    for module_attrs in tlh.find_base_translation_modules(cwd):
        module = tlh.UMCModuleTranslation.from_source_package(module_attrs, args.language_code)
        tlh.update_package_translation_files(module, cwd, args.pot)


def install(args):  # type: (argparse.Namespace) -> None
    """
    Generate and install GNU gettext Message Objects (MO files) from debian/\\*.univention-l10n files.

    This script reads :file:`debian/*univention-l10n` files inside the current working
    directory. It builds the message catalogs and installs them to the path defined
    within.

    The intended usage is to add it to the install target inside :file:`debian/rules` to
    automate in-package translations.

    Example file: `debian/rules` override::

        %:
            dh --with univention-l10n

    or alternatively::

        override_dh_auto_install:
            univention-l10n-install fr
            dh_auto_install
    """
    for scase in tlh.get_special_cases_from_srcpkg(os.getcwd(), args.language_code):
        for source_file_set in scase.get_source_file_sets():
            source_file_set.process_target(scase.new_po_path, scase.destination)


if __name__ == "__main__":
    main()
