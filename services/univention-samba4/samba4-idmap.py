# -*- coding: utf-8 -*-
#
# Univention Samba
#  listener module: manage idmap
#
# Copyright 2001-2011 Univention GmbH
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

import listener
import os
import univention.debug

import ldb
# from samba.ndr import ndr_pack, ndr_unpack
# from samba.dcerpc import security
from samba.idmap import IDmapDB
from samba.auth import system_session
from samba.param import LoadParm

### Globals
lp = LoadParm()
idmap = None

name='samba4-idmap'
description='Update local IDmap entries'
filter='(&(|(objectClass=sambaSamAccount)(objectClass=sambaGroupMapping))(sambaSID=*))'
atributes=[]

def add_modify_idmap_entry(lp, sambaSID, xidNumber, type_string):
	try:
		idmap_type = {
			'ID_TYPE_UID': idmap.TYPE_UID,
			'ID_TYPE_GID': idmap.TYPE_GID,
			'ID_TYPE_BOTH': idmap.TYPE_BOTH
		}
		idmap.setup_name_mapping(sambaSID, idmap_type[type_string], xidNumber)
		##
		## or directly:
		##
		## idmap.add({"dn": "CN=%s" % sambaSID, "objectClass": "sidMap",
		##		"cn": sambaSID, "objectSid": [ndr_pack(security.dom_sid(sambaSID))],
		##		"xidNumber": [str(xidNumber)], "type": [type_string]})

		univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS,
			"%s: added entry for %s" % (name, sambaSID) )

	except ldb.LdbError, (enum, estr):
		## ok, there is an entry for this sambaSID, let's replace it
		try:
			res = idmap.search('', ldb.SCOPE_SUBTREE, "(&(objectClass=sidMap)(cn=%s))" % sambaSID, attrs = ["objectSid", "xidNumber", "type"])
			record = res.msgs[0]

			msg = ldb.Message()
			msg.dn = ldb.Dn(idmap, str(record.dn))
			if record["type"][0] != type_string:
				msg["type"] = ldb.MessageElement([type_string], ldb.FLAG_MOD_REPLACE, "type")
			if record["xidNumber"][0] != str(xidNumber):
				msg["xidNumber"] = ldb.MessageElement([str(xidNumber)], ldb.FLAG_MOD_REPLACE, "xidNumber")

			if len(msg) != 0:
				# objectSid = ndr_unpack(security.dom_sid, record["objectSid"][0])
				univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS,
					"%s: modifying entry for %s" % (name, sambaSID) )
				if "xidNumber" in msg:
					univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO,
						"%s: changing xidNumber from %s to %s" % (name, record["xidNumber"][0], xidNumber) )
				if "type" in msg:
					univention.debug.debug(univention.debug.LISTENER, univention.debug.INFO,
						"%s: changing type from %s to %s" % (name, record["type"][0], type_string) )

			idmap.modify(msg)

		except ldb.LdbError, (enum, estr):
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, estr)

def remove_idmap_entry(sambaSID, xidNumber, type_string):
	try:
		res = idmap.search('', ldb.SCOPE_SUBTREE, "(&(objectClass=sidMap)(cn=%s))" % sambaSID, attrs = ["objectSid", "xidNumber", "type"])
		record = res.msgs[0]

		univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS,
			"%s: removing entry for %s" % (name, sambaSID) )

		idmap.delete(ldb.Dn(idmap, str(record.dn)))

		if record["xidNumber"][0] != str(xidNumber):
			univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN,
				"%s: removed entry xidNumber %s did not match object xidNumber %s" % (name, record["xidNumber"][0], xidNumber) )
		if record["type"][0] != type_string:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN,
				"%s: removed entry type %s did not match object type %s" % (name, record["type"][0], type_string) )

	except ldb.LdbError, (enum, estr):
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, estr)

def handler(dn, new, old):

	if new:
		if 'uidNumber' in new:
			add_modify_idmap_entry(lp, new['sambaSID'][0], new['uidNumber'][0], 'ID_TYPE_UID')
		elif 'gidNumber' in new:
			add_modify_idmap_entry(lp, new['sambaSID'][0], new['gidNumber'][0], 'ID_TYPE_GID')
	elif old:
		if 'uidNumber' in old:
			remove_idmap_entry(new['sambaSID'][0], new['uidNumber'][0], 'ID_TYPE_UID')
		if 'gidNumber' in old:
			remove_idmap_entry(new['sambaSID'][0], new['gidNumber'][0], 'ID_TYPE_GID')

def initialize():
	global lp, idmap
	lp.load('/etc/samba/smb.conf')

	listener.setuid(0)
	try:
		idmap = IDmapDB('/var/lib/samba/private/idmap.ldb', session_info=system_session(), lp=lp)
	finally:
		listener.unsetuid()

