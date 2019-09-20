#!/usr/bin/python2.7
#
# Copyright 2013-2019 Univention GmbH
#
# sysvol-cleanup.py searches for all GPOs defined in LDAP but not available
# in the local filesystem. With parameter --move the GPOs can be moved
# to a given backup directory.
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

from univention import config_registry
from optparse import OptionParser

import os
import shutil
import sys
import subprocess
import time


def _sysvol_directory(ucr):
	return '/var/lib/samba/sysvol/%s/Policies/' % ucr.get('domainname')


def getLDAPGPOs(options):
	ldapGPOs = []

	p1 = subprocess.Popen(['univention-s4search', 'objectClass=groupPolicyContainer', 'cn'], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	res = p1.communicate()
	if p1.returncode != 0:
		if options.verbose:
			print 'Failed to search via univention-s4search.'
			print res[1]
		return None

	stdout = res[0]

	plainGPOAttribute = []
	currentGPO = None
	for line in stdout.split('\n'):
		# The result looks like this:
		# record 1
		#   dn: CN={31B2F340-016D-11D2-945F-00C04FB984F9},CN=Policies,CN=System,DC=deadlock50,DC=local
		#   cn: {31B2F340-016D-11D2-945F-00C04FB984F9}
		#   ...
		#

		if line.lower().startswith('cn: '):
			currentGPO = line[4:]
		elif line.startswith(' '):
			# if the attributes value uses more than one line
			currentGPO += line.split(' ', 1)[1]
		else:
			if currentGPO:
				plainGPOAttribute.append(currentGPO)
			currentGPO = None

	# Get GPO ID
	for gpo in plainGPOAttribute:

		bracketOpen = gpo.find('{')
		bracketClose = gpo.find('}')

		if bracketOpen < 0 or bracketClose < 0:
			if options.verbose:
				print 'Unknown GPO format: "%s"' % gpo
			continue

		ldapGPOs.append(gpo[bracketOpen:bracketClose + 1])

	return ldapGPOs


def getFileSystemGPOs(sysvolDirectory):
	return filter(lambda x: x.startswith('{'), os.listdir(sysvolDirectory))


if __name__ == '__main__':
	usage = '''%s [options]''' % sys.argv[0]
	parser = OptionParser(usage=usage)

	parser.add_option("--move", action="store", dest="target_directory", help="Move unused GPOs to given directory")
	parser.add_option("--verbose", action="store_true", dest="verbose", default=False, help="Print verbose messages")

	(options, args) = parser.parse_args()

	# load UCR
	ucr = config_registry.ConfigRegistry()
	ucr.load()

	sysvolDirectory = _sysvol_directory(ucr)

	ldapGPOs = getLDAPGPOs(options)

	if not ldapGPOs:
		print 'No LDAP GPOs found. Abort!'
		sys.exit(1)

	fileSystemGPOs = getFileSystemGPOs(sysvolDirectory)

	if options.verbose:
		print 'The following LDAP GPOs were found:'
		for ldapGPO in ldapGPOs:
			print ' - %s' % ldapGPO
		print

		print 'The following file system GPOs were found:'
		for fileSystemGPO in fileSystemGPOs:
			print ' - %s' % fileSystemGPO
		print

	for fileSystemGPO in fileSystemGPOs:

		if fileSystemGPO in ldapGPOs:
			# LDAP GPO is also available in sysvol directory
			continue

		if not options.target_directory:
			# In this case we print only
			print 'Found unused GPO: %s' % fileSystemGPO
			continue

		# Move GPO
		src = os.path.join(sysvolDirectory, fileSystemGPO)
		dest = os.path.join(options.target_directory, '%s_%s' % (fileSystemGPO, time.strftime("%Y%m%d%H%M", time.localtime())))
		if options.verbose:
			print 'Move unused GPO %s to %s' % (fileSystemGPO, dest)
		shutil.move(src, dest)

	sys.exit(0)
