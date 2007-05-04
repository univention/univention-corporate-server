#!/usr/bin/python2.4
#
# Univention Baseconfig
#  add and remove nfs shares from the LDAP directory to /etc/fstab
#
# Copyright (C) 2004, 2005, 2006 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# Binary versions of this file provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import univention_baseconfig
import ldap
import string

baseConfig=univention_baseconfig.baseConfig()
baseConfig.load()

def exit(result, message = None):
	import sys
	script = os.path.basename(sys.argv[0])
	if message:
		print '%s: %s' % (script, message)
	sys.exit(result)

def query_policy(dn):
	nfsmount = []
	policy = 'univention_policy_result'
	pipe = os.popen('%s -s "%s"' % (policy, dn))
	for line in pipe:
		line = line.strip()
		if line.startswith('univentionNFSMounts='):
			nfsmount.append(line.split('=', 1)[1].split('"',2)[1])
	result = pipe.close()
	if result is not None:
		exit(result, "FAIL: failed to execute `%s'" % policy)
	return nfsmount

def main():
	if not baseConfig.has_key( 'ldap/hostdn' ):
		exit( 0 )
	
	nfsmounts = query_policy( baseConfig['ldap/hostdn'] )

	ldap_server = baseConfig['ldap/server/name']

	fqdn = "%s.%s" % (baseConfig['hostname'], baseConfig['domainname'])

	lo = ldap.initialize("ldap://%s" % ldap_server)
	lo.simple_bind_s("","")

	# remove all nfs mounts from the fstab
	os.system('cat /etc/fstab | grep -v "#LDAP Entry DN:" >/etc/fstab.new')

	mount_points = []
	sources = []

	fp = open("/etc/fstab.new", "r")
	lines = fp.readlines()
	fp.close()

	for line in lines:
		sp = line.split(' ')[0]
		if sp == '#':
			continue
		sources.append(sp)
		try:
			mp = line.split(' ')[1]
			if mp != '#':
				mount_points.append(mp)
		except:
			pass

	#if not nfsmounts:
	#	exit( 0 )

	to_mount = []

	for nfsmount in nfsmounts:
		dn = nfsmount.split(' ')[0]
		mp = nfsmount.split(' ')[-1]
		if not dn:
			continue

		result = lo.search_s(dn, ldap.SCOPE_SUBTREE, 'objectclass=*', attrlist=['univentionShareHost', 'univentionSharePath'])
		try:
			attributes = result[0][1]
		except:
			continue

		if attributes.has_key('univentionShareHost'):
			share_host = attributes['univentionShareHost'][0]
		if attributes.has_key('univentionSharePath'):
			share_path = attributes['univentionSharePath'][0]

		if not share_host or not share_path:
			continue

		if not mp:
			mp = share_path

		if share_host == fqdn:
			continue

		nfs_path_fqdn = "%s:%s" % (share_host, share_path)
		nfs_path_ip = "%s:%s" % (share_host, share_path)

		# get the ip of the share_host
		hostname = share_host.split('.',1)[0]
		domain = string.join(share_host.split('.',1)[1:], '.')
		result = lo.search_s(baseConfig['ldap/base'], ldap.SCOPE_SUBTREE, '(&(relativeDomainName=%s)(zoneName=%s))' % (hostname, domain), attrlist=['aRecord'])
		try:
			attributes = result[0][1]
			if attributes.has_key('aRecord'):
				nfs_path_ip = "%s:%s" % (attributes['aRecord'][0], share_path)
		except:
			pass

		# check if the source or target already in the fstab
		if nfs_path_fqdn in sources or nfs_path_ip in sources or mp in mount_points:
			continue

		fp = open("/etc/fstab.new", "a+")
		fp.write("%s\t%s\tnfs\tdefaults\t0\t0\t#LDAP Entry DN: %s\n" % (nfs_path_ip, mp, dn))
		fp.close()

		to_mount.append(mp)

		if not os.path.exists(mp):
			os.system('mkdir -p %s' % mp)

	os.system('mv /etc/fstab.new /etc/fstab')

	already_mounted = []
	fp = open('/etc/mtab')
	lines = fp.readlines()
	for line in lines:
		already_mounted.append(line.split(' ')[1])

	for mp in to_mount:
		if mp not in already_mounted:
			os.system('mount %s &' % mp)

if __name__ == '__main__':
	main()

