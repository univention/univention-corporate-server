#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Configuration Registry
#  add and remove nfs shares from the LDAP directory to /etc/fstab
#
# Copyright 2004-2021 Univention GmbH
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

from __future__ import print_function

import argparse
import os
import shlex
import subprocess
import sys

import ldap
from ldap.filter import filter_format

import univention.config_registry
import univention.uldap

try:
	from StringIO import StringIO  # for Python 2
except ImportError:
	from io import StringIO  # for Python 3

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()
verbose = False
simulate = False

ldap_hostdn = configRegistry.get('ldap/hostdn')

MAGIC_LDAP = '#LDAP Entry DN:'


def debug(msg, out=sys.stderr):
	"""Print verbose information 'msg' to 'out'."""
	if verbose:
		print(msg, file=out)


def exit(result, message=None):
	"""Exit with optional error message."""
	script = os.path.basename(sys.argv[0])
	if message:
		print('%s: %s' % (script, message), file=sys.stderr)
	sys.exit(result)


def query_policy(host_dn, server=None, password_file="/etc/machine.secret", verbose=False):
	"""Get NFS shares from LDAP as per policy for dn."""
	nfsmount = set()
	debug('Retrieving policy for %s...\n' % host_dn)
	try:
		p = subprocess.Popen(['univention_policy_result', '-D', ldap_hostdn, '-y', '/etc/machine.secret', '-s', host_dn], shell=False, stdout=subprocess.PIPE)
		stdout, stderr = p.communicate()
	except OSError:
		exit(1, "FAIL: failed to execute `univention_policy_result %s'" % (host_dn,))
	for line in stdout.splitlines():
		line = line.rstrip('\n')
		k, v = line.split('=', 1)
		debug("Retrieved %s=%s\n" % (k, v))
		if k == 'univentionNFSMounts':
			v, = shlex.split(v)
			debug("Found %s\n" % v)
			nfsmount.add(v)
	return nfsmount


def main():
	# parse command line
	description = "Add NFS mount points from LDAP to /etc/fstab and mount them"
	parser = argparse.ArgumentParser(description=description)
	parser.add_argument('--dn', default=configRegistry.get('ldap/hostdn'), help=argparse.SUPPRESS)
	parser.add_argument('-s', '--simulate', action='store_true', help='simulate and show values to be set')
	parser.add_argument('-v', '--verbose', action='store_true', help='print verbose information')
	args = parser.parse_args()

	global simulate, verbose
	simulate = args.simulate
	verbose = args.verbose

	if not args.dn:
		parser.error("ldap/hostdn is not set.")
	debug("Hostdn is %s\n" % args.dn)

	nfsmounts = query_policy(args.dn)

	lo = univention.uldap.getMachineConnection()

	# remove all nfs mounts from the fstab
	debug("Rewriting /etc/fstab...\n")
	fstab_new = "/etc/fstab.new.%d" % (os.getpid(),)
	sources = set()
	mount_points = set()
	try:
		f_old = open('/etc/fstab', 'r')
		if simulate:
			# f_new = os.fdopen(os.dup(sys.stderr.fileno()), "w")
			f_new = StringIO()
		else:
			f_new = open(fstab_new, 'w')
		for line in f_old:
			if MAGIC_LDAP not in line:
				f_new.write(line)
				debug("= %s" % line)
			else:
				debug("- %s" % line)
			if line.startswith('#'):
				continue

			line = line.rstrip('\n')
			fields = line.split(' ')  # source_spec mount_point fs options freq passno

			sp = fields[0]
			sources.add(sp)

			try:
				mp = fields[1]
				if not mp.startswith('#'):
					mount_points.add(mp)
			except IndexError:
				pass

		f_old.close()
	except IOError as e:
		exit(1, e)

	fqdn = "%(hostname)s.%(domainname)s" % configRegistry
	to_mount = set()
	for nfsmount in nfsmounts:
		debug("NFS Mount: %s ..." % nfsmount)
		fields = nfsmount.split(' ')  # dn_univentionShareNFS mount_point
		dn = fields[0]
		if not dn:
			debug('no dn, skipping\n')
			continue

		try:
			result = lo.lo.search_s(
				dn,
				ldap.SCOPE_SUBTREE,
				'objectclass=*',
				attrlist=['univentionShareHost', 'univentionSharePath'])
		except ldap.NO_SUCH_OBJECT:
			continue

		try:
			attributes = result[0][1]
			share_host = attributes['univentionShareHost'][0].decode('ASCII')
			share_path = attributes['univentionSharePath'][0].decode('utf-8')
		except LookupError:
			debug('not found, skipping\n')
			continue

		# skip share if from self
		if share_host == fqdn:
			debug('is self, skipping\n')
			continue

		mp = fields[-1] or share_path
		# skip share if target already in fstab
		if mp in mount_points:
			debug('already mounted on %s, skipping\n' % mp)
			continue

		nfs_path_fqdn = "%s:%s" % (share_host, share_path)
		# skip share if the source is already in the fstab
		if nfs_path_fqdn in sources:
			debug('already mounted from %s, skipping\n' % nfs_path_fqdn)
			continue

		# get the ip of the share_host
		hostname, domain = share_host.split('.', 1)
		result = lo.lo.search_s(configRegistry['ldap/base'], ldap.SCOPE_SUBTREE, filter_format('(&(relativeDomainName=%s)(zoneName=%s))', (hostname, domain)), attrlist=['aRecord'])
		try:
			attributes = result[0][1]
			nfs_path_ip = "%s:%s" % (attributes['aRecord'][0], share_path)
		except LookupError:
			nfs_path_ip = nfs_path_fqdn

		# skip share if the source is already in the fstab
		if nfs_path_ip in sources:
			debug('already mounted from %s, skipping\n' % nfs_path_ip)
			continue

		line = "%s\t%s\tnfs\tdefaults\t0\t0\t%s %s\n" % (nfs_path_ip, mp, MAGIC_LDAP, dn)
		f_new.write(line)
		debug("\n+ %s" % line)
		to_mount.add(mp)

	f_new.close()
	debug('Switching /etc/fstab...\n')
	if not simulate:
		if os.path.isfile(fstab_new) and os.path.getsize(fstab_new) > 0:
			os.rename(fstab_new, '/etc/fstab')

	# Discard already mounted
	fp = open('/etc/mtab', 'r')
	for line in fp:
		line = line.rstrip('\n')
		fields = line.split(' ')  # source_spec mount_point fs options freq passno
		to_mount.discard(fields[1])

	# mount
	for mp in sorted(to_mount):
		if not os.path.exists(mp):
			os.makedirs(mp)
		debug('Mounting %s...\n' % mp)
		if not simulate:
			subprocess.Popen(['mount', mp])


if __name__ == '__main__':
	main()
