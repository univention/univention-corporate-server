#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Samba
#  listener module: manage idmap
#
# Copyright 2001-2012 Univention GmbH
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

__package__='' 	# workaround for PEP 366
import listener
import os
import univention.debug

import ldb
from samba.ndr import ndr_pack, ndr_unpack
from samba.dcerpc import security
from samba.idmap import IDmapDB
from samba.auth import system_session
from samba.param import LoadParm

name='samba4-idmap'
description='Update local IDmap entries'
filter='(&(|(objectClass=sambaSamAccount)(objectClass=sambaGroupMapping))(sambaSID=*))'
attributes=['sambaSID', 'univentionSamba4SID', 'uidNumber', 'gidNumber']

### Globals
lp = LoadParm()
lp.load('/etc/samba/smb.conf')

sidAttribute='sambaSID'
if listener.configRegistry.is_false('connector/s4/mapping/sid', False):
	sidAttribute='univentionSamba4SID'


def open_idmap():
	global lp
	listener.setuid(0)
	try:
		idmap = IDmapDB('/var/lib/samba/private/idmap.ldb', session_info=system_session(), lp=lp)
	except ldb.LdbError:
		univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR,
				"%s: /var/lib/samba/private/idmap.ldb could not be opened" % name )
		raise
	finally:
		listener.unsetuid()

	return idmap


def rename_or_modify_idmap_entry(old_sambaSID, new_sambaSID, xidNumber, type_string, idmap=None):
	if not idmap:
		## need to open idmap here in case it has been removed since the module  was loaded
		idmap = open_idmap()

	try:
		res = idmap.search('', ldb.SCOPE_SUBTREE, "(&(objectClass=sidMap)(cn=%s))" % old_sambaSID, attrs = ["objectSid", "type"])
		record = res.msgs[0]

		if record["type"][0] != type_string:
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR,
				"%s: %s entry type %s does not match object type %s" % (name, old_sambaSID, record["type"][0], type_string) )
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR,
				"%s: skipping rename of %s to %s" % (name, old_sambaSID, new_sambaSID) )
			return False

		univention.debug.debug(univention.debug.LISTENER, univention.debug.PROCESS,
			"%s: renaming entry for %s to %s" % (name, old_sambaSID, new_sambaSID) )

		## try a modrdn
		idmap.rename(str(record.dn), "CN=%s" % new_sambaSID)
		## and update related attributes
		msg = ldb.Message()
		msg.dn = ldb.Dn(idmap, "CN=%s" % new_sambaSID)
		msg["cn"] = ldb.MessageElement( [ new_sambaSID ] , ldb.FLAG_MOD_REPLACE, "cn")
		new_objectSid = ndr_pack(security.dom_sid(new_sambaSID))
		msg["objectSid"] = ldb.MessageElement([ new_objectSid ] , ldb.FLAG_MOD_REPLACE, "objectSid")
		idmap.modify(msg)

	except ldb.LdbError, (enum, estr):
		univention.debug.debug(univention.debug.LISTENER, univention.debug.WARN, estr)
		## ok, there is an entry for the target sambaSID, let's remove the old sambaSID and modify the target
		remove_idmap_entry(old_sambaSID, xidNumber, type_string, idmap)
		modify_idmap_entry(new_sambaSID, xidNumber, type_string, idmap)

def modify_idmap_entry(sambaSID, xidNumber, type_string, idmap=None):
	if not idmap:
		## need to open idmap here in case it has been removed since the module  was loaded
		idmap = open_idmap()

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

def add_or_modify_idmap_entry(sambaSID, xidNumber, type_string, idmap=None):
	if not idmap:
		## need to open idmap here in case it has been removed since the module  was loaded
		idmap = open_idmap()

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
		modify_idmap_entry(sambaSID, xidNumber, type_string, idmap)

def remove_idmap_entry(sambaSID, xidNumber, type_string, idmap=None):
	if not idmap:
		## need to open idmap here in case it has been removed since the module  was loaded
		idmap = open_idmap()

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
		try:
			if 'sambaSamAccount' in new['objectClass']:
				xid_attr = 'uidNumber'
				xid_type = 'ID_TYPE_UID'
			elif 'sambaGroupMapping' in new['objectClass']:
				xid_attr = 'gidNumber'
				xid_type = 'ID_TYPE_GID'

			new_xid = new.get(xid_attr, [''] )[0]
			if new_xid:
				new_sambaSID = new.get(sidAttribute, [''])[0]
				old_sambaSID = old.get(sidAttribute, [''])[0]
				if old and old_sambaSID:
					if new_sambaSID != old_sambaSID:
						rename_or_modify_idmap_entry(old_sambaSID, new_sambaSID, new_xid, xid_type)
					old_xid = old.get(xid_attr, [''] )[0]
					if new_xid != old_xid:
						add_or_modify_idmap_entry(new_sambaSID, new_xid, xid_type)
				else:
					add_or_modify_idmap_entry(new_sambaSID, new_xid, xid_type)
		except ldb.LdbError, (enum, estr):
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR,
				"%s: entry for %s could not be updated" % (name, new['sambaSID'][0]) )
	elif old:
		try:
			if 'sambaSamAccount' in old['objectClass']:
				xid_attr = 'uidNumber'
				xid_type = 'ID_TYPE_UID'
			elif 'sambaGroupMapping' in old['objectClass']:
				xid_attr = 'gidNumber'
				xid_type = 'ID_TYPE_GID'
			
			old_xid = old.get(xid_attr, [''] )[0]
			if old_xid:
				remove_idmap_entry(old[sidAttribute][0], old_xid, xid_type)
		except ldb.LdbError, (enum, estr):
			univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR,
				"%s: entry for %s could not be updated" % (name, old[sidAttribute][0]) )


if __name__ == '__main__':
	from optparse import OptionParser
	parser = OptionParser(usage="%prog [-h|--help] [--direct-resync]")
	parser.add_option("--direct-resync", action="store_true", dest="direct_resync", default=False,
		help="Filter the output of univention-ldapsearch through the this module")
	(options, args) = parser.parse_args()

	if not options.direct_resync:
		parser.error("The option --direct-resync is required to run this module directly")
		import sys
		sys.exit(1)

	univention.debug.init("stderr", univention.debug.NO_FLUSH, univention.debug.NO_FUNCTION)
	from univention.config_registry import ConfigRegistry
	ucr = ConfigRegistry()
	ucr.load()
	univention.debug.set_level(univention.debug.LISTENER, int(ucr.get('listener/debug/level', 2)))

	import subprocess
	cmd = ['/usr/bin/univention-ldapsearch', '-xLLL', filter, 'objectClass']
	cmd.extend(attributes)
	p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE)
	(stdout, stderr) = p1.communicate()

	from ldif import LDIFParser
	class ListenerHandler(LDIFParser):
		def __init__(self,input):
			LDIFParser.__init__(self,input)
		def handle(self,dn,entry):
			handler(dn, entry, {})

	import StringIO
	parser=ListenerHandler(StringIO.StringIO(stdout))
	parser.parse()
