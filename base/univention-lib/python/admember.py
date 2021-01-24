#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention Common Python Library
#
# Copyright 2014-2021 Univention GmbH
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

from __future__ import print_function
from __future__ import absolute_import

import ldap
import ldap.sasl
from ldap.filter import filter_format

import os
import sys
import subprocess
import locale
import socket
import tempfile
import ipaddress
import time
from datetime import datetime, timedelta
import pipes

import six
if not six.PY2:
	import ldb
	from samba.dcerpc import nbt, security
	from samba.dcerpc.security import DOMAIN_RID_ADMINS, DOMAIN_RID_ADMINISTRATOR
	from samba.ndr import ndr_unpack
	from samba.net import Net
	from samba.param import LoadParm
else:
	from collections import namedtuple
	DOMAIN_RID_ADMINS = 512
	DOMAIN_RID_ADMINISTRATOR = 500

import univention.config_registry
import univention.uldap
import univention.lib.package_manager
from univention.lib.misc import custom_groupname
import univention.debug as ud
from univention.config_registry.interfaces import Interfaces

import dns.resolver


# Ensure univention debug is initialized
def initialize_debug():
	# Use a little hack to determine if univention.debug has been initialized
	# get_level(..) returns always ud.ERROR if univention.debug is not initialized
	oldLevel = ud.get_level(ud.MODULE)
	if oldLevel == ud.PROCESS:
		ud.set_level(ud.MODULE, ud.DEBUG)
		is_ready = (ud.get_level(ud.MODULE) == ud.DEBUG)
	else:
		ud.set_level(ud.MODULE, ud.PROCESS)
		is_ready = (ud.get_level(ud.MODULE) == ud.PROCESS)
	if not is_ready:
		ud.init('/var/log/univention/join.log', ud.FLUSH, ud.FUNCTION)
		ud.set_level(ud.MODULE, ud.PROCESS)
	else:
		ud.set_level(ud.MODULE, oldLevel)


class failedToSetService(Exception):

	'''ucs_addServiceToLocalhost failed'''


class invalidUCSServerRole(Exception):

	'''Invalid UCS Server Role'''


class failedADConnect(Exception):

	'''Connection to AD Server failed'''


class failedToSetAdministratorPassword(Exception):

	'''Failed to set the password of the UCS Administrator to the AD password'''


class failedToCreateAdministratorAccount(Exception):

	'''Failed to create the administrator account in UCS'''


class sambaSidNotSetForAdministratorAccount(Exception):

	'''sambaSID is not set for Administrator account in UCS'''


class failedToSearchForWellKnownSid(Exception):

	'''failed to search for well known SID'''


class failedToAddAdministratorAccountToDomainAdmins(Exception):

	'''failed to add Administrator account to Domain Admins'''


class domainnameMismatch(Exception):

	'''Domain Names don't match'''


class connectionFailed(Exception):

	'''Connection to AD failed'''


class notDomainAdminInAD(Exception):

	'''User is not member of Domain Admins group in AD'''


class univentionSambaWrongVersion(Exception):

	'''univention-samba candidate has wrong version'''


class timeSyncronizationFailed(Exception):

	'''Time synchronization failed.'''


class manualTimeSyncronizationRequired(timeSyncronizationFailed):

	'''Time difference critical for Kerberos but synchronization aborted.'''


class sambaJoinScriptFailed(Exception):

	'''26univention-samba.inst failed'''


class failedToAddServiceRecordToAD(Exception):

	'''failed to add SRV record in AD'''


class failedToGetUcrVariable(Exception):

	'''failed to get ucr variable'''


def is_localhost_in_admember_mode(ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()
	return ucr.is_true('ad/member', False)


def is_localhost_in_adconnector_mode(ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	if ucr.is_false('ad/member', True) and ucr.get('connector/ad/ldap/host'):
		return True
	return False


def is_domain_in_admember_mode(ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()
	lo = univention.uldap.getMachineConnection()
	res = lo.search(base=ucr.get('ldap/base'), filter='(&(univentionServerRole=master)(univentionService=AD Member))')
	if res:
		return True
	return False


def _get_kerberos_ticket(principal, password, ucr=None):
	ud.debug(ud.MODULE, ud.INFO, "running _get_kerberos_ticket")
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	# We need to remove the target credential cache first,
	# otherwise kinit may use an old ticket and run into "krb5_get_init_creds: Clock skew too great".
	cmd = ("/usr/bin/kdestroy",)
	p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
	stdout, stderr = p1.communicate()
	if p1.returncode != 0:
		ud.debug(ud.MODULE, ud.ERROR, "kdestroy failed:\n%s" % stdout.decode('UTF-8', 'replace'))

	f = tempfile.NamedTemporaryFile('w+', delete=False)
	try:
		os.chmod(f.name, 0o600)
		f.write(password)
		f.close()

		cmd = ("/usr/bin/kinit", "--no-addresses", "--password-file=%s" % (f.name,), principal)
		p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
		stdout, stderr = p1.communicate()
		if p1.returncode != 0:
			msg = "kinit failed:\n%s" % (stdout.decode('UTF-8', 'replace'),)
			ud.debug(ud.MODULE, ud.ERROR, msg)
			raise connectionFailed(msg)
		if stdout:
			ud.debug(ud.MODULE, ud.WARN, "kinit output:\n%s" % stdout.decode('UTF-8', 'replace'))
	finally:
		if os.path.exists(f.name):
			os.unlink(f.name)


def check_connection(ad_domain_info, username, password):
	ud.debug(ud.MODULE, ud.INFO, "running check_connection")

	test_share = '//%s/sysvol' % ad_domain_info["DC IP"]
	cmd = ('smbclient', '-U', '%s%%%s' % (username, password), '-c', 'quit', test_share)
	p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
	stdout, stderr = p1.communicate()
	if p1.returncode != 0:
		raise connectionFailed(stdout.decode('UTF-8', 'replace'))


def flush_nscd_hosts_cache():
	if os.path.exists("/usr/sbin/nscd"):
		cmd = ("/usr/sbin/nscd", "--invalidate=hosts")
		p1 = subprocess.Popen(cmd, close_fds=True)
		p1.communicate()


def decode_sid(value):
	if six.PY3:
		return ndr_unpack(security.dom_sid, value)
	# SID in AD
	#
	#   | Byte 1         | Byte 2-7           | Byte 9-12                | Byte 13-16 |
	#   ----------------------------------------------------------------------------------------------------------------
	#   | Der erste Wert | Gibt die Laenge    | Hier sind jetzt          | siehe 9-12 |
	#   | der SID, also  | des restlichen     | die eiegntlichen         |            |
	#   | der Teil nach  | Strings an, da die | SID Daten.               |            |
	#   | S-             | SID immer relativ  | In einem int Wert        |            |
	#   |                | kurz ist, meistens | sind die Werte           |            |
	#   |                | nur das 2. Byte    | Hexadezimal gespeichert. |            |
	#
	sid = 'S-'
	sid += "%d" % ord(value[0])

	sid_len = ord(value[1])

	sid += "-%d" % ord(value[7])

	for i in range(0, sid_len):
		res = ord(value[8 + (i * 4)]) + (ord(value[9 + (i * 4)]) << 8) + (ord(value[10 + (i * 4)]) << 16) + (ord(value[11 + (i * 4)]) << 24)
		sid += "-%u" % res

	return sid


def check_ad_account(ad_domain_info, username, password, ucr=None):
	'''
	returns True if account is Administrator in AD
	returns False if account is just a member of Domain Admins
	raises exception notDomainAdminInAD if neither criterion is met.
	'''

	ud.debug(ud.MODULE, ud.INFO, "running check_account")
	ad_server_ip = ad_domain_info["DC IP"]
	ad_server_name = ad_domain_info["DC DNS Name"]
	ad_ldap_base = ad_domain_info["LDAP Base"]
	ad_domain = ad_domain_info["Domain"]
	ad_realm = ad_domain.upper()

	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	try:
		time_sync(ad_server_ip)
	except timeSyncronizationFailed as ex:
		ud.debug(ud.MODULE, ud.WARN, "Time sync failed, trying to authenticate anyway. Original exception: %s" % (ex,))

	(previous_dns_ucr_set, previous_dns_ucr_unset) = set_nameserver([ad_server_ip], ucr)
	(previous_krb_ucr_set, previous_krb_ucr_unset) = prepare_kerberos_ucr_settings(realm=ad_realm, ucr=ucr)
	(previous_host_static_ucr_set, previous_host_static_ucr_unset) = prepare_dns_reverse_settings(ad_domain_info, ucr=ucr)

	try:
		principal = "%s@%s" % (username, ad_realm)
		_get_kerberos_ticket(principal, password, ucr)
		auth = ldap.sasl.gssapi("")
	except Exception:
		set_ucr(previous_dns_ucr_set, previous_dns_ucr_unset)
		set_ucr(previous_krb_ucr_set, previous_krb_ucr_unset)
		set_ucr(previous_host_static_ucr_set, previous_host_static_ucr_unset)
		flush_nscd_hosts_cache()
		raise

	# Ok, ready and set for kerberized LDAP lookup
	try:
		subprocess.call(['systemctl', 'stop', 'nscd'])
		lo_ad = univention.uldap.access(host=ad_server_name, port=389, base=ad_ldap_base, binddn=None, bindpw=None, start_tls=0, use_ldaps=False, decode_ignorelist=["objectSid"])
		lo_ad.lo.set_option(ldap.OPT_PROTOCOL_VERSION, ldap.VERSION3)
		lo_ad.lo.set_option(ldap.OPT_REFERRALS, 0)
		lo_ad.lo.sasl_interactive_bind_s("", auth)
	except (ldap.INVALID_CREDENTIALS, ldap.UNWILLING_TO_PERFORM) as exc:
		ud.debug(ud.MODULE, ud.ERROR, str(exc))
		raise connectionFailed(exc)
	finally:
		subprocess.call(['systemctl', 'start', 'nscd'])
		set_ucr(previous_dns_ucr_set, previous_dns_ucr_unset)
		set_ucr(previous_krb_ucr_set, previous_krb_ucr_unset)
		set_ucr(previous_host_static_ucr_set, previous_host_static_ucr_unset)
		flush_nscd_hosts_cache()

	try:
		res = lo_ad.search(scope="base", attr=["objectSid"])
	except ldap.OPERATIONS_ERROR:
		# Try again
		try:
			subprocess.call(['systemctl', 'stop', 'nscd'])
			lo_ad = univention.uldap.access(host=ad_server_name, port=389, base=ad_ldap_base, binddn=None, bindpw=None, start_tls=0, use_ldaps=False, decode_ignorelist=["objectSid"])
			lo_ad.lo.set_option(ldap.OPT_PROTOCOL_VERSION, ldap.VERSION3)
			lo_ad.lo.set_option(ldap.OPT_REFERRALS, 0)
			lo_ad.lo.sasl_interactive_bind_s("", auth)
		except (ldap.INVALID_CREDENTIALS, ldap.UNWILLING_TO_PERFORM) as exc:
			msg = "second attempt: " + str(exc)
			ud.debug(ud.MODULE, ud.ERROR, msg)
			raise connectionFailed(exc)
		finally:
			subprocess.call(['systemctl', 'start', 'nscd'])
			set_ucr(previous_dns_ucr_set, previous_dns_ucr_unset)
			set_ucr(previous_krb_ucr_set, previous_krb_ucr_unset)
			set_ucr(previous_host_static_ucr_set, previous_host_static_ucr_unset)
			flush_nscd_hosts_cache()
		res = lo_ad.search(scope="base", attr=["objectSid"])

	if not res or "objectSid" not in res[0][1]:
		msg = "Determination of AD domain SID failed"
		ud.debug(ud.MODULE, ud.ERROR, msg)
		raise connectionFailed(msg)

	domain_sid = decode_sid(res[0][1]["objectSid"][0])

	res = lo_ad.search(filter=filter_format("(sAMAccountName=%s)", [username]), attr=["objectSid", "primaryGroupID"])
	if not res or "objectSid" not in res[0][1]:
		msg = "Determination user SID failed"
		ud.debug(ud.MODULE, ud.ERROR, msg)
		raise connectionFailed(msg)

	user_sid = decode_sid(res[0][1]["objectSid"][0])
	admin_sid = u"%s-%d" % (domain_sid, security.DOMAIN_RID_ADMINISTRATOR)
	admins_sid = "%s-%d" % (domain_sid, security.DOMAIN_RID_ADMINS)
	if six.PY3:
		admin_sid = security.dom_sid(admin_sid)
		admins_sid = security.dom_sid(admins_sid)

	if user_sid == admin_sid:
		ud.debug(ud.MODULE, ud.PROCESS, "User is default AD Administrator")
		return True

	if int(res[0][1]["primaryGroupID"][0]) == DOMAIN_RID_ADMINS:
		ud.debug(ud.MODULE, ud.PROCESS, "User is primary member of Domain Admins")
		return False

	user_dn = res[0][0]

	res = lo_ad.search(filter=filter_format("(sAMAccountName=%s)", [username]), base=user_dn, scope="base", attr=["tokenGroups"])
	if not res or "tokenGroups" not in res[0][1]:
		msg = "Lookup of AD group memberships for user failed"
		ud.debug(ud.MODULE, ud.ERROR, msg)
		raise connectionFailed(msg)

	if "tokenGroups" not in res[0][1]:
		raise notDomainAdminInAD()

	for group_sid_ndr in res[0][1]["tokenGroups"]:
		group_sid = decode_sid(group_sid_ndr)
		if group_sid == admins_sid:
			return False
	else:
		ud.debug(ud.MODULE, ud.ERROR, "User is not member of Domain Admins")
		raise notDomainAdminInAD()


def _sid_of_ucs_sambadomain(lo=None, ucr=None):
	if not lo:
		lo = univention.uldap.getMachineConnection()

	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	res = lo.search(filter=filter_format("(&(objectclass=sambadomain)(sambaDomainName=%s))", [ucr.get("windows/domain")]), attr=["sambaSID"], unique=True)
	if not res:
		ud.debug(ud.MODULE, ud.ERROR, "No UCS LDAP search result for sambaDomainName=%s" % ucr.get("windows/domain"))
		raise ldap.NO_SUCH_OBJECT({'desc': 'no object'})

	ucs_domain_sid = res[0][1].get("sambaSID", [None])[0]
	if not ucs_domain_sid:
		ud.debug(ud.MODULE, ud.ERROR, "No sambaSID found for sambaDomainName=%s" % ucr.get("windows/domain"))
		raise ldap.NO_SUCH_OBJECT({'desc': 'no object'})

	return ucs_domain_sid.decode('ASCII')


def _dn_of_udm_domain_admins(lo=None, ucr=None):
	if not lo:
		lo = univention.uldap.getMachineConnection()

	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	ucs_domain_sid = _sid_of_ucs_sambadomain(lo, ucr)
	domain_admins_sid = "%s-%d" % (ucs_domain_sid, DOMAIN_RID_ADMINS)
	res = lo.searchDn(filter=filter_format("(sambaSID=%s)", [domain_admins_sid]), unique=True)
	if not res:
		ud.debug(ud.MODULE, ud.ERROR, "Failed to determine DN of UCS Domain Admins group")
		raise ldap.NO_SUCH_OBJECT({'desc': 'no object'})

	return res[0]


def _create_domain_admin_account_in_udm(username, password, lo=None, ucr=None):
	if not lo:
		lo = univention.uldap.getMachineConnection()

	ud.debug(ud.MODULE, ud.INFO, "running _create_domain_admin_account_in_udm")
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	domain_admins_dn = _dn_of_udm_domain_admins(lo, ucr)

	cmd = ("univention-directory-manager", "users/user", "create", "--position", "cn=users,%s" % ucr.get("ldap/base"), "--set", "username=%s" % username, "--set", "lastname=tmp", "--set", "password=%s" % password, "--set", "primaryGroup=%s" % domain_admins_dn)

	p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
	stdout, stderr = p1.communicate()
	if p1.returncode != 0:
		ud.debug(ud.MODULE, ud.ERROR, "Account creation for %s failed" % username)
		if stdout:
			ud.debug(ud.MODULE, ud.ERROR, "udm users/user create output:\n%s" % stdout.decode('UTF-8', 'replace'))
		return False
	return True


def _ucs_sid_is_well_known_administrator(user_sid, lo=None, ucr=None):
	if not lo:
		lo = univention.uldap.getMachineConnection()

	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	ucs_domain_sid = _sid_of_ucs_sambadomain(lo, ucr)
	administrator_sid = "%s-%d" % (ucs_domain_sid, DOMAIN_RID_ADMINISTRATOR)
	if user_sid == administrator_sid:
		return True
	return False


def _add_udm_account_to_domain_admins(user_dn, lo=None, ucr=None):
	if not lo:
		lo = univention.uldap.getMachineConnection()

	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	domain_admins_dn = _dn_of_udm_domain_admins(lo, ucr)
	cmd = ("univention-directory-manager", "users/user", "modify", "--dn", user_dn, "--append", "groups=%s" % domain_admins_dn)
	p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
	stdout, stderr = p1.communicate()
	if p1.returncode != 0:
		ud.debug(ud.MODULE, ud.ERROR, "Adding %s to Domain Admins failed" % user_dn)
		if stdout:
			ud.debug(ud.MODULE, ud.ERROR, "udm users/user modify groups output:\n%s" % stdout.decode('UTF-8', 'replace'))
		return False
	return True


def _set_udm_account_password(user_dn, password):
	cmd = ('univention-directory-manager', 'users/user', 'modify', '--dn', user_dn, '--set', 'password=%s' % password, '--set', 'overridePWHistory=1', '--set', 'overridePWLength=1')
	p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
	stdout, stderr = p1.communicate()
	if p1.returncode != 0:
		ud.debug(ud.MODULE, ud.ERROR, "Failed to set AD password in UDM for %s" % user_dn)
		if stdout:
			ud.debug(ud.MODULE, ud.ERROR, "udm users/user modify password output:\n%s" % stdout.decode('UTF-8', 'replace'))
		return False
	return True


def prepare_administrator(username, password, ucr=None):
	ud.debug(ud.MODULE, ud.PROCESS, "Prepare administrator account")

	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	# First check if account exists in LDAP, otherwise create it:
	lo = univention.uldap.getMachineConnection()
	res = lo.search(filter=filter_format("(&(uid=%s)(objectClass=shadowAccount))", (username,)), attr=["userPassword", "sambaSID"])
	if not res:
		ud.debug(ud.MODULE, ud.INFO, "No UCS LDAP search result for uid=%s" % username)
		try:
			success = _create_domain_admin_account_in_udm(username, password, lo, ucr)
		except ldap.NO_SUCH_OBJECT:
			success = False
		if not success:
			raise failedToCreateAdministratorAccount()
		return

	# Second, if the account existed already, check if it has the well known Administrator SID
	user_dn = res[0][0]
	user_sid = res[0][1].get("sambaSID", [None])[0]
	old_hash = res[0][1].get("userPassword", [None])[0]

	if not user_sid:
		ud.debug(ud.MODULE, ud.ERROR, "UCS LDAP search for sambaSID of uid=%s failed" % username)
		raise sambaSidNotSetForAdministratorAccount()

	is_well_known_admin = False
	try:
		is_well_known_admin = _ucs_sid_is_well_known_administrator(user_sid.decode('ASCII'), lo, ucr)
	except ldap.NO_SUCH_OBJECT:
		raise failedToSearchForWellKnownSid()

	# Third, if the account doesn't have the well known Administrator SID, add it to Domain Admins
	if not is_well_known_admin:
		try:
			success = _add_udm_account_to_domain_admins(user_dn, lo, ucr)
		except ldap.NO_SUCH_OBJECT:
			success = False
		if not success:
			raise failedToAddAdministratorAccountToDomainAdmins()
		return

	# Finally, if the account does have the Administrator SID, set it's UDM password to the AD one.
	if old_hash == b'{KINIT}':
		return

	success = _set_udm_account_password(user_dn, password)
	if not success:
		raise failedToSetAdministratorPassword()


def _mapped_ad_dn(ad_dn, ad_ldap_base, ucr=None):
	"""
	>>> _mapped_ad_dn('uid=Administrator + CN=admin,OU=users,CN=univention,Foo=univention,bar=base', 'foo=univention,bar = base', {'ldap/base': 'dc=base'})
	'uid=Administrator+cn=admin,ou=users,cn=univention,dc=base'
	"""
	parent = ad_dn
	while parent:
		if univention.uldap.access.compare_dn(parent, ad_ldap_base):
			break
		parent = univention.uldap.parentDn(parent)
	else:
		ud.debug(ud.MODULE, ud.ERROR, "Mapping of AD DN %r failed, base is not %r" % (ad_dn, ad_ldap_base))
		return

	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	base = ldap.dn.str2dn(ad_ldap_base)
	dn = [[(attr[0].lower() if attr[0] in ('CN', 'OU') else attr[0], attr[1], attr[2]) for attr in x] for x in ldap.dn.str2dn(ad_dn)[:-len(base)]]
	return ldap.dn.dn2str(dn + ldap.dn.str2dn(ucr.get("ldap/base")))


def synchronize_account_position(ad_domain_info, username, password, ucr=None):
	ud.debug(ud.MODULE, ud.PROCESS, "running synchronize_account_position")

	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	# First determine target position from AD:
	ad_server_ip = ad_domain_info["DC IP"]
	ad_server_name = ad_domain_info["DC DNS Name"]
	ad_ldap_base = ad_domain_info["LDAP Base"]
	ad_domain = ad_domain_info["Domain"]
	ad_realm = ad_domain.upper()

	try:
		time_sync(ad_server_ip)
	except timeSyncronizationFailed as ex:
		ud.debug(ud.MODULE, ud.WARN, "Time sync failed, trying to authenticate anyway. Original exception: %s" % (ex,))

	principal = "%s@%s" % (username, ad_realm)
	_get_kerberos_ticket(principal, password, ucr)

	try:
		lo_ad = univention.uldap.access(host=ad_server_name, port=389, base=ad_ldap_base, binddn=None, bindpw=None, start_tls=0, use_ldaps=False, decode_ignorelist=["objectSid"])
		lo_ad.lo.set_option(ldap.OPT_PROTOCOL_VERSION, ldap.VERSION3)
		lo_ad.lo.set_option(ldap.OPT_REFERRALS, 0)

		auth = ldap.sasl.gssapi("")
		lo_ad.lo.sasl_interactive_bind_s("", auth)
	except (ldap.INVALID_CREDENTIALS, ldap.UNWILLING_TO_PERFORM):
		return False  # Massive failure, but no issue to be raised here.

	res = lo_ad.searchDn(filter=filter_format("(sAMAccountName=%s)", [username]))
	if not res:
		ud.debug(ud.MODULE, ud.ERROR, "Lookup of AD DN for user %s failed" % username)
		return False  # Massive failure, but no issue to be raised here.
	ad_user_dn = res[0]

	# Second determine position in UCS LDAP:
	lo = univention.uldap.getMachineConnection()
	res = lo.searchDn(filter=filter_format("(&(uid=%s)(objectClass=shadowAccount))", (username,)), unique=True)
	if not res:
		ud.debug(ud.MODULE, ud.ERROR, "No UCS LDAP search result for uid=%s" % username)
		return False  # Massive failure, but no issue to be raised here.

	ucs_user_dn = res[0]
	if ucs_user_dn.lower() == ad_user_dn.lower():
		return True

	mapped_ad_user_dn = _mapped_ad_dn(ad_user_dn, ad_ldap_base, ucr)
	target_position = lo.parentDn(mapped_ad_user_dn)

	cmd = ("univention-directory-manager", "users/user", "move", "--dn", ucs_user_dn, "--position", target_position)
	p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
	stdout, stderr = p1.communicate()
	if p1.returncode != 0:
		ud.debug(ud.MODULE, ud.ERROR, "Moving UDM object %s to %s failed" % (ucs_user_dn, target_position))
		if stdout:
			ud.debug(ud.MODULE, ud.ERROR, "udm users/user modify groups output:\n%s" % stdout.decode('UTF-8', 'replace'))
		return False
	return True


def _server_supports_ssl(server):
	ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
	ldapuri = "ldap://%s:389" % (server)
	lo = ldap.initialize(ldapuri)
	try:
		lo.start_tls_s()
	except ldap.UNAVAILABLE:
		return False
	except ldap.SERVER_DOWN:
		return False
	return True


def server_supports_ssl(server):
	ud.debug(ud.MODULE, ud.PROCESS, "Check if server supports SSL")
	# we have to create a new process because there is only one sec context allowed in python-ldap
	p1 = subprocess.Popen([sys.executable, "-c", 'import univention.lib.admember; print(univention.lib.admember._server_supports_ssl(%r))' % (server,)], close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = p1.communicate()
	if p1.returncode == 0 and stdout.strip() == b'True':
		ud.debug(ud.MODULE, ud.PROCESS, "SSL True")
		return True
	else:
		ud.debug(ud.MODULE, ud.PROCESS, "SSL False")
		return False


def enable_ssl():
	ud.debug(ud.MODULE, ud.PROCESS, "Enable connector SSL")
	univention.config_registry.handler_set([
		u'connector/ad/ldap/ssl=yes',
		u'ldap/sasl/secprops/maxssf=128',
	])


def disable_ssl():
	ud.debug(ud.MODULE, ud.PROCESS, "Disable connector SSL")
	univention.config_registry.handler_set([u'connector/ad/ldap/ssl=no'])
	univention.config_registry.handler_unset([u'ldap/sasl/secprops/maxssf'])


def _add_service_to_localhost(service):
	ud.debug(ud.MODULE, ud.PROCESS, "Adding service %s to localhost" % service)
	res = subprocess.call('. /usr/share/univention-lib/ldap.sh; ucs_addServiceToLocalhost %s' % (pipes.quote(service),), shell=True)
	if res != 0:
		raise failedToSetService()


def _remove_service_from_localhost(service):
	ud.debug(ud.MODULE, ud.PROCESS, "Remove service %s from localhost" % service)
	res = subprocess.call('. /usr/share/univention-lib/ldap.sh; ucs_removeServiceFromLocalhost %s' % (pipes.quote(service),), shell=True)
	if res != 0:
		raise failedToSetService()


def add_admember_service_to_localhost():
	_add_service_to_localhost('AD Member')


def add_adconnector_service_to_localhost():
	_add_service_to_localhost('AD Connector')


def remove_admember_service_from_localhost():
	_remove_service_from_localhost('AD Member')


def info_handler(msg):
	ud.debug(ud.MODULE, ud.PROCESS, msg)


def error_handler(msg):
	ud.debug(ud.MODULE, ud.ERROR, msg)


def remove_install_univention_samba(info_handler=info_handler, step_handler=None, error_handler=error_handler, install=True, uninstall=True):  # TODO: replace with univention-remove?
	pm = univention.lib.package_manager.PackageManager(
		info_handler=info_handler,
		step_handler=step_handler,
		error_handler=error_handler,
		always_noninteractive=True,
	)
	if not pm.update():
		return False
	pm.noninteractive()

	# uninstall first to get rid of the configured samba/* ucr vars
	if uninstall and pm.is_installed('univention-samba'):
		ud.debug(ud.MODULE, ud.PROCESS, "Uninstall univention-samba")
		if not pm.uninstall('univention-samba'):
			return False

	# install
	if install:
		ud.debug(ud.MODULE, ud.PROCESS, "Install univention-samba")
		if not pm.install('univention-samba'):
			ud.debug(ud.MODULE, ud.PROCESS, "Installation of univention-samba failed. Try to re-create sources.list and try again.")
			univention.config_registry.handler_commit(['/etc/apt/sources.list.d/15_ucs-online-version.list', '/etc/apt/sources.list.d/20_ucs-online-component.list'])
			if not pm.update():
				return False
			if not pm.install('univention-samba'):
				ud.debug(ud.MODULE, ud.ERROR, "Installation of univention-samba failed. Abort.")
				return False

	return True


SAMBA_TOOL_FIELDNAMES_TO_CLDAP_RES = {
	'Forest': 'forest',
	'Domain': 'dns_domain',
	'Netbios domain': 'domain_name',
	'DC name': 'pdc_dns_name',
	'DC netbios name': 'pdc_name',
	'Server site': 'server_site',
	'Client site': 'client_site'
}


def cldap_finddc(ip, use_samba_lib=six.PY3):
	if use_samba_lib:
		lp = LoadParm()
		lp.load('/dev/null')
		net = Net(creds=None, lp=lp)
		cldap_res = net.finddc(address=ip, flags=nbt.NBT_SERVER_LDAP | nbt.NBT_SERVER_DS | nbt.NBT_SERVER_WRITABLE)
	else:
		cmd = ['samba-tool', 'domain', 'info', ip]
		p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
		output, _ = p1.communicate()
		if not output:
			raise RuntimeError("No output from command: %s" % " ".join(cmd))
		res = {}
		for line in output.rstrip().decode('UTF-8').split('\n'):
			try:
				fieldname, value = line.split(':', 1)
			except ValueError as exc:
				raise RuntimeError("Parsing samba-tool output failed: %s (%s)\nfull output:\n%s" % (line, exc, output))
			fieldname = fieldname.rstrip()
			try:
				res[SAMBA_TOOL_FIELDNAMES_TO_CLDAP_RES[fieldname]] = value.lstrip()
			except KeyError:
				pass  # Unknown field, output may have changed

		for fieldname, key in list(SAMBA_TOOL_FIELDNAMES_TO_CLDAP_RES.items()):
			if key not in res:
				raise RuntimeError("Missing field in samba-tool output: %s\nfull output:\n%s" % (fieldname, output))
		CLDAP_RES = namedtuple('CLDAP_RES', SAMBA_TOOL_FIELDNAMES_TO_CLDAP_RES.values())
		cldap_res = CLDAP_RES(**res)
	return cldap_res


def get_defaultNamingContext(ad_server_ip, use_samba_lib=six.PY3):
	if use_samba_lib:
		try:
			remote_ldb = ldb.Ldb()
			remote_ldb.connect(url="ldap://%s" % ad_server_ip)
			return str(remote_ldb.get_default_basedn())
		except ldb.LdbError as exc:
			raise RuntimeError(exc)
	else:
		cmd = ['ldapsearch', '-xLLL', '-h', ad_server_ip, '-s', 'base', '-b', '', 'defaultNamingContext']
		try:
			p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
			output, _ = p1.communicate()
		except OSError as exc:
			raise RuntimeError("Command failed: %s (%s)" % (" ".join(cmd), exc))
		lines = output.rstrip().decode('UTF-8').split('\n')
		if len(lines) < 2:
			raise RuntimeError("No output from command: %s" % " ".join(cmd))
		if not lines[1].startswith('defaultNamingContext: '):
			raise RuntimeError("defaultNamingContext not found on %s" % (ad_server_ip,))
		return lines[1][22:]


def lookup_adds_dc(ad_server=None, ucr=None, check_dns=True):
	'''CLDAP lookup'''

	ud.debug(ud.MODULE, ud.PROCESS, "Lookup ADDS DC")

	ad_domain_info = {}
	ips = []
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()
	if not ad_server:
		ad_server = ucr.get('domainname')

	# get ip addresses
	try:
		ipaddress.ip_address(u'%s' % (ad_server,))
		ips.append(ad_server)
	except ValueError:
		dig_sources = []
		dig_sources_ucr = []
		for source in ['dns/forwarder1', 'dns/forwarder2', 'dns/forwarder3', 'nameserver1', 'nameserver2', 'nameserver3']:
			if source in ucr:
				dig_sources.append("@%s" % ucr[source])
				dig_sources_ucr.append(source)
		for dig_source in dig_sources:
			try:
				cmd = ['dig', dig_source, ad_server, '+short', '+nocookie']
				ud.debug(ud.MODULE, ud.PROCESS, "running %s" % cmd)
				p1 = subprocess.Popen(cmd, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				stdout, stderr = p1.communicate()
				stdout, stderr = stdout.decode('UTF-8', 'replace'), stderr.decode('UTF-8', 'replace')
				ud.debug(ud.MODULE, ud.PROCESS, "stdout: %s" % stdout)
				ud.debug(ud.MODULE, ud.PROCESS, "stderr: %s" % stderr)
				if p1.returncode == 0:
					for i in stdout.split(u'\n'):
						if i:
							ips.append(i)
				if ips:
					break
			except OSError as ex:
				ud.debug(ud.MODULE, ud.ERROR, "%s failed: %s" % (cmd, ex.args[1]))

	# no ip addresses
	if not ips:
		raise failedADConnect(["DNS lookup of AD Server %s failed. Sources: %s" % (ad_server, ", ".join(dig_sources_ucr))])

	ad_server_ip = None
	check_results = []
	for ip in ips:
		try:  # check cldap
			cldap_res = cldap_finddc(ip)
		except RuntimeError as ex:
			ud.debug(ud.MODULE, ud.ERROR, "Connection to AD Server %s failed: %s" % (ip, ex.args[0]))
			check_results.append("CLDAP: %s" % ex.args[0])
		else:
			if not check_dns:
				ad_server_ip = ip
				break
			try:  # check dns
				cmd = ['dig', '@%s' % ip, '+nocookie']
				ud.debug(ud.MODULE, ud.PROCESS, "running %s" % cmd)
				p1 = subprocess.Popen(cmd, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				stdout, stderr = p1.communicate()
				stdout, stderr = stdout.decode('UTF-8', 'replace'), stderr.decode('UTF-8', 'replace')
				ud.debug(ud.MODULE, ud.PROCESS, "stdout: %s" % stdout)
				ud.debug(ud.MODULE, ud.PROCESS, "stderr: %s" % stderr)
				if p1.returncode == 0:  # yes, this is also a DNS server, we are good
					ad_server_ip = ip
					break
			except OSError as ex:
				ud.debug(ud.MODULE, ud.ERROR, "%s failed: %s" % (cmd, ex.args[1]))
				check_results.append("DNS: %s" % ex.args[1])

	if ad_server_ip is None:
		raise failedADConnect(["Connection to AD Server %s failed (%s)" % (ad_server, ",".join(check_results))])

	ad_ldap_base = None
	try:
		ad_ldap_base = get_defaultNamingContext(ad_server_ip)
	except RuntimeError as ex:
		raise failedADConnect(["Could not detect LDAP base on %s: %s" % (ad_server_ip, ex.args[1])])

	ad_domain_info = {
		"Forest": cldap_res.forest,
		"Domain": cldap_res.dns_domain,
		"Netbios Domain": cldap_res.domain_name,
		"DC DNS Name": cldap_res.pdc_dns_name,
		"DC Netbios Name": cldap_res.pdc_name,
		"Server Site": cldap_res.server_site,
		"Client Site": cldap_res.client_site,
		"LDAP Base": ad_ldap_base,
		"DC IP": ad_server_ip,
	}

	ud.debug(ud.MODULE, ud.PROCESS, "AD Info: %s" % ad_domain_info)

	return ad_domain_info


def set_timeserver(timeserver, ucr=None):
	ud.debug(ud.MODULE, ud.PROCESS, "Setting timeserver to %s" % timeserver)
	univention.config_registry.handler_set([u'timeserver=%s' % (timeserver,)])
	restart_service("ntp")


def stop_service(service):
	return invoke_service(service, "stop")


def start_service(service):
	return invoke_service(service, "start")


def restart_service(service):
	return invoke_service(service, "restart")


def invoke_service(service, cmd):
	init_script = '/etc/init.d/%s' % service
	if not os.path.exists(init_script):
		return
	try:
		p1 = subprocess.Popen([init_script, cmd], close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = p1.communicate()
	except OSError as ex:
		ud.debug(ud.MODULE, ud.ERROR, "%s %s failed: %s" % (init_script, cmd, ex.args[1],))
		return

	if p1.returncode:
		ud.debug(ud.MODULE, ud.ERROR, "%s %s failed (%d)" % (init_script, cmd, p1.returncode,))
		return

	ud.debug(ud.MODULE, ud.PROCESS, "%s %s: %s" % (init_script, cmd, stdout.decode('UTF-8', 'replace')))


def do_time_sync(ad_ip):
	ud.debug(ud.MODULE, ud.PROCESS, "Synchronizing time to %s" % ad_ip)
	p1 = subprocess.Popen(["rdate", "-s", "-n", ad_ip], close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = p1.communicate()
	if p1.returncode:
		ud.debug(ud.MODULE, ud.ERROR, "rdate -s -p failed (%d)" % (p1.returncode,))
		return False
	return True


def time_sync(ad_ip, tolerance=180, critical_difference=360):
	'''Try to sync the local time with an AD server'''

	stdout = b""
	env = os.environ.copy()
	env["LC_ALL"] = "C"
	try:
		p1 = subprocess.Popen(["rdate", "-p", "-n", ad_ip], close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
		stdout, stderr = p1.communicate()
	except OSError as ex:
		ud.debug(ud.MODULE, ud.ERROR, "rdate -p -n %s: %s" % (ad_ip, ex.args[1]))
		return False

	if p1.returncode:
		ud.debug(ud.MODULE, ud.ERROR, "rdate failed (%d)" % (p1.returncode,))
		return False

	TIME_FORMAT = "%a %b %d %H:%M:%S %Z %Y"
	time_string = stdout.strip().decode('ASCII')
	old_locale = locale.getlocale(locale.LC_TIME)
	try:
		locale.setlocale(locale.LC_TIME, (None, None))  # 'C' as env['LC_ALL'] some lines earlier
		remote_datetime = datetime.strptime(time_string, TIME_FORMAT)
	except ValueError:
		raise timeSyncronizationFailed("AD Server did not return proper time string: %s" % time_string)
	finally:
		locale.setlocale(locale.LC_TIME, old_locale)

	local_datetime = datetime.today()
	delta_t = local_datetime - remote_datetime
	if abs(delta_t) < timedelta(0, tolerance):
		ud.debug(ud.MODULE, ud.PROCESS, "Time difference is less than %d seconds, skipping reset of local time" % (tolerance,))
	elif local_datetime > remote_datetime:
		if abs(delta_t) >= timedelta(0, critical_difference):
			raise manualTimeSyncronizationRequired("Remote clock is behind local clock by more than %s seconds, refusing to turn back time." % critical_difference)
		else:
			ud.debug(ud.MODULE, ud.WARN, "Remote clock is behind local clock by more than %s seconds, refusing to turn back time, should be accurate enough." % (tolerance,))
			return False
	else:
		if not do_time_sync(ad_ip):
			raise timeSyncronizationFailed("Time synchronization failed")
	return True


def check_server_role(ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()
	if ucr.get("server/role") != "domaincontroller_master":
		raise invalidUCSServerRole("The function become_ad_member can only be run on an UCS Primary Directory Node")


def check_domain(ad_domain_info, ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()
	if ad_domain_info["Domain"].lower() != ucr["domainname"].lower():
		raise domainnameMismatch("The domain of the AD Server does not match the local domain: %s" % (ad_domain_info["Domain"],))


def set_nameserver(server_ips, ucr=None):
	previous_ucr_set = []
	previous_ucr_unset = []
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()
	count = 1
	for server_ip in server_ips:
		var = u'nameserver%d' % count
		val = ucr.get(var)
		if val is not None:
			previous_ucr_set.append(u'%s=%s' % (var, val))
		else:
			previous_ucr_unset.append(u'%s' % (var,))
		univention.config_registry.handler_set([u'%s=%s' % (var, server_ip)])
		count += 1
	for i in range(count, 4):
		var = u'nameserver%s' % i
		val = ucr.get(var)
		if val is not None:
			previous_ucr_set.append(u'%s=%s' % (var, val))
			univention.config_registry.handler_unset([var])
	return (previous_ucr_set, previous_ucr_unset)


def rename_well_known_sid_objects(username, password, ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	ud.debug(ud.MODULE, ud.PROCESS, "Matching well known object names")

	# First determine current name Domain Admins (trivial)
	lo = univention.uldap.getMachineConnection()
	ucs_domain_sid = _sid_of_ucs_sambadomain(lo, ucr)

	domain_admins_sid = "%s-%d" % (ucs_domain_sid, DOMAIN_RID_ADMINS)
	res = lo.search(filter=filter_format("(&(sambaSID=%s)(objectClass=sambaGroupMapping))", [domain_admins_sid]), attr=["cn"], unique=True)
	if not res or "cn" not in res[0][1]:
		ud.debug(ud.MODULE, ud.ERROR, "Lookup of group name for Domain Admins sid failed")
		domain_admins_name = u"Domain Admins"  # sensible guess
	else:
		domain_admins_name = res[0][1]["cn"][0].decode('UTF-8')

	# Next run the renaming script
	binddn = '%s@%s' % (username, ucr.get('kerberos/realm'))
	with tempfile.NamedTemporaryFile('w+') as fd:
		fd.write(password)
		fd.flush()
		p1 = subprocess.Popen(
			['/usr/share/univention-ad-connector/scripts/well-known-sid-object-rename', '--binddn', binddn, '--bindpwdfile', fd.name],
			stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
		stdout, stderr = p1.communicate()
		ud.debug(ud.MODULE, ud.PROCESS, "%s" % stdout.decode('UTF-8', 'replace'))

	if p1.returncode != 0:
		msg = "well-known-sid-object-rename failed with %d (%s)" % (p1.returncode, stderr.decode('UTF-8', 'replace'))
		ud.debug(ud.MODULE, ud.ERROR, msg)
		raise connectionFailed(msg)

	# Finally wait for replication and slapd restart to ensure that new LDAP ACLs are active:
	res = lo.search(filter=filter_format("(&(sambaSID=%s)(objectClass=sambaGroupMapping))", [domain_admins_sid]), attr=["cn"], unique=True)
	if not res or "cn" not in res[0][1]:
		ud.debug(ud.MODULE, ud.ERROR, "Lookup of new group name for Domain Admins sid failed")
		new_domain_admins_name = u"Domain Admins"
	else:
		new_domain_admins_name = res[0][1]["cn"][0].decode('UTF-8')

	wait_for_postrun = False
	if new_domain_admins_name != domain_admins_name:
		t0 = time.time()
		ud.debug(ud.MODULE, ud.INFO, "Waiting for well-known-sid-name-mapping listener to map Domain Admins")
		while custom_groupname(domain_admins_name) != new_domain_admins_name:
			if (time.time() - t0) > 15:
				break
			time.sleep(1)
		else:
			wait_for_postrun = True

	if wait_for_postrun:
		ud.debug(ud.MODULE, ud.ERROR, "Waiting for postrun of well-known-sid-name-mapping")
		time.sleep(15)


def make_deleted_objects_readable_for_this_machine(username, password, ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	ud.debug(ud.MODULE, ud.PROCESS, "Make Deleted Objects readable for this machine")

	with tempfile.NamedTemporaryFile('w+') as fd:
		fd.write(password)
		fd.flush()
		binddn = '%s@%s' % (username, ucr.get('kerberos/realm'))
		p1 = subprocess.Popen(
			['/usr/share/univention-ad-connector/scripts/make-deleted-objects-readable-for-this-machine', '--binddn', binddn, '--bindpwdfile', fd.name],
			stdout=subprocess.PIPE, stderr=subprocess.PIPE,
			close_fds=True)
		stdout, stderr = p1.communicate()
		ud.debug(ud.MODULE, ud.PROCESS, "%s" % stdout.decode('UTF-8', 'replace'))
	if p1.returncode != 0:
		msg = "make-deleted-objects-readable-for-this-machine failed with %d (%s)" % (p1.returncode, stderr.decode('UTF-8', 'replace'))
		ud.debug(ud.MODULE, ud.ERROR, msg)
		raise connectionFailed(msg)


def prepare_dns_reverse_settings(ad_domain_info, ucr=None):
	# For python-ldap / GSSAPI / AD we need working reverse DNS lookups
	# Otherwise one ends up with:
	#
	# SASL(-1): generic failure: GSSAPI Error: Miscellaneous failure (see text)
	#           (Matching credential (ldap/10.20.30.123@10.20.30.123) not found)
	#
	# Or even worse, in case there had been a (nscd cached?) PTR record
	# in the ucs.domain:
	#
	# SASL(-1): generic failure: GSSAPI Error: Miscellaneous failure (see text)
	#           (Matching credential (ldap/adhost.ucs.domain@UCS.DOMAIN) not found)
	#

	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	# Flush the cache, just in case
	flush_nscd_hosts_cache()

	# Test DNS resolution (just for fun)
	try:
		hostname, aliaslist, ipaddrlist = socket.gethostbyaddr(ad_domain_info['DC IP'])
		ud.debug(ud.MODULE, ud.INFO, "%s resolves to %s" % (ad_domain_info['DC IP'], hostname))
	except (socket.herror, socket.gaierror) as exc:
		ud.debug(ud.MODULE, ud.INFO, "Resolving %s failed: %s" % (ad_domain_info['DC IP'], exc.args[1]))

	# Set a hosts/static anyway, to be safe from DNS issues (Bug #38285)
	previous_ucr_set = []
	previous_ucr_unset = []

	ad_server_name = ad_domain_info['DC DNS Name']
	ip = socket.gethostbyname(ad_server_name)
	ucr_key = u'hosts/static/%s' % (ip,)
	ucr_set = [u'%s=%s' % (ucr_key, ad_server_name), ]

	for setting in ucr_set:
		var = setting.split("=", 1)[0]
		old_val = ucr.get(var)
		if old_val is not None:
			previous_ucr_set.append(u'%s=%s' % (var, old_val))
		else:
			previous_ucr_unset.append(u'%s' % (var,))

	ud.debug(ud.MODULE, ud.PROCESS, "Setting UCR variables: %s" % ucr_set)
	univention.config_registry.handler_set(ucr_set)

	return (previous_ucr_set, previous_ucr_unset)


def prepare_kerberos_ucr_settings(realm=None, ucr=None):
	ud.debug(ud.MODULE, ud.PROCESS, "Prepare Kerberos UCR settings")

	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	previous_ucr_set = []
	previous_ucr_unset = []

	ucr_set = [
		u'kerberos/defaults/dns_lookup_kdc=true',
	]
	if realm and realm != ucr.get('kerberos/realm'):
		ucr_set.append(u'kerberos/realm=%s' % realm)

	for setting in ucr_set:
		var = setting.split("=", 1)[0]
		old_val = ucr.get(var)
		if old_val is not None:
			previous_ucr_set.append(u'%s=%s' % (var, old_val))
		else:
			previous_ucr_unset.append(u'%s' % (var,))

	ud.debug(ud.MODULE, ud.PROCESS, "Setting UCR variables: %s" % ucr_set)
	univention.config_registry.handler_set(ucr_set)

	ucr_unset = [
		u'kerberos/kdc',
		u'kerberos/kpasswdserver',
		u'kerberos/adminserver',
	]

	for var in ucr_unset:
		val = ucr.get(var)
		if val is not None:
			previous_ucr_set.append(u'%s=%s' % (var, val))

	ud.debug(ud.MODULE, ud.PROCESS, "Unsetting UCR variables: %s" % ucr_unset)
	univention.config_registry.handler_unset(ucr_unset)

	return (previous_ucr_set, previous_ucr_unset)


def set_ucr(ucr_set, ucr_unset):
	univention.config_registry.handler_set(ucr_set)
	univention.config_registry.handler_unset(ucr_unset)


def prepare_ucr_settings():

	ud.debug(ud.MODULE, ud.PROCESS, "Prepare UCR settings")

	# Show warnings in UMC
	# Change displayed name of users from "username" to "displayName" (as in AD)
	ucr_set = [
		u'ad/member=true',
		u'connector/ad/mapping/user/password/kinit=true',
		u'directory/manager/web/modules/users/user/display=displayName',
		u'nameserver/external=true',
		u'connector/ad/mapping/group/primarymail=true',
		u'connector/ad/mapping/user/primarymail=true',
	]
	modules = ('computers/computer', 'groups/group', 'users/user', 'dns/dns')
	ucr_set += [u'directory/manager/web/modules/%s/show/adnotification=true' % (module,) for module in modules]

	ud.debug(ud.MODULE, ud.PROCESS, "Setting UCR variables: %s" % ucr_set)
	univention.config_registry.handler_set(ucr_set)

	prepare_kerberos_ucr_settings()


def revert_ucr_settings():

	ud.debug(ud.MODULE, ud.PROCESS, "Revert UCR settings")

	# TODO something else?
	ucr_unset = [
		u'ad/member',
		u'directory/manager/web/modules/users/user/display',
		u'kerberos/defaults/dns_lookup_kdc',
	]
	modules = ('computers/computer', 'groups/group', 'users/user', 'dns/dns')
	ucr_unset += [u'directory/manager/web/modules/%s/show/adnotification' % (module,) for module in modules]
	ud.debug(ud.MODULE, ud.PROCESS, "Unsetting UCR variables: %s" % ucr_unset)
	univention.config_registry.handler_unset(ucr_unset)

	ucr_set = [
		u'nameserver/external=false',
	]
	ud.debug(ud.MODULE, ud.PROCESS, "Setting UCR variables: %s" % ucr_set)
	univention.config_registry.handler_set(ucr_set)


def prepare_connector_settings(username, password, ad_domain_info, ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	ud.debug(ud.MODULE, ud.PROCESS, "Prepare connector settings")

	binddn = '%s$' % (ucr.get('hostname'))
	ucr_set = [
		u'connector/ad/ldap/host=%s' % ad_domain_info["DC DNS Name"],
		u'connector/ad/ldap/base=%s' % ad_domain_info["LDAP Base"],
		u'connector/ad/ldap/binddn=%s' % binddn,
		u'connector/ad/ldap/bindpw=/etc/machine.secret',
		u'connector/ad/ldap/kerberos=true',
		u'connector/ad/mapping/syncmode=read',
		u'connector/ad/mapping/user/ignorelist=krbtgt,root,pcpatch',
	]
	ud.debug(ud.MODULE, ud.PROCESS, "Setting UCR variables: %s" % ucr_set)
	univention.config_registry.handler_set(ucr_set)


def revert_connector_settings(ucr=None):

	ud.debug(ud.MODULE, ud.PROCESS, "Revert connector settings")

	# TODO something else?
	ucr_unset = [
		u'connector/ad/ldap/host',
		u'connector/ad/ldap/base',
		u'connector/ad/ldap/binddn',
		u'connector/ad/ldap/bindpw',
		u'connector/ad/ldap/kerberos',
		u'connector/ad/mapping/syncmode',
		u'connector/ad/mapping/user/ignorelist',
	]
	ud.debug(ud.MODULE, ud.PROCESS, "Unsetting UCR variables: %s" % ucr_unset)
	univention.config_registry.handler_unset(ucr_unset)


def disable_local_samba4():

	ud.debug(ud.MODULE, ud.PROCESS, "Disable local samba4")
	stop_service("samba")
	univention.config_registry.handler_set([u'samba4/autostart=false'])


def disable_local_heimdal():

	ud.debug(ud.MODULE, ud.PROCESS, "Disable local heimdal")
	stop_service("heimdal-kdc")
	univention.config_registry.handler_set([u'kerberos/autostart=false'])


def run_samba_join_script(username, password, ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	ud.debug(ud.MODULE, ud.PROCESS, "Running samba join script")

	lo = univention.uldap.getMachineConnection()
	res = lo.searchDn(filter=filter_format("(&(uid=%s)(objectClass=shadowAccount))", (username,)), unique=True)
	if not res:
		ud.debug(ud.MODULE, ud.ERROR, "No UCS LDAP search result for uid=%s" % username)
		raise sambaJoinScriptFailed()
	binddn = res[0]

	with tempfile.NamedTemporaryFile('w+') as fd:
		fd.write(password)
		fd.flush()
		my_env = os.environ
		my_env['SMB_CONF_PATH'] = '/etc/samba/smb.conf'
		cmd = ('/usr/lib/univention-install/26univention-samba.inst', '--binddn', binddn, '--bindpwdfile', fd.name)
		p1 = subprocess.Popen(cmd, close_fds=True, env=my_env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		stdout, stderr = p1.communicate()
		ud.debug(ud.MODULE, ud.PROCESS, "%s" % stdout.decode('UTF-8', 'replace'))
	if p1.returncode != 0:
		if stderr:
			ud.debug(ud.MODULE, ud.ERROR, "stderr:\n%s" % (stderr.decode('UTF-8', 'replace'),))
		ud.debug(ud.MODULE, ud.ERROR, "26univention-samba.inst failed with %d" % (p1.returncode,))
		raise sambaJoinScriptFailed()


def add_host_record_in_ad(uid=None, binddn=None, bindpw=None, bindpwdfile=None, fqdn=None, ip=None, sso=False):

	pwdfile = None
	create_pwdfile = False
	ucr = univention.config_registry.ConfigRegistry()
	ucr.load()
	domainname = ucr.get('domainname')

	if binddn:
		uids = [y[1] for x in ldap.dn.str2dn(binddn) for y in x if ('uid' in y)]
		if uids:
			uid = uids[0]
	if bindpwdfile:
		create_pwdfile = False
		pwdfile = bindpwdfile
	elif bindpw:
		create_pwdfile = True
		pwdfile = bindpw

	# take myself as default
	if not ip:
		ip = Interfaces().get_default_ip_address().ip

	if sso and not fqdn:
		fqdn = ucr.get('ucs/server/sso/fqdn', 'ucs-sso.' + domainname)

	if not uid or not pwdfile or not fqdn or not ip:
		print('Missing binddn/bindpw/bindpwdfile/fqdn or ip, do nothing!')
		return False

	ad_domain_info = lookup_adds_dc()
	ad_ip = ad_domain_info['DC IP']
	found = False

	print("Create %s (%s) A record on %s" % (fqdn, ip, ad_ip))

	# check if we are already defined as host record
	try:
		resolver = dns.resolver.Resolver()
		resolver.lifetime = 10
		resolver.nameservers = [ad_ip]
		response = resolver.query(fqdn, 'A')
		for data in response:
			if str(data) == str(ip):
				found = True
	except dns.resolver.NXDOMAIN:
		found = False
	except Exception as err:
		print('failed to query for A record (%s, %s)' % (err.__class__.__name__, err))
		found = False
	if found:
		print('%s A record for %s found' % (fqdn, ip))
		return True

	# create host record  # FIXME; missing quoting
	fd = tempfile.NamedTemporaryFile('w+', delete=False)
	fd.write('server %s\n' % ad_ip)
	fd.write('update add %s 86400 A %s\n' % (fqdn, ip))
	fd.write('send\n')
	fd.write('quit\n')
	fd.close()

	# create pwd file
	if create_pwdfile:
		tmp = tempfile.NamedTemporaryFile('w+', delete=False)
		tmp.write('%s' % pwdfile)
		tmp.close()
		pwdfile = tmp.name

	cmd = ['kinit', '--password-file=%s' % pwdfile, uid]
	cmd += ['nsupdate', '-v', '-g', fd.name]
	try:
		p1 = subprocess.Popen(cmd, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = p1.communicate()
		ud.debug(ud.MODULE, ud.PROCESS, '%s' % stdout.decode('UTF-8', 'replace'))
		if p1.returncode:
			print('%s failed with %d (%s)' % (cmd, p1.returncode, stderr.decode('UTF-8', 'replace')))
			print('failed to add A record for ucs-sso to %s' % ad_ip)
			return False
	finally:
		os.unlink(fd.name)
		if create_pwdfile:
			os.unlink(pwdfile)

	return True


def get_domaincontroller_srv_record(domain, nameserver=None):
	if not domain:
		return False

	resolver = dns.resolver.Resolver()
	resolver.lifetime = 10  # make sure that we get an early timeout
	if nameserver:
		resolver.nameservers = [nameserver]

	# perform a SRV lookup
	try:
		response = resolver.query('_domaincontroller_master._tcp.%s.' % domain, 'SRV')
		if len(response) != 1:
			ud.debug(ud.MODULE, ud.ERROR, 'Non-unique SRV record: %s!' % (response.rrset,))
			return None
		return str(response[0].target)
	except dns.resolver.NoAnswer:
		ud.debug(ud.MODULE, ud.WARN, 'Received no answer to query for _domaincontroller_master._tcp.%s. SRV record.' % (domain,))
	except dns.resolver.NXDOMAIN:
		ud.debug(ud.MODULE, ud.WARN, 'Domain (%s) not resolvable!' % (domain,))
	except dns.resolver.NoNameservers:
		ud.debug(ud.MODULE, ud.WARN, 'No name servers in domain (%s) available to answer the query.' % (domain,))
	except dns.exception.Timeout as exc:
		ud.debug(ud.MODULE, ud.WARN, 'Lookup for Primary Directory Node record timed out: %s' % (exc,))
	return None


def add_domaincontroller_srv_record_in_ad(ad_ip, username, password, ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	ud.debug(ud.MODULE, ud.PROCESS, "Create _domaincontroller_master SRV record on %s" % ad_ip)
	hostname = ucr.get('hostname')
	domainname = ucr.get('domainname')
	fqdn_with_trailing_dot = "%s.%s." % (hostname, domainname)
	srv_record = "_domaincontroller_master._tcp.%s" % (domainname,)
	current_record = get_domaincontroller_srv_record(domainname)
	if current_record == fqdn_with_trailing_dot:
		ud.debug(ud.MODULE, ud.PROCESS, "Ok, SRV record %s already points to this server" % (srv_record,))
		return True

	if current_record:
		# remove the existing SRV record. Important when replacing an existing Primary Directory Node system!
		# we need Administrator permissions to do this.
		ud.debug(ud.MODULE, ud.PROCESS, "Removing previous SRV record %s" % (current_record,))
		with tempfile.NamedTemporaryFile('w+') as fd, tempfile.NamedTemporaryFile('w+') as fd2:
			fd2.write(password)
			fd2.flush()
			# FIXME: missing quoting
			fd.write('server %s\n' % ad_ip)
			fd.write('update delete %s. SRV\n' % (srv_record,))
			fd.write('send\n')
			fd.write('quit\n')
			fd.flush()
			cmd = ['kinit', '--password-file=%s' % (fd2.name,), username, 'nsupdate', '-v', '-g', fd.name]
			p1 = subprocess.Popen(cmd, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			stdout, stderr = p1.communicate()
			ud.debug(ud.MODULE, ud.PROCESS, "%s" % stdout.decode('UTF-8', 'replace'))
			if p1.returncode:
				ud.debug(ud.MODULE, ud.ERROR, "%s failed with %d (%s)" % (cmd, p1.returncode, stderr.decode('UTF-8', 'replace')))
				ud.debug(ud.MODULE, ud.ERROR, "failed to remove SRV record. Ignoring error.")
			subprocess.call(['kdestroy'])

	# FIXME: missing quoting
	fd = tempfile.NamedTemporaryFile('w+', delete=False)
	fd.write('server %s\n' % ad_ip)
	fd.write('update add %s. 10800 SRV 0 0 0 %s\n' % (srv_record, fqdn_with_trailing_dot))
	fd.write('send\n')
	fd.write('quit\n')
	fd.close()

	cmd = ['kinit', '--password-file=/etc/machine.secret']
	# use the machine account so that the server has permissions to modify this record
	cmd += [r'%s\$' % hostname]
	cmd += ['nsupdate', '-v', '-g', fd.name]
	try:
		p1 = subprocess.Popen(cmd, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = p1.communicate()
		ud.debug(ud.MODULE, ud.PROCESS, "%s" % stdout.decode('UTF-8', 'replace'))
		if p1.returncode:
			ud.debug(ud.MODULE, ud.ERROR, "%s failed with %d (%s)" % (cmd, p1.returncode, stderr.decode('UTF-8', 'replace')))
			ud.debug(ud.MODULE, ud.ERROR, "failed to add SRV record to %s" % ad_ip)
			# raise failedToAddServiceRecordToAD("failed to add SRV record to %s" % ad_ip)
			return False
	finally:
		os.unlink(fd.name)

	return True


def get_ucr_variable_from_ucs(host, server, var):
	cmd = ['univention-ssh', '/etc/machine.secret']
	cmd += [r'%s\$@%s' % (host, server)]
	cmd += ['/usr/sbin/ucr get %s' % (pipes.quote(var),)]
	p1 = subprocess.Popen(cmd, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = p1.communicate()
	if p1.returncode:
		ud.debug(ud.MODULE, ud.ERROR, "%s failed with %d (%s)" % (cmd, p1.returncode, stderr.decode('UTF-8', 'replace')))
		raise failedToGetUcrVariable("failed to get UCR variable %s from %s" % (var, server))
	return stdout.decode('UTF-8', 'replace').strip()


def set_nameserver_from_ucs_master(ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	ud.debug(ud.MODULE, ud.PROCESS, "Set nameservers")

	for var in ['nameserver1', 'nameserver2', 'nameserver3']:
		value = get_ucr_variable_from_ucs(ucr.get('hostname'), ucr.get('ldap/master'), var)
		if value:
			ud.debug(ud.MODULE, ud.PROCESS, "Setting %s=%s" % (var, value))
			univention.config_registry.handler_set([u'%s=%s' % (var, value)])


def configure_ad_member(ad_server_ip, username, password):

	check_server_role()

	ad_domain_info = lookup_adds_dc(ad_server_ip)

	check_domain(ad_domain_info)

	check_connection(ad_domain_info, username, password)

	set_timeserver(ad_server_ip)

	set_nameserver([ad_server_ip])

	prepare_ucr_settings()

	add_admember_service_to_localhost()

	disable_local_heimdal()
	disable_local_samba4()

	prepare_administrator(username, password)

	prepare_dns_reverse_settings(ad_domain_info)

	remove_install_univention_samba()

	prepare_connector_settings(username, password, ad_domain_info)

	rename_well_known_sid_objects(username, password)

	run_samba_join_script(username, password)

	add_domaincontroller_srv_record_in_ad(ad_server_ip, username, password)

	if server_supports_ssl(server=ad_domain_info["DC DNS Name"]):
		enable_ssl()
	else:
		ud.debug(ud.MODULE, ud.WARN, "WARNING: ssl is not supported")
		disable_ssl()

	start_service('univention-ad-connector')

	return True


def configure_backup_as_ad_member():
	# TODO something else?
	set_nameserver_from_ucs_master()
	remove_install_univention_samba()
	prepare_ucr_settings()


def configure_slave_as_ad_member():
	# TODO something else?
	set_nameserver_from_ucs_master()
	remove_install_univention_samba()
	prepare_ucr_settings()


def configure_member_as_ad_member():
	# TODO something else?
	set_nameserver_from_ucs_master()
	remove_install_univention_samba()
	prepare_ucr_settings()


def configure_container_as_ad_member():
	prepare_ucr_settings()


def revert_backup_ad_member():
	# TODO something else?
	remove_install_univention_samba(install=False)
	revert_ucr_settings()


def revert_slave_ad_member():
	# TODO something else?
	remove_install_univention_samba(install=False)
	revert_ucr_settings()


def revert_member_ad_member():
	# TODO something else?
	remove_install_univention_samba(install=False)
	revert_ucr_settings()


def revert_container_ad_member():
	revert_ucr_settings()
