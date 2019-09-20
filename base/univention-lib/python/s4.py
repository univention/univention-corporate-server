#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
"""
Univention common Python Library for
common |AD| constants.
"""
# Copyright 2012-2019 Univention GmbH
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

well_known_sids = {
	"S-1-2": "Local Authority",
	"S-1-2-0": "Local",
	"S-1-2-1": "Console Logon",
	"S-1-3": "Creator Authority",
	"S-1-3-2": "Creator Owner Server",
	"S-1-3-3": "Creator Group Server",
	"S-1-4": "Non-unique Authority",
	"S-1-5": "NT Authority",
	"S-1-5-1": "Dialup",
	"S-1-5-32-544": "Administrators",
	"S-1-5-32-545": "Users",
	"S-1-5-32-546": "Guests",
	"S-1-5-32-547": "Power Users",
	"S-1-5-32-548": "Account Operators",
	"S-1-5-32-549": "Server Operators",
	"S-1-5-32-550": "Print Operators",
	"S-1-5-32-551": "Backup Operators",
	"S-1-5-32-552": "Replicator",
	"S-1-5-32-554": "Pre-Windows 2000 Compatible Access",
	"S-1-5-32-555": "Remote Desktop Users",
	"S-1-5-32-556": "Network Configuration Operators",
	"S-1-5-32-557": "Incoming Forest Trust Builders",
	"S-1-5-32-558": "Performance Monitor Users",
	"S-1-5-32-559": "Performance Log Users",
	"S-1-5-32-560": "Windows Authorization Access Group",
	"S-1-5-32-561": "Terminal Server License Servers",
	"S-1-5-32-562": "Distributed COM Users",
	"S-1-5-32-569": "Cryptographic Operators",
	"S-1-5-32-573": "Event Log Readers",
	"S-1-5-32-574": "Certificate Service DCOM Access",
	"S-1-5-80-0": "All Services",
	"S-1-5-32-568": "IIS_IUSRS",
}
"""Well known security identifiers."""

well_known_domain_rids = {
	"500": "Administrator",
	"501": "Guest",
	"502": "KRBTGT",
	"512": "Domain Admins",
	"513": "Domain Users",
	"514": "Domain Guests",
	"515": "Domain Computers",
	"516": "Domain Controllers",
	"517": "Cert Publishers",
	"518": "Schema Admins",
	"519": "Enterprise Admins",
	"520": "Group Policy Creator Owners",
	"553": "RAS and IAS Servers",
	# Windows Server 2008
	"498": "Enterprise Read-only Domain Controllers",
	"521": "Read-Only Domain Controllers",
	"571": "Allowed RODC Password Replication Group",
	"572": "Denied RODC Password Replication Group",
	# Windows Server "8"
	"522": "Cloneable Domain Controllers",
}
"""
Mapping of well known relative (security) identifiers to their (English) names.

See :py:data:`rids_for_well_known_security_identifiers` for the reverse mapping.
"""

rids_for_well_known_security_identifiers = {
	# All lowercase for lookup
	"administrator": "500",
	"guest": "501",
	"krbtgt": "502",
	"domain admins": "512",
	"domain users": "513",
	"domain guests": "514",
	"domain computers": "515",
	"domain controllers": "516",
	"cert publishers": "517",
	"schema admins": "518",
	"enterprise admins": "519",
	"group policy creator owners": "520",
	"ras and ias servers": "553",
	# Windows Server 2008
	"enterprise read-only domain controllers": "498",
	"read-only domain controllers": "521",
	"allowed rodc password replication group": "571",
	"denied rodc password replication group": "572",
	# Windows Server "8"
	"cloneable domain controllers": "522",
}
"""
Mapping of lower cases English names to to well known relative (security) identifiers.

See :py:data:`well_known_domain_rids` for the reverse mapping.
"""
