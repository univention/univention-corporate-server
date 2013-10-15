#!/usr/bin/python2.6
#
# Copyright 2013 Univention GmbH
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

import sys
import univention.admin.allocators
import univention.admin.uldap
from optparse import OptionParser, OptionValueError
from univention.config_registry import ConfigRegistry

from optparse import (OptionParser,BadOptionError,AmbiguousOptionError)

class PassThroughOptionParser(OptionParser):
	"""
	An unknown option pass-through implementation of OptionParser.

	When unknown arguments are encountered, bundle with largs and try again,
	until rargs is depleted.  

	sys.exit(status) will still be called if a known argument is passed
	incorrectly (e.g. missing arguments or bad argument types, etc.)		
	"""
	def _process_args(self, largs, rargs, values):
		while rargs:
			try:
				OptionParser._process_args(self,largs,rargs,values)
			except (BadOptionError,AmbiguousOptionError), e:
				largs.append(e.opt_str)

def create_group_Enterprise_Domain_Controllers(lo):

	position = univention.admin.uldap.position(lo.base)

	sambaSID = "S-1-5-9"
	groupName = "Enterprise Domain Controllers"
	groupDN = "cn=%s,cn=groups,%s" % (groupName, lo.base)

	alloc = []
	try:
		uid = univention.admin.allocators.request(lo, position, 'groupName', value=groupName)
		alloc.append(("groupName",groupName))
	except univention.admin.uexceptions.noLock, e:
		univention.admin.allocators.release(lo, position, 'groupName', groupName)
		print "Group already exists"
		sys.exit(1)

	ldap_filter = "(&(univentionService=Samba 4)(objectClass=univentionDomainController))"
	s4dc_dnlist = lo.searchDn(ldap_filter, lo.base)
	s4dc_uidlist = [ "%s$" % univention.admin.uldap.explodeDn(s4dcdn, 1)[0] for s4dcdn in s4dc_dnlist ]

	gidNumber = univention.admin.allocators.request(lo, position, 'gidNumber')
	alloc.append(("gidNumber",gidNumber))

	ocs = ["top", "posixGroup", "univentionGroup", "sambaGroupMapping", "univentionObject"]
	al = [("objectClass", ocs)]
	al.append(("gidNumber", [gidNumber]))
	al.append(("sambaSID", [sambaSID]))
	al.append(("sambaGroupType", ["5"]))
	al.append(("uniqueMember", s4dc_dnlist))
	al.append(("memberUid", s4dc_uidlist))
	al.append(("univentionObjectType", "groups/group"))
	al.append(("univentionObjectFlag", "hidden"))
	try:
		lo.add(groupDN, al)
	except Exception, err:
		print "Exception:", err
		for i, j in alloc:
			univention.admin.allocators.release(lo, position, i, j)
	for i, j in alloc:
		univention.admin.allocators.confirm(lo, position, i, j)

if __name__ == "__main__":
	parser = PassThroughOptionParser()
	parser.add_option("--binddn", dest="binddn")
	parser.add_option("--bindpwd", dest="bindpw")
	parser.add_option("--bindpwdfile", dest="bindpwdfile")
	opts, args = parser.parse_args()
	
	ucr = ConfigRegistry()
	ucr.load()

	if not opts.binddn:
		try:
			opts.bindpw = open('/etc/ldap.secret').read().rstrip('\n')
			opts.binddn = "cn=admin,%s" % ucr['ldap/base']
		except IOError:
			fatal('Could not read /etc/ldap.secret')

	if opts.bindpwdfile and not opts.bindpw:
		opts.bindpw = open(opts.bindpwdfile, 'r').read().strip()

	try:
		lo = univention.admin.uldap.access(host=ucr['ldap/master'], port=int(ucr.get('ldap/master/port', '7389')), base=ucr['ldap/base'], binddn=opts.binddn, bindpw=opts.bindpw, start_tls=2)
	except Exception, e:
		print "Error during uldap.access: ", str(e)
		sys.exit(1)

	create_group_Enterprise_Domain_Controllers(lo)
