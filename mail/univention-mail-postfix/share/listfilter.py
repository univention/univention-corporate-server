#!/usr/bin/python2.6 -u
#
# Univention mail Postfix Policy
#  check allowed email senders for groups and distlist
#
# Copyright 2005-2015 Univention GmbH
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


import univention.uldap
import optparse 
import sys
import re


usage = "help"
parser = optparse.OptionParser(usage=usage)
parser.add_option("-b", "--ldap_base", dest="ldap_base", help="ldap base")
parser.add_option("-s", "--sender", dest="sender", help="sender address (for use with -t)")
parser.add_option("-r", "--recipient", dest="recipient", help="sender address (for use with -t)")
parser.add_option("-t", "--test", dest="test", help="test run", action="store_true", default=False)
options, args = parser.parse_args()

def listfilter(attr):

	sender = attr.get("sender", None)
	recipient = attr.get("recipient", None)
	action = "DUNNO default"
	allowed = {}

	if options.ldap_base and sender and recipient:

		# reuse secret file of univention-mail-cyrus
		ldap = univention.uldap.getMachineConnection(ldap_master=False, secret_file = "/etc/postfix/listfilter.secret")

		userDn = ""
		userGroups = []
		allowedUserDns = []
		allowedGroupDns = []

		# try the ldap stuff, if that fails send email anyway
		try:
			# get dn and groups of sender 
			filter = '(&(|(mailPrimaryAddress=%s)(mailAlternativeAddress=%s)(mail=%s))(objectclass=posixAccount))' % (sender, sender, sender)
			userResult = ldap.search(base=options.ldap_base, filter=filter, attr=["dn"])
			if userResult:
				userDn = userResult[0][0]
				filter = '(uniqueMember=%s)' % userDn
				groupResult = ldap.search(base=options.ldap_base, filter=filter, attr=["dn"])
				if groupResult:
					for i in groupResult:
						userGroups.append(i[0])
		
			# get recipient restriction 
			ldapAttr = ["univentionAllowedEmailGroups", "univentionAllowedEmailUsers"]
			filter = '(&(mailPrimaryAddress=%s)(|(objectclass=univentionMailList)(objectclass=posixGroup)))' % recipient
			result = ldap.search(base=options.ldap_base, filter=filter, attr=ldapAttr)

			if result:
				# get allowed user and group dns
				for g in result[0][1].get("univentionAllowedEmailGroups", []):
					allowedGroupDns.append(g)
				for u in result[0][1].get("univentionAllowedEmailUsers", []):
					allowedUserDns.append(u)

				# check if there are restrictions
				if allowedUserDns or allowedGroupDns:

					# check userdn in univentionAllowedEmailUsers
					if allowedUserDns:
						if userDn:
							if userDn in allowedUserDns:
								return "DUNNO allowed per user dn"

					# check groups
					if allowedGroupDns:
						if userGroups:
							# check user groups in univentionAllowedEmailGroups
							for j in userGroups:
								if j in allowedGroupDns:
									return "DUNNO allowed per group membership"
							# check nested group in univentionAllowedEmailGroups, depth 1!
							for a in allowedGroupDns:
								nested = ldap.getAttr(a, 'uniqueMember')
								for b in userGroups:
									if b in nested:
										return "DUNNO allowed per nested group"

					return "REJECT Access denied for %s to restricted list %s" % (sender, recipient)
				else:
					return "DUNNO no restrictions"
			else:
				return "DUNNO no group found for %s" % recipient
		except Exception, e:
			return "DUNNO search exception %s" % e

	return "DUNNO default"

# main
attr = {}

# testing
if options.test:
	if not options.sender or not options.recipient:
		sys.stderr.write("sender and recipient are required\n")
		parser.print_help()
		sys.exit(1)
	attr["sender"] = options.sender
	attr["recipient"] = options.recipient
	action = listfilter(attr)
	print "action=" + action
else:
	# read from stdin python -u is required for unbufferd streams
	while True:
		data = sys.stdin.readline()
		m = re.match(r'([^=]+)=(.*)\n', data)
		if m:
			attr[m.group(1).strip()] = m.group(2).strip()
	
		elif data == "\n":
			if attr.get("request", None) == "smtpd_access_policy":
				action = listfilter(attr)
				sys.stdout.write("action=%s\n\n" % action)
			else:
				sys.stderr.write("unknown action in %s" % attr)
				sys.exit(1)
			attr = {}
		else:
			sys.exit(1)

