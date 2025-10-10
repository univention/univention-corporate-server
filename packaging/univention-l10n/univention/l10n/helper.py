#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2013-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
import subprocess
from typing import Any


class Error(SystemExit):
    pass


def make_parent_dir(path: str) -> None:
    """
    Create parent directories for file.

    :param path: Path for a file.
    """
    dir_path = os.path.dirname(path)
    try:
        os.makedirs(dir_path)
    except OSError:
        if not os.path.isdir(dir_path):
            raise


def call(*argv: str, **kwargs: Any) -> int:
    """
    Execute argv and wait.

    :param args: List of command and arguments.
    :param kwargs: Optiona key-word argument for :py:func:`subprocess.check_call`.

    >>> call('true')
    0
    """
    errmsg = kwargs.pop('errmsg', 'Gettext failed {0.cmd}')

    verbose = os.environ.get('DH_VERBOSE')
    if verbose:
        print('\t%s' % ' '.join(argv))
    try:
        return subprocess.check_call(argv, **kwargs)
    except subprocess.CalledProcessError as ex:
        if verbose:
            print(ex)
        raise Error(errmsg.format(ex))
