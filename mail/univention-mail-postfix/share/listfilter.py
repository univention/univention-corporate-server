#!/usr/bin/python2.7 -u
#
# Univention mail Postfix Policy
#  check allowed email senders for groups and distlist
#
# Copyright 2005-2016 Univention GmbH
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
import traceback
import syslog

syslog.openlog(ident="listfilter", logoption=syslog.LOG_PID, facility=syslog.LOG_MAIL)

usage = "help"
parser = optparse.OptionParser(usage=usage)
parser.add_option("-b", "--ldap_base", dest="ldap_base", help="ldap base")
parser.add_option("-s", "--sender", dest="sender", help="sender address (for use with -t)")
parser.add_option("-r", "--recipient", dest="recipient", help="sender address (for use with -t)")
parser.add_option("-t", "--test", dest="test", help="test run", action="store_true", default=False)
options, args = parser.parse_args()


def listfilter(attrib):

	sender = attrib.get("sender", None)
	recipient = attrib.get("recipient", None)

	if not options.ldap_base:
		return "443 LDAP base not set."
	elif not recipient:
		# We will never get here, because an empty recipient will have been rejected
		# earlier by Postfix with '554 5.5.1 Error: no valid recipients'.
		return "REJECT Access denied for empty recipient."
	else:
		try:
			# reuse secret file of univention-mail-cyrus
			ldap = univention.uldap.getMachineConnection(ldap_master=False, secret_file="/etc/listfilter.secret")

			user_dn = ""
			users_groups = []
			allowed_user_dns = []
			allowed_group_dns = []

			# try the ldap stuff, if that fails send email anyway
			# get recipient restriction
			ldap_attr = ["univentionAllowedEmailGroups", "univentionAllowedEmailUsers"]
			ldap_filter = '(&(mailPrimaryAddress=%s)(|(objectclass=univentionMailList)(objectclass=posixGroup)))' % recipient
			result = ldap.search(base=options.ldap_base, filter=ldap_filter, attr=ldap_attr)

			if result:
				# get allowed user and group dns
				for g in result[0][1].get("univentionAllowedEmailGroups", []):
					allowed_group_dns.append(g)
				for u in result[0][1].get("univentionAllowedEmailUsers", []):
					allowed_user_dns.append(u)

				# check if there are restrictions, check sender first
				if allowed_user_dns or allowed_group_dns:
					if not sender:
						return "REJECT Access denied for empty sender to restricted list %s" % (recipient, )

					# get dn and groups of sender
					ldap_filter = '(&(|(mailPrimaryAddress=%s)(mailAlternativeAddress=%s)(mail=%s))(objectclass=posixAccount))' % (sender, sender, sender)
					user_result = ldap.search(base=options.ldap_base, filter=ldap_filter, attr=["dn"])
					if user_result:
						user_dn = user_result[0][0]
						ldap_filter = '(uniqueMember=%s)' % user_dn
						group_result = ldap.search(base=options.ldap_base, filter=ldap_filter, attr=["dn"])
						if group_result:
							for i in group_result:
								users_groups.append(i[0])

					# check userdn in univentionAllowedEmailUsers
					if allowed_user_dns:
						if user_dn:
							if user_dn in allowed_user_dns:
								return "DUNNO allowed per user dn"

					# check groups
					if allowed_group_dns:
						if users_groups:
							# check user groups in univentionAllowedEmailGroups
							for j in users_groups:
								if j in allowed_group_dns:
									return "DUNNO allowed per group membership"
							# check nested group in univentionAllowedEmailGroups, depth 1!
							for a in allowed_group_dns:
								nested = ldap.getAttr(a, 'uniqueMember')
								for b in users_groups:
									if b in nested:
										return "DUNNO allowed per nested group"

					return "REJECT Access denied for %s to restricted list %s" % (sender, recipient)
				else:
					return "DUNNO no restrictions"
			else:
				return "DUNNO no group found for %s" % recipient
		except Exception as exc:
			syslog.syslog(syslog.LOG_ERR, "Error with attrib={} traceback={}".format(attrib, traceback.format_exc()))
			return "DUNNO search exception %s" % exc

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
