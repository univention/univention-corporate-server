#!/usr/bin/python3
# vim:set fileencoding=utf-8 filetype=python tabstop=4 shiftwidth=4 expandtab:
from __future__ import print_function

import json
from itertools import groupby
from operator import itemgetter

try:
    from typing import Dict, Iterable, List, Sequence, Tuple  # noqa F401
except ImportError:
    pass

import six


MAJOR = 3
MINOR = 0
PATCH = 1
ERRAT = 3
PART = 'part'
ARCH = 'amd64'


class MockPopen(object):

    """Mockup for Popen."""
    mock_commands = []  # type: List[Sequence[str]]
    mock_stdout = b''
    mock_stderr = b''

    def __init__(self, cmd, shell=False, *args, **kwargs):  # pylint: disable-msg=W0613
        self.returncode = 0
        self.stdin = b''
        self.stdout = MockPopen.mock_stdout
        self.stderr = MockPopen.mock_stderr
        if shell:
            MockPopen.mock_commands.append(cmd)
        else:
            if isinstance(cmd, six.string_types):
                cmd = (cmd,)
            try:
                fd_script = open(cmd[0], 'r')
                try:
                    content = fd_script.read(1024)
                finally:
                    fd_script.close()
            except (IOError, UnicodeDecodeError) as ex:
                content = ex
            MockPopen.mock_commands.append(tuple(cmd) + (content,))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def wait(self, timeout=None):
        """Return result code."""
        return self.returncode

    def poll(self):
        """Return result code."""
        return self.returncode

    def communicate(self, stdin=None):  # pylint: disable-msg=W0613
        """Return stdout and strerr."""
        return self.stdout, self.stderr

    @classmethod
    def mock_get(cls):
        """Return list of called commands."""
        commands = cls.mock_commands
        cls.mock_commands = []
        return commands

    @classmethod
    def mock_reset(cls):
        """Reset list of called commands."""
        cls.mock_commands = []
        cls.mock_stdout = cls.mock_stderr = b''


def gen_releases(releases=[], major=MAJOR, minor=MINOR, patches=range(0, PATCH + 1)):  # type: (Iterable[Tuple[int, int, int]], int, int, Iterable[int]) -> bytes
    """
    Generate a releases.json string from a list of given releases.

    :param releases: List of UCS releases.
    :param major: UCS major version.
    :param minor: UCS minor version.
    :param patches: List of UCS patch-level versions.

    >>> gen_releases([(MAJOR, MINOR, 0), (MAJOR, MINOR, 1)]) == gen_releases(patches=[0, 1])
    True
    """
    releases = list(releases) or [(major, minor, patch) for patch in patches]
    data = dict(
        releases=[
            dict(
                major=major,
                minors=[
                    dict(
                        minor=minor,
                        patchlevels=[
                            dict(
                                patchlevel=patchlevel,
                                status="maintained",
                            ) for major, minor, patchlevel in patchelevels
                        ]
                    ) for minor, patchelevels in groupby(minors, key=itemgetter(1))
                ]
            ) for major, minors in groupby(releases, key=itemgetter(0))
        ]
    )
    return json.dumps(data).encode('UTF-8')
