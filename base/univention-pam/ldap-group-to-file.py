#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention PAM
#   Dump all ldap groups with members to a single file
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2011-2022 Univention GmbH
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

import argparse
import shutil
import sys
import os
import tempfile
import subprocess

import ldap.dn
import univention.uldap
import univention.lib.locking


def _get_members(lo, groupdn, gattr, recursion_list, check_member=False):
	result = []
	for member_dn in gattr.get('uniqueMember', []):
		member_dn = member_dn.decode('UTF-8')
		if member_dn.startswith('uid='):
			# Does the member exist?
			if check_member:
				try:
					lo.search(base=member_dn, scope='base', filter='uid=*', attr=['uid'], required=True)
				except ldap.NO_SUCH_OBJECT:
					continue
			result.append(ldap.dn.str2dn(member_dn)[0][0][1])
		elif member_dn.startswith('cn='):
			try:
				memberdn, memberattr = lo.search(base=member_dn, scope='base', filter='objectClass=*', attr=['uniqueMember', 'gidNumber', 'objectClass', 'cn'], unique=True, required=True)[0]
			except ldap.NO_SUCH_OBJECT:
				# Member not found
				continue

			if b'univentionGroup' in memberattr.get('objectClass', []):
				if memberdn not in recursion_list:
					recursion_list.append(groupdn)
					result += _get_members(lo, memberdn, memberattr, recursion_list, check_member)
				else:
					# Recursion !!!
					pass
			else:
				result.append(memberattr['cn'][0].decode('UTF-8') + '$')
	return result


def _run_hooks(options):
	HOOK_DIR = '/var/lib/ldap-group-to-file-hooks.d'
	if os.path.exists(HOOK_DIR):
		cmd = ['/bin/run-parts', '--verbose', HOOK_DIR]
		with open(os.path.devnull, 'wb+') as null:
			if options.verbose:
				subprocess.call(cmd, stdin=null)
			else:
				subprocess.call(cmd, stdin=null, stdout=null, stderr=null)
	elif options.verbose:
		print('%s does not exist' % (HOOK_DIR,))


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--file", default='/var/lib/extrausers/group', help="write result to the given file, default is /var/lib/extrausers/group")
	parser.add_argument("--verbose", default=False, action="store_true", help="verbose output")
	parser.add_argument("--check_member", default=False, action="store_true", help="checks if the member exists")
	options = parser.parse_args()

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

	for groupdn, group in groups:
		groupname = ldap.dn.str2dn(groupdn)[0][0][1]
		members = _get_members(lo, groupdn, group, [], options.check_member)
		# The list(set(members)) call removes all duplicates from the group members
		fd.write('%s:*:%s:%s\n' % (groupname, group.get('gidNumber', [b''])[0].decode('ASCII'), ','.join(set(members))))
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
