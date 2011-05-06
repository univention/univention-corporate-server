# -*- coding: iso-8859-15 -*-

try:
	import univention.ucslint.base as uub
except:
	import ucslint.base as uub
import re, os

class UniventionPackageCheck(uub.UniventionPackageCheckBase):
	def __init__(self):
		uub.UniventionPackageCheckBase.__init__(self)
		self.name = '0009-Python'

	def getMsgIds(self):
		return { '0009-1': [ uub.RESULT_WARN, 'failed to open file' ],
				 '0009-2': [ uub.RESULT_ERROR, 'python file does not specify python version in hashbang' ],
				 '0009-3': [ uub.RESULT_ERROR, 'python file specifies wrong python version in hashbang' ],
				 '0009-4': [ uub.RESULT_WARN, 'python file contains whitespace and maybe arguments after python command' ],
				 }

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """
		pass

	def check(self, path):
		""" the real check """

		fnlist_joinscripts = {}

		if not os.path.isdir( os.path.join(path, 'debian') ):
			print "ERROR: directory %s does not exist!" % path
			return

		py_files = []
		for dirpath, dirnames, filenames in os.walk( path ):
			if '/.svn/' in dirpath or dirpath.endswith('/.svn'):   # ignore svn files
				continue
			for fn in filenames:
				try:
					content = open( os.path.join( dirpath, fn), 'r').read(100)
					if content.startswith('#!'):
						py_files.append( os.path.join( dirpath, fn ) )
				except:
					pass

		for fn in py_files:
			try:
				content = open(fn, 'r').read(100)
			except:
				self.addmsg( '0009-1', 'failed to open and read file %s' % fn )
				continue
			self.debug('testing %s' % fn)

			if not content:
				continue

			firstline = content.splitlines()[0]
			if firstline.startswith('#! /'):
				firstline = '#!' + firstline[3:]
			if firstline.startswith('#!/usr/bin/python'):
				if firstline == '#!/usr/bin/python' or firstline.startswith('#!/usr/bin/python '):
					self.addmsg( '0009-2', '%s does not specify python version in hashbang' % (fn) )
				elif firstline.startswith('#!/usr/bin/python2.3') or firstline.startswith('#!/usr/bin/python2.5'):
					self.addmsg( '0009-3', '%s specifies wrong python version in hashbang' % (fn) )
				elif firstline.startswith('#!/usr/bin/python2.4 '):
					self.addmsg( '0009-4', '%s contains whitespace after python command' % (fn) )
