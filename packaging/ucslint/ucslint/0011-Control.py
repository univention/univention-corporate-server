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
		return { '0011-1': [ uub.RESULT_WARN, 'failed to open file' ],
				 '0011-2': [ uub.RESULT_ERROR, 'source package name differs in debian/control an debian/changelog' ],
				 '0011-3': [ uub.RESULT_WARN, 'wrong section - should be "Univention"' ],
				 '0011-4': [ uub.RESULT_WARN, 'wrong priority - should be "optional"' ],
				 '0011-5': [ uub.RESULT_ERROR, 'wrong maintainer - should be "univention GmbH <packages@univention.de>"' ],
				 '0011-6': [ uub.RESULT_ERROR, 'XS-Python-Version without python-central in build-dependencies' ],
				 '0011-7': [ uub.RESULT_ERROR, 'XS-Python-Version without XB-Python-Version in binary package entries' ],
				 '0011-8': [ uub.RESULT_WARN, 'XS-Python-Version should be "2.4"' ],
				 '0011-9': [ uub.RESULT_ERROR, 'cannot determine source package name' ],
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
			self.msg.append( uub.UPCMessage( '0011-1', 'failed to open and read file %s' % fn ) )

		fn = os.path.join(path, 'debian', 'control')
		try:
			content_control = open(fn, 'r').read()
		except:
			self.msg.append( uub.UPCMessage( '0011-1', 'failed to open and read file %s' % fn ) )
			return


		# compare package name
		reChangelogPackage = re.compile('^([a-z0-9-]+) \((.*?)\) (.*?)\n')
		match = reChangelogPackage.match(content_changelog)
		if match:
			srcpkgname = match.group(1)
		else:
			srcpkgname = None
			self.msg.append( uub.UPCMessage( '0011-9', 'cannot determine source package name in debian/changelog' ) )

		reControlPackage = re.compile('^Source: ([a-z0-9-]+)\n')
		match = reControlPackage.match(content_control)
		if match:
			controlpkgname = match.group(1)
		else:
			controlpkgname = None
			self.msg.append( uub.UPCMessage( '0011-9', 'cannot determine source package name in debian/control' ) )

		if srcpkgname and controlpkgname:
			if srcpkgname != controlpkgname:
				self.msg.append( uub.UPCMessage( '0011-2', 'source package name differs in debian/changelog and debian/control' ) )


		# parse source section of debian/control
		source_entries = {}
		for line in content_control.splitlines():
			if line == '':
				break
			key, val = line.split(': ',1)
			source_entries[ key ] = val

		if not source_entries.get('Section', '') in ( 'univention' ):
			self.msg.append( uub.UPCMessage( '0011-3', 'debian/control: wrong Section entry - should be "univention"' ) )

		if not source_entries.get('Priority', '') in ( 'optional' ):
			self.msg.append( uub.UPCMessage( '0011-4', 'debian/control: wrong Priority entry - should be "optional"' ) )

		if not source_entries.get('Maintainer', '') in ( 'Univention GmbH <packages@univention.de>' ):
			self.msg.append( uub.UPCMessage( '0011-5', 'debian/control: wrong Maintainer entry - should be "Univention GmbH <packages@univention.de>"' ) )

		if source_entries.get('XS-Python-Version', ''):
			if not source_entries.get('XS-Python-Version', '') in ( '2.4' ):
				self.msg.append( uub.UPCMessage( '0011-8', 'debian/control: XS-Python-Version should be "2.4"' ) )

			if not 'python-central' in source_entries.get('Build-Depends', ''):
				self.msg.append( uub.UPCMessage( '0011-6', 'debian/control: XS-Python-Version is used but no python-central in Build-Depends' ) )

			for l in content_control.splitlines():
				if l.startswith('XB-Python-Version: '):
					break
			else:
				self.msg.append( uub.UPCMessage( '0011-7', 'debian/control: XS-Python-Version is used without XB-Python-Version in binary section' ) )
