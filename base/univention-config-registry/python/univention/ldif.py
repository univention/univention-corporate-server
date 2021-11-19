#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright 2004-2022 Univention GmbH
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
Univention LDIF tool
"""

from __future__ import print_function

import re
import sys
from argparse import ArgumentParser, FileType
from base64 import b64decode
from typing import IO, Iterable, Iterator  # noqa F401

__all__ = [
	"ldif_decode",
	"ldif_unwrap",
	"ldif_normalize",
]

RE_B64 = re.compile(r'^([a-zA-Z0-9-]+):: (.*)')


def ldif_decode(src=sys.stdin, dst=sys.stdout.buffer):
	# type: (IO[str], IO[bytes]) -> None
	"""Decode bas64 in LDIF."""
	try:
		for line in src:
			dst.write(decode64(line))
	except BrokenPipeError:
		pass


def decode(stream):
	# type: (Iterable[str]) -> Iterator[bytes]
	for line in stream:
		yield decode64(line)


def decode64(line):
	# type: (str) -> bytes
	m = RE_B64.search(line)
	if m:
		attr, encoded = m.groups()
		decoded = b64decode(encoded)
		return b"%s: %s\n" % (attr.encode("utf-8"), decoded)
	else:
		return line.encode("utf-8")


def ldif_unwrap(src=sys.stdin, dst=sys.stdout.buffer):
	# type: (IO[str], IO[bytes]) -> None
	"""Unwrap LDIF."""
	try:
		for line in unwrap(src):
			dst.write(line.encode("utf-8"))
	except BrokenPipeError:
		pass


def unwrap(stream):
	# type: (Iterable[str]) -> Iterator[str]
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


def ldif_normalize(src=sys.stdin, dst=sys.stdout.buffer):
	# type: (IO[str], IO[bytes]) -> None
	"""Unwrap and base64 decode LDIF."""
	try:
		for line in unwrap(src):
			dst.write(decode64(line))
	except BrokenPipeError:
		pass


def main():
	# type: () -> None
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
