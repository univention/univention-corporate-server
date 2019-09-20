#!/usr/bin/python2.7
#
# Import example user data including profile images to UCS
#
# Copyright 2013-2019 Univention GmbH
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


import os
import csv
import sys
# from univention.config_registry import ConfigRegistry

# ucr = ConfigRegistry()
# ucr.load()

CWD = os.path.dirname(sys.argv[0])

# LDAPBASE=ucr.get('ldap/base')
LDAPBASE = '"$ldap_base"'
IMPORTFILE = '%s/data.csv' % CWD
IMPORTIMAGEDIR = '%s/images' % CWD
# DOMAIN=ucr.get('domainname')
DOMAIN = '"$domainname"'

NAGIOS_SERVICES = (
	"UNIVENTION_PING",
	"UNIVENTION_DISK_ROOT",
	"UNIVENTION_DNS",
	"UNIVENTION_SWAP",
	"UNIVENTION_LDAP_AUTH",
	"UNIVENTION_NTP",
	"UNIVENTION_SMTP2",
	"UNIVENTION_SSL",
	"UNIVENTION_LOAD",
	"UNIVENTION_REPLICATION",
	"UNIVENTION_NSCD",
	"UNIVENTION_JOINSTATUS",
	"UNIVENTION_CUPS",
)
DC_OPTIONS = '--option kerberos --option samba --option posix --option nagios'
NAGIOS_OPTIONS = ' '.join([
	'--append nagiosServices=cn=%s,cn=nagios,%s' % (iservice, LDAPBASE)
	for iservice in NAGIOS_SERVICES
])


def importRow(row):
	''' Import one row containing a user definition '''
	# dwdn = row[0]
	uid = row[1]
	firstname = row[2]
	lastname = row[3]
	displayName = row[4]
	gender = row[5]
	birthplace = row[6]
	birthday = row[7]
	age = row[8]  # calculated in 2012
	imageref = row[9]  # always broken
	# mail = row[10] # broken in csv
	mail = "%s@%s" % (uid, DOMAIN)
	office = row[11]  # name of a city
	organisation = row[12]
	department = row[13]
	employeeType = row[14]
	degree = row[15]
	manager = row[16]  # LDAP-DN
	phone = row[23]  # partly broken, only phone extension (no complete numbers)
	roomNumber = row[24]
	employeeNumber = row[28]
	computerType = row[29]

	# print "generate %s %s / %s in %s" % (firstname, lastname, mail, office)

	# check if container for user exists
	print 'udm container/ou create --ignore_exist --position "ou=People,%s" --set name="%s" --set userPath="1" --set groupPath="1"' % (LDAPBASE, office)  # create OU for User

	# generate udm call to create user
	userSetMap = [
		('username', uid),
		('description', "%s - %s %s %s" % (displayName, employeeType, department, office)),
		('password', 'univention'),
		('firstname', firstname),
		('lastname', lastname),
		('mailPrimaryAddress', mail),
		('organisation', organisation),
		('birthday', birthday),
		('jpegPhoto', '$(cat %s/%s.%s.jpg|base64)' % (IMPORTIMAGEDIR, firstname.lower(), lastname.lower())),
		('employeeType', employeeType),
		('phone', phone),
		('roomNumber', roomNumber),
		('departmentNumber', department),  # mhm, might not "fit"
		('city', office),
		('employeeNumber', employeeNumber)
	]
	callUser = 'udm users/user create --position "ou=%s,ou=People,%s"' % (office, LDAPBASE)
	for (udmOption, value) in userSetMap:
		callUser = '%s --set "%s"="%s"' % (callUser, udmOption, value)
	print callUser

	groups = ["users office %s" % office, "users office %s" % department]
	for group in groups:
		print 'udm groups/group create --ignore_exist --position "ou=People,%s" --set name="%s"' % (LDAPBASE, group)  # create group
		print 'udm groups/group modify --dn "cn=%s,ou=People,%s" --append users="uid=%s,ou=%s,ou=People,%s"' % (group, LDAPBASE, uid, office, LDAPBASE)

	# check if container for computer in this department exists
	print 'udm container/ou create --ignore_exist --position "ou=Departments,%s" --set name="%s" --set computerPath="1"' % (LDAPBASE, office)

	# check if DC slave for this department exists
	print 'udm computers/domaincontroller_slave create --ignore_exist --position "ou=Departments,%s" --set name="server-%s" --set network="cn=default,cn=networks,%s" %s %s' % (LDAPBASE, office, LDAPBASE, DC_OPTIONS, NAGIOS_OPTIONS)

	# generate computer object per user
	print 'udm %s create  --ignore_exists --position "ou=%s,ou=Departments,%s" --set name="workstation%s" --set network="cn=default,cn=networks,%s"' % (computerType, office, LDAPBASE, roomNumber, LDAPBASE)

# print default commands


print 'eval $(ucr shell)'
print 'udm container/ou create --ignore_exists --set name=People --set description="Employees of this company" --set groupPath="1"'
print 'udm container/ou create --ignore_exists --set name=Departments --set description="Resources of this company organized by department"'
print 'udm mail/domain create --ignore_exists --position="cn=domain,cn=mail,%s" --set name="%s"' % (LDAPBASE, DOMAIN)
print 'udm computers/domaincontroller_backup create --ignore_exist --position "cn=dc,cn=computers,%s" --set name="dcbackup" --set network="cn=default,cn=networks,%s" %s %s' % (LDAPBASE, LDAPBASE, DC_OPTIONS, NAGIOS_OPTIONS)

with open(IMPORTFILE, 'rb') as importfile:
	importreader = csv.reader(importfile, delimiter=',', quotechar='"')
	for row in importreader:
		importRow(row)
