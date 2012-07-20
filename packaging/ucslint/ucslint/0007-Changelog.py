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
		self.name = '0007-Changelog'

	def getMsgIds(self):
		return { '0007-1': [ uub.RESULT_WARN, 'failed to open file' ],
				 '0007-2': [ uub.RESULT_WARN, 'changelog does not contain ticket number or bug number' ],
				 }

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """
		pass

	def check(self, path):
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		fn = os.path.join(path, 'debian', 'changelog')
		try:
			content = open(fn, 'r').read()
		except IOError:
			self.addmsg( '0007-1', 'failed to open and read file', fn )
			return

		REchangelog = re.compile('^ -- [^<]+ <[^>]+>', re.M )
		REticket = re.compile('(Bug:? #[0-9]{1,6}|Ticket(#: |:? #)2[0-9]{3}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])(?:1[0-9]{7}|21[0-9]{6}))([^0-9]|$)')

		firstEntry = REchangelog.split( content )[0]
		match = REticket.search(firstEntry)
		if not match:
			self.addmsg( '0007-2', 'latest changelog entry does not contain bug or ticket number', fn)
