# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""
APT package sources in the DEB822 format, see :manpage:`sources.list(5)`.

UCS writes its package sources as :file:`*.sources` files to :file:`/etc/apt/sources.list.d/`.
The one-line format is still used for :file:`/etc/apt/mirror.list`, because :program:`apt-mirror` doesn't support DEB822.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from dataclasses import dataclass
from typing import IO, TYPE_CHECKING

from debian.deb822 import Deb822


if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

SOURCES_DIR = '/etc/apt/sources.list.d'
FN_APTSOURCES_VERSION = os.path.join(SOURCES_DIR, '15_ucs-online-version.sources')
FN_APTSOURCES_COMPONENT = os.path.join(SOURCES_DIR, '20_ucs-online-component.sources')
FN_SOURCES_LIST = '/etc/apt/sources.list'
FN_MOVED_FROM_MAIN = os.path.join(SOURCES_DIR, 'moved-from-main.sources')

# one-line option -> DEB822 field, see sources.list(5)
OPTIONS = {
    'arch': 'Architectures',
    'lang': 'Languages',
    'target': 'Targets',
    'pdiffs': 'PDiffs',
    'by-hash': 'By-Hash',
    'allow-insecure': 'Allow-Insecure',
    'allow-weak': 'Allow-Weak',
    'allow-downgrade-to-insecure': 'Allow-Downgrade-To-Insecure',
    'trusted': 'Trusted',
    'signed-by': 'Signed-By',
    'check-valid-until': 'Check-Valid-Until',
    'valid-until-min': 'Valid-Until-Min',
    'valid-until-max': 'Valid-Until-Max',
    'check-date': 'Check-Date',
    'date-max-future': 'Date-Max-Future',
    'inrelease-path': 'InRelease-Path',
    'snapshot': 'Snapshot',
}
# options with a comma separated list in the one-line format and a space separated list in DEB822
LIST_OPTIONS = {'arch', 'lang', 'target', 'signed-by'}
FIELDS = ('Types', 'URIs', 'Suites', 'Components')

RE_LINE = re.compile(r'^\s*(?P<type>deb|deb-src)\s+(?:\[(?P<options>[^\]]*)\]\s+)?(?P<uri>\S+)\s+(?P<suite>\S+)(?:\s+(?P<components>[^#]*?))?\s*(?:#.*)?$')
RE_OPTION = re.compile(r'^(?P<key>[a-z-]+?)(?P<op>[+-]?)=(?P<value>.*)$')


@dataclass(frozen=True)
class SourcesEntry:
    """
    One stanza of a DEB822 :file:`.sources` file.

    >>> e = SourcesEntry(types=('deb',), uris=('https://updates.software-univention.de/',), suites=('ucs530', 'errata530'), components=('main',))
    >>> print(e)
    Types: deb
    URIs: https://updates.software-univention.de/
    Suites: ucs530 errata530
    Components: main
    >>> list(e.lines())
    ['deb https://updates.software-univention.de/ ucs530 main', 'deb https://updates.software-univention.de/ errata530 main']
    """

    types: tuple[str, ...]
    uris: tuple[str, ...]
    suites: tuple[str, ...]
    components: tuple[str, ...] = ()
    options: tuple[tuple[str, str], ...] = ()

    def deb822(self) -> Deb822:
        """
        Return the stanza as a :py:class:`debian.deb822.Deb822` paragraph.

        An exact path as suite has no components:

        >>> e = SourcesEntry(types=('deb',), uris=('https://updates.software-univention.de/5.3/maintained/component/comp/',), suites=('./',), options=(('Trusted', 'yes'),))
        >>> e.deb822().dump()
        'Types: deb\\nURIs: https://updates.software-univention.de/5.3/maintained/component/comp/\\nSuites: ./\\nTrusted: yes\\n'
        """
        paragraph = Deb822()
        paragraph['Types'] = ' '.join(self.types)
        paragraph['URIs'] = ' '.join(self.uris)
        paragraph['Suites'] = ' '.join(self.suites)
        if self.components:
            paragraph['Components'] = ' '.join(self.components)
        for key, value in self.options:
            paragraph[key] = value
        return paragraph

    def __str__(self) -> str:
        return self.deb822().dump().rstrip('\n')

    def lines(self) -> Iterator[str]:
        """
        Return the stanza in the one-line format.

        >>> e = SourcesEntry(types=('deb', 'deb-src'), uris=('http://h/',), suites=('./',), options=(('Trusted', 'yes'), ('Architectures', 'amd64 i386')))
        >>> list(e.lines())
        ['deb [trusted=yes arch=amd64,i386] http://h/ ./', 'deb-src [trusted=yes arch=amd64,i386] http://h/ ./']
        """
        reverse = {field: option for option, field in OPTIONS.items()}
        opts = []
        for key, value in self.options:
            option = reverse.get(key, key.lower())
            opts.append('%s=%s' % (option, ','.join(value.split()) if option in LIST_OPTIONS else value))
        prefix = '[%s] ' % ' '.join(opts) if opts else ''
        for typ in self.types:
            for uri in self.uris:
                for suite in self.suites:
                    yield ' '.join([typ, prefix + uri, suite, *self.components])

    @classmethod
    def from_deb822(cls, paragraph: Deb822) -> SourcesEntry:
        """
        Create an entry from a parsed DEB822 paragraph.

        >>> SourcesEntry.from_deb822(Deb822({'Types': 'deb', 'URIs': 'http://h/', 'Suites': 'a/all/', 'Trusted': 'yes'}))
        SourcesEntry(types=('deb',), uris=('http://h/',), suites=('a/all/',), components=(), options=(('Trusted', 'yes'),))
        """
        return cls(
            types=tuple(paragraph.get('Types', '').split()),
            uris=tuple(paragraph.get('URIs', '').split()),
            suites=tuple(paragraph.get('Suites', '').split()),
            components=tuple(paragraph.get('Components', '').split()),
            options=tuple((key, value) for key, value in paragraph.items() if key not in FIELDS),
        )

    @classmethod
    def parse_line(cls, line: str) -> SourcesEntry | None:
        """
        Convert a line in the one-line format.

        :param line: A line of a :file:`.list` file.
        :returns: The entry, or `None` for empty lines, comments and entries which can't be expressed in DEB822 like `cdrom:` entries.
        :raises ValueError: for an unknown option.

        >>> SourcesEntry.parse_line('deb https://updates.software-univention.de/ ucs530 main')
        SourcesEntry(types=('deb',), uris=('https://updates.software-univention.de/',), suites=('ucs530',), components=('main',), options=())
        >>> SourcesEntry.parse_line('deb https://updates.software-univention.de/5.3/maintained/component/ comp/amd64/')
        SourcesEntry(types=('deb',), uris=('https://updates.software-univention.de/5.3/maintained/component/',), suites=('comp/amd64/',), components=(), options=())
        >>> SourcesEntry.parse_line('deb-src [ trusted=yes arch=amd64,i386 lang-=de ] http://h/ ./  # comment')
        SourcesEntry(types=('deb-src',), uris=('http://h/',), suites=('./',), components=(), options=(('Trusted', 'yes'), ('Architectures', 'amd64 i386'), ('Languages-Remove', 'de')))
        >>> SourcesEntry.parse_line('# deb http://h/ ./') is None
        True
        >>> SourcesEntry.parse_line('deb cdrom:[UCS 5.3-0 Release amd64]/ ucs530 main') is None
        True
        >>> SourcesEntry.parse_line('deb [foo=bar] http://h/ ./')
        Traceback (most recent call last):
        ...
        ValueError: Unknown option: foo=bar
        """
        match = RE_LINE.match(line)
        if not match or match['uri'].startswith('cdrom:'):
            return None

        options = []
        for option in (match['options'] or '').split():
            opt = RE_OPTION.match(option)
            if not opt or opt['key'] not in OPTIONS:
                raise ValueError('Unknown option: %s' % option)
            key = OPTIONS[opt['key']] + {'+': '-Add', '-': '-Remove', '': ''}[opt['op']]
            value = ' '.join(opt['value'].split(',')) if opt['key'] in LIST_OPTIONS else opt['value']
            options.append((key, value))

        return cls(
            types=(match['type'],),
            uris=(match['uri'],),
            suites=(match['suite'],),
            components=tuple((match['components'] or '').split()),
            options=tuple(options),
        )


def render(entries: Iterable[SourcesEntry]) -> str:
    """
    Render the entries as the content of a DEB822 :file:`.sources` file.

    >>> print(render([SourcesEntry(('deb',), ('http://a/',), ('./',)), SourcesEntry(('deb',), ('http://b/',), ('./',))]), end='')
    Types: deb
    URIs: http://a/
    Suites: ./
    <BLANKLINE>
    Types: deb
    URIs: http://b/
    Suites: ./
    >>> render([])
    ''
    """
    text = '\n\n'.join(str(entry) for entry in entries)
    return text + '\n' if text else ''


def iter_entries(fp: IO[str], enabled_only: bool = True) -> Iterator[SourcesEntry]:
    """
    Parse a DEB822 :file:`.sources` file. Comments are ignored.

    :param fp: The opened file.
    :param enabled_only: Skip entries with `Enabled: no`.

    >>> import io
    >>> text = '# comment\\n\\nTypes: deb\\n# comment\\nURIs: http://h/\\nSuites: ./\\n\\nTypes: deb\\nURIs: http://x/\\nSuites: ./\\nEnabled: no\\n'
    >>> [e.uris for e in iter_entries(io.StringIO(text))]
    [('http://h/',)]
    >>> [e.uris for e in iter_entries(io.StringIO(text), enabled_only=False)]
    [('http://h/',), ('http://x/',)]
    """
    for paragraph in Deb822.iter_paragraphs(fp, use_apt_pkg=False):
        if enabled_only and paragraph.get('Enabled', 'yes').lower() == 'no':
            continue
        yield SourcesEntry.from_deb822(paragraph)


def migrate_sources_list(source: str = FN_SOURCES_LIST, target: str = FN_MOVED_FROM_MAIN, backup: str | None = None) -> int:
    """
    Move the entries from :file:`/etc/apt/sources.list` to a DEB822 :file:`.sources` file.

    Converted lines are commented out in the source file.
    Comments, `cdrom:` entries and lines which can't be converted are kept.

    :param source: The file in the one-line format.
    :param target: The DEB822 file. New entries are appended if the file exists.
    :param backup: The path for a copy of the original source file, written only if entries are converted and the file doesn't exist yet.
    :returns: The number of converted entries.
    """
    try:
        with open(source) as fp:
            lines = fp.readlines()
    except FileNotFoundError:
        return 0

    entries: list[SourcesEntry] = []
    new_lines: list[str] = []
    for line in lines:
        try:
            entry = SourcesEntry.parse_line(line)
        except ValueError as ex:
            print('Not converted: %s (%s)' % (line.strip(), ex), file=sys.stderr)
            entry = None
        if entry is None:
            new_lines.append(line)
            continue
        entries.append(entry)
        new_lines.append('# Moved to %s: %s' % (target, line))

    if not entries:
        return 0

    if backup and not os.path.exists(backup):
        shutil.copy2(source, backup)

    header = '# Moved from %s\n' % (source,)
    with open(target, 'a') as fp:
        if fp.tell():
            fp.write('\n')
        fp.write(header + render(entries))

    with open(source, 'w') as fp:
        fp.writelines(new_lines)

    return len(entries)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--migrate', action='store_true', help='Move the entries of the one-line file to a DEB822 file')
    parser.add_argument('--source', default=FN_SOURCES_LIST, help='The file in the one-line format [%(default)s]')
    parser.add_argument('--target', default=FN_MOVED_FROM_MAIN, help='The DEB822 file [%(default)s]')
    parser.add_argument('--backup', help='Copy of the original source file')
    args = parser.parse_args(argv)

    if args.migrate:
        count = migrate_sources_list(args.source, args.target, args.backup)
        if count:
            print('Moved %d entries from %s to %s' % (count, args.source, args.target))
    return 0
