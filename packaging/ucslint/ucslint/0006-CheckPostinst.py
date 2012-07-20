# -*- coding: iso-8859-15 -*-

try:
	import univention.ucslint.base as uub
except:
	import ucslint.base as uub
import re, os
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
				 '0006-7': [ uub.RESULT_ERROR,  'script contains "eval $(ucr shell)" without proper quoting' ],
				 }

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """
		pass

	def check(self, path):
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		fnlist_scripts = {}
		REucr_shell = re.compile('eval\s+(`|[$][(])\s*(/usr/sbin/)?(ucr|univention-baseconfig|univention-config-registry)\s+shell\s*[^`)]*[`)]\s*')

		#
		# search debian scripts
		#
		for f in os.listdir( os.path.join(path, 'debian') ):
			fn = os.path.join(path, 'debian', f)
			if f.endswith('.preinst') or f.endswith('.postinst') or f.endswith('.prerm') or f.endswith('.postrm') or \
					f in [ 'preinst', 'postinst', 'prerm', 'postrm' ]:
				fnlist_scripts[f] = { 	'debhelper' : False,
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
		for js in fnlist_scripts.keys():
			try:
				content = open(os.path.join(path, 'debian', js), 'r').read()
			except:
				content = ''

			if not content:
				continue

			if '#DEBHELPER#' in content:
				fnlist_scripts[js]['debhelper'] = True

			# look for "set -e" in hashbang
			hashbang = content.splitlines()[0]
			if '/bin/sh -e' in hashbang or '/bin/bash -e' in hashbang:
				fnlist_scripts[js]['set-e-hashbang'] += 1

			for line in content.splitlines():
				line = line.strip()
				self.debug('line: %s' % line)
				for cmd in [ 'univention-directory-manager ', '/usr/sbin/univention-directory-manager ', 'univention-admin ', '/usr/sbin/univention-admin ' ]:
					if line.startswith( cmd ):
						fnlist_scripts[js]['udm_calls'] += 1
					elif cmd in line:
						fnlist_scripts[js]['udm_in_line'] += 1

				if REucr_shell.search(line):
					self.debug('unquoted ucr_shell found')
					fnlist_scripts[js]['unquoted_ucr_shell'] += 1

				# search for "set -e" in line
				if line.startswith( 'set -e' ):
					fnlist_scripts[js]['set-e-body'] = True
				elif 'set -e' in line:
					fnlist_scripts[js]['set-e-body'] = True

			tmpcontent = copy.deepcopy(content)
			tmpcontent = tmpcontent.strip(' \n\r\t')
			if tmpcontent.endswith('exit 0'):
				fnlist_scripts[js]['endswith-exit-0'] = True

		#
		# create result
		#
		for js in fnlist_scripts.keys():
			fn = os.path.join('debian',js)
			if not fnlist_scripts[js]['debhelper']:
				self.addmsg( '0006-1', 'script does not contain #DEBHELPER#', fn )

			if fnlist_scripts[js]['set-e-hashbang']:
				self.addmsg( '0006-4', 'script contains "sh -e" in hashbang', fn )

			if fnlist_scripts[js]['set-e-body']:
				self.addmsg( '0006-5', 'script contains "set -e"', fn )

			if fnlist_scripts[js]['udm_calls'] > 0:
				self.addmsg( '0006-2', 'script contains %d calls of univention-directory-manager or univention-admin - use a join script' % fnlist_scripts[js]['udm_calls'], fn )
			if fnlist_scripts[js]['udm_in_line'] > 0:
				self.addmsg( '0006-3', 'script may contain %d calls of univention-directory-manager or univention-admin - please check and use a join script' % fnlist_scripts[js]['udm_in_line'], fn )

			if not fnlist_scripts[js]['endswith-exit-0']:
				self.addmsg( '0006-6', 'script contains no "exit 0" at end of file', fn )

			if fnlist_scripts[js]['unquoted_ucr_shell'] > 0:
				self.addmsg( '0006-7', 'script contains %d unquoted calls of eval $(ucr shell)' % fnlist_scripts[js]['unquoted_ucr_shell'], fn )
