#!/usr/bin/python
"""Unit test for univention.config_registry."""
# pylint: disable-msg=C0103,E0611,R0904

import univention.config_registry as UCR


def test_private(tmpucr):
	assert UCR.ucr_factory() is not UCR.ucr_factory()
