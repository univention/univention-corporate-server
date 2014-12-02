#!/usr/bin/python2.7
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
import locale
import socket
import tempfile
import ipaddr
from datetime import datetime, timedelta
from samba.dcerpc import nbt, security
from samba.net import Net
from samba.param import LoadParm
from samba.ndr import ndr_unpack
import univention.config_registry
import univention.uldap
import univention.lib.package_manager
import univention.debug as ud

class failedToSetService(Exception):
	'''ucs_addServiceToLocalhost failed'''

class invalidUCSServerRole(Exception):
	'''Invalid UCS Server Role'''

class failedADConnect(Exception):
	'''Connection to AD Server failed'''

class failedToSetAdministratorPassword(Exception):
	'''Failed to set the password of the UCS Administrator to the AD password'''

class domainnameMismatch(Exception):
	'''Domain Names don't match'''

class connectionFailed(Exception):
	'''Connection to AD failed'''

class notDefaultADAdmin(Exception):
	'''The given account is not the standard AD administrator'''

class univentionSambaWrongVersion(Exception):
	'''univention-samba candiate has wrong version'''

class timeSyncronizationFailed(Exception):
	'''Time synchronization failed.'''

class manualTimeSyncronizationRequired(timeSyncronizationFailed):
	'''Time difference critical for Kerberos but syncronization aborted.'''

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

def check_connection(ad_server_ip, username, password, ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	try:
		lo_ad = univention.uldap.access(uri="ldap://%s" % ad_server_ip, base=ucr.get("ldap/base"), binddn="%s@%s" % (username, ucr.get("kerberos/realm")), bindpw=password, start_tls=False, reconnect=False)
	except ldap.INVALID_CREDENTIALS:
		raise connectionFailed()
	except ldap.UNWILLING_TO_PERFORM:
		raise connectionFailed()

	lo_ad.lo.set_option(ldap.OPT_REFERRALS,0)
	res = lo_ad.search(filter="(sAMAccountName=%s)" % username, attr=["objectSid"])

	if not res:
		raise connectionFailed()
	objectSid = ndr_unpack(security.dom_sid, res[0][1]["objectSid"][0])
	if not str(objectSid).endswith("-500"):
		raise notDefaultADAdmin()

def prepare_administrator(username, password, ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	ud.debug(ud.MODULE, ud.PROCESS, "Prepare administrator account")

	lo = univention.uldap.getAdminConnection()
	res = lo.search(filter='(&(uid=Administrator)(objectClass=shadowAccount))', attr=['userPassword'])
	if not res:
		return

	administrator_dn = res[0][0]
	old_hash = res[0][1].get('userPassword', [None])[0]

	if old_hash == '{KINIT}':
		return

	p1 = subprocess.Popen(['univention-directory-manager', 'users/user', 'modify', '--dn', administrator_dn, '--set', 'password=%s' % password, '--set', 'overridePWHistory=1', '--set', 'overridePWLength=1'], close_fds=True)
	stdout, stderr = p1.communicate()
	if p1.returncode != 0:
		ud.debug(ud.MODULE, ud.ERROR, "failed to set administrator password: %s" % stderr)
		raise failedToSetAdministratorPassword()
	ud.debug(ud.MODULE, ud.PROCESS, "%s" % stdout)

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
	p1 = subprocess.Popen(["python", "-c", 'import univention.lib.admember; print univention.lib.admember._server_supports_ssl("%s")' % server], close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = p1.communicate()
	if p1.returncode == 0 and stdout.strip() == 'True':
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
	res = subprocess.call('. /usr/share/univention-lib/ldap.sh; ucs_addServiceToLocalhost "%s"' % service, shell=True)
	if res != 0:
		raise failedToSetService

def _remove_service_from_localhost(service):
	ud.debug(ud.MODULE, ud.PROCESS, "Remove service %s from localhost" % service)
	res = subprocess.call('. /usr/share/univention-lib/ldap.sh; ucs_removeServiceFromLocalhost "%s"' % service, shell=True)
	if res != 0:
		raise failedToSetService

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

def remove_install_univention_samba(info_handler=info_handler, step_handler=None, error_handler=error_handler, install=True, uninstall=True):
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
			return False

	return True


def lookup_adds_dc(ad_server=None, ucr=None, check_dns=True):
	'''CLDAP lookup'''

	ud.debug(ud.MODULE, ud.PROCESS, "Lookup ADDS DC")

	ad_domain_info = {}
	ips = []
	lp = LoadParm()
	lp.load('/dev/null')
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()
	if not ad_server:
		ad_server = ucr.get('domainname')

	# get ip addresses
	try:
		ipaddr.IPAddress(ad_server)
		ips.append(ad_server)
	except ValueError:
		dig_sources = []
		for source in ['dns/forwarder1', 'dns/forwarder2', 'dns/forwarder3', 'nameserver1', 'nameserver2', 'nameserver3']:
			if source in ucr:
				dig_sources.append("@%s" % ucr[source])
		for dig_source in dig_sources:
			try:
				cmd = ['dig', dig_source, ad_server, '+short']
				ud.debug(ud.MODULE, ud.PROCESS, "running %s" % cmd)
				p1 = subprocess.Popen(cmd, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				stdout, stderr = p1.communicate()
				ud.debug(ud.MODULE, ud.PROCESS, "stdout: %s" % stdout)
				ud.debug(ud.MODULE, ud.PROCESS, "stderr: %s" % stderr)
				if p1.returncode == 0:
					for i in stdout.split('\n'):
						if i:
							ips.append(i)
				if ips:
					break
			except OSError as ex:
				ud.debug(ud.MODULE, ud.ERROR, "%s failed: %s" % (cmd, ex.args[1]))

	# no ip addresses
	if not ips:
		raise failedADConnect(["Connection to AD Server %s failed" % (ad_server)])

	ad_server_ip = None
	for ip in ips:
		try: # check cldap
			net = Net(creds=None, lp=lp)
			cldap_res = net.finddc(address=ip, flags=nbt.NBT_SERVER_LDAP | nbt.NBT_SERVER_DS | nbt.NBT_SERVER_WRITABLE)
		except RuntimeError as ex:
			ud.debug(ud.MODULE, ud.ERROR, "Connection to AD Server %s failed: %s" % (ip, ex.args[0]))
		else:
			if not check_dns:
				ad_server_ip = ip
				break
			try: # check dns
				cmd = ['dig', '@%s' % ip]
				ud.debug(ud.MODULE, ud.PROCESS, "running %s" % cmd)
				p1 = subprocess.Popen(cmd, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				stdout, stderr = p1.communicate()
				ud.debug(ud.MODULE, ud.PROCESS, "stdout: %s" % stdout)
				ud.debug(ud.MODULE, ud.PROCESS, "stderr: %s" % stderr)
				if p1.returncode == 0: # yes, this is also a DNS server, we are good
					ad_server_ip = ip
					break
			except OSError as ex:
				ud.debug(ud.MODULE, ud.ERROR, "%s failed: %s" % (cmd, ex.args[1]))

	if ad_server_ip is None:
		raise failedADConnect(["Connection to AD Server %s failed" % (ad_server)])

	ad_ldap_base = None
	remote_ldb = ldb.Ldb()
	try:
		remote_ldb.connect(url="ldap://%s" % ad_server_ip)
		ad_ldap_base = str(remote_ldb.get_root_basedn())
	except ldb.LdbError as ex:
		raise failedADConnect(["Could not detect LDAP base on %s: %s" % (ad_server, ex.args[1])])

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
	if not os.path.exists('/etc/init.d/%s' % service):
		return
	try:
		p1 = subprocess.Popen(["invoke-rc.d", service, cmd],
			close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = p1.communicate()
	except OSError as ex:
		ud.debug(ud.MODULE, ud.ERROR, "invoke-rc.d %s %s failed: %s" % (service, cmd, ex.args[1],))
		return

	if p1.returncode:
		ud.debug(ud.MODULE, ud.ERROR, "invoke-rc.d %s %s failed (%d)" % (service, cmd, p1.returncode,))
		return

	ud.debug(ud.MODULE, ud.PROCESS, "invoke-rc.d %s %s: %s" % (service, cmd, stdout)) 


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
		ud.debug(ud.MODULE, ud.ERROR, "rdate -p -n %s: %s" % (ad_ip, ex.args[1]))
		return False

	if p1.returncode:
		ud.debug(ud.MODULE, ud.ERROR, "rdate failed (%d)" % (p1.returncode,))
		return False

	TIME_FORMAT = "%a %b %d %H:%M:%S %Z %Y"
	time_string = stdout.strip()
	old_locale = locale.getlocale(locale.LC_TIME)
	try:
		locale.setlocale(locale.LC_TIME, (None, None)) # 'C' as env['LC_ALL'] some lines earlier
		remote_datetime = datetime.strptime(time_string, TIME_FORMAT)
	except ValueError as ex:
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
			ud.debug(ud.MODULE, ud.WARN, "Remote clock is behind local clock by more than %s seconds, refusing to turn back time." % (tolerance,))
			return False
	else:
		ud.debug(ud.MODULE, ud.PROCESS, "Syncronizing time to %s" % ad_ip)
		p1 = subprocess.Popen(["rdate", "-s", "-n", ad_ip],
			close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = p1.communicate()
		if p1.returncode:
			ud.debug(ud.MODULE, ud.ERROR, "rdate -s -p failed (%d)" % (p1.returncode,))
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
	if ad_domain_info["Domain"].lower() != ucr["domainname"].lower():
		raise domainnameMismatch("The domain of the AD Server does not match the local domain: %s"
			% (ad_domain_info["Domain"],))


def set_nameserver(server_ips, ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()
	count = 1
	for server_ip in server_ips:
		univention.config_registry.handler_set([u'nameserver%d=%s' % (count, server_ip)])
		count += 1
	for i in range(count, 4):
		var = u'nameserver%s' % i
		if ucr.get(var):
			univention.config_registry.handler_unset([var])

def rename_well_known_sid_objects(username, password, ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	ud.debug(ud.MODULE, ud.PROCESS, "Matching well known object names")

	binddn = '%s@%s' % (username, ucr.get('kerberos/realm'))
	p1 = subprocess.Popen(['/usr/share/univention-ad-connector/scripts/well-known-sid-object-rename', '--binddn', binddn, '--bindpwd', password],
		stdout=subprocess.PIPE, stderr=subprocess.PIPE,
		close_fds=True)
	stdout, stderr = p1.communicate()
	ud.debug(ud.MODULE, ud.PROCESS, "%s" % stdout)
	if p1.returncode != 0:
		ud.debug(ud.MODULE, ud.ERROR, "well-known-sid-object-rename failed with %d (%s)" % (p1.returncode, stderr))
		raise connectionFailed()

def make_deleted_objects_readable_for_this_machine(username, password, ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()

	ud.debug(ud.MODULE, ud.PROCESS, "Make Deleted Objects readable for this machine")

	binddn = '%s@%s' % (username, ucr.get('kerberos/realm'))
	p1 = subprocess.Popen(['/usr/share/univention-ad-connector/scripts/make-deleted-objects-readable-for-this-machine', '--binddn', binddn, '--bindpwd', password],
		stdout=subprocess.PIPE, stderr=subprocess.PIPE,
		close_fds=True)
	stdout, stderr = p1.communicate()
	ud.debug(ud.MODULE, ud.PROCESS, "%s" % stdout)
	if p1.returncode != 0:
		ud.debug(ud.MODULE, ud.ERROR, "make-deleted-objects-readable-for-this-machine failed with %d (%s)" % (p1.returncode, stderr))
		raise connectionFailed()

def prepare_dns_reverse_settings(ad_server_ip, ad_domain_info):
	# For python-ldap / GSSAPI / AD we need working reverse looksups
	try:
		socket.gethostbyaddr(ad_server_ip)
	except socket.herror:
		ip = socket.gethostbyname(ad_domain_info['DC DNS Name'])
		univention.config_registry.handler_set([u'hosts/static/%s=%s' % (ip, ad_domain_info['DC DNS Name'])])
	

def prepare_ucr_settings():

	ud.debug(ud.MODULE, ud.PROCESS, "Prepare UCR settings")

	# Show warnings in UMC
	# Change displayed name of users from "username" to "displayName" (as in AD)
	ucr_set = [
		u'kerberos/defaults/dns_lookup_kdc=true',
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

	ucr_unset = [
		u'kerberos/kdc',
		u'kerberos/kpasswdserver',
		u'kerberos/adminserver',
	]
	ud.debug(ud.MODULE, ud.PROCESS, "Unsetting UCR variables: %s" % ucr_unset)
	univention.config_registry.handler_unset(ucr_unset)


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
	stop_service("samba4")
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

	binddn = 'uid=%s,cn=users,%s' % (username, ucr.get('ldap/base'))
	my_env = os.environ
	my_env['SMB_CONF_PATH'] = '/etc/samba/smb.conf'
	p1 = subprocess.Popen(['/usr/lib/univention-install/26univention-samba.inst', '--binddn', binddn, '--bindpwd', password],
		close_fds=True, env=my_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = p1.communicate()
	ud.debug(ud.MODULE, ud.PROCESS, "%s" % stdout)
	if p1.returncode != 0:
		ud.debug(ud.MODULE, ud.ERROR, "26univention-samba.inst failed with %d (%s)" % (p1.returncode, stderr))
		raise sambaJoinScriptFailed()


def add_domaincontroller_srv_record_in_ad(ad_ip, ucr=None):
	if not ucr:
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()
	
	ud.debug(ud.MODULE, ud.PROCESS, "Create _domaincontroller_master SRV record on %s" % ad_ip)
	
	fd = tempfile.NamedTemporaryFile(delete=False)
	fd.write('server %s\n' % ad_ip)
	fd.write('update add _domaincontroller_master._tcp.%s. 10800 SRV 0 0 0 %s.%s.\n' %
		(ucr.get('domainname'), ucr.get('hostname'), ucr.get('domainname')))
	fd.write('send\n')
	fd.write('quit\n')
	fd.close()

	cmd = ['kinit', '--password-file=/etc/machine.secret']
	cmd += ['%s\$' % ucr.get('hostname')]
	cmd += ['nsupdate', '-v', '-g', fd.name]
	p1 = subprocess.Popen(cmd, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = p1.communicate()
	ud.debug(ud.MODULE, ud.PROCESS, "%s" % stdout)
	if p1.returncode:
		ud.debug(ud.MODULE, ud.ERROR, "%s failed with %d (%s)" % (cmd, p1.returncode, stderr))
		raise failedToAddServiceRecordToAD("failed to add SRV record to %s" % ad_ip)
	os.unlink(fd.name)


def get_ucr_variable_from_ucs(host, server, var):
	cmd = ['univention-ssh', '/etc/machine.secret']
	cmd += ['%s\$@%s' % (host, server)]
	cmd += ['/usr/sbin/ucr get %s' % var]
	p1 = subprocess.Popen(cmd, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = p1.communicate()
	if p1.returncode:
		ud.debug(ud.MODULE, ud.ERROR, "%s failed with %d (%s)" % (cmd, p1.returncode, stderr))
		raise failedToGetUcrVariable("failed to get UCR variable %s from %s" % (var, server))
	return stdout.strip()


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

	check_connection(ad_server_ip, username, password)

	time_sync(ad_server_ip)

	set_timeserver(ad_server_ip)

	set_nameserver([ad_server_ip])

	prepare_ucr_settings()

	add_admember_service_to_localhost()

	disable_local_heimdal()
	disable_local_samba4()

	prepare_administrator(username, password)

	prepare_dns_reverse_settings(ad_server_ip, ad_domain_info)

	remove_install_univention_samba()

	prepare_connector_settings(username, password, ad_domain_info)

	rename_well_known_sid_objects(username, password)

	run_samba_join_script(username, password)

	add_domaincontroller_srv_record_in_ad(ad_server_ip)

	
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

def revert_backup_ad_member ():
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

