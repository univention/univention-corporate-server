#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Unit tests for the DEB822 APT sources."""

import pytest

import univention.updater.scripts.updater as updater_script
from univention.updater.sources import SourcesEntry, iter_entries, main, migrate_sources_list


ENTRY = SourcesEntry(types=('deb',), uris=('https://updates.software-univention.de/',), suites=('ucs530',), components=('main',))


class TestTemporarySources:

    @pytest.fixture(autouse=True)
    def tmp_sources(self, tmp_path, monkeypatch):
        new = tmp_path / '00_ucs_temporary_installation.sources'
        old = (tmp_path / '00_ucs_temporary_installation.list', tmp_path / '00_ucs_update_in_progress.list')
        monkeypatch.setattr(updater_script, 'TMPSOURCE', str(new))
        monkeypatch.setattr(updater_script, 'TMPSOURCES_OLD', tuple(str(fn) for fn in old))
        return new, old

    def test_add(self, tmp_sources):
        new, _old = tmp_sources
        updater_script.add_temporary_sources_list([ENTRY, ENTRY])
        with new.open() as fp:
            assert list(iter_entries(fp)) == [ENTRY, ENTRY]
        assert new.read_text().count('\n\n') == 1

    def test_remove(self, tmp_sources):
        new, old = tmp_sources
        for fn in (new, *old):
            fn.write_text('')
        updater_script.remove_temporary_sources_list()
        assert not any(fn.exists() for fn in (new, *old))

    def test_remove_missing(self):
        updater_script.remove_temporary_sources_list()


class TestMigrateSourcesList:

    @pytest.fixture
    def files(self, tmp_path):
        return tmp_path / 'sources.list', tmp_path / 'moved-from-main.sources', tmp_path / 'sources.list.upgrade530.bak'

    def test_missing(self, files):
        source, target, backup = files
        assert migrate_sources_list(str(source), str(target), str(backup)) == 0
        assert not target.exists()

    def test_only_comments(self, files):
        source, target, backup = files
        text = '# This file is not maintained via Univention Configuration Registry\n\n'
        source.write_text(text)
        assert migrate_sources_list(str(source), str(target), str(backup)) == 0
        assert source.read_text() == text
        assert not target.exists()
        assert not backup.exists()

    def test_convert(self, files):
        source, target, backup = files
        text = (
            '# header\n'
            'deb cdrom:[UCS 5.3-0 Release amd64]/ ucs530 main\n'
            'deb [trusted=yes] http://example.org/repo/ ./\n'
            'deb http://example.org/debian trixie main contrib\n'
            'deb [foo=bar] http://example.org/unknown/ ./\n'
        )
        source.write_text(text)
        target.write_text('Types: deb\nURIs: http://old/\nSuites: ./\n')

        assert migrate_sources_list(str(source), str(target), str(backup)) == 2

        assert backup.read_text() == text
        lines = source.read_text().splitlines()
        assert lines[0] == '# header'
        assert lines[1] == 'deb cdrom:[UCS 5.3-0 Release amd64]/ ucs530 main'
        assert lines[2].startswith('# Moved to ') and lines[2].endswith('deb [trusted=yes] http://example.org/repo/ ./')
        assert lines[3].startswith('# Moved to ')
        assert lines[4] == 'deb [foo=bar] http://example.org/unknown/ ./'
        with target.open() as fp:
            entries = list(iter_entries(fp))
        assert [entry.uris for entry in entries] == [('http://old/',), ('http://example.org/repo/',), ('http://example.org/debian',)]
        assert entries[1].options == (('Trusted', 'yes'),)
        assert entries[2].components == ('main', 'contrib')

    def test_backup_kept(self, files):
        source, target, backup = files
        backup.write_text('original\n')
        source.write_text('deb http://example.org/debian trixie main\n')
        assert migrate_sources_list(str(source), str(target), str(backup)) == 1
        assert backup.read_text() == 'original\n'

    def test_main(self, files, capsys):
        source, target, backup = files
        source.write_text('deb http://example.org/debian trixie main\n')
        assert main(['--migrate', '--source', str(source), '--target', str(target), '--backup', str(backup)]) == 0
        assert 'Moved 1 entries' in capsys.readouterr().out
        assert target.exists()
