# -*- coding: iso-8859-15 -*-
"""Find unquoted usage of eval "$(ucr shell)"."""

try:
	import univention.ucslint.base as uub
except ImportError:
	import ucslint.base as uub
import re


def containsHashBang(path):
	try:
		fp = open(path, 'r')
	except IOError:
		return False
	try:
		for line in fp:
			if '#!/bin/sh' in line or '#!/bin/bash' in line:
				return True
		return False
	finally:
		fp.close()


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):
	def __init__(self):
		super(UniventionPackageCheck, self).__init__()
		self.name = '0017-Shell'
		self.tester = uub.UPCFileTester()
		self.tester.addTest(re.compile(r'eval\s+(`|[$][(])\s*(/usr/sbin/)?(ucr|univention-baseconfig|univention-config-registry)\s+shell\s*[^`)]*[`)]\s*'),
				'0017-1', 'unquoted call of eval "$(ucr shell)"', cntmax=0)

	def getMsgIds(self):
		return { '0017-1': [ uub.RESULT_WARN,   'script contains unquoted calls of eval "$(ucr shell)"' ]}

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """
		pass

	def check(self, path):
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		#
		# search shell scripts and execute test
		#
		for fn in uub.FilteredDirWalkGenerator(path):
			if fn.endswith('.sh') or containsHashBang(fn):
				self.tester.open(fn)
				msglist = self.tester.runTests()
				self.msg.extend(msglist)
