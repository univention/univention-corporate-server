#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2013-2022 Univention GmbH
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

"""
Import example user data including profile images to UCS
"""

from __future__ import print_function

import csv
from os.path import dirname, join
from typing import Dict

CWD = dirname(__file__)

LDAPBASE = '$ldap_base'
DOMAIN = '$domainname'

IMPORTFILE = '%s/data.csv' % CWD
IMPORTIMAGEDIR = '%s/images' % CWD
FIELDS = (
	"dn uid firstname lastname displayName gender birthplace birthday age imageref "  # 0-9
	"mail office organisation department employeeType degree manager managerDN "  # 10-17
	"ip18 num19 ip20 num21 home22 phone roomNumber num25 str26 uid27 employeeNumber computerType"  # 18-30
).split()

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
NAGIOS_OPTIONS = ' '.join(
	'--append nagiosServices=cn=%s,cn=nagios,%s' % (iservice, LDAPBASE)
	for iservice in NAGIOS_SERVICES
)


def importRow(row: Dict[str, str]) -> None:
	''' Import one row containing a user definition '''

	row["LDAPBASE"] = LDAPBASE
	row["DOMAIN"] = DOMAIN
	row["DC_OPTIONS"] = DC_OPTIONS
	row["NAGIOS_OPTIONS"] = NAGIOS_OPTIONS
	row["MAIL"] = "%(uid)s@%(DOMAIN)s" % row
	row["IMG"] = '$(base64 "%s")' % join(IMPORTIMAGEDIR, ("%(firstname)s.%(lastname)s.jpg" % row).lower())

	# OU container for user
	print(
		'udm container/ou create --ignore_exist '
		'--position "ou=People,%(LDAPBASE)s" '
		'--set name="%(office)s" '
		'--set userPath="1" '
		'--set groupPath="1"' % row
	)

	# create user
	cmd = [
		'udm', 'users/user', 'create',
		'--position', '"ou=%(office)s,ou=People,%(LDAPBASE)s":',
		'--set', 'username="%(uid)s"',
		'--set', 'description="%(displayName)s - %(employeeType)s %(department)s %(office)s"',
		'--set', 'password="univention"',
		'--set', 'firstname="%(firstname)s"',
		'--set', 'lastname="%(lastname)s"',
		'--set', 'mailPrimaryAddress="%(MAIL)s"',
		'--set', 'organisation="%(organisation)s"',
		'--set', 'birthday="%(birthday)s"',
		'--set', 'jpegPhoto="%(IMG)s"',
		'--set', 'employeeType="%(employeeType)s"',
		'--set', 'phone="%(phone)s"',
		'--set', 'roomNumber="%(roomNumber)s"',
		'--set', 'departmentNumber="%(department)s"',  # mhm, might not 'fit'
		'--set', 'city="%(office)s"',
		'--set', 'employeeNumber="%(employeeNumber)s"',
	]
	print(" ".join(arg % row for arg in cmd))

	for row["GROUP"] in [
		"users office %(office)s" % row,
		"users department %(department)s" % row,
	]:
		print(
			'udm groups/group create --ignore_exist '
			'--position "ou=People,%(LDAPBASE)s" '
			'--set name="%(GROUP)s"' % row
		)
		print(
			'udm groups/group modify '
			'--dn "cn=%(GROUP)s,ou=People,%(LDAPBASE)s" '
			'--append users="uid=%(uid)s,ou=%(office)s,ou=People,%(LDAPBASE)s"' % row
		)

	# container for computer in this department
	print(
		'udm container/ou create --ignore_exist '
		'--position "ou=Departments,%(LDAPBASE)s" '
		'--set name="%(office)s" '
		'--set computerPath="1"' % row
	)

	# DC slave for this department
	print(
		'udm computers/domaincontroller_slave create --ignore_exist '
		'--position "ou=Departments,%(LDAPBASE)s" '
		'--set name="server-%(office)s" '
		'--set network="cn=default,cn=networks,%(LDAPBASE)s" '
		'%(DC_OPTIONS)s %(NAGIOS_OPTIONS)s' % row
	)

	# computer object per user
	print(
		'udm %(computerType)s create  --ignore_exists '
		'--position "ou=%(office)s,ou=Departments,%(LDAPBASE)s" '
		'--set name="workstation%(roomNumber)s" '
		'--set network="cn=default,cn=networks,%(LDAPBASE)s"' % row
	)


HEADER = """\
#!/bin/sh
eval "$(ucr shell)"
udm container/ou create --ignore_exists \
	--set name=People --set description="Employees of this company" --set groupPath="1"
udm container/ou create --ignore_exists \
	--set name=Departments --set description="Resources of this company organized by department"
udm mail/domain create --ignore_exists \
	--position="cn=domain,cn=mail,%(LDAPBASE)s" --set name="%(DOMAIN)s"
udm computers/domaincontroller_backup create --ignore_exist \
	--position "cn=dc,cn=computers,%(LDAPBASE)s" \
	--set name="dcbackup" \
	--set network="cn=default,cn=networks,%(LDAPBASE)s" %(DC_OPTIONS)s %(NAGIOS_OPTIONS)s
"""


def main() -> None:
	print(HEADER % globals())

	with open(IMPORTFILE, 'r', newline='') as importfile:
		importreader = csv.DictReader(importfile, delimiter=',', quotechar='"', fieldnames=FIELDS)
		for row in importreader:
			importRow(row)


if __name__ == "__main__":
	main()
