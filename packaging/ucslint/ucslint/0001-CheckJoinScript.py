# -*- coding: iso-8859-15 -*-

try:
	import univention.ucslint.base as uub
except:
	import ucslint.base as uub
import re, os

# Prüfen, ob ein Join-Skript im Paket vorhanden ist
# - Prüfen, ob das Join-Skript in rules installiert wird
# - Prüfen, ob das Join-Skript in postinst aufgerufen wird
# - Prüfen, ob das Join-Skript "VERSION=" enthält
# - Prüfen, ob das Join-Skript " v${VERSION} " enthält
#
# FIXME: Prüfen, ob das Join-Skript den richtigen Dateinamen per grep in .index.txt sucht und mit echo einträgt
# FIXME: Prüfen, ob das Join-Skript im postinst richtig aufgerufen wird:
#           if [ "$server_role" = "domaincontroller_master" ] || [ "$server_role" = "domaincontroller_backup" ]; then
#               /usr/lib/univention-install/38univention-management-console-distribution.inst || true
#           fi
#           ==> mit "|| true" und Abfrage auf DC Master oder DC Backup


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):
	def __init__(self):
		super(UniventionPackageCheck, self).__init__()
		self.name = '0001-CheckJoinScript'

	def getMsgIds(self):
		return { '0001-1': [ uub.RESULT_STYLE, 'the old command "univention-admin" is used' ],
				 '0001-2': [ uub.RESULT_ERROR, '"$@" for passing credentials to univention-directory-manager is missing' ],
				 '0001-3': [ uub.RESULT_WARN,  'join scripts are now versioned - the variable VERSION is not set' ],
				 '0001-4': [ uub.RESULT_WARN,  'join scripts are now versioned - the string " v${VERSION} " within grep/echo is missing' ],
				 '0001-5': [ uub.RESULT_ERROR, 'debian/rules is missing' ],
				 '0001-6': [ uub.RESULT_WARN,  'join script seems not to be installed via debian/rules' ],
				 '0001-7': [ uub.RESULT_WARN,  'join script seems not to be called in any postinst file' ],
				 '0001-8': [ uub.RESULT_WARN,  'join scripts should be called with "|| true" do avoid failing postinst scripts if "set -e" is used' ],
				 '0001-9': [ uub.RESULT_WARN,  'cannot open specified file' ],
				 '0001-10': [ uub.RESULT_ERROR, 'join script contains "eval $(ucr shell)" without proper quoting' ],
				 '0001-11': [ uub.RESULT_ERROR, 'join script contains lines with unquoted $@' ],
				 '0001-12': [ uub.RESULT_ERROR, 'join script contains more than one line with VERSION=  statement' ],
				 '0001-13': [ uub.RESULT_ERROR, 'join script does not include "joinscripthelper.lib"' ],
				 '0001-14': [ uub.RESULT_ERROR, 'join script does not call "joinscript_init"' ],
				 '0001-15': [ uub.RESULT_ERROR, 'join script does not call "joinscript_save_current_version"' ],
				 }

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """
		pass

	def check(self, path):
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		RElineEndsWithTrue = re.compile('\|\|[ \t]+true[ \t]*$')
		RElineContainsSetE = re.compile('\n[\t ]*set -e', re.M)
		REucr_shell = re.compile('eval\s+(`|[$][(])\s*(/usr/sbin/)?(ucr|univention-baseconfig|univention-config-registry)\s+shell\s*[^`)]*[`)]\s*')

		fnlist_joinscripts = {}

		#
		# search join scripts
		#
		for f in os.listdir( path ):
			if len(f) > 2 and f[0:2].isdigit() and f.endswith('.inst'):
				fnlist_joinscripts[f] = False
				self.debug('found %s' % f)

		#
		# check if join scripts use versioning
		#
		for js in fnlist_joinscripts.keys():
			try:
				content = open( os.path.join(path, js), 'r').read()
			except:
				self.addmsg( '0001-9', 'failed to open and read file', fn )
				continue

			lines = content.splitlines()
			cnt = { 'unquoted_ucr_shell' : 0,
					'version': 0,
					'vversion': 0,
					'credential_arg_missing': 0,
					'unquoted_credential_arg': 0,
					'old_cmd_name': 0,
					'joinscripthelper.lib': 0,
					'joinscript_init': 0,
					'joinscript_save_current_version': 0,
					}
			for line in lines:
				if REucr_shell.search(line):
					self.debug('unquoted ucr_shell found')
					cnt['unquoted_ucr_shell'] += 1

				# check for old style joinscript
				if line.startswith( 'VERSION=' ):
					cnt['version'] += 1
				if line.find( ' v${VERSION} ' ) >= 0:
					cnt['vversion'] += 1

				# check for new style joinscript
				if line.strip().startswith('source /usr/share/univention-join/joinscripthelper.lib') or line.strip().startswith('. /usr/share/univention-join/joinscripthelper.lib'):
					cnt['joinscripthelper.lib'] += 1
				if 'joinscript_init' in line:
					cnt['joinscript_init'] += 1
				if 'joinscript_save_current_version' in line:
					cnt['joinscript_save_current_version'] += 1

				# check udm calls
				if 'univention-admin ' in line or 'univention-directory-manager ' in line or 'udm ' in line:
					if not line.lstrip()[0] == '#':
						if 'univention-admin ' in line:
							cnt['old_cmd_name'] += 1
						if not ' $@ ' in line and not ' "$@" ' in line:
							cnt['credential_arg_missing'] += 1
							self.debug('line contains no $@:\n%s' % line)
				if ' $@ ' in line:
					cnt['unquoted_credential_arg'] += 1
					self.debug('line contains unquoted $@:\n%s' % line)

			if cnt['old_cmd_name'] > 0:
				self.addmsg( '0001-1', 'join script contains %d lines using "univention-admin"' % (cnt['old_cmd_name']), js )
			if cnt['credential_arg_missing'] > 0:
				self.addmsg( '0001-2', 'join script contains %s lines with missing "$@"' % (cnt['credential_arg_missing']), js )
			if cnt['unquoted_credential_arg'] > 0:
				self.addmsg( '0001-11', 'join script contains %d lines with unquoted $@' % (cnt['unquoted_credential_arg']), js )

			if cnt['version'] == 0:
				self.addmsg( '0001-3', 'join script does not set VERSION', js )
			if cnt['version'] > 1:
				self.addmsg( '0001-12', 'join script does set VERSION more than once', js )

			if cnt['unquoted_ucr_shell'] > 0:
				self.addmsg( '0001-10', 'join script contains %s lines with unquoted calls of eval $(ucr shell)' % (cnt['unquoted_ucr_shell']), js )

			if not cnt['joinscripthelper.lib']:
				# no usage of joinscripthelper.lib
				if cnt['vversion'] > 0 and cnt['vversion'] < 2:
					self.addmsg( '0001-4', 'join script does not grep for " v${VERSION} "', js )
				elif cnt['vversion'] == 0:
					self.addmsg( '0001-13', 'join script does not use joinscripthelper.lib', js )
			else:
				if not cnt['joinscript_init']:
					self.addmsg( '0001-14', 'join script does not use joinscript_init', js )
				if not cnt['joinscript_save_current_version']:
					self.addmsg( '0001-15', 'join script does not use joinscript_save_current_version', js )

		#
		# check if join scripts are present in debian/rules
		#
		found = {}
		debianpath = os.path.join( path, 'debian' )
		# get all .install files
		fnlist = [ x for x in uub.FilteredDirWalkGenerator( debianpath,	suffixes=['.install'] ).items() ]
		# append debian/rules
		fnlist.append( os.path.join( debianpath, 'rules' ) )

		for fn in fnlist:
			try:
				content = open(fn, 'r').read()
			except:
				self.addmsg( '0001-9', 'failed to open and read file', fn )

			for js in fnlist_joinscripts.keys():
				self.debug('looking for %s in debian/rules' % js)
				if js in content:
					found[js] = found.get(js,0) + 1

		for js in fnlist_joinscripts.keys():
			if found.get(js,0) == 0:
				self.addmsg( '0001-6', 'join script is not mentioned in debian/rules or *.install files', js )

		#
		# check if join scripts are present in debian/*postinst
		#
		for f in os.listdir( os.path.join(path, 'debian') ):
			if ( f.endswith('.postinst') and not f.endswith('.debhelper.postinst') ) or ( f == 'postinst' ):
				fn = os.path.join( path, 'debian', f )
				self.debug('loading %s' % (fn))
				try:
					content = open(fn, 'r').read()
				except:
					self.addmsg( '0001-9', 'failed to open and read file', fn )
					continue

				for js in fnlist_joinscripts.keys():
					self.debug('looking for %s in %s' % (js, fn))
					if js in content:
						fnlist_joinscripts[js] = True
						self.debug('found %s in %s' % (js, fn))

						match = RElineContainsSetE.search(content)
						if match:
							self.debug('found "set -e" in %s' % fn)
							for line in content.splitlines():
								if js in line:
									match = RElineEndsWithTrue.search(line)
									if not match:
										self.addmsg( '0001-8', 'the join script %s is not called with "|| true" but "set -e" is set' % js, fn )


		for js in fnlist_joinscripts.keys():
			if not fnlist_joinscripts[js]:
				self.addmsg( '0001-7', 'Join script %s is not mentioned in debian/*.postinst' % js )

