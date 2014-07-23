#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Common Python Library
#
# Copyright 2014 Univention GmbH
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

import ldb
import ldap
import os
import subprocess
from datetime import datetime, timedelta
from samba.dcerpc import nbt
from samba.net import Net
from samba.param import LoadParm
import univention.config_registry
import univention.uldap
import univention.lib.package_manager


class faildToSetService(Exception):
	'''ucs_addServiceToLocalhost failed'''


class invalidUCSServerRole(Exception):
	'''Invalid UCS Server Role'''


class failedADConnect(Exception):
	'''Connection to AD Server failed'''


class domainnameMismatch(Exception):
	'''Domain Names don't match'''


class timeSyncronizationFailed(Exception):
	'''Time synchronization failed.'''


class manualTimeSyncronizationRequired(timeSyncronizationFailed):
	'''Time difference critical for Kerberos but syncronization aborted.'''


def is_localhost_in_admember_mode(ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()
	return ucr.is_true('ad/member', False)


def is_localhost_in_adconnector_mode(ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()
	lo = univention.uldap.getMachineConnection()
	res = lo.search(base=ucr.get('ldap/hostdn'), scope=ldap.SCOPE_BASE, filter='(univentionService=AD Connector)')
	if res:
		return True
	return False

def log(msg):
	print msg


def is_domain_in_admember_mode(ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()
	lo = univention.uldap.getMachineConnection()
	res = lo.search(base=ucr.get('ldap/base'), filter='(&(univentionServerRole=master)(univentionService=AD Member))')
	if res:
		return True
	return False


def server_supports_ssl(server):
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


def enable_ssl():
	univention.config_registry.handler_set([u'connector/ad/ldap/ssl=yes'])


def disable_ssl():
	univention.config_registry.handler_set([u'connector/ad/ldap/ssl=no'])


def _add_service_to_localhost(service):
	res = subprocess.call('. /usr/share/univention-lib/ldap.sh; ucs_addServiceToLocalhost "%s"' % service, shell=True)
	if res != 0:
		raise faildToSetService


def add_admember_service_to_localhost():
	_add_service_to_localhost('AD Member')


def add_adconnector_service_to_localhost():
	_add_service_to_localhost('AD Connector')


def install_univention_samba():
	pm = univention.lib.package_manager.PackageManager()
	pm.update()
	pm.noninteractive()
	if not pm.is_installed('univention-samba'):
		pm.install('univention-samba')


def lookup_adds_dc(ad_server=None, realm=None, ucr=None):
	'''CLDAP lookup'''

	ad_domain_info = {}

	if not ad_server and not realm:
		if not ucr:
			ucr = univention.config_registry.ConfigRegistry()
			ucr.load()

		realm = ucr.get("kerberos/realm")

	if not ad_server and not realm:
		return ad_domain_info

	lp = LoadParm()
	lp.load('/dev/null')

	if ad_server:
		try:
			net = Net(creds=None, lp=lp)
			cldap_res = net.finddc(address=ad_server,
				flags=nbt.NBT_SERVER_LDAP | nbt.NBT_SERVER_DS | nbt.NBT_SERVER_WRITABLE)
		except RuntimeError as ex:
			raise failedADConnect(["Connection to AD Server %s failed" % (ad_server,), ex.args[0]])
	elif realm:
		try:
			net = Net(creds=None, lp=lp)
			cldap_res = net.finddc(domain=realm,
				flags=nbt.NBT_SERVER_LDAP | nbt.NBT_SERVER_DS | nbt.NBT_SERVER_WRITABLE)
			ad_server = cldap_res.pdc_dns_name
		except RuntimeError as ex:
			log("No AD Server found for realm %s." % (realm,))
			return ad_domain_info

	ad_server_ip = None
	if cldap_res.pdc_dns_name:
		try:
			p1 = subprocess.Popen(['net', 'lookup', cldap_res.pdc_dns_name],
				close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			stdout, stderr = p1.communicate()
			ad_server_ip = stdout.strip()
		except OSError as ex:
			log("INFO: net lookup %s failed: %s" % (cldap_res.pdc_dns_name, ex.args[1]))

	if not ad_server_ip:
		ad_server_ip = ad_server

	ad_ldap_base = None
	remote_ldb = ldb.Ldb()

	if ad_server_ip:
		try:
			remote_ldb.connect(url="ldap://%s" % ad_server_ip)
			ad_ldap_base = str(remote_ldb.get_root_basedn())
		except ldb.LdbError as ex:
			log("INFO: LDAP connect to %s failed: %s" % (ad_server_ip, ex.args[1]))

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

	return ad_domain_info


def set_timeserver(timeserver, ucr=None):
	univention.config_registry.handler_set([u'timeserver=%s' % (timeserver,)])

	restart_service("ntp")


def stop_service(service):
	return invoke_service(service, "stop")


def start_service(service):
	return invoke_service(service, "start")


def restart_service(service):
	return invoke_service(service, "restart")


def invoke_service(service, cmd):
	if not os.path.exists('/etc/init.d/%s' % service):
		return
	try:
		p1 = subprocess.Popen(["invoke-rc.d", service, cmd],
			close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = p1.communicate()
	except OSError as ex:
		log("ERROR: invoke-rc.d %s %s failed: %s" % (service, cmd, ex.args[1],))
		return

	if p1.returncode:
		log("ERROR: invoke-rc.d %s %s failed (%d)" % (service, cmd, p1.returncode,))
		return


def time_sync(ad_ip, tolerance=180, critical_difference=360):
	'''Try to sync the local time with an AD server'''

	stdout = ""
	env = os.environ.copy()
	env["LC_ALL"] = "C"
	try:
		p1 = subprocess.Popen(["rdate", "-p", "-n", ad_ip],
			close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
		stdout, stderr = p1.communicate()
	except OSError as ex:
		log("ERROR: rdate -p -n %s: %s" % (ad_ip, ex.args[1]))
		return False

	if p1.returncode:
		log("ERROR: rdate failed (%d)" % (p1.returncode,))
		return False

	TIME_FORMAT = "%a %b %d %H:%M:%S %Z %Y"
	try:
		remote_datetime = datetime.strptime(stdout.strip(), TIME_FORMAT)
	except ValueError as ex:
		raise timeSyncronizationFailed("AD Server did not return proper time string: %s" % (stdout.strip(),))

	local_datetime = datetime.today()
	delta_t = local_datetime - remote_datetime
	if abs(delta_t) < timedelta(0, tolerance):
		log("INFO: Time difference is less than %d seconds, skipping reset of local time" % (tolerance,))
	elif local_datetime > remote_datetime:
		if abs(delta_t) >= timedelta(0, critical_difference):
			raise manualTimeSyncronizationRequired("Remote clock is behind local clock by more than %s seconds, refusing to turn back time." % critical_difference)
		else:
			log("INFO: Remote clock is behind local clock by more than %s seconds, refusing to turn back time." % (tolerance,))
			return False
	else:
		log("INFO: Syncronizing time to %s" % ad_ip)
		p1 = subprocess.Popen(["rdate", "-s", "-n", ad_ip],
			close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = p1.communicate()
		if p1.returncode:
			log("ERROR: rdate -s -p failed (%d)" % (p1.returncode,))
			raise timeSyncronizationFailed("rdate -s -p failed (%d)" % (p1.returncode,))
	return True


def check_server_role(ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()
	if ucr.get("server/role") != "domaincontroller_master":
		raise invalidUCSServerRole("The function become_ad_member can only be run on an UCS DC Master")


def check_domain(ad_domain_info, ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()
	if ad_domain_info["Domain"] != ucr["domainname"]:
		raise domainnameMismatch("The domain of the AD Server does not match the local domain: %s"
			% (ad_domain_info["Domain"],))


def set_nameserver(server_ips, ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()
	count = 0
	for server_ip in server_ips:
		univention.config_registry.handler_set([u'nameserver%d=%s' % (count, server_ip)])
		count += 1
	for i in range(count, 4):
		var = u'nameserver%s' % i
		if ucr.get(var):
			univention.config_registry.handler_unset([var])


def prepare_ucr_settings():
	# Show warnings in UMC
	# Change displayed name of users from "username" to "displayName" (as in AD)
	univention.config_registry.handler_set(
		[
			u'kerberos/defaults/dns_lookup_kdc=true',
			u'ad/member=true',
			u'connector/ad/mapping/user/password/kinit=true',
			u'directory/manager/web/modules/computers/computer/show/adnotification=true',
			u'directory/manager/web/modules/groups/group/show/adnotification=true',
			u'directory/manager/web/modules/users/user/show/adnotification=true',
			u'directory/manager/web/modules/users/user/display=displayName',
		]
	)
	univention.config_registry.handler_unset(
		[
			u'kerberos/kdc',
			u'kerberos/kpasswdserver'
		]
	)


def prepare_connector_settings(username, password, ad_domain_info):
	### Store bind information for univention-ad-connector

	bindpw_file = "/etc/univention/connector/ad/bindpw"
	if not os.path.exists(os.path.dirname(bindpw_file)):
		os.makedirs(os.path.dirname(bindpw_file))
	with file(bindpw_file, 'w') as f:
		os.chmod(bindpw_file, 0600)
		f.write(password)

	binddn = 'cn=%s,cn=users,%s' % (username, ad_domain_info["LDAP Base"])

	univention.config_registry.handler_set(
		[
			u'connector/ad/ldap/host=%s' % ad_domain_info["DC DNS Name"],
			u'connector/ad/ldap/base=%s' % ad_domain_info["LDAP Base"],
			u'connector/ad/ldap/binddn=%s' % binddn,
			u'connector/ad/ldap/bindpw=%s' % bindpw_file,
			u'connector/ad/mapping/syncmode=read',
			u'connector/ad/mapping/user/ignorelist=krbtgt,root,pcpatch',
		]
	)


def disable_local_samba4():
	stop_service("samba4")
	univention.config_registry.handler_set([u'samba4/autostart=false'])


def disable_local_heimdal():
	stop_service("heimdal-kdc")
	univention.config_registry.handler_set([u'kerberos/autostart=false'])


def configure_ad_member(ad_server_ip, username, password):

	check_server_role()

	ad_domain_info = lookup_adds_dc(ad_server_ip)

	check_domain(ad_domain_info)

	time_sync(ad_server_ip)

	set_timeserver(ad_server_ip)

	set_nameserver(ad_server_ip)

	set_nameserver([ad_server_ip])

	prepare_ucr_settings()

	add_admember_service_to_localhost()

	disable_local_heimdal()
	disable_local_samba4()

	prepare_ucr_settings()

	install_univention_samba()

	prepare_connector_settings(username, password, ad_domain_info)

	
	if server_supports_ssl(server=ad_domain_info["DC DNS Name"]):
		enable_ssl()
	else:
		print "WARNING: ssl is not supported"
		disable_ssl()

	return True


