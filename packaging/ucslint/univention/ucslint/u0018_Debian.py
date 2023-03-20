# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright (C) 2016-2023 Univention GmbH
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

"""Find maintainer scripts using wrong header."""

from __future__ import annotations

import re
from itertools import cycle
from pathlib import Path
from shlex import split
from typing import Iterable, Iterator, Set

from debian.changelog import Changelog, ChangelogParseError  # Version

import univention.ucslint.base as uub
from univention.ucslint.common import RE_DEBIAN_PACKAGE_VERSION


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

    # https://www.debian.org/doc/debian-policy/ch-maintainerscripts.html#summary-of-ways-maintainer-scripts-are-called
    # https://wiki.debian.org/DpkgTriggers
    ACTIONS = {
        'preinst': {'install', 'upgrade', 'abort-upgrade'},
        'postinst': {'configure', 'abort-upgrade', 'abort-remove', 'abort-deconfigure', 'triggered'},
        'prerm': {'remove', 'upgrade', 'deconfigure', 'failed-upgrade'},
        'postrm': {'remove', 'purge', 'upgrade', 'disappear', 'failed-upgrade', 'abort-install', 'abort-upgrade'},
    }
    SCRIPTS = frozenset(ACTIONS)

    def getMsgIds(self) -> uub.MsgIds:
        return {
            '0018-1': (uub.RESULT_STYLE, 'wrong script name in comment'),
            '0018-2': (uub.RESULT_STYLE, 'Unneeded entry in debian/dirs; the directory is implicitly created by another debhelper'),
            '0018-3': (uub.RESULT_WARN, 'Invalid action in Debian maintainer script'),
            '0018-4': (uub.RESULT_WARN, 'Use debian/*.pyinstall to install Python modules'),
            '0018-5': (uub.RESULT_INFO, 'Maintainer script contains old upgrade code'),
        }

    def check(self, path: Path) -> None:
        super().check(path)
        debianpath = path / 'debian'
        self.check_scripts(uub.FilteredDirWalkGenerator(debianpath, suffixes=self.SCRIPTS))
        self.check_dirs(uub.FilteredDirWalkGenerator(debianpath, suffixes=['install', 'pyinstall', 'dirs']))

    def check_files(self, paths: Iterable[Path]) -> None:
        paths = list(paths)
        self.check_scripts(paths)
        self.check_dirs(paths)

    def get_debian_version(self, path: Path) -> Version:
        try:
            fn_changelog = path / 'debian' / 'changelog'
            with fn_changelog.open() as fd:
                changelog = Changelog(fd)
        except (OSError, ChangelogParseError) as ex:
            self.debug(f'Failed open {fn_changelog!r}: {ex}')
            return Version('0')
        else:
            return Version(changelog.version.full_version)

    def check_scripts(self, paths: Iterable[Path]) -> None:
        version = self.get_debian_version(self.path)
        for script_path in paths:
            if script_path.suffix not in ('.%s' % suf for suf in self.SCRIPTS):
                continue
            package, suffix = self.split_pkg(script_path)

            other_scripts = self.SCRIPTS - {suffix}
            other_actions = {action for actions in self.ACTIONS.values() for action in actions} - self.ACTIONS[suffix]
            self.debug(f'script={suffix}')
            self.debug(f'actions={" ".join(sorted(self.ACTIONS[suffix]))}')
            self.debug(f'other_script={" ".join(sorted(other_scripts))}')
            self.debug(f'other_actions={" ".join(sorted(other_actions))}')

            content = script_path.read_text()

            for row, line in enumerate(content.splitlines(), start=1):
                if not line.startswith('#'):
                    break
                for script_name in other_scripts:
                    if script_name in line:
                        self.addmsg(
                            '0018-1',
                            f'wrong script name: {line.strip()!r}',
                            script_path, row, line=line)

            for row, line in enumerate(content.splitlines(), start=1):
                if line.startswith('#'):
                    continue
                for match in self.RE_TEST.finditer(line):
                    try:
                        actions = self.parse_test(split(match['cond'])) & other_actions
                    except ValueError as ex:
                        self.debug(f'Failed {script_path}:{row}: {ex} in {line}')
                        continue
                    if actions:
                        self.addmsg(
                            '0018-3',
                            f'Invalid actions "{",".join(actions)}" in Debian maintainer script',
                            script_path, row, line=line)

                for match in self.RE_COMPARE_VERSIONS.finditer(line):
                    ver_a, op, ver_b = match.groups()
                    for arg in (ver_a, ver_b):
                        if self.RE_ARG2.match(arg):
                            continue
                        unquoted = arg[1:-1] if arg[0] == arg[-1] in {"'", '"'} else arg
                        if not RE_DEBIAN_PACKAGE_VERSION.match(unquoted):
                            self.debug(f'{script_path}:{row}: Unknown argument {arg!r}')
                            continue

                        ver = Version(unquoted)
                        self.debug(f"{ver} << {version}?")
                        if ver.numeric and version.numeric and ver.numeric[0] < version.numeric[0] - 1:
                            self.addmsg(
                                '0018-5',
                                f'Maintainer script contains old upgrade code for {ver} << {version}',
                                script_path, row, match.start(0), line)

            for row, col, match in uub.line_regexp(content, self.RE_CASE):
                for cases in match['cases'].split(';;'):
                    cases = cases.lstrip('\t\n\r (')
                    cases = cases.split(')', 1)[0]
                    actions = {action for case in cases.split('|') for action in split(case)} & other_actions
                    if actions:
                        self.addmsg(
                            '0018-3',
                            f'Invalid actions "{",".join(actions)}" in Debian maintainer script',
                            script_path, row, col, line=line)

    @classmethod
    def parse_test(cls, tokens: list[str]) -> set[str]:
        """
        Parse test string and return action names

        :param tokens: `test` string tokens.
        :returns: Set containing the action names

        >>> UniventionPackageCheck.parse_test(['$1', '=', 'upgrade'])
        {'upgrade'}
        >>> UniventionPackageCheck.parse_test(['upgrade', '!=', '${1}'])
        {'upgrade'}
        >>> UniventionPackageCheck.parse_test(['(', '-n', '$1', ')'])
        set()
        >>> UniventionPackageCheck.parse_test(['-n', '$1'])
        set()
        >>> UniventionPackageCheck.parse_test(['-n', '$1', '-a', '-z', '$1'])
        set()
        >>> UniventionPackageCheck.parse_test(['1', '-le', '2'])
        set()
        >>> UniventionPackageCheck.parse_test(['$1'])
        set()
        """
        COND = {'-a', '-o'}
        UNARY = {'-b', '-c', '-d', '-e', '-f', '-g', '-G', '-h', '-k', '-L', '-n', '-O', '-p', '-r', '-s', '-S', '-t', '-u', '-w', '-x', '-z'}
        COMP1 = {'-ot', '-nt', '-ef', '-ne', '-lt', '-le', '-gt', '-ge', '-eq'}
        COMP2 = {'=', '!=', '==', '=~'}
        result = set()
        while tokens:
            t = tokens.pop(0)
            if t == ')':
                break
            if t == '(':
                result |= cls.parse_test(tokens)
            elif t == '!':
                pass
            elif t in COND:
                pass
            elif t in UNARY:
                tokens.pop(0)
            elif t.startswith('-'):
                raise ValueError(t)
            elif tokens:
                op = tokens.pop(0)
                if op in COMP1 | COMP2:
                    arg = tokens.pop(0)
                    if op in COMP2:
                        if cls.RE_ARG1.match(t):
                            result.add(arg)
                        elif cls.RE_ARG1.match(arg):
                            result.add(t)
                elif op in COND:
                    pass  # [-n] t
                else:
                    raise ValueError(op)
            else:
                pass  # [-n] t

        return result

    def check_dirs(self, paths: Iterable[Path]) -> None:
        paths = list(paths)
        dirs: dict[str, Dirs] = {}

        for fp in paths:
            if fp.suffix != '.install':
                continue
            package, suffix = self.split_pkg(fp)
            pkg = dirs.setdefault(package, Dirs(package))
            # ~/doc/2018-04-11-ApiDoc/pymerge
            for row, line in self.lines(fp):
                dst = Path()
                for src, dst in self.process_install(fp, line):
                    self.debug(f'{fp}:{row} Installs {src} to {dst}')
                    pkg.add(dst)

                if self.RE_PYTHONPATHS.match(dst.as_posix()):
                    self.addmsg(
                        '0018-4',
                        'Use debian/*.pyinstall to install Python modules',
                        fp, row)

        for fp in paths:
            if fp.suffix != '.pyinstall':
                continue
            package, suffix = self.split_pkg(fp)
            pkg = dirs.setdefault(package, Dirs(package))
            for row, line in self.lines(fp):
                for src, dst in self.process_pyinstall(fp, line):
                    self.debug(f'{fp}:{row} Installs {src} to {dst}')
                    pkg.add(dst)

        for fp in paths:
            if fp.suffix != '.dirs':
                continue
            package, suffix = self.split_pkg(fp)
            pkg = dirs.setdefault(package, Dirs(package))
            for row, line in self.lines(fp):
                path = Path(line.strip('/'))
                if path in pkg:
                    self.addmsg('0018-2', f'Unneeded directory {line!r}', fp, row)

    @staticmethod
    def lines(path: Path) -> Iterator[tuple[int, str]]:
        with path.open() as stream:
            for row, line in enumerate(stream, start=1):
                line = line.strip()
                if not line:
                    continue
                if line.startswith('#'):
                    continue
                yield (row, line)

    @staticmethod
    def split_pkg(path: Path) -> tuple[str, str]:
        package, _, suffix = path.name.rpartition(".")
        return (package, suffix)

    @staticmethod
    def process_install(path: Path, line: str, *, _glob: Iterable[Path] = ()) -> Iterator[tuple[Path, Path]]:
        """
        Parse :file:`debian/*.install` lines.

        >>> list(UniventionPackageCheck.process_install(Path(), "usr"))
        [(PosixPath('usr'), PosixPath('usr'))]
        >>> list(UniventionPackageCheck.process_install(Path(), "usr    prefix/"))
        [(PosixPath('usr'), PosixPath('prefix/usr'))]
        >>> list(UniventionPackageCheck.process_install(Path(), "src/*.py", _glob=[Path('src/__init__.py')]))
        [(PosixPath('src/__init__.py'), PosixPath('src/__init__.py'))]
        >>> list(UniventionPackageCheck.process_install(Path(), "src/*.py    prefix/", _glob=[Path('src/__init__.py')]))
        [(PosixPath('src/__init__.py'), PosixPath('prefix/__init__.py'))]
        """
        args = [_.strip('/') for _ in line.split()]
        dst = Path(args.pop()) if len(args) >= 2 else Path(args[0]).parent

        for src in args:
            for fn in (_glob or path.glob(src)) if ('*' in src or '?' in src or '[' in src) else [path / src]:
                if fn.is_dir():
                    for src_path in fn.glob("**/*"):
                        yield (src_path, dst / src_path.relative_to(fn))
                else:
                    yield (fn, dst / fn.name)

    @classmethod
    def process_pyinstall(cls, path: Path, line: str, *, _glob: Iterable[Path] = ()) -> Iterator[tuple[Path, Path]]:
        """
        Parse :file:`debian/*.pyinstall` lines.

        >>> list(UniventionPackageCheck.process_pyinstall(Path(), "foo.py"))
        [(PosixPath('foo.py'), PosixPath('foo.py'))]
        >>> list(UniventionPackageCheck.process_pyinstall(Path(), "*.py", _glob=[Path('foo.py')]))
        [(PosixPath('foo.py'), PosixPath('foo.py'))]
        >>> list(UniventionPackageCheck.process_pyinstall(Path(), "foo/bar.py 2.6-"))
        [(PosixPath('foo/bar.py'), PosixPath('foo/bar.py'))]
        >>> list(UniventionPackageCheck.process_pyinstall(Path(), "foo/bar.py spam"))
        [(PosixPath('foo/bar.py'), PosixPath('spam/bar.py'))]
        >>> list(UniventionPackageCheck.process_pyinstall(Path(), "foo/bar.py spam.egg 2.5"))
        [(PosixPath('foo/bar.py'), PosixPath('spam/egg/bar.py'))]
        """
        args = line.split()
        src = args.pop(0)
        if args and cls.RE_VERSION_RANGE.match(args[-1]):
            args.pop(-1)
        dst = path / args.pop(0).replace('.', '/') if args and cls.RE_NAMESPACE.match(args[0]) else Path(src).parent
        assert not args, args

        for fn in (_glob or path.glob(src)) if ('*' in src or '?' in src or '[' in src) else [path / src]:
            yield (fn, dst / fn.name)

    RE_TEST = re.compile(
        r'''
        (?:(?P<test>\[{1,2}) | \b test)
        \s+
        (?P<cond>.+?)
        (?(test)\s+\]{1,2} | (?:\s*(?:; | && | \|\| | $)))
        ''', re.VERBOSE)
    RE_CASE = re.compile(
        r'''
        \b
        case
        \s+
        (?P<quot>"?)
        (?:\$(?:1|\{1[#%:?+=/-[^}]*\}))
        (?P=quot)
        \s+
        in
        \s+
        (?P<cases>.+?)
        \b
        esac
        \b
        ''', re.VERBOSE | re.DOTALL)
    RE_ARG1 = re.compile(r'\$(?:1|\{1[#%:?+=/-[^}]*\})')
    # /usr/share/dh-python/dhpython/version.py # VERSION_RE
    RE_VERSION_RANGE = re.compile(
        r'''^
        \d+\.\d+
        (?:- (?:\d+\.\d+)? )?
        (?:,
           \d+\.\d+
           (?:- (?:\d+\.\d+)? )?
        )*
        $''', re.VERBOSE)
    # /usr/share/dh-python/dhpython/tools.py # INSTALL_RE
    RE_NAMESPACE = re.compile(
        r'''^
        (?![0-9])\w+
        (?:\. (?![0-9])\w+ )*
        $''', re.VERBOSE)
    RE_PYTHONPATHS = re.compile(
        r'''^/?
        (?:usr/lib/pymodules/python[0-9.]+/
          |usr/lib/python[0-9.]+/
          |usr/share/pyshared/
        )''', re.VERBOSE)
    RE_COMPARE_VERSIONS = re.compile(
        r'''
        \b dpkg \s+ --compare-versions
        \s+
        ( (?: '[^']*' | "[^"]*" | \S )+ )
        \s+
        ([lg][et](?:-nl)?|eq|ne|<[<=]?|=|>[>=]?)
        \s+
        ( (?: '[^']*' | "[^"]*" | \S )+ )
        \s*(?: $ | ; | && | \|\| | \))
        ''', re.VERBOSE)
    RE_ARG2 = re.compile(r'^("?)\$(?:2|\{2[#%:?+=/-[^}]*\})(\1)$')


class Dirs(Set[Path]):
    """Set of directories."""

    DIRS = frozenset({
        Path('bin'),
        Path('etc'),
        Path('etc/cron.d'),
        Path('etc/cron.hourly'),
        Path('etc/cron.daily'),
        Path('etc/cron.weekly'),
        Path('etc/cron.monthly'),
        Path('etc/default'),
        Path('etc/init.d'),
        Path('lib'),
        Path('lib/security'),
        Path('sbin'),
        Path('usr'),
        Path('usr/bin'),
        Path('usr/lib'),
        Path('usr/sbin'),
        Path('var'),
        Path('var/lib'),
        Path('var/log'),
        Path('var/www'),
    })

    def __init__(self, package: str) -> None:
        set.__init__(self, {Path(f'usr/share/doc/{package}')} | self.DIRS)

    def add(self, dst: Path) -> None:
        self |= set(dst.parents)


class Version:
    """
    Version as a sqeunce of numeric and non-numeric parts.

    >>> str(Version('1'))
    '1'
    >>> str(Version('first'))
    'first'
    >>> str(Version("1:2.34alpha~5-6.7"))
    '1:2.34alpha~5-6.7'
    """

    __slots__ = ('text', 'numeric')

    RE_VERSION = re.compile(r'([0-9]+)')

    def __init__(self, text: str) -> None:
        parts = self.RE_VERSION.split(text)
        self.text = parts[::2]
        self.numeric = [int(number) for number in parts[1::2]]

    def __iter__(self) -> Iterator[str | int]:
        try:
            for next in cycle(iter(part).__next__ for part in (self.text, self.numeric)):  # type: ignore
                yield next()
        except StopIteration:
            pass

    def __str__(self) -> str:
        return ''.join(str(part) for part in self)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.__str__()!r})'
