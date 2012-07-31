# -*- coding: iso-8859-15 -*-

try:
	import univention.ucslint.base as uub
except ImportError:
	import ucslint.base as uub
import re
import os
import copy

# Prüfen, ob #DEBHELPER# in (pre|post)(inst|rm) enthalten ist

class UniventionPackageCheck(uub.UniventionPackageCheckDebian):
	def __init__(self):
		super(UniventionPackageCheck, self).__init__()
		self.name = '0006-CheckPostinst'

	def getMsgIds(self):
		return { '0006-1': [ uub.RESULT_WARN,   'postinst script does not contain string "#DEBHELPER#"' ],
				 '0006-2': [ uub.RESULT_ERROR,  'script contains univention-directory-manager or univention-admin at beginning of a line - please use a join script' ],
				 '0006-3': [ uub.RESULT_WARN,   'script contains univention-directory-manager or univention-admin - please use a join script' ],
				 '0006-4': [ uub.RESULT_WARN,   'script contains "sh -e" in hashbang' ],
				 '0006-5': [ uub.RESULT_WARN,   'script contains "set -e"' ],
				 '0006-6': [ uub.RESULT_ERROR,  'script contains no "exit 0" at end of file' ],
				 }

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """
		pass

	def check(self, path):
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		fnlist_scripts = {}

		#
		# search debian scripts
		#
		for f in os.listdir( os.path.join(path, 'debian') ):
			fn = os.path.join(path, 'debian', f)
			if f.endswith('.preinst') or f.endswith('.postinst') or f.endswith('.prerm') or f.endswith('.postrm') or \
					f in [ 'preinst', 'postinst', 'prerm', 'postrm' ]:
				fnlist_scripts[fn] = { 	'debhelper' : False,
										'udm_calls': 0,
										'unquoted_ucr_shell': 0,
										'udm_in_line': 0,
										'set-e-hashbang': False,
										'set-e-body': 0,
										'endswith-exit-0': False,
										}
				self.debug('found %s' % fn)

		#
		# check scripts
		#
		for fn, checks in fnlist_scripts.items():
			try:
				content = open(fn, 'r').read()
			except IOError:
				content = ''

			if not content:
				continue

			lines = content.splitlines()

			if '#DEBHELPER#' in lines:
				checks['debhelper'] = True

			# look for "set -e" in hashbang
			hashbang = lines[0]
			if '/bin/sh -e' in hashbang or '/bin/bash -e' in hashbang:
				checks['set-e-hashbang'] += 1

			for line in lines:
				line = line.strip()
				if not line or line.startswith('#'):
					continue
				self.debug('line: %s' % line)
				for cmd in [ 'univention-directory-manager ', '/usr/sbin/univention-directory-manager ', 'univention-admin ', '/usr/sbin/univention-admin ' ]:
					if line.startswith( cmd ):
						checks['udm_calls'] += 1
					elif cmd in line:
						checks['udm_in_line'] += 1

				# search for "set -e" in line
				if line.startswith( 'set -e' ):
					checks['set-e-body'] = True
				elif 'set -e' in line:
					checks['set-e-body'] = True

				checks['endswith-exit-0'] = line.endswith('exit 0')

		#
		# create result
		#
		for fn, checks in fnlist_scripts.items():
			if not checks['debhelper']:
				self.addmsg( '0006-1', 'script does not contain #DEBHELPER#', fn )

			if checks['set-e-hashbang']:
				self.addmsg( '0006-4', 'script contains "sh -e" in hashbang', fn )

			if checks['set-e-body']:
				self.addmsg( '0006-5', 'script contains "set -e"', fn )

			if checks['udm_calls'] > 0:
				self.addmsg('0006-2', 'script contains %(udm_calls)d calls of univention-directory-manager or univention-admin - use a join script' % checks, fn)
			if checks['udm_in_line'] > 0:
				self.addmsg('0006-3', 'script may contain %(udm_in_line)d calls of univention-directory-manager or univention-admin - please check and use a join script' % checks, fn)

			if not checks['endswith-exit-0']:
				self.addmsg( '0006-6', 'script contains no "exit 0" at end of file', fn )

