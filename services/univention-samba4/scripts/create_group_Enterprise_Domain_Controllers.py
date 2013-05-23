#!/usr/bin/python2.6
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
	al.append(("sambaGroupType", ["2"]))
	al.append(("uniqueMember", s4dc_dnlist))
	al.append(("memberUid", s4dc_uidlist))
	al.append(("univentionObjectType", "groups/group"))
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

	if opts.bindpwdfile and not opts.bindpw:
		opts.bindpw = open(opts.bindpwdfile, 'r').read().strip()

	try:
		lo = univention.admin.uldap.access(host=ucr['ldap/master'], port=int(ucr.get('ldap/master/port', '7389')), base=ucr['ldap/base'], binddn=opts.binddn, bindpw=opts.bindpw, start_tls=2)
	except Exception, e:
		print "Error during uldap.access: ", str(e)
		sys.exit(1)

	create_group_Enterprise_Domain_Controllers(lo)
