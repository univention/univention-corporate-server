#!/usr/bin/pytest-3
# vim:set fileencoding=utf-8:
"""Unit test for univention.config_registry.misc."""

import string
from io import StringIO

import pytest

import univention.config_registry.misc as ucrm


@pytest.fixture
def out():
	return StringIO()


@pytest.mark.parametrize("text,out", [
	("str", "str"),
	(u"unicode", "unicode"),
	(u"Tür", "T?r"),
])
def test_asciify(text, out):
	assert ucrm.asciify(text) == out


@pytest.mark.parametrize("line", list(string.ascii_letters))
def test_key_shell_escape_letters(line):
	assert ucrm.key_shell_escape(line) == line


@pytest.mark.parametrize("line", list(string.digits))
def test_key_shell_escape_digits(line):
	assert ucrm.key_shell_escape(line) == "_" + line


@pytest.mark.parametrize("line", [chr(o) for o in range(256) if chr(o) not in ucrm.VALID_CHARS])
def test_key_shell_escape_replace(line):
	assert ucrm.key_shell_escape(line) == "_"


def test_key_shell_escape_error():
	with pytest.raises(ValueError):
		ucrm.key_shell_escape("")


@pytest.mark.parametrize("key", list(u"""[]\r\n!"#$%'()+,;<=>?\\`{}""") + [u": "])
def test_validate_key_invalid(key, out):
	assert not ucrm.validate_key(key, out)


@pytest.mark.parametrize("key", list(u"""ÄäÖöÜüß"""))
def test_validate_key_valid(key, out):
	assert ucrm.validate_key(key, out)


@pytest.mark.parametrize("key", [
	".",
	".a",
	"a.",
	"a..b",
	"-",
	"_",
	"0",
	"a",
	"a b",
	"a:b",
	"a/b",
])
def test_validate_key(key, out):
	assert ucrm.validate_key(key, out)


def test_directory_files(tmpdir):
	base = tmpdir.mkdir("test")
	files = [
		base.ensure("file"),
		base.mkdir("sub").ensure("file"),
	]
	broken = base.ensure("broken")
	base.join("link").mksymlinkto(broken),
	broken.remove()
	assert set(ucrm.directory_files(str(base))) == {str(path) for path in files}
