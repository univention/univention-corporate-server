#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2016-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
"""
This module collects utilities for installing and building message catalogs
while applying Univention specific options.
"""

import os

import polib

from .helper import Error, call, make_parent_dir


def _clean_header(po_path: str) -> None:
    pof = polib.pofile(po_path)
    pof.header = ""
    pof.metadata.update({
        'Content-Type': 'text/plain; charset=utf-8',
    })
    pof.metadata_is_fuzzy = None
    pof.save(po_path)


def concatenate_po(src_po_path: str, dest_po_path: str) -> None:
    """
    Append first to second `.po` file.

    :param src_po_path: File to merge.
    :param dest_po_path: File to merge into.
    """
    call(
        'msgcat',
        '--unique',
        '--output', dest_po_path,
        src_po_path,
        dest_po_path,
    )
    _clean_header(dest_po_path)


def create_empty_po(binary_pkg_name: str, new_po_path: str) -> None:
    """
    Create a new empty `.po` file.

    :param binary_pkg_name: Package name.
    :param new_po_path: File name for new file.
    """
    make_parent_dir(new_po_path)
    call(
        'xgettext',
        '--force-po',
        '--add-comments=i18n',
        '--from-code=UTF-8',
        '--sort-output',
        f'--package-name={binary_pkg_name}',
        '--msgid-bugs-address=packages@univention.de',
        '--copyright-holder=Univention GmbH',
        # Suppress warning about /dev/null being an unknown source type
        '--language', 'C',
        '-o', new_po_path,
        '/dev/null')
    _clean_header(new_po_path)


def merge_po(template: str, translation: str) -> None:
    """
    Merge old translation with new template file.

    :param template: New template `.pot` file.
    :param translation: Old translation `.po` file.
    """
    call(
        'msgmerge',
        '--update',
        '--sort-output',
        '--backup=off',
        translation,
        template)


def join_existing(language: str, output_file: str, input_files: str | list[str], cwd: str = os.getcwd()) -> None:
    """
    Extract strings from source code and merge into existing translation file.

    :param language: Source code language, e.g. `JavaScript`, `Python`, `Shell`.
    :param output_file: Template file name.
    :param input_files: Sequence of input files.
    :param cwd: Base directory used as new woring directory.
    """
    if not os.path.isfile(output_file):
        raise Error(f"Can't join input files into {output_file}. File does not exist.")
    if not isinstance(input_files, list):
        input_files = [input_files]
    # make input_files relative so the location lines in the resulting po
    # will be relative to cwd
    input_files = [os.path.relpath(p, start=cwd) for p in input_files]
    call(
        'xgettext',
        '--from-code=UTF-8',
        '--join-existing',
        '--omit-header',
        '--language', language,
        '--keyword=N_:1',
        '-o', output_file,
        *input_files,
        cwd=cwd)


def univention_location_lines(pot_path: str, abs_path_source_pkg: str) -> None:
    """
    Convert absolute paths to relative paths.

    :param pot_path: Path to :file:`.pot` file.
    :param abs_path_source_pkg: Source package base path.
    """
    po_file = polib.pofile(pot_path)
    for entry in po_file:
        entry.occurrences = [
            ((os.path.relpath(path, start=abs_path_source_pkg), linenum))
            for path, linenum in entry.occurrences
        ]
    po_file.save(pot_path)
