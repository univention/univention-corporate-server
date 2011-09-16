#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention S4 Connector
#  sid sync
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


import ldap
import univention.debug2 as ud
import univention.s4connector.s4

def sid_to_s4(s4connector, key, object):
	ud.debug(ud.LDAP, ud.INFO, "sid_to_s4 object: %s" % object)
	# object dn was already mapped to the s4 DN:
	s4_dn = object['dn']
	modlist = []
	
	# search the ucs object via 
	if not object['attributes'].has_key('sambaSID'):
		ud.debug(ud.LDAP, ud.INFO, 'sid_to_s4: UCS object does not have a sambaSID')
		return


	sambaSID = object['attributes']['sambaSID']
	# get the ad sid
	(s4_dn, s4_attributes) = s4connector.lo_s4.lo.search_s(s4_dn, ldap.SCOPE_BASE, '(objectSid=*)', ['objectSid'] )[0]
	objectSid = s4_attributes.get('objectSid')
	if objectSid:
		decoded_s4_sid = univention.s4connector.s4.decode_sid(objectSid[0])
		if decoded_s4_sid == sambaSID[0]:
			ud.debug(ud.LDAP, ud.INFO, 'sid_to_s4: objectSID and sambaSID are equal')
			return

		# change objectSID
		# objectSid modification for an AD object seems to be not possible:
		#	http://serverfault.com/questions/53717/how-can-i-change-the-sid-of-a-user-account-in-the-active-directory
		#	http://technet.microsoft.com/en-us/library/cc961998.aspx

		ud.debug(ud.LDAP, ud.INFO, 'sid_to_s4: The objectSid modification in S4 / AD is not allowed.')
		#encoded_sambaSID = univention.s4connector.s4.encode_sid(sambaSID[0])
	 	#modlist.append((ldap.MOD_REPLACE, 'objectSid', encoded_sambaSID))
		#s4connector.lo_s4.lo.modify_ext_s(s4_dn, modlist)

	pass
	
def sid_to_ucs(s4connector, key, s4_object):
	ud.debug(ud.LDAP, ud.INFO, "sid_to_ucs S4: %s" % s4_object)

	# modlist
	ml = []

	# object dn is already mapped to the UCS DN:
	ucs_dn = s4_object['dn']
	ud.debug(ud.LDAP, ud.INFO, "sid_to_s4: UCS DN %s" % ucs_dn)
	
	if s4_object.has_key('attributes') and s4_object['attributes'].has_key('objectSid'):
		ud.debug(ud.LDAP, ud.INFO, 'sid_to_ucs: objectSid found: %s' % s4_object['attributes']['objectSid'])
	else:
		ud.debug(ud.LDAP, ud.INFO, 'sid_to_ucs: objectSid not found in attributes!')
		return

	(ucs_dn, ucs_attributes) = s4connector.lo.lo.search(base=ucs_dn, scope='base', attr=['sambaSID', 'objectClass'])[0]

	if not ucs_dn:
		ud.debug(ud.LDAP, ud.WARN, 'sid_to_ucs: UCS object (%s) not found' % ucs_dn)
		return

	objectSid = s4_object['attributes'].get('objectSid')[0]
	sambaSID = ucs_attributes.get('sambaSID')
	if not sambaSID or objectSid != sambaSID:
		ml.append(('sambaSID', sambaSID, s4_object['attributes'].get('objectSid')[0]))
		if 'user' in s4_object['attributes'].get('objectClass', []):
			if not 'sambaSamAccount' in ucs_attributes.get('objectClass'):
				ml.append(('objectClass',ucs_attributes.get('objectClass'), ucs_attributes.get('objectClass')+['sambaSamAccount']))
		if 'group' in s4_object['attributes'].get('objectClass', []):
			if not 'sambaGroupMapping' in ucs_attributes.get('objectClass'):
				ml.append(('objectClass',ucs_attributes.get('objectClass'), ucs_attributes.get('objectClass')+['sambaGroupMapping']))
	if ml:
		ud.debug(ud.LDAP, ud.INFO, 'sid_to_ucs: modlist = %s' % ml)
		s4connector.lo.lo.modify(ucs_dn, ml)

	return
