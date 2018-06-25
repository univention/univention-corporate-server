#!/usr/share/ucs-test/runner python
# -*- coding: utf-8 -*-
## desc: Run UDM API doctests
## exposure: dangerous
## roles: [domaincontroller_master]
## packages: [python-univention-directory-manager]

import unittest

testSuite = unittest.TestSuite()

import doctest
from univention.udm import factory_config

testSuite.addTest(doctest.DocTestSuite(factory_config))
unittest.TextTestRunner(verbosity=2).run(testSuite)
