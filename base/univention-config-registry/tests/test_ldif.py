#!/usr/bin/python3
"""Unit test for univention.ldif."""
# pylint: disable-msg=C0103,E0611,R0904

from io import BytesIO, StringIO

import pytest

import univention.ldif as ul


@pytest.fixture
def dst():
	return BytesIO()


def idfn(val):
	if isinstance(val, bytes):
		return val.decode("utf-8", errors="replace")
	elif isinstance(val, list):
		return "".join(val)


def test_ldif_decode(dst):
	ul.ldif_decode(StringIO(u"dn: cn=foo\ncn:: Zm9v\n"), dst)
	assert dst.getvalue() == b"dn: cn=foo\ncn: foo\n"


@pytest.mark.parametrize("line,out", [
	(u"dn: foo\n", b"dn: foo\n"),
	(u"dn:: Zm9v\n", b"dn: foo\n"),
], ids=idfn)
def test_decode(line, out):
	assert b"".join(ul.decode(StringIO(line))) == out


@pytest.mark.parametrize("line,out", [
	("dn: foo\n", b"dn: foo\n"),
	("dn:: Zm9v\n", b"dn: foo\n"),
	("dn:: gQ==\n", b"dn: \x81\n"),
], ids=idfn)
def test_decode64(line, out):
	assert ul.decode64(line) == out


def test_ldif_unwrap(dst):
	ul.ldif_unwrap(StringIO(u"dn: cn=foo\n bar\n"), dst)
	assert dst.getvalue() == b"dn: cn=foobar\n"


@pytest.mark.parametrize("lines,out", [
	(["dn: foo\n"], ["dn: foo\n"]),
	(["dn: foo\n", " bar\n"], ["dn: foobar\n"]),
	(["dn: foo \n", " bar\n"], ["dn: foo bar\n"]),
	(["dn: foo\n", "  bar\n"], ["dn: foo bar\n"]),
	(["dn: foo\n", "\t bar\n"], ["dn: foo bar\n"]),
], ids=idfn)
def test_unwrap(lines, out):
	assert list(ul.unwrap(lines)) == out


def test_ldif_normalize(dst):
	ul.ldif_normalize(StringIO(u"dn: cn=foo\n bar\ncn:: Zm9v\n\tYmFy"), dst)
	assert dst.getvalue() == b"dn: cn=foobar\ncn: foobar\n"
