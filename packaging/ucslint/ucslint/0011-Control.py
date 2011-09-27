# -*- coding: iso-8859-15 -*-

try:
	import univention.ucslint.base as uub
except:
	import ucslint.base as uub
import re, os

class UniventionPackageCheck(uub.UniventionPackageCheckBase):
	def __init__(self):
		uub.UniventionPackageCheckBase.__init__(self)
		self.name = '0011-Control'

	def getMsgIds(self):
		return { '0011-1': [ uub.RESULT_WARN, 'failed to open/read file' ],
				 '0011-2': [ uub.RESULT_ERROR, 'source package name differs in debian/control an debian/changelog' ],
				 '0011-3': [ uub.RESULT_WARN, 'wrong section - should be "Univention"' ],
				 '0011-4': [ uub.RESULT_WARN, 'wrong priority - should be "optional"' ],
				 '0011-5': [ uub.RESULT_ERROR, 'wrong maintainer - should be "Univention GmbH <packages@univention.de>"' ],
				 '0011-6': [ uub.RESULT_ERROR, 'XS-Python-Version without python-central in build-dependencies' ],
				 '0011-7': [ uub.RESULT_ERROR, 'XS-Python-Version without XB-Python-Version in binary package entries' ],
				 '0011-8': [ uub.RESULT_WARN, 'XS-Python-Version should be "2.4"' ],
				 '0011-9': [ uub.RESULT_ERROR, 'cannot determine source package name' ],
				 '0011-10': [uub.RESULT_ERROR, 'parsing error in debian/control' ],
				 '0011-11': [uub.RESULT_WARN,  'debian/control: XS-Python-Version is not required any longer' ],
				 '0011-12': [uub.RESULT_ERROR, 'debian/control: please use python-support instead of python-central in Build-Depends' ],
				 '0011-13': [uub.RESULT_WARN,  'debian/control: ucslint is missing in Build-Depends' ],
				 }

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """
		pass

	def check(self, path):
		""" the real check """

		if not os.path.isdir( os.path.join(path, 'debian') ):
			print "ERROR: directory %s/debian does not exist!" % path
			return

		fn = os.path.join(path, 'debian', 'changelog')
		try:
			content_changelog = open(fn, 'r').read(1024)
		except:
			self.addmsg( '0011-1', 'failed to open and read file', filename=fn )
			return

		fn = os.path.join(path, 'debian', 'control')
		try:
			parser = uub.ParserDebianControl(fn)
		except uub.FailedToReadFile:
			self.addmsg( '0011-1', 'failed to open and read file', filename=fn )
			return
		except uub.UCSLintException:
			self.addmsg( '0011-11', 'parsing error', filename=fn )
			return

		# compare package name
		reChangelogPackage = re.compile('^([a-z0-9.-]+) \((.*?)\) (.*?)\n')
		match = reChangelogPackage.match(content_changelog)
		if match:
			srcpkgname = match.group(1)
		else:
			srcpkgname = None
			self.addmsg( '0011-9', 'cannot determine source package name', filename='debian/changelog' )

		controlpkgname = parser.source_section.get('Source')
		if not controlpkgname:
			self.addmsg( '0011-9', 'cannot determine source package name', filename='debian/control' )

		if srcpkgname and controlpkgname:
			if srcpkgname != controlpkgname:
				self.addmsg( '0011-2', 'source package name differs in debian/changelog and debian/control' )


		# parse source section of debian/control
		if not parser.source_section.get('Section', '') in ( 'univention' ):
			self.addmsg( '0011-3', 'wrong Section entry - should be "univention"', filename='debian/control' )

		if not parser.source_section.get('Priority', '') in ( 'optional' ):
			self.addmsg( '0011-4', 'wrong Priority entry - should be "optional"', filename='debian/control' )

		if not parser.source_section.get('Maintainer', '') in ( 'Univention GmbH <packages@univention.de>' ):
			self.addmsg( '0011-5', 'wrong Maintainer entry - should be "Univention GmbH <packages@univention.de>"', filename='debian/control' )

		if parser.source_section.get('XS-Python-Version', ''):
			self.addmsg( '0011-11', 'XS-Python-Version is not required any longer', filename='debian/control' )

		if 'python-central' in parser.source_section.get('Build-Depends', ''):
			self.addmsg( '0011-12', 'please use python-support instead of python-central in Build-Depends', filename='debian/control' )

		if not 'ucslint' in parser.source_section.get('Build-Depends', ''):
			self.addmsg( '0011-13', 'ucslint is missing in Build-Depends', filename='debian/control' )
