#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2020-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
>>> RE_DEBIAN_PACKAGE_NAME.match("0").groups()
('0',)
>>> RE_DEBIAN_PACKAGE_VERSION.match("0").groups()
(None, '0', None)
>>> RE_DEBIAN_PACKAGE_VERSION.match("0-0").groups()
(None, '0', '0')
>>> RE_DEBIAN_PACKAGE_VERSION.match("0-0-0").groups()
(None, '0-0', '0')
>>> RE_DEBIAN_CHANGELOG.match("0 (0) unstable; urgency=low").groups()
('0', '0', ' unstable', ' urgency=low')
>>> RE_HASHBANG_SHELL.match('#!/bin/sh') is not None
True
>>> RE_HASHBANG_SHELL.match('#! /bin/bash') is not None
True
"""

import re


# /usr/share/perl5/Dpkg/Changelog/Entry/Debian.pm
WORD_CHARS = '[0-9a-z]'
NAME_CHARS = '[+.0-9a-z-]'
RE_DEBIAN_PACKAGE_NAME = re.compile(
    rf"""^
    ({WORD_CHARS}{NAME_CHARS}*)  # Package name
    $""",
    re.VERBOSE,
)
RE_DEBIAN_PACKAGE_VERSION = re.compile(
    r'''^
    (?: (?P<epoch>[0-9]+) : )?
    (?P<upstream> [0-9][+.0-9a-z~-]*? )
    (?: - (?P<revision>[+.0-9a-z~]+) )?
    $''', re.VERBOSE)
RE_DEBIAN_CHANGELOG = re.compile(
    rf"""^
    ({WORD_CHARS}{NAME_CHARS}*)  # Package name
    [ ]
    \( ([^ ()]+) \)  # Package version
    ( (?: \s+ (?:UNRELEASED|{NAME_CHARS}+) )+ )  # Target distribution
    ;
    (.*?)  # key=value options
    \s*$""",
    re.MULTILINE | re.VERBOSE,
)
RE_HASHBANG_SHELL = re.compile(r'^#!\s*/bin/(?:a|ba|c|da|z)?sh\b')
