"""Univention Configuration Registry helper functions."""
#  main configuration registry classes
#
# SPDX-FileCopyrightText: 2004-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import os
import re
import string  # pylint: disable-msg=W0402
import sys
from shlex import quote as escape_value
from typing import IO


__all__ = [
    'INVALID_KEY_CHARS',
    'directory_files',
    'escape_value',
    'key_shell_escape',
    'replace_dict',
    'replace_umlaut',
    'validate_key',
]


def replace_dict(line: str, dictionary: dict[str, str]) -> str:
    """
    Map any character from line to its value from dictionary.

    >>> replace_dict('kernel', {'e': 'E', 'k': '', 'n': 'pp'})
    'ErppEl'
    """
    return ''.join(dictionary.get(_, _) for _ in line)


def replace_umlaut(line: str) -> str:
    """
    Replace german umlauts.

    >>> replace_umlaut(u'überschrieben') == u'ueberschrieben'
    True
    """
    return replace_dict(line, UMLAUTS)  # pylint: disable-msg=E1101


UMLAUTS = {  # type: ignore # pylint: disable-msg=W0612
    'Ä': 'Ae',
    'ä': 'ae',
    'Ö': 'Oe',
    'ö': 'oe',
    'Ü': 'Ue',
    'ü': 'ue',
    'ß': 'ss',
}


def asciify(text: str) -> str:
    """
    Replace any non-ASCII characters.

    :param text: Input text.
    :returns: Replaced text.
    """
    return text.encode('ascii', 'replace').decode("ascii")


def key_shell_escape(line: str) -> str:
    """
    Escape variable name by substituting shell invalid characters by '_'.

    :param line: UCR variable name.
    :returns: substitued variable name
    """
    if not line:
        raise ValueError('got empty line')
    new_line = []
    if line[0] in string.digits:
        new_line.append('_')
    for letter in line:
        if letter in VALID_CHARS:  # pylint: disable-msg=E1101
            new_line.append(letter)
        else:
            new_line.append('_')

    return ''.join(new_line)


VALID_CHARS = (  # type: ignore # pylint: disable-msg=W0612
    string.ascii_letters + string.digits + '_')


def validate_key(key: str, out: IO = sys.stderr) -> bool:
    """
    Check if key consists of only shell valid characters.

    :param key: UCR variable name to check.
    :param out: Output stream where error message is printed to.
    :returns: `True` if the name is valid, `False` otherwise.
    """
    old = key
    key = replace_umlaut(key)

    if old != key:
        print('Umlauts in config variable key are not recommended. Please consider renaming "%s" to %s.' % (old, key), file=out)
        # return False  # Bug #53742

    if len(key) > 0:
        if ': ' in key:
            print('Please fix invalid ": " in config variable key "%s".' % (key,), file=out)
            return False
        match = INVALID_KEY_CHARS.search(key)

        if not match:
            return True
        print('Please fix invalid character "%s" in config variable key "%s".' % (match.group(), key), file=out)
    return False


INVALID_KEY_CHARS = re.compile('[][\r\n!"#$%&\'()+,;<=>?\\\\`{}§]')


def directory_files(directory: str) -> list[str]:
    """
    Return a list of all files below the given directory.

    :param directory: Base directory path.
    :returns: List of absolute file names.
    """
    result = []
    for dirpath, _dirnames, filenames in os.walk(directory):
        for filename in filenames:
            filename = os.path.join(dirpath, filename)
            if os.path.isfile(filename):
                result.append(filename)
    return result
