# -*- coding: utf-8 -*-

try:
	import univention.ucslint.base as uub
except:
	import ucslint.base as uub
import re
import os
import time
import tre
import sys

class UniventionPackageCheck(uub.UniventionPackageCheckBase):
	def __init__(self):
		uub.UniventionPackageCheckBase.__init__(self)
		self.name = '0015-Names'

	def getMsgIds(self):
		return { '0015-1': [ uub.RESULT_WARN, 'failed to open file' ],
				 '0015-2': [ uub.RESULT_WARN, 'file contain "univention" incorrectly written' ],
				 }

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """
		pass

	def check(self, path):
		""" the real check """

		if not os.path.isdir( os.path.join(path, 'debian') ):
			print "ERROR: directory %s does not exist!" % path
			return

		whiteword = re.compile('|'.join("""
[0-9][0-9]univention
punivention
fBunivention
invention
[Kk]uhnivention
onvention
unintention
univention
Univention
UNIVENTION
_univention
univention_
""".split()))

		whiteline = re.compile('|'.join("""
\\\\[tnr]univention
-.univention
[SK]?[0-9][0-9]univention
univention[0-9]
univentionr\\._baseconfig
/var/lib/univentions-client-boot/
""".split()))

		fz = tre.Fuzzyness(maxerr = 2)
		pt = tre.compile("\<univention\>", tre.EXTENDED | tre.ICASE)

		for root, dirs, files in os.walk('.'):
			for f in files:
				path = os.path.join(root, f)[2:]
				if not os.path.exists(path):
					continue
				try:
					fd = open(path,'r')
					for lnr, line in enumerate(fd):
						origline = line
						if whiteline.match(line):
							continue
						pos = 0
						while True:
							m = pt.search(line[pos:], fz)
							if m:
								if not whiteword.match(m[0]):
									self.debug('%s:%d: found="%s"  origline="%s"' % (path, lnr+1, m[0], origline))
									self.addmsg('0015-2', 'univention is incorrectly spelled: %s' % m[0], filename=path, line=lnr+1)
								pos += m.groups()[0][1]
							else:
								break
				finally:
					fd.close()
			if 'CVS' in dirs:
				dirs.remove('CVS')
			if '.svn' in dirs:
				dirs.remove('.svn')
			if '.git' in dirs:
				dirs.remove('.git')
