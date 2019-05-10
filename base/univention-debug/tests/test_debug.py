#!/usr/bin/python

# univention-debug is part of the namespace package univention-python
# and has therefor no __init__.py -> Manually add a local univention
# package so we can test inside the build directory
from types import ModuleType
import sys
import re
m = ModuleType("univention")
m.__path__ = ['univention']
sys.modules[m.__name__] = m
import univention.debug as ud


def test_import_path():
	# Assert that the just build version is tested and not the installed one
	assert ud.__file__.startswith('univention/debug.py')


def test_debug(capfd):
	fd = ud.init("stdout", ud.NO_FLUSH, ud.FUNCTION)
	assert hasattr(fd, 'write')

	ud.debug(ud.MAIN, ud.ERROR, "Error in main: %%%")
	ud.debug(ud.MAIN, ud.WARN, "Warning in main: %%%")
	ud.debug(ud.MAIN, ud.PROCESS, "Process in main: %%%")
	ud.debug(ud.MAIN, ud.INFO, "Information in main: %%%")
	ud.debug(ud.MAIN, ud.ALL, "All in main: %%%")

	ud.set_level(ud.MAIN, ud.PROCESS)
	l = ud.get_level(ud.MAIN)
	assert l == ud.PROCESS

	ud.reopen()

	ud.set_function(ud.FUNCTION)
	ud.begin("Function")
	ud.end("Function")

	ud.set_function(ud.NO_FUNCTION)
	ud.begin("No function")
	ud.end("No function")

	ud.exit()

	ud.set_level(ud.MAIN, ud.ALL)
	l = ud.get_level(ud.MAIN)
	assert l != ud.ALL

	ud.debug(ud.MAIN, ud.ALL, "No crash")
	ud_output = capfd.readouterr()[0]
	norm_ud_output = '\n'.join([re.sub(
		r'^[0-3][0-9]\.[01][0-9]\.[0-9][0-9] [0-2][0-9]:[0-5][0-9]:[0-5][0-9]\.[0-9][0-9][0-9]',
		'00.00.00 00:00:00.000',
		line
	) for line in ud_output.splitlines()])
	with open('tests/test.out', 'r') as expected_output:
		assert norm_ud_output == expected_output.read().rstrip()
