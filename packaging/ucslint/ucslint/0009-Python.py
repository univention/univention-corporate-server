# -*- coding: iso-8859-15 -*-

try:
	import univention.ucslint.base as uub
except ImportError:
	import ucslint.base as uub
import re


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):
	"""Python specific checks."""
	def __init__(self):
		super(UniventionPackageCheck, self).__init__()
		self.name = '0009-Python'

	def getMsgIds(self):
		return { '0009-1': [ uub.RESULT_WARN, 'failed to open file' ],
				 '0009-2': [ uub.RESULT_ERROR, 'python file does not specify python version in hashbang' ],
				 '0009-3': [ uub.RESULT_ERROR, 'python file specifies wrong python version in hashbang' ],
				 '0009-4': [ uub.RESULT_WARN, 'python file contains whitespace and maybe arguments after python command' ],
				 '0009-5': [ uub.RESULT_WARN, 'dict.has_key is deprecated in python3 - please use "if key in dict:"' ],
				 '0009-6': [ uub.RESULT_WARN, 'raise "text" is deprecated in python3' ],
				 }

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """
		pass

	def check(self, path):
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		py_files = []
		for fn in uub.FilteredDirWalkGenerator(path):
			if fn.endswith('.py'): # add all files to list that end with ".py"
				py_files.append(fn)
				continue

			try:
				content = open(fn, 'r').read(100)  # add all files that contain a hashbang in first line
			except OSError:
				pass
			else:
				if content.startswith('#!'):
					py_files.append(fn)

		tester = uub.UPCFileTester()
		tester.addTest( re.compile('.has_key\s*\('), '0009-5', 'dict.has_key is deprecated in python3 - please use "if key in dict:"', cntmax=0 )
		tester.addTest( re.compile(r'''\braise\s*(?:'[^']+'|"[^"]+")'''), '0009-6', 'raise "text" is deprecated in python3', cntmax=0 )
		for fn in py_files:
			try:
				content = open(fn, 'r').read(100)
			except OSError:
				self.addmsg( '0009-1', 'failed to open and read file', filename=fn )
				continue
			self.debug('testing %s' % fn)

			if not content:
				continue

			tester.open(fn)
			msglist = tester.runTests()
			self.msg.extend( msglist )

			firstline = content.splitlines()[0]
			if firstline.startswith('#! /'):
				firstline = '#!' + firstline[3:]
			if firstline.startswith('#!/usr/bin/python'):
				if firstline == '#!/usr/bin/python' or firstline.startswith('#!/usr/bin/python '):
					self.addmsg( '0009-2', 'file does not specify python version in hashbang', filename=fn )
				elif firstline.startswith('#!/usr/bin/python2.') and not firstline.startswith('#!/usr/bin/python2.6'):
					self.addmsg( '0009-3', 'file specifies wrong python version in hashbang', filename=fn )
				elif firstline.startswith('#!/usr/bin/python3'):
					self.addmsg( '0009-3', 'file specifies wrong python version in hashbang', filename=fn )
				elif firstline.startswith('#!/usr/bin/python2.6 '):
					self.addmsg( '0009-4', 'file contains whitespace after python command', filename=fn )
