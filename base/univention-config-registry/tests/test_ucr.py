#!/usr/bin/python
"""Unit test for univention.config_registry."""
# pylint: disable-msg=C0103,E0611,R0904

import sys

import pytest

import univention.config_registry as UCR

if sys.version_info >= (3,):
	from importlib import reload


def test_private(tmpucr):
	assert UCR.ucr_factory() is not UCR.ucr_factory()


def test_ro(ucrf):
	reload(UCR)
	assert not isinstance(UCR.ucr, UCR.ConfigRegistry)
	assert UCR.ucr["foo"] == "LDAP"
	assert UCR.ucr["bam"] is None
	with pytest.raises(TypeError):
		UCR.ucr["foo"] = "42"
	with pytest.raises(TypeError):
		del UCR.ucr["foo"]


def test_ro_stale(ucr0):
	reload(UCR)
	ucr0["baz"] = "BEFORE"
	ucr0.save()
	assert UCR.ucr["baz"] == "BEFORE"
	ucr0["baz"] = "AFTER"
	ucr0.save()
	assert UCR.ucr["baz"] == "BEFORE"
