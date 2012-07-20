# -*- coding: iso-8859-15 -*-

try:
	import univention.ucslint.base as uub
except ImportError:
	import ucslint.base as uub
import re
import os

class UniventionPackageCheck(uub.UniventionPackageCheckDebian):
	def __init__(self):
		super(UniventionPackageCheck, self).__init__()
		self.name = '0011-Control'

	def getMsgIds(self):
		return { '0011-1': [ uub.RESULT_WARN, 'failed to open/read file' ],
				 '0011-2': [ uub.RESULT_ERROR, 'source package name differs in debian/control and debian/changelog' ],
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
		super(UniventionPackageCheck, self).check(path)

		fn_changelog = os.path.join(path, 'debian', 'changelog')
		try:
			content_changelog = open(fn_changelog, 'r').read(1024)
		except IOError:
			self.addmsg('0011-1', 'failed to open and read file', filename=fn_changelog)
			return

		fn_control = os.path.join(path, 'debian', 'control')
		try:
			parser = uub.ParserDebianControl(fn_control)
		except uub.FailedToReadFile:
			self.addmsg('0011-1', 'failed to open and read file', filename=fn_control)
			return
		except uub.UCSLintException:
			self.addmsg('0011-11', 'parsing error', filename=fn_control)
			return

		# compare package name
		reChangelogPackage = re.compile('^([a-z0-9.-]+) \((.*?)\) (.*?)\n')
		match = reChangelogPackage.match(content_changelog)
		if match:
			srcpkgname = match.group(1)
		else:
			srcpkgname = None
			self.addmsg('0011-9', 'cannot determine source package name', filename=fn_changelog)

		controlpkgname = parser.source_section.get('Source')
		if not controlpkgname:
			self.addmsg('0011-9', 'cannot determine source package name', filename=fn_control)

		if srcpkgname and controlpkgname:
			if srcpkgname != controlpkgname:
				self.addmsg('0011-2', 'source package name differs in debian/changelog and debian/control', filename=fn_changelog)


		# parse source section of debian/control
		if not parser.source_section.get('Section', '') in ( 'univention' ):
			self.addmsg('0011-3', 'wrong Section entry - should be "univention"', filename=fn_control)

		if not parser.source_section.get('Priority', '') in ( 'optional' ):
			self.addmsg('0011-4', 'wrong Priority entry - should be "optional"', filename=fn_control)

		if not parser.source_section.get('Maintainer', '') in ( 'Univention GmbH <packages@univention.de>' ):
			self.addmsg('0011-5', 'wrong Maintainer entry - should be "Univention GmbH <packages@univention.de>"', filename=fn_control)

		if parser.source_section.get('XS-Python-Version', ''):
			self.addmsg('0011-11', 'XS-Python-Version is not required any longer', filename=fn_control)

		if 'python-central' in parser.source_section.get('Build-Depends', ''):
			self.addmsg('0011-12', 'please use python-support instead of python-central in Build-Depends', filename=fn_control)

		if not 'ucslint' in parser.source_section.get('Build-Depends', ''):
			self.addmsg('0011-13', 'ucslint is missing in Build-Depends', filename=fn_control)
