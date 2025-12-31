#!/usr/bin/python3
# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Univention LDIF tool"""


import re
import sys
from argparse import ArgumentParser, FileType
from base64 import b64decode
from collections.abc import Iterable, Iterator
from typing import IO


__all__ = [
    "ldif_decode",
    "ldif_normalize",
    "ldif_unwrap",
]

RE_B64 = re.compile(r'^([a-zA-Z0-9-]+):: (.*)')


def ldif_decode(src: IO[str] = sys.stdin, dst: IO[bytes] = sys.stdout.buffer) -> None:
    """Decode bas64 in LDIF."""
    try:
        for line in src:
            dst.write(decode64(line))
    except BrokenPipeError:
        pass


def decode(stream: Iterable[str]) -> Iterator[bytes]:
    for line in stream:
        yield decode64(line)


def decode64(line: str) -> bytes:
    m = RE_B64.search(line)
    if m:
        attr, encoded = m.groups()
        decoded = b64decode(encoded)
        return b"%s: %s\n" % (attr.encode("utf-8"), decoded)
    else:
        return line.encode("utf-8")


def ldif_unwrap(src: IO[str] = sys.stdin, dst: IO[bytes] = sys.stdout.buffer) -> None:
    """Unwrap LDIF."""
    try:
        for line in unwrap(src):
            dst.write(line.encode("utf-8"))
    except BrokenPipeError:
        pass


def unwrap(stream: Iterable[str]) -> Iterator[str]:
    prev = ""
    for line in stream:
        if line[:1] in (' ', '\t'):
            prev = prev.rstrip("\n\r") + line[1:]
        else:
            if prev:
                yield prev
            prev = line

    if prev:
        yield prev


def ldif_normalize(src: IO[str] = sys.stdin, dst: IO[bytes] = sys.stdout.buffer) -> None:
    """Unwrap and base64 decode LDIF."""
    try:
        for line in unwrap(src):
            dst.write(decode64(line))
    except BrokenPipeError:
        pass


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--src", "-s", type=FileType("r"), default="-", help="Source input")
    parser.add_argument("--dst", "-d", type=FileType("w"), default="-", help="Destination output")

    parser.set_defaults(func=ldif_normalize)
    subparsers = parser.add_subparsers(help="Sub-command help")

    parser_decode = subparsers.add_parser("decode", help=ldif_decode.__doc__)
    parser_decode.set_defaults(func=ldif_decode)

    parser_unwrap = subparsers.add_parser("unwrap", help=ldif_unwrap.__doc__)
    parser_unwrap.set_defaults(func=ldif_unwrap)

    args = parser.parse_args()
    args.func(args.src, args.dst.buffer)


if __name__ == "__main__":
    main()
