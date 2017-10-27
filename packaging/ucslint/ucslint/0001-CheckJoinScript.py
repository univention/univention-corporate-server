# -*- coding: utf-8 -*-
# pylint: disable=C0301
#
# Copyright (C) 2008-2017 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

try:
	import univention.ucslint.base as uub
except ImportError:
	import ucslint.base as uub
import re
import os


class UniventionPackageCheck(uub.UniventionPackageCheckDebian):

	def __init__(self):
		super(UniventionPackageCheck, self).__init__()
		self.name = '0001-CheckJoinScript'

	def getMsgIds(self):
		return {
			'0001-1': [uub.RESULT_STYLE, 'the old command "univention-admin" is used'],
			'0001-2': [uub.RESULT_ERROR, '"$@" for passing credentials to univention-directory-manager is missing'],
			'0001-3': [uub.RESULT_WARN, 'join scripts are now versioned - the variable VERSION is not set'],
			'0001-4': [uub.RESULT_WARN, 'join scripts are now versioned - the string " v${VERSION} " within grep/echo is missing'],
			'0001-5': [uub.RESULT_ERROR, 'debian/rules is missing'],
			'0001-6': [uub.RESULT_WARN, 'join script seems not to be installed via debian/rules'],
			'0001-7': [uub.RESULT_WARN, 'join script seems not to be called in any postinst file'],
			'0001-8': [uub.RESULT_WARN, 'join scripts should be called with "|| true" do avoid failing postinst scripts if "set -e" is used'],
			'0001-9': [uub.RESULT_WARN, 'cannot open specified file'],
			'0001-10': [uub.RESULT_ERROR, 'join script contains "eval $(ucr shell)" without proper quoting'],  # unused, moved to 0017
			'0001-11': [uub.RESULT_ERROR, 'join script contains lines with unquoted $@'],
			'0001-12': [uub.RESULT_ERROR, 'join script contains more than one line with VERSION=  statement'],
			'0001-13': [uub.RESULT_ERROR, 'join script does not include "joinscripthelper.lib"'],
			'0001-14': [uub.RESULT_ERROR, 'join script does not call "joinscript_init"'],
			'0001-15': [uub.RESULT_ERROR, 'join script does not call "joinscript_save_current_version"'],
			'0001-16': [uub.RESULT_ERROR, 'join script is not mentioned in *.install'],
			'0001-17': [uub.RESULT_WARN, 'join script is not called via call_joinscript in *.postinst'],
			'0001-18': [uub.RESULT_ERROR, 'unjoin script is not removed in *.postinst'],
			'0001-19': [uub.RESULT_ERROR, 'unjoin script is not copied in *.prerm'],
			'0001-20': [uub.RESULT_WARN, 'join script is not called via call_unjoinscript in *.postrm'],
			'0001-21': [uub.RESULT_ERROR, 'unjoin script is not mentioned in *.install'],
		}

	def postinit(self, path):
		""" checks to be run before real check or to create precalculated data for several runs. Only called once! """

	RE_LINE_ENDS_WITH_TRUE = re.compile('\|\|[ \t]+true[ \t]*$')  # pylint: disable=W1401
	RE_LINE_CONTAINS_SET_E = re.compile('\n[\t ]*set -e', re.M)
	RE_DH_UMC = re.compile(r'\bdh-umc-module-install\b')
	RE_DH_JOIN = re.compile(r'\bunivention-install-joinscript\b')

	def check_unjoin_script_boilerplate(self, path, filename):
		js_basename = os.path.basename(filename)

		found_install = False
		found_postrm_call_unjoinscript = False
		found_postinst_remove1 = False
		found_postinst_remove2 = False
		found_prerm_copy = False

		# check for automatic installation via univention-install-joinscript
		fn = os.path.join(path, 'debian', 'rules')
		try:
			content = open(fn, 'r').read()
			if 'univention-install-joinscript' in content:
				self.debug('Check install: found univention-install-joinscript in %s - skipping other checks' % (fn,))
				return
		except (IOError, OSError):
			self.addmsg('0001-9', 'failed to open and read file', fn)

		# check for manual installation
		for fn in os.listdir(os.path.join(path, 'debian')):
			fn = os.path.join(path, 'debian', fn)
			# check for entry in *.install
			if fn.endswith('.install'):
				try:
					lines = open(fn, 'r').readlines()
				except IOError:
					self.addmsg('0001-9', 'failed to open and read file', fn)
				else:
					for line in lines:
						items = line.split()
						self.debug('Check install: items=%r' % (items,))
						if len(items) >= 2 and items[0] == js_basename and items[1].strip('/') == 'usr/lib/univention-uninstall':
							found_install = True
							self.debug('Check install: found line in %s' % (fn,))
			# check for removal in postinst
			if fn.endswith('.postinst') or fn.endswith('/postinst'):
				try:
					lines = open(fn, 'r').readlines()
				except IOError:
					self.addmsg('0001-9', 'failed to open and read file', fn)
				else:
					for line in lines:
						items = line.split()
						self.debug('Check removal 1 in postinst: items=%r' % (items,))
						if len(items) >= 1 and items[0].replace('"', '').replace("'", '') == 'uinst=/usr/lib/univention-install/%s' % (js_basename,):
							found_postinst_remove1 = True
							self.debug('Check removal in postinst: found line in %s' % (fn,))
						line = line.strip().replace(' ', '').replace('\t', '')
						self.debug('Check removal 2 in postinst: stripped line=%r' % (line,))
						if line == '[-e"$uinst"]&&rm"$uinst"':
							found_postinst_remove2 = True
							self.debug('Check removal in postinst: found line in %s' % (fn,))

			# check copy in *.prerm
			if fn.endswith('.prerm') or fn.endswith('/prerm'):
				try:
					content = open(fn, 'r').read()
				except IOError:
					self.addmsg('0001-9', 'failed to open and read file', fn)
				else:
					lines = content.replace('\\\n', ' ').splitlines()
					for line in lines:
						items = line.split()
						self.debug('Check copy in prerm: items=%r' % (items,))
						if len(items) >= 3 and items[0] == 'cp' and items[1] == '/usr/lib/univention-uninstall/%s' % (js_basename,) and items[2].rstrip('/') == '/usr/lib/univention-install':
							found_prerm_copy = True
							self.debug('Check copy in prerm: found line in %s' % (fn,))

			# check for call_unjoinscript
			if fn.endswith('.postrm') or fn.endswith('/postrm'):
				try:
					lines = open(fn, 'r').readlines()
				except IOError:
					self.addmsg('0001-9', 'failed to open and read file', fn)
				else:
					for line in lines:
						items = line.split()
						self.debug('Check call_unjoinscript: items=%r' % (items,))
						if len(items) >= 2 and items[0] == 'call_unjoinscript' and items[1] == js_basename:
							found_postrm_call_unjoinscript = True
							self.debug('Check call_unjoinscript: found line in %s' % (fn,))

		if not found_install:
			self.addmsg('0001-21', 'Unjoinscript %s is not mentioned in debian/*.install' % (js_basename,), js_basename)
		if not(found_postinst_remove1 and found_postinst_remove2):
			self.addmsg('0001-18', 'Unjoinscript %s is not removed in debian/*.postinst' % (js_basename,), js_basename)
		if not found_prerm_copy:
			self.addmsg('0001-19', 'Unjoinscript %s is not copied in debian/*.prerm' % (js_basename,), js_basename)
		if not found_postrm_call_unjoinscript:
			self.addmsg('0001-20', 'Unjoinscript %s is not called via call_unjoinscript() in debian/*.postrm' % (js_basename,), js_basename)

	def check_join_script_boilerplate(self, path, filename):
		js_basename = os.path.basename(filename)

		found_install = False
		found_call_joinscript = False

		# check for automatic installation via univention-install-joinscript
		fn = os.path.join(path, 'debian', 'rules')
		try:
			content = open(fn, 'r').read()
			if 'univention-install-joinscript' in content:
				found_install = True
				self.debug('Check install: found univention-install-joinscript in %s' % (fn,))
		except (IOError, OSError):
			self.addmsg('0001-9', 'failed to open and read file', fn)

		# check for manual installation
		for fn in os.listdir(os.path.join(path, 'debian')):
			fn = os.path.join(path, 'debian', fn)
			# check for entry in *.install
			if fn.endswith('.install') or fn.endswith('/install'):
				try:
					lines = open(fn, 'r').readlines()
				except IOError:
					self.addmsg('0001-9', 'failed to open and read file', fn)
				else:
					for line in lines:
						items = line.split()
						self.debug('Check install: items=%r' % (items,))
						if len(items) >= 2 and items[0] == js_basename and items[1].strip('/') == 'usr/lib/univention-install':
							found_install = True
							self.debug('Check install: found line in %s' % (fn,))
			# check for call_joinscript
			if fn.endswith('.postinst') or fn.endswith('/postinst'):
				try:
					lines = open(fn, 'r').readlines()
				except IOError:
					self.addmsg('0001-9', 'failed to open and read file', fn)
				else:
					for line in lines:
						items = line.split()
						self.debug('Check call_joinscript: items=%r' % (items,))
						if len(items) >= 2 and items[0] == 'call_joinscript' and items[1] == js_basename:
							found_call_joinscript = True
							self.debug('Check call_joinscript: found line in %s' % (fn,))

		if not found_install:
			self.addmsg('0001-16', 'Joinscript %s is not mentioned in debian/*.install (please check debian/rules for dh-umc-module-build or univention-install-joinscript)' % (js_basename,), js_basename)
		if not found_call_joinscript:
			self.addmsg('0001-17', 'Joinscript %s is not called via call_joinscript() in debian/*.postinst' % (js_basename,), js_basename)

	def check_join_script(self, filename):
		"""Check a single join script."""
		try:
			content = open(filename, 'r').read()
		except (OSError, IOError):
			self.addmsg('0001-9', 'failed to open and read file', filename)
			return

		lines = content.splitlines()
		cnt = {
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
			line = line.strip()
			if not line or line.startswith('#'):
				continue

			# check for old style joinscript
			if line.startswith('VERSION='):
				cnt['version'] += 1
			if line.find(' v${VERSION} ') >= 0:
				cnt['vversion'] += 1

			# check for new style joinscript
			if line.startswith('source /usr/share/univention-join/joinscripthelper.lib') or line.startswith('. /usr/share/univention-join/joinscripthelper.lib'):
				cnt['joinscripthelper.lib'] += 1
			if 'joinscript_init' in line:
				cnt['joinscript_init'] += 1
			if 'joinscript_save_current_version' in line:
				cnt['joinscript_save_current_version'] += 1

			# check udm calls
			if 'univention-admin ' in line or 'univention-directory-manager ' in line or 'udm ' in line:
				if 'univention-admin ' in line:
					cnt['old_cmd_name'] += 1
				if ' $@ ' not in line and ' "$@" ' not in line and ' "${@}" ' not in line:
					cnt['credential_arg_missing'] += 1
					self.debug('line contains no $@:\n%s' % line)
			if ' $@ ' in line or ' ${@} ' in line:
				cnt['unquoted_credential_arg'] += 1
				self.debug('line contains unquoted $@:\n%s' % line)

		if cnt['old_cmd_name'] > 0:
			self.addmsg('0001-1', 'join script contains %d lines using "univention-admin"' % (cnt['old_cmd_name']), filename)
		if cnt['credential_arg_missing'] > 0:
			self.addmsg('0001-2', 'join script contains %s lines with missing "$@"' % (cnt['credential_arg_missing']), filename)
		if cnt['unquoted_credential_arg'] > 0:
			self.addmsg('0001-11', 'join script contains %d lines with unquoted $@' % (cnt['unquoted_credential_arg']), filename)

		if cnt['version'] == 0:
			self.addmsg('0001-3', 'join script does not set VERSION', filename)
		if cnt['version'] > 1:
			self.addmsg('0001-12', 'join script does set VERSION more than once', filename)

		if not cnt['joinscripthelper.lib']:
			# no usage of joinscripthelper.lib
			if cnt['vversion'] > 0 and cnt['vversion'] < 2:
				self.addmsg('0001-4', 'join script does not grep for " v${VERSION} "', filename)
			elif cnt['vversion'] == 0:
				self.addmsg('0001-13', 'join script does not use joinscripthelper.lib', filename)
		else:
			if not cnt['joinscript_init']:
				self.addmsg('0001-14', 'join script does not use joinscript_init', filename)
			if not cnt['joinscript_save_current_version']:
				self.addmsg('0001-15', 'join script does not use joinscript_save_current_version', filename)

	def check(self, path):
		""" the real check """
		super(UniventionPackageCheck, self).check(path)

		fnlist_joinscripts = {}  # { path_to_joinscript(str) --> joinscript_is_installed(bool) }
		fnlist_unjoinscripts = {}  # { path_to_unjoinscript(str) --> unjoinscript_is_installed(bool) }

		#
		# search join scripts
		#
		for f in os.listdir(path):
			if f.endswith('.inst') and f[0:2].isdigit():
				fn = os.path.join(path, f)
				fnlist_joinscripts[fn] = False
				self.debug('found %s' % fn)
			if f.endswith('.uinst') and f[0:2].isdigit():
				fn = os.path.join(path, f)
				fnlist_unjoinscripts[fn] = False
				self.debug('found %s' % fn)

		#
		# check if join scripts use versioning
		#
		for js in fnlist_joinscripts:
			self.check_join_script(js)
			self.check_join_script_boilerplate(path, js)
		for js in fnlist_unjoinscripts:
			self.check_unjoin_script_boilerplate(path, js)

		#
		# check if join scripts are present in debian/rules || debian/*.install
		#
		found = {}
		debianpath = os.path.join(path, 'debian')
		# get all .install files
		fnlist = list(uub.FilteredDirWalkGenerator(debianpath, suffixes=['.install']))
		# append debian/rules
		fn_rules = os.path.join(path, 'debian', 'rules')
		fnlist.append(fn_rules)

		# Look for dh-umc-modules-install
		try:
			content = open(fn_rules, 'r').read()
		except IOError:
			self.addmsg('0001-9', 'failed to open and read file', fn_rules)
		else:
			if UniventionPackageCheck.RE_DH_JOIN.search(content):
				self.debug('Detected use of univention-install-joinscript')
				try:
					fn_control = os.path.join(path, 'debian', 'control')
					parser = uub.ParserDebianControl(fn_control)
				except uub.UCSLintException:
					self.debug('Errors in debian/control. Skipping here')
				else:
					for binary_package in parser.binary_sections:
						package = binary_package.get('Package')
						for js in fnlist_joinscripts:
							if re.match(r'^\./\d\d%s.inst$' % re.escape(package), js):
								self.debug('univention-install-joinscript will take care of %s' % js)
								fnlist_joinscripts[js] = True
								found[js] = found.get(js, 0) + 1
			if UniventionPackageCheck.RE_DH_UMC.search(content):
				self.debug('Detected use of dh-umc-module-install')
				for fn in uub.FilteredDirWalkGenerator(debianpath, suffixes=['.umc-modules']):
					package = os.path.basename(fn)[:-len('.umc-modules')]
					inst = '%s.inst' % (package,)
					for js in fnlist_joinscripts:
						if js.endswith(inst):
							self.debug('%s installed by dh-umc-module-install' % (js,))
							found[js] = found.get(js, 0) + 1
							fnlist_joinscripts[js] = True

		for fn in fnlist:
			try:
				content = open(fn, 'r').read()
			except IOError:
				self.addmsg('0001-9', 'failed to open and read file', fn)

			for js in fnlist_joinscripts:
				name = os.path.basename(js)
				self.debug('looking for %s in %s' % (name, fn))
				if name in content:
					self.debug('found %s in %s' % (name, fn))
					found[js] = found.get(js, 0) + 1

		for js in fnlist_joinscripts:
			if found.get(js, 0) == 0:
				self.addmsg('0001-6', 'join script is not mentioned in debian/rules or *.install files', js)

		#
		# check if join scripts are present in debian/*postinst
		#
		for f in os.listdir(os.path.join(path, 'debian')):
			if (f.endswith('.postinst') and not f.endswith('.debhelper.postinst')) or (f == 'postinst'):
				fn = os.path.join(path, 'debian', f)
				self.debug('loading %s' % (fn))
				try:
					content = open(fn, 'r').read()
				except IOError:
					self.addmsg('0001-9', 'failed to open and read file', fn)
					continue

				for js in fnlist_joinscripts:
					name = os.path.basename(js)
					self.debug('looking for %s in %s' % (name, fn))
					if name in content:
						fnlist_joinscripts[js] = True
						self.debug('found %s in %s' % (name, fn))

						match = UniventionPackageCheck.RE_LINE_CONTAINS_SET_E.search(content)
						if match:
							self.debug('found "set -e" in %s' % fn)
							for line in content.splitlines():
								if name in line:
									match = UniventionPackageCheck.RE_LINE_ENDS_WITH_TRUE.search(line)
									if not match:
										self.addmsg('0001-8', 'the join script %s is not called with "|| true" but "set -e" is set' % (name,), fn)

		for js, found in fnlist_joinscripts.items():
			if not found:
				self.addmsg('0001-7', 'Join script is not mentioned in debian/*.postinst', js)
