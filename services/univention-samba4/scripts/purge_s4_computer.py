#!/usr/bin/python2.7
#
# Univention helper script
#  to remove computer with DC objects from Samba 4 and UDM
#
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

from optparse import OptionParser
import sys
import os
from univention import config_registry
import samba
from samba.samdb import SamDB
from samba.auth import system_session
from samba.param import LoadParm
from samba.ndr import ndr_unpack
from samba.dcerpc import misc
import univention.admin.uldap
import univention.admin.uexceptions
import univention.admin.modules
import univention.admin.objects
import univention.admin.config
import traceback
univention.admin.modules.update()

SAMBA_DIR = '/var/lib/samba'
SAMBA_PRIVATE_DIR = os.path.join(SAMBA_DIR, 'private')


def purge_s4_dns_records(ucr, binddn, bindpw, computername, NTDS_objectGUID, Domain_GUID, site_list=None):

	try:
		uldap_access = univention.admin.uldap.access(host=ucr["ldap/master"], base=ucr["ldap/base"], binddn=binddn, bindpw=bindpw, start_tls=2)
	except Exception as e:
		print 'authentication error: %s' % str(e)
		sys.exit(1)

	dns_position = univention.admin.uldap.position(uldap_access.base)
	dns_position.setDn(univention.admin.config.getDefaultContainer(uldap_access, 'dns/'))

	module = univention.admin.modules.get("dns/forward_zone")
	univention.admin.modules.init(uldap_access, dns_position, module)
	filter = univention.admin.filter.expression("zone", ucr["domainname"])

	objs = module.lookup(None, uldap_access, filter, scope="domain", base=dns_position.getDn(), unique=True)
	if not objs:
		print >>sys.stderr, "Lookup of dns/forward_zone %s via UDM failed." % (ucr["domainname"],)
		sys.exit(1)

	zone_obj = objs[0]
	zone_position = univention.admin.uldap.position(uldap_access.base)
	zone_position.setDn(zone_obj.dn)

	if NTDS_objectGUID:
		dns_record = "%s._msdcs" % NTDS_objectGUID
		module = univention.admin.modules.get("dns/alias")
		univention.admin.modules.init(uldap_access, zone_position, module)
		filter = univention.admin.filter.expression("name", dns_record)
		objs = module.lookup(None, uldap_access, filter, superordinate=zone_obj, scope="domain", base=zone_position.getDn(), unique=True)
		if objs:
			print "Removing dns/alias '%s' from Univention Directory Manager" % (dns_record,)
			obj = objs[0]
			try:
				obj.remove()
			except univention.admin.uexceptions.ldapError as e:
				print >>sys.stderr, "Removal of dns/alias %s via UDM failed." % (dns_record,)
				sys.exit(1)

	fqdn = "%s.%s" % (computername, ucr["domainname"])
	module = univention.admin.modules.get("dns/srv_record")
	univention.admin.modules.init(uldap_access, zone_position, module)

	if not site_list:
		site_list = ["Default-First-Site-Name"]

	# SRV Records
	# Kerberos SRV records
	srv_record_name_list = []
	srv_record_name_list.extend(("_kerberos._tcp", "_kerberos._udp", "_kerberos._tcp.dc._msdcs"))
	for sitename in site_list:
		srv_record_name_list.extend(("_kerberos._tcp.%s._sites" % sitename, "_kerberos._tcp.%s._sites.dc._msdcs" % sitename))
	srv_record_name_list.extend(("_kpasswd._tcp", "_kpasswd._udp"))
	# LDAP SRV records
	srv_record_name_list.extend(("_ldap._tcp", "_ldap._tcp.dc._msdcs", "_ldap._tcp.%s.domains._msdcs" % Domain_GUID, "_ldap._tcp.pdc._msdcs"))
	for sitename in site_list:
		srv_record_name_list.extend(("_ldap._tcp.%s._sites" % sitename, "_ldap._tcp.%s._sites.dc._msdcs" % sitename))
	# GC SRV records
	srv_record_name_list.extend(("_gc._tcp", "_ldap._tcp.gc._msdcs"))
	for sitename in site_list:
		srv_record_name_list.extend(("_gc._tcp.%s._sites" % sitename, "_ldap._tcp.%s._sites.gc._msdcs" % sitename))

	for srv_record_name in srv_record_name_list:
		filter = univention.admin.filter.expression("name", srv_record_name)
		objs = module.lookup(None, uldap_access, filter, superordinate=zone_obj, scope="domain", base=zone_position.getDn(), unique=True)
		if objs:
			obj = objs[0]
			target_location = None
			filtered_location_list = []
			for location in obj["location"]:
				if location[3] == "%s." % fqdn:
					target_location = " ".join(location)
				else:
					filtered_location_list.append(location)
			if target_location:
				if filtered_location_list:
					print "Removing location '%s' from dns/srv_record %s via UDM" % (target_location, srv_record_name)
					obj["location"] = filtered_location_list
					try:
						obj.modify()
					except univention.admin.uexceptions.ldapError as e:
						print >>sys.stderr, "Removal of location '%s' from dns/srv_record %s via UDM failed: %s" % (target_location, srv_record_name, e)
						sys.exit(1)
				else:
					print "Removing dns/srv_record %s via UDM" % (srv_record_name,)
					try:
						obj.remove()
					except univention.admin.uexceptions.ldapError as e:
						print >>sys.stderr, "Removal of dns/srv_record %s via UDM failed: %s" % (srv_record_name, e)
						sys.exit(1)

	# We would need to check the IP address before removing gc._msdcs. Probably that's a bad idea anyway..
	# module = univention.admin.modules.get("dns/host_record")
	# univention.admin.modules.init(uldap_access, zone_position, module)
	# dns_record = "gc._msdcs"
	# filter = univention.admin.filter.expression("name", dns_record)
	# objs = module.lookup(None, uldap_access, filter, superordinate=zone_obj, scope="domain", base=zone_position.getDn(), unique=True)
	# if objs:
	# 	print "Removing dns/host_record '%s' from Univention Directory Manager" % (dns_record,)
	# 	obj = objs[0]
	# 	try:
	# 		obj.remove()
	# 	except univention.admin.uexceptions.ldapError, e:
	# 		print >>sys.stderr, "Removal of dns/host_record %s via UDM failed." % (dns_record,)
	# 		sys.exit(1)


def purge_udm_computer(ucr, binddn, bindpw, computername):

	try:
		uldap_access = univention.admin.uldap.access(host=ucr["ldap/master"], base=ucr["ldap/base"], binddn=binddn, bindpw=bindpw, start_tls=2)
	except Exception as e:
		print 'authentication error: %s' % str(e)
		sys.exit(1)
	computer_filter = "(&(objectClass=univentionHost)(uid=%s$))" % computername
	result = uldap_access.search(filter=computer_filter, base=ucr["ldap/base"], scope='sub', attr=['univentionObjectType'], unique=True)
	if result and len(result) > 0 and result[0] and len(result[0]) > 0 and result[0][0]:
		univentionObjectType = result[0][1]['univentionObjectType'][0]
		module = univention.admin.modules.get(univentionObjectType)
		position = univention.admin.uldap.position(ucr["ldap/base"])
		univention.admin.modules.init(uldap_access, position, module)
		filter = univention.admin.filter.expression('name', computername)
		objs = module.lookup(None, uldap_access, filter, scope='domain', base=position.getDn(), unique=True)
		if objs:
			print "Removing Samba 4 computer account '%s' from Univention Directory Manager" % computername
			obj = objs[0]
			try:
				obj.remove()
			except univention.admin.uexceptions.ldapError as e:
				print >>sys.stderr, "Removal of UDM computer account %s via UDM failed (univentionObjectType: %s)." % (computername, univentionObjectType,)
				sys.exit(1)
			if univention.admin.objects.wantsCleanup(obj):
				univention.admin.objects.performCleanup(obj)


def purge_computer_with_DC_objects(ucr, binddn, bindpw, computername):

	lp = LoadParm()
	lp.load('/etc/samba/smb.conf')

	samdb = SamDB(os.path.join(SAMBA_PRIVATE_DIR, "sam.ldb"), session_info=system_session(lp), lp=lp)

	backlink_attribute_list = ["serverReferenceBL", "frsComputerReferenceBL", "msDFSR-ComputerReferenceBL"]
	msgs = samdb.search(base=ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_SUBTREE, expression="(&(objectClass=computer)(sAMAccountName=%s$))" % computername, attrs=backlink_attribute_list)
	if not msgs:
		print "Samba 4 computer account '%s' not found." % (computername,)
		sys.exit(1)

	answer = raw_input("Really remove %s from Samba 4? [y/N]: " % computername)
	if not answer.lower() in ('y', 'yes'):
		print "Ok, stopping as requested.\n"
		sys.exit(2)

	computer_obj = msgs[0]

	# Confirmation check
	answer = raw_input("If you are really sure type YES and hit enter: ")
	if not answer == 'YES':
		print "The answer was not 'YES', confirmation failed.\n"
		sys.exit(1)
	else:
		print "Ok, continuing as requested.\n"

	# Determine the NTDS_objectGUID
	NTDS_objectGUID = None
	if "serverReferenceBL" in computer_obj:
		msgs = samdb.search(base=computer_obj["serverReferenceBL"][0], scope=samba.ldb.SCOPE_SUBTREE, expression="(CN=NTDS Settings)", attrs=["objectGUID"])
		if msgs and "objectGUID" in msgs[0]:
			NTDS_objectGUID = str(ndr_unpack(misc.GUID, msgs[0]["objectGUID"][0]))

	# Determine the Domain_GUID
	msgs = samdb.search(base=ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_BASE, attrs=["objectGUID"])
	if not msgs:
		print "Samba 4 Domain_GUID for base dn '%s' not found." % (ucr["samba4/ldap/base"],)
		sys.exit(1)
	Domain_GUID = str(ndr_unpack(misc.GUID, msgs[0]["objectGUID"][0]))

	# Build current site list
	msgs = samdb.search(base="CN=Configuration,%s" % ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_SUBTREE, expression="(objectClass=site)", attrs=["cn"])
	site_list = [obj["cn"][0] for obj in msgs]

	# Remove Samba 4 DNS records
	purge_s4_dns_records(ucr, binddn, bindpw, computername, NTDS_objectGUID, Domain_GUID, site_list)

	# remove objects from Samba 4 SAM database
	for backlink_attribute in backlink_attribute_list:
		if backlink_attribute in computer_obj:
			backlink_object = computer_obj[backlink_attribute][0]
			try:
				print "Removing %s from SAM database." % (backlink_object,)
				samdb.delete(backlink_object, ["tree_delete:0"])
			except:
				print >>sys.stderr, "Removal of Samba 4 %s objects %s from Samba 4 SAM database failed." % (backlink_attribute, backlink_object,)
				print traceback.format_exc()

	# Now delete the Samba 4 computer account and sub-objects
	# Cannot use tree_delete on isCriticalSystemObject, perform recursive delete like ldbdel code does it:
	msgs = samdb.search(base=computer_obj.dn, scope=samba.ldb.SCOPE_SUBTREE, attrs=["dn"])
	obj_dn_list = [obj.dn for obj in msgs]
	obj_dn_list.sort(key=len)
	obj_dn_list.reverse()
	for obj_dn in obj_dn_list:
		try:
			print "Removing %s from SAM database." % (obj_dn,)
			samdb.delete(obj_dn)
		except:
			print >>sys.stderr, "Removal of Samba 4 computer account object %s from Samba 4 SAM database failed." % (obj_dn,)
			print >>sys.stderr, traceback.format_exc()

	answer = raw_input("Really remove %s from UDM as well? [y/N]: " % computername)
	if not answer.lower() in ('y', 'yes'):
		print "Ok, stopping as requested.\n"
		sys.exit(2)

	# Finally, for consistency remove S4 computer object from UDM
	purge_udm_computer(ucr, binddn, bindpw, computername)


if __name__ == '__main__':

	parser = OptionParser("%prog [options] <AD server name>")
	# parser.add_option("-v", "--verbose", action="store_true")
	parser.add_option("--computername", dest="computername", help="Hostname of the Samba computer account to delete")
	parser.add_option("-U", "--bind_account", dest="bind_account")
	parser.add_option("-P", "--bind_password", dest="bind_password")
	opts, args = parser.parse_args()

	if not opts.computername:
		parser.print_help()
		sys.exit(1)

	ucr = config_registry.ConfigRegistry()
	ucr.load()

	if (opts.bind_account and opts.bind_password):
		machine_secret = ''
		if os.path.exists('/etc/machine.secret'):
			with file('/etc/machine.secret') as f:
				machine_secret = f.read().rstrip('\n')
		else:
			print "/etc/machine.secret missing, maybe the system is not joined yet?"
			sys.exit(1)

		try:
			lo = univention.admin.uldap.access(host=ucr["ldap/server/name"], base=ucr["ldap/base"], binddn=ucr["ldap/hostdn"], bindpw=machine_secret, start_tls=0)
		except Exception as e:
			print 'authentication error: %s' % str(e)
			sys.exit(1)

		user_searchfilter = "(&(|(&(objectClass=posixAccount)(objectClass=shadowAccount))(objectClass=sambaSamAccount))(uid=%s))" % opts.bind_account
		result = lo.searchDn(filter=user_searchfilter, base=ucr["ldap/base"], scope='sub', unique=True)
		if result:
			binddn = result[0]
		else:
			print "Cannot determine DN for bind account %s" % opts.bind_account
			sys.exit(1)
		bindpw = opts.bind_password
	elif os.path.exists('/etc/ldap.secret'):
		binddn = "cn=admin,%s" % ucr["ldap/base"]
		with file('/etc/ldap.secret') as f:
			bindpw = f.read().rstrip('\n')
	else:
		print "On this system the options --bind_account and --bind_password are required."
		parser.print_help()
		sys.exit(1)

	purge_computer_with_DC_objects(ucr, binddn, bindpw, opts.computername)
