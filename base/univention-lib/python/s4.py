#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2012-2024 Univention GmbH
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
Univention common Python Library for
common |AD| constants.
"""

# Upstream documentation:
# * https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/understand-security-identifiers
# * https://learn.microsoft.com/en-us/windows/win32/secauthz/well-known-sids
# * https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-dtyp/81d92bba-d22b-4a8c-908a-554ab29148ab
# * https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-pac/55fc19f2-55ba-4251-8a6a-103dd7c66280
well_known_sids = {
    "S-1-0": "Null Authority",
    "S-1-1": "World Authority",
    "S-1-0-0": "Nobody",
    "S-1-1-0": "Everyone",
    "S-1-2": "Local Authority",
    "S-1-2-0": "Local",
    "S-1-2-1": "Console Logon",
    "S-1-3": "Creator Authority",
    "S-1-3-0": "Creator Owner",
    "S-1-3-1": "Creator Group",
    "S-1-3-2": "Creator Owner Server",
    "S-1-3-3": "Creator Group Server",
    "S-1-3-4": "Owner Rights",
    "S-1-4": "Non-unique Authority",
    "S-1-5": "NT Authority",
    "S-1-5-1": "Dialup",
    "S-1-5-2": "Network",
    "S-1-5-3": "Batch",
    "S-1-5-4": "Interactive",
    "S-1-5-6": "Service",
    "S-1-5-7": "Anonymous Logon",
    "S-1-5-8": "Proxy",
    "S-1-5-9": "Enterprise Domain Controllers",
    "S-1-5-10": "Self",
    "S-1-5-11": "Authenticated Users",
    "S-1-5-12": "Restricted",
    "S-1-5-13": "Terminal Server User",
    "S-1-5-14": "Remote Interactive Logon",
    "S-1-5-15": "This Organization",
    "S-1-5-1000": "Other Organization",
    "S-1-5-17": "IUSR",
    "S-1-5-18": "System",
    "S-1-5-19": "Local Service",
    "S-1-5-20": "Network Service",
    # "S-1-5-32": "Builtin",
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
    "S-1-5-32-568": "IIS_IUSRS",
    "S-1-5-32-569": "Cryptographic Operators",
    "S-1-5-32-573": "Event Log Readers",
    "S-1-5-32-574": "Certificate Service DCOM Access",
    "S-1-5-32-575": "RDS Remote Access Servers",
    "S-1-5-32-576": "RDS Endpoint Servers",
    "S-1-5-32-577": "RDS Management Servers",
    "S-1-5-32-578": "Hyper-V Administrators",
    "S-1-5-32-579": "Access Control Assistance Operators",
    "S-1-5-32-580": "Remote Management Users",
    "S-1-5-32-582": "Storage Replica Admins",
    # "S-1-5-33": "Write Restricted Code",
    "S-1-5-64-10": "NTLM Authentication",
    "S-1-5-64-14": "SChannel Authentication",
    "S-1-5-64-21": "Digest Authentication",
    # "S-1-5-65-1": "This Organization Certificate",
    "S-1-5-80": "NT Service",
    "S-1-5-80-0": "All Services",
    "S-1-5-83-0": "Virtual Machines",
    # "S-1-5-84-0-0-0-0-0": "User Mode Drivers",
    # "S-1-5-90-0": "Windows Manager Group",
    # "S-1-15-2-1": "All App Packages",
    # "S-1-16-0": "Untrusted Mandatory Level",
    "S-1-18": "Authentication Authority",
    "S-1-18-1": "Authentication authority asserted identity",
    "S-1-18-2": "Service asserted identity",
    "S-1-18-3": "Fresh Public Key identity",
    "S-1-18-4": "Key trust",
    "S-1-18-5": "MFA key property",
    "S-1-18-6": "Attested key property",
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
