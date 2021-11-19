#!/usr/bin/python3
"""Unit test for univention.ldif."""
# pylint: disable-msg=C0103,E0611,R0904

from io import StringIO

import pytest

import univention.ldif as ul


def test_ldif_decode(mocker, capsys):
	mocker.patch("sys.stdin", StringIO(u"dn: cn=foo\ncn:: Zm9v\n"))
	ul.ldif_decode()
	stdout, stderr = capsys.readouterr()
	assert stdout == "dn: cn=foo\ncn: foo\n"
	assert stderr == ""


@pytest.mark.parametrize("line,out", [
	(u"dn: foo\n", u"dn: foo\n"),
	(u"dn:: Zm9v\n", u"dn: foo\n"),
])
def test_decode(line, out):
	assert "".join(ul.decode(StringIO(line))) == out


@pytest.mark.parametrize("line,out", [
	("dn: foo\n", "dn: foo\n"),
	("dn:: Zm9v\n", "dn: foo\n"),
])
def test_decode64(line, out):
	assert ul.decode64(line) == out


def test_ldif_unwrap(mocker, capsys):
	mocker.patch("sys.stdin", StringIO(u"dn: cn=foo\n bar\n"))
	ul.ldif_unwrap()
	stdout, stderr = capsys.readouterr()
	assert stdout == "dn: cn=foobar\n"
	assert stderr == ""


@pytest.mark.parametrize("lines,out", [
	(["dn: foo\n"], ["dn: foo\n"]),
	(["dn: foo\n", " bar\n"], ["dn: foobar\n"]),
	(["dn: foo \n", " bar\n"], ["dn: foo bar\n"]),
	(["dn: foo\n", "  bar\n"], ["dn: foo bar\n"]),
	(["dn: foo\n", "\t bar\n"], ["dn: foo bar\n"]),
])
def test_unwrap(lines, out):
	assert list(ul.unwrap(lines)) == out


def test_ldif_normalize(mocker, capsys):
	mocker.patch("sys.stdin", StringIO(u"dn: cn=foo\n bar\ncn:: Zm9v\n\tYmFy"))
	ul.ldif_normalize()
	stdout, stderr = capsys.readouterr()
	assert stdout == "dn: cn=foobar\ncn: foobar\n"
	assert stderr == ""
