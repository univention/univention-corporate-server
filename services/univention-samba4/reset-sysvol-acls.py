#!/usr/bin/python
#
# Listener module to set reset the sysvol ACLs for a specified GPO
#
# Copyright 2016 Univention GmbH
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
# -*- coding: utf-8 -*-

__package__ = ''  # workaround for PEP 366

import listener

from samba.param import LoadParm
from samba.dcerpc import security, idmap
from samba.ntacls import setntacl, dsacl2fsacl
from samba.samdb import SamDB
from samba.samba3 import param as s3param, passdb
from samba.ndr import ndr_pack, ndr_unpack
from samba import provision
import ldb
import univention.debug as ud

import os
import sys

from samba.auth import system_session
import samba
import optparse
import os.path

name = 'reset-sysvol-acls'
description = 'Reset the sysvol ACLs for a changed GPO'
filter = '(objectClass=msGPOContainer)'

_changed_gpos = []

def reset_sysvol_acl(gpo):
	lp = LoadParm()
	path = lp.private_path("secrets.ldb")
	sysvol = '/var/lib/samba/sysvol'
	samdb = SamDB(session_info=system_session(), lp=lp)

	domain_sid = security.dom_sid(samdb.domain_sid)

	s3conf = s3param.get_context()
	s3conf.load(lp.configfile)
	s3conf.set("passdb backend", "samba_dsdb:%s" % samdb.url)

	s4_passdb = passdb.PDB(s3conf.get("passdb backend"))

	if gpo[0] != '{' and gpo[-1] != '}':
		gpo = '{%s}' % gpo
	policy_path = os.path.join(sysvol, lp.get("realm").lower(), 'Policies', gpo)
	if not os.path.exists(policy_path):
		ud.debug(ud.LISTENER, ud.WARN, 'Policy not found: %s' % policy_path)
		return

	res = samdb.search(base="CN=Policies,CN=System,%s"%(samdb.domain_dn()),
			attrs=["cn", "nTSecurityDescriptor"],
			expression="cn=%s" % (gpo), scope=ldb.SCOPE_ONELEVEL)

	for policy in res:
		acl = ndr_unpack(security.descriptor,
				 str(policy["nTSecurityDescriptor"])).as_sddl()
		ud.debug(ud.LISTENER, ud.PROCESS, 'Setting ACLs for: %s' % policy_path)
		acls = dsacl2fsacl(acl, domain_sid)
		setntacl(lp, policy_path, acls, str(domain_sid),
				 use_ntvfs=False, skip_invalid_chown=True,
				 passdb=s4_passdb, service=provision.SYSVOL_SERVICE)
		for root, dirs, files in os.walk(policy_path, topdown=False):
			for name in files:
				ud.debug(ud.LISTENER, ud.INFO, 'Setting ACLs for: %s' % os.path.join(root, name))
				setntacl(lp, os.path.join(root, name), acls, str(domain_sid),
						 use_ntvfs=False, skip_invalid_chown=True,
						 passdb=s4_passdb, service=provision.SYSVOL_SERVICE)
			for name in dirs:
				ud.debug(ud.LISTENER, ud.INFO, 'Setting ACLs for: %s' % os.path.join(root, name))
				setntacl(lp, os.path.join(root, name), acls, str(domain_sid),
						 use_ntvfs=False, skip_invalid_chown=True,
						 passdb=s4_passdb, service=provision.SYSVOL_SERVICE)

def handler(dn, new, old):
	if listener.configRegistry.is_false('connector/s4/autostart', True):
		return
	# We could check if the nTSecurityDescriptor value has been changed
	# but currently it is not synchronized in every environment.
	global _changed_gpos
	if new and new.get('cn'):
		_changed_gpos.append(new.get('cn')[0])

def postrun():
	global _changed_gpos

	if not _changed_gpos:
		return

	listener.setuid(0)
	try:
		for gpo in _changed_gpos:
			reset_sysvol_acl(gpo)
	finally:
		listener.unsetuid()
	_changed_gpos[:] = []

if __name__ == '__main__':
	parser = optparse.OptionParser("$prog [options] <host>")
	parser.add_option("-g", "--gpo", dest="gpo")
	opts, args = parser.parse_args()
	ud.init('stdout', ud.NO_FLUSH, ud.NO_FUNCTION)
	ud.set_level(ud.LISTENER, ud.PROCESS)
	if not opts.gpo:
		print >> sys.stderr, "Option -g or --gpo needed"
		sys.exit(1)

	reset_sysvol_acl(opts.gpo)
