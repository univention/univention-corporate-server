# -*- coding: utf-8 -*-

try:
	import univention.ucslint.base as uub
except ImportError:
	import ucslint.base as uub
import re
import os
import tre

class UniventionPackageCheck(uub.UniventionPackageCheckDebian):
	def __init__(self):
		super(UniventionPackageCheck, self).__init__()
		self.name = '0015-Names'

	def getMsgIds(self):
		return { '0015-1': [ uub.RESULT_WARN, 'failed to open file' ],
				 '0015-2': [ uub.RESULT_WARN, 'file contain "univention" incorrectly written' ],
				 }

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """
		pass

	RE_WHITEWORD = re.compile('|'.join("""
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

	RE_WHITELINE = re.compile('|'.join(r"""
        \\[tnr]univention
        -.univention
        [SK]?[0-9][0-9]univention
        univention[0-9]
        univentionr\._baseconfig
        /var/lib/univentions-client-boot/
        """.split()))

	def check(self, path):
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		fz = tre.Fuzzyness(maxerr = 2)
		pt = tre.compile("\<univention\>", tre.EXTENDED | tre.ICASE)

		for fn in uub.FilteredDirWalkGenerator(path):
				fd = open(fn, 'r')
				try:
					for lnr, line in enumerate(fd, start=1):
						origline = line
						if UniventionPackageCheck.RE_WHITELINE.match(line):
							continue
						pos = 0
						while True:
							m = pt.search(line[pos:], fz)
							if m:
								if not UniventionPackageCheck.RE_WHITEWORD.match(m[0]):
									self.debug('%s:%d: found="%s"  origline="%s"' % (fn, lnr, m[0], origline))
									self.addmsg('0015-2', 'univention is incorrectly spelled: %s' % m[0], filename=fn, line=lnr)
								pos += m.groups()[0][1]
							else:
								break
				finally:
					fd.close()
