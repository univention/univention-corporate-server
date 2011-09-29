#!/usr/bin/env python

#
# Copyright 2004-2011 Univention GmbH
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

# This script was adjusted from the Tests for ntacls manipulation
# Copyright (C) Matthieu Patou <mat@matws.net> 2009-2010
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""Set NT ACL for sysvol directory"""

from samba.ntacls import setntacl, getntacl, XattrBackendError
from samba.dcerpc import xattr, security
from samba.param import LoadParm
import os, sys
import optparse
import samba.getopt

def test_setntacl(lp, dir):
	## 1. Grant Full File Access (FA) to Domain Admins (DA) : (A;OICI;FA;;;DA)
	##    where FA = 0x1f01ff, see libcli/security/security.h
	## 2. Grant File Read Access (FR) to Domain Users (DU) : (A;OICI;FR;;;DU)
	##    where FR = 0x120089, see libcli/security/security.h
	acl = "O:LAG:DAD:(A;OICI;0x001f01ff;;;DA)(A;OICI;0x00120089;;;DU)"
	ntacl = xattr.NTACL()
	ntacl.version = 1

	## maybe there is a more efficient way to retrive the domain_sid? This takes ages..
	from samba.samdb import SamDB
	samdb = SamDB('/var/lib/samba/private/sam.ldb', lp=lp)

	setntacl(lp, dir, acl, samdb.domain_sid)

def test_getntacl(dir):
	ntacl = xattr.NTACL()
	ntacl.version = 1
	facl = getntacl(lp,dir)
	anysid = security.dom_sid(security.SID_NT_SELF)
	print "getacl:", facl.info.as_sddl(anysid)

parser = optparse.OptionParser("set_sysvol_ntacls.py [options] <directory>")
parser.add_option("-v", "--verbose", action="store_true")
opts, args = parser.parse_args()

sambaopts = samba.getopt.SambaOptions(parser)
lp = sambaopts.get_loadparm()

if len(args) != 1:
	print "Need one directory name"
	sys.exit(1)

test_setntacl(lp, args[0])
if opts.verbose:
	test_getntacl(args[0])
