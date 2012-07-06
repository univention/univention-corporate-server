# -*- coding: iso-8859-15 -*-

try:
	import univention.ucslint.base as uub
except:
	import ucslint.base as uub
import re
import os
import time

class UniventionPackageCheck(uub.UniventionPackageCheckBase):
	def __init__(self):
		uub.UniventionPackageCheckBase.__init__(self)
		self.name = '0010-Copyright'

	def getMsgIds(self):
		return { '0010-1': [ uub.RESULT_WARN, 'failed to open file' ],
				 '0010-2': [ uub.RESULT_ERROR, 'file contains no copyright text block' ],
				 '0010-3': [ uub.RESULT_WARN, 'copyright is outdated' ],
				 '0010-4': [ uub.RESULT_ERROR, 'cannot find copyright line containing year' ],
				 '0010-5': [ uub.RESULT_ERROR, 'file debian/copyright is missing' ],
				 }

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """
		pass

	def check(self, path):
		""" the real check """

		if not os.path.isdir( os.path.join(path, 'debian') ):
			print "ERROR: directory %s does not exist!" % path
			return

		check_files = []

		# check if copyright file is missing
		if not os.path.exists( os.path.join(path, 'debian', 'copyright' ) ):
			self.addmsg( '0010-5', 'file is missing', filename='debian/copyright' )

		# looking for files below debian/
		for f in os.listdir( os.path.join(path, 'debian') ):
			fn = os.path.join(path, 'debian', f)
			if f.endswith('.preinst') or f.endswith('.postinst') or f.endswith('.prerm') or f.endswith('.postrm') or \
					f in [ 'preinst', 'postinst', 'prerm', 'postrm', 'copyright' ]:
				check_files.append( fn )

		# looking for python files
		for dirpath, dirnames, filenames in os.walk( path ):
			if '.svn' in dirnames:
				dirnames.remove('.svn')
			for fn in filenames:
				if fn.endswith('~'):
					continue
				try:
					content = open( os.path.join( dirpath, fn), 'r').read(100)
					if content.startswith('#!'):
						check_files.append( os.path.join( dirpath, fn ) )
				except:
					pass

		# Copyright (C) 2004, 2005, 2006-2012 Univention GmbH
		# Copyright 2008 by
		reCopyrightVersion = re.compile('Copyright(\s+\(C\))?\s+([0-9, -]+)\s+(by|Univention\s+GmbH)')

		# check files for copyright
		for fn in check_files:
			try:
				content = open(fn, 'r').read()
			except:
				self.addmsg( '0010-1', 'failed to open and read file', filename=fn )
				continue
			self.debug('testing %s' % fn)

			copyright_strings = ( 'under the terms of the GNU Affero General Public License version 3',
								  'Binary versions of this',
								  'provided by Univention to you as',
								  'cryptographic keys etc. are subject to a license agreement between',
								  'the terms of the GNU AGPL V3',
								  'You should have received a copy of the GNU Affero General Public',
								  )

			for teststr in copyright_strings:
				if not teststr in content:
					self.debug('Missing copyright string: %s' % teststr)
					self.addmsg( '0010-2', 'file contains no copyright text block', filename=fn )
					break
			else:
				# copyright text block is present - lets check if it's outdated
				match = reCopyrightVersion.search( content )
				if not match:
					self.addmsg( '0010-4', 'cannot find copyright line containing year', filename=fn )
				else:
					years = match.group(2)
					current_year = str(time.localtime()[0])
					if not current_year in years:
						self.debug('Current year=%s  years="%s"' % (current_year, years))
						self.addmsg( '0010-3', 'copyright line seems to be outdated', filename=fn )
