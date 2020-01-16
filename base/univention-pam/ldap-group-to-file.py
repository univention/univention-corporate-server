#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention PAM
#   Dump all ldap groups with members to a single file
#
# Copyright 2011-2019 Univention GmbH
#
# https://www.univention.de/
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
# <https://www.gnu.org/licenses/>.

import optparse
import ldap
import shutil
import string
import sys
import os
import tempfile
import subprocess

import univention.uldap
import univention.lib.locking


def _get_members(lo, g, recursion_list, check_member=False):
	result = []
	for m in g[1].get('uniqueMember', []):
		if m.startswith('uid='):
			# Does the member exist?
			if check_member:
				try:
					res = lo.search(base=m, scope=ldap.SCOPE_BASE, filter='uid=*', attr=['uid'])
					if len(res) < 1:
						# Not found
						continue
				except ldap.NO_SUCH_OBJECT:
					continue
			mrdn = ldap.explode_rdn(m)
			mname = string.join(string.split(mrdn[0], '=')[1:], '=')
			result.append(mname)
		elif m.startswith('cn='):
			try:
				members = lo.search(base=m, scope=ldap.SCOPE_BASE, filter='objectClass=*', attr=['uniqueMember', 'gidNumber', 'objectClass', 'cn'])
			except ldap.NO_SUCH_OBJECT:
				# Member not found
				continue

			if len(members) == 1:
				member = members[0]
			elif len(members) > 1:
				# Not possible
				continue
			else:
				# Member not found
				continue
			if 'univentionGroup' in member[1].get('objectClass', []):
				if member[0] not in recursion_list:
					recursion_list.append(g[0])
					result += _get_members(lo, member, recursion_list, check_member)
				else:
					# Recursion !!!
					pass
			else:
				result.append(member[1].get('cn')[0] + '$')
	return result


def _run_hooks(options):
	HOOK_DIR = '/var/lib/ldap-group-to-file-hooks.d'
	if os.path.exists(HOOK_DIR):
		cmd = ['/bin/run-parts', '--verbose', HOOK_DIR]
		with open(os.path.devnull, 'w+') as null:
			if options.verbose:
				p = subprocess.Popen(cmd, stdin=null, shell=False)
			else:
				p = subprocess.Popen(cmd, stdin=null, stdout=null, stderr=null, shell=False)
		_stdout, _stderr = p.communicate()
	elif options.verbose:
		print('%s does not exist' % HOOK_DIR)


def main():
	parser = optparse.OptionParser()
	parser.add_option("--file", dest="file", default='/var/lib/extrausers/group', action="store", help="write result to the given file, default is /var/lib/extrausers/group")
	parser.add_option("--verbose", dest="verbose", default=False, action="store_true", help="verbose output")
	parser.add_option("--check_member", dest="check_member", default=False, action="store_true", help="checks if the member exists")
	(options, args) = parser.parse_args()

	try:
		lo = univention.uldap.getMachineConnection(ldap_master=False, random_server=True)
	except ldap.SERVER_DOWN:
		print("Abort: Can't contact LDAP server.")
		sys.exit(1)

	lock = univention.lib.locking.get_lock('ldap-group-to-file', nonblocking=True)
	try:
		if not lock:
			print('Abort: Process is locked, another instance is already running.')
			sys.exit(2)
		return doit(options, lo)
	finally:
		if lock:
			univention.lib.locking.release_lock(lock)


def doit(options, lo):
	groups = lo.search('objectClass=univentionGroup', attr=['uniqueMember', 'cn', 'gidNumber'])
	if options.verbose:
		print('Found %d ldap groups' % len(groups))

	if len(groups) < 1:
		print('Abort: Did not found any LDAP group.')
		sys.exit(1)

	# Write to a temporary file
	(fdtemp, fdname) = tempfile.mkstemp()
	fd = os.fdopen(fdtemp, 'w')

	for group in groups:
		rdn = ldap.explode_rdn(group[0])
		groupname = string.join(string.split(rdn[0], '=')[1:], '=')
		members = _get_members(lo, group, [], options.check_member)
		# The list(set(members)) call removes all duplicates from the group members
		fd.write('%s:*:%s:%s\n' % (groupname, group[1].get('gidNumber', [''])[0], string.join(list(set(members)), ',')))
	fd.close()

	os.chmod(fdname, 0o644)

	# Move the file
	shutil.move(fdname, options.file)
	if options.verbose:
		print('The file %s was created.' % options.file)

	_run_hooks(options)

	sys.exit(0)


if __name__ == '__main__':
	main()
