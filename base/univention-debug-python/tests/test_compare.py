#!/usr/bin/python2.7
# vim: set fileencoding=utf-8 backupcopy=auto sw=4 ts=4:

import univention.debug as ud
import univention.debug2 as ud2


def test_compare():
	# type: () -> None
	native = set(_ for _ in dir(ud) if not _.startswith('_'))
	native -= set(('_debug', 'begin', 'end'))
	python = set(_ for _ in dir(ud2) if not _.startswith('_'))
	python -= set(('logging', 'DEFAULT', 'print_function'))

	# The C implementation implements everything from the Python version
	assert python <= native, 'Missing C implementation: %s' % (python - native,)

	# The Python implementation implements everything from the C version
	assert native <= python, 'Missing Python implementation: %s' % (native - python,)
