#!/usr/bin/env python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2008-2024 Univention GmbH
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
Univention ucslint
Check UCS packages for policy compliance.
"""

from __future__ import annotations

import re
import sys
from argparse import ArgumentParser, FileType, Namespace
from errno import ENOENT
from fnmatch import fnmatch
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import IO, Container, Dict

import univention.ucslint.base as uub


try:
    from junit_xml import TestSuite  # type: ignore
except ImportError:
    pass


RE_OVERRIDE = re.compile(
    r'''^
    (?P<module> \d+-[BEFNW]?\d+)
    (?: [:]
        (?: \s* (?P<pattern> .+?) \s*
            (?: [:] \s* (?P<linenumber> \d+)
            )?
        )?
    )?
    $''', re.VERBOSE)


Plugins = Dict[str, ModuleType]


def load_plugins(opt: Namespace) -> Plugins:
    """
    Load policy checker plugins.

    :param opt: Command line arguments.
    :returns: Mapping of plugin ID to loaded module.
    """
    plugins: Plugins = {}

    plugindirs = [path.resolve() for path in (opt.plugindir or [Path('~/.ucslint').expanduser(), Path(uub.__file__).parent])]
    enabled = [clean_modid(x) for mod in opt.enabled_modules for x in mod.split(',')]
    disabled = [clean_modid(x) for mod in opt.disabled_modules for x in mod.split(',')]

    for plugindir in plugindirs:
        if not plugindir.is_dir():
            if opt.debug:
                print(f'WARNING: plugindir {plugindir} does not exist', file=sys.stderr)
        else:
            for fn in plugindir.glob("[0-9][0-9][0-9][0-9]*.py"):
                code = fn.stem[0:4]
                if code in disabled:
                    if opt.debug:
                        print(f'Module {fn.stem} is disabled', file=sys.stderr)
                elif enabled and code not in enabled:
                    if opt.debug:
                        print(f'Module {fn.stem} is not enabled', file=sys.stderr)
                else:
                    modname = fn.stem
                    try:
                        spec = spec_from_file_location(fn.stem[:-3], fn)
                        assert spec is not None
                        module = module_from_spec(spec)
                        assert spec.loader
                        spec.loader.exec_module(module)  # type: ignore
                        plugins[modname] = module
                    except Exception as exc:
                        print(f'ERROR: Loading module {fn} failed: {exc}', file=sys.stderr)
                        if opt.debug:
                            raise

    return plugins


class DebianPackageCheck:
    """
    Check Debian package for policy compliance.

    :param path: Base directory of Debian package to check.
    :param plugins: Mapping of loaded plugins.
    :param debuglevel: Vebosity level.
    """

    def __init__(self, path: Path, plugins: Plugins, debuglevel: int = 0):
        self.path = path
        self.pluginlist = plugins
        self.debuglevel = debuglevel
        self.msglist: list[uub.UPCMessage] = []
        self.msgidlist: dict[str, tuple[int, str]] = {}
        self.overrides: set[tuple[str, str | None, int | None]] = set()

    def check(self) -> None:
        """Run plugin on files in path."""
        for plugin in self.pluginlist.values():
            obj = plugin.UniventionPackageCheck()  # type: ignore
            self.msgidlist.update(obj.getMsgIds())
            obj.setdebug(self.debuglevel)
            obj.postinit(self.path)
            try:
                obj.check(self.path)
            except uub.UCSLintException as ex:
                print(ex, file=sys.stderr)
            self.msglist.extend(obj.result())

    def check_files(self, files) -> None:
        """Run plugin on given files."""
        for plugin in self.pluginlist.values():
            obj = plugin.UniventionPackageCheck()  # type: ignore
            obj.path = self.path
            self.msgidlist.update(obj.getMsgIds())
            obj.setdebug(self.debuglevel)
            obj.postinit(self.path)
            try:
                obj.check_files(files)
            except uub.UCSLintException as ex:
                print(ex, file=sys.stderr)
            self.msglist.extend(obj.result())

    def loadOverrides(self) -> None:
        """Parse :file:`debian/ucslint.overrides` file."""
        self.overrides = set()
        fn = self.path / 'debian' / 'ucslint.overrides'
        try:
            with fn.open() as overrides:
                for row, line in enumerate(overrides, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith('#'):
                        continue
                    result = RE_OVERRIDE.match(line)
                    if not result:
                        print(f'IGNORED: debian/ucslint.overrides:{row}: {line}', file=sys.stderr)
                        continue

                    module, pattern, linenumber = result.groups()
                    override = (module, pattern, int(linenumber) if pattern and linenumber else None)
                    self.overrides.add(override)
        except OSError as ex:
            if ex.errno != ENOENT:
                print(f'WARNING: load debian/ucslint.overrides: {ex}', file=sys.stderr)

    def in_overrides(self, msg: uub.UPCMessage) -> bool:
        """
        Check message against overrides.

        :param msg: Message to check.
        :returns: `True` when the check should be ignored, `False` otherwise.
        """
        filepath = msg.filename.relative_to(self.path) if msg.filename else Path("")
        for (modulename, pattern, linenumber) in self.overrides:
            if modulename != msg.getId():
                continue
            if pattern and not fnmatch(filepath.as_posix(), pattern):
                continue
            if linenumber is not None and linenumber != msg.row:
                continue
            return True
        return False

    def printResult(self, ignore_IDs: Container[str], display_only_IDs: Container[str], display_only_categories: str, exitcode_categories: str, junit: IO[str] | None = None) -> tuple[int, int]:
        """
        Print result of checks.

        :param ignore_IDs: List of message identifiers to ignore.
        :param display_only_IDs: List of message identifiers to display.
        :param display_only_categories: List of message categories to display.
        :param exitcode_categories: List of message categories to signal as fatal.
        :param junit: Generate JUnit XML output to given file.
        :returns: 2-tuple (incident-count, exitcode-count)
        """
        incident_cnt = 0
        exitcode_cnt = 0

        self.loadOverrides()
        test_cases: list[uub.TestCase] = []

        for msg in self.msglist:
            tc = msg.junit()
            test_cases.append(tc)

            if msg.getId() in ignore_IDs:
                tc.add_skipped_info('ignored')
                continue
            if display_only_IDs and msg.getId() not in display_only_IDs:
                tc.add_skipped_info('hidden')
                continue
            if self.in_overrides(msg):
                # ignore msg if mentioned in overrides files
                tc.add_skipped_info('overridden')
                continue

            msgid = msg.getId()
            try:
                lvl, _msgstr = self.msgidlist[msgid]
                category = uub.RESULT_INT2STR[lvl]
            except LookupError:
                category = 'FIXME'

            if category in display_only_categories or display_only_categories == '':
                print(f'{category}:{msg}')
                incident_cnt += 1

            if category in exitcode_categories or exitcode_categories == '':
                exitcode_cnt += 1

        if junit:
            ts = TestSuite("ucslint", test_cases)
            TestSuite.to_file(junit, [ts], prettyprint=False)

        return incident_cnt, exitcode_cnt


def clean_id(idstr: str) -> str:
    """
    Format message ID string.

    :param idstr: message identifier.
    :returns: formatted message identifier.

    >>> clean_id('1-2')
    '0001-2'
    """
    if '-' not in idstr:
        raise ValueError(f'no valid id ({idstr}) - missing dash')
    modid, msgid = idstr.strip().split('-', 1)
    return f'{clean_modid(modid)}-{clean_msgid(msgid)}'


def clean_modid(modid: str) -> str:
    """
    Format module ID string.

    :param modid: module number.
    :returns: formatted module number.

    >>> clean_modid('1')
    '0001'
    """
    if not modid.isdigit():
        raise ValueError(f'modid contains invalid characters: {modid}')
    return f'{int(modid):04d}'


def clean_msgid(msgid: str) -> str:
    """
    Format message ID string.

    :param msgid: message number.
    :returns: formatted message number.

    >>> clean_msgid('01')
    '1'
    """
    if not msgid.isdigit():
        raise ValueError(f'msgid contains invalid characters: {msgid}')
    return f'{int(msgid):d}'


def parse_args(parser: ArgumentParser) -> Namespace:
    """
    Parse command line arguments.

    :returns: parsed options.
    """
    parser.add_argument(
        '--debug',
        '-d',
        default=0,
        type=int,
        help='if set, debugging is activated and set to the specified level',
        metavar='LEVEL',
    )
    parser.add_argument(
        '--modules',
        '-m',
        action='append',
        default=[],
        help='list of modules to be loaded (e.g. -m 0009,27)',
        dest='enabled_modules',
    )
    parser.add_argument(
        '--exclude-modules',
        '-x',
        action='append',
        default=[],
        help='list of modules to be disabled (e.g. -x 9,027)',
        metavar='MODULES',
        dest='disabled_modules',
    )
    parser.add_argument(
        '--display-only',
        '-o',
        action='append',
        default=[],
        help='list of IDs to be displayed (e.g. -o 9-1,0027-12)',
        metavar='MODULES',
        dest='display_only_IDs',
    )
    parser.add_argument(
        '--ignore',
        '-i',
        action='append',
        default=[],
        help='list of IDs to be ignored (e.g. -i 0003-4,19-27)',
        metavar='MODULES',
        dest='ignore_IDs',
    )
    parser.add_argument(
        '--skip-univention',
        '-U',
        action='append_const',
        const='0007-2,0010-2,0010-3,0010-4,0011-3,0011-4,0011-5,0011-13',
        help='Ignore Univention specific tests',
        dest='ignore_IDs',
    )
    parser.add_argument(
        '--plugindir',
        '-p',
        action='append',
        default=[],
        type=Path,
        help='override plugin directory with <plugindir>',
        metavar='DIRECTORY',
    )
    parser.add_argument(
        '--display-categories',
        '-c',
        default='',
        help='categories to be displayed (e.g. -c EWIS)',
        metavar='CATEGORIES',
        dest='display_only_categories',
    )
    parser.add_argument(
        '--exitcode-categories',
        '-e',
        default='E',
        help='categories that cause an exitcode != 0 (e.g. -e EWIS)',
        metavar='CATEGORIES',
    )
    parser.add_argument(
        '--junit-xml',
        '-j',
        type=FileType('w'),
        help='generate JUnit-XML output',
        metavar='FILE',
    )

    args = parser.parse_args()

    if args.junit_xml and not uub.JUNIT:
        parser.error("Missing Python support for JUNIT_XML")

    if args.debug:
        print(f'Using univention.ucslint.base from {uub.__file__}')

    return args


def debian_dir(pkgpath: str) -> Path:
    """
    Check if given path is base for a Debian package.

    :param pkgpath: base path.
    :returns: same path.
    """
    p = Path(pkgpath)
    if not p.is_dir():
        raise ValueError(f"{pkgpath!r} is no directory!")

    debdir = p / 'debian'
    if not debdir.is_dir():
        raise ValueError(f"{debdir!r} does not exist or is not a directory!")

    return p


def run() -> None:
    """Run a single given check on selected files."""
    parser = ArgumentParser()
    parser.add_argument(
        'files',
        nargs='*',
        help='The files which are suitable for the selected module.',
    )
    options = parse_args(parser)

    plugins = load_plugins(options)

    ignore_IDs = [clean_id(x) for ign in options.ignore_IDs for x in ign.split(',')]
    display_only_IDs = [clean_id(x) for dsp in options.display_only_IDs for x in dsp.split(',')]

    def group_by_package(files):
        """group files by traversing the filesystem up until a debian directory is found"""
        packages = {}
        for filename in files:
            parent_dir = Path(filename).absolute().parent
            while not (parent_dir / 'debian').is_dir():
                parent_dir = parent_dir.parent
                if parent_dir == Path('/'):
                    break
            packages.setdefault(parent_dir.relative_to(Path('.').absolute()), []).append(Path(filename).absolute().relative_to(Path('.').absolute()))
        return packages.items()

    fail = False
    for base, files in group_by_package(options.files):
        chk = DebianPackageCheck(base, plugins, debuglevel=options.debug)
        try:
            chk.check_files(files)
        except uub.UCSLintException as ex:
            print(ex, file=sys.stderr)

        _incident_cnt, exitcode_cnt = chk.printResult(ignore_IDs, display_only_IDs, options.display_only_categories, options.exitcode_categories, options.junit_xml)
        fail |= bool(exitcode_cnt)

    if fail:
        sys.exit(2)


def main() -> None:
    """Run checks."""
    parser = ArgumentParser()
    parser.add_argument(
        'pkgpath',
        nargs='*',
        type=debian_dir,
        default=[Path(".")],
        help='Source package directory',
    )
    options = parse_args(parser)

    plugins = load_plugins(options)

    ignore_IDs = [clean_id(x) for ign in options.ignore_IDs for x in ign.split(',')]
    display_only_IDs = [clean_id(x) for dsp in options.display_only_IDs for x in dsp.split(',')]

    fail = False
    for pkgpath in options.pkgpath:
        chk = DebianPackageCheck(pkgpath, plugins, debuglevel=options.debug)
        try:
            chk.check()
        except uub.UCSLintException as ex:
            print(ex, file=sys.stderr)

        _incident_cnt, exitcode_cnt = chk.printResult(ignore_IDs, display_only_IDs, options.display_only_categories, options.exitcode_categories, options.junit_xml)
        fail |= bool(exitcode_cnt)

    if fail:
        sys.exit(2)


if __name__ == '__main__':
    main()
