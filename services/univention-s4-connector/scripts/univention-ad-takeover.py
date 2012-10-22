#!/usr/bin/python2.6
#
# Univention Migrate SBS
#  Migrates a SBS server to the local Samba 4 system
#
# Copyright 2012-2013 Univention GmbH
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

from optparse import OptionParser, OptionValueError
import samba.getopt
import sys, os
import subprocess
import shutil
from univention import config_registry
import ldb
import samba
from samba.samdb import SamDB
from samba.auth import system_session
from samba.param import LoadParm
import socket, time, struct
import ldap
import re
from samba.ndr import ndr_pack, ndr_unpack
from samba.dcerpc import security
import univention.admin.uldap
import univention.admin.uexceptions
import string
import sqlite3
import univention.admin.modules
import univention.admin.objects
import univention.admin.config
import ipaddr

samba_dir = '/var/lib/samba'
samba_private_dir = os.path.join(samba_dir, 'private')
sysvol_path = os.path.join(samba_dir, 'sysvol')

well_known_sids = {
	"Null Authority": "S-1-0",
	"Nobody": "S-1-0-0",
	"World Authority": "S-1-1",
	"Everyone": "S-1-1-0",
	"Local Authority": "S-1-2",
	"Local": "S-1-2-0",
	"Console Logon": "S-1-2-1",
	"Creator Authority": "S-1-3",
	"Creator Owner": "S-1-3-0",
	"Creator Group": "S-1-3-1",
	"Creator Owner Server": "S-1-3-2",
	"Creator Group Server": "S-1-3-3",
	"Owner Rights":	"S-1-3-4",
	"All Services": "S-1-5-80-0",
	"Non-unique Authority": "S-1-4",
	"NT Authority": "S-1-5",
	"Dialup": "S-1-5-1",
	"Network": "S-1-5-2",
	"Batch": "S-1-5-3",
	"Interactive": "S-1-5-4",
	"Service": "S-1-5-6",
	"Anonymous": "S-1-5-7",
	"Proxy": "S-1-5-8",
	"Enterprise Domain Controllers": "S-1-5-9",
	"Principal Self": "S-1-5-10",
	"Authenticated Users": "S-1-5-11",
	"Restricted Code": "S-1-5-12",
	"Terminal Server Users": "S-1-5-13",
	"Remote Interactive Logon": "S-1-5-14",
	"This Organization": "S-1-5-15",
	"IUSR": "S-1-5-17",
	"Local System": "S-1-5-18",
	"NT Authority": "S-1-5-20",
	"Administrators": "S-1-5-32-544",
	"Users": "S-1-5-32-545",
	"Guests": "S-1-5-32-546",
	"Power Users": "S-1-5-32-547",
	"Account Operators": "S-1-5-32-548",
	"Server Operators": "S-1-5-32-549",
	"System Operators": "S-1-5-32-549",	## duplicate names
	"Print Operators": "S-1-5-32-550",
	"Backup Operators": "S-1-5-32-551",
	"Replicators": "S-1-5-32-552",
}

well_known_domain_rids = {
	"Administrator": 500,
	"Guest": 501,
	"KRBTGT": 502,
	"Domain Admins": 512,
	"Domain Users": 513,
	"Domain Guests": 514,
	"Domain Computers": 515,
	"Domain Controllers": 516,
	"Cert Publishers": 517,
	"Schema Admins": 518,
	"Enterprise Admins": 519,
	"Group Policy Creator Owners": 520,
	"RAS and IAS Servers": 553,
	## Windows Server 2008
	"Enterprise Read-only Domain Controllers": 498,
	"Read-Only Domain Controllers": 521,
	"Allowed RODC Password Replication Group": 571,
	"Denied RODC Password Replication Group": 572,
	## Windows Server "8"
	"Cloneable Domain Controllers": 522,
}

def _connect_ucs(ucr, binddn=None, bindpwd=None):
	''' Connect to OpenLDAP '''

	if binddn and bindpwd:
		bindpw = bindpwd
	else:
		bindpw_file = ucr.get('connector/ldap/bindpw', '/etc/ldap.secret')
		binddn = ucr.get('connector/ldap/binddn', 'cn=admin,'+ucr['ldap/base'])
		bindpw=open(bindpw_file).read()
		if bindpw[-1] == '\n':
			bindpw=bindpw[0:-1]

	host = ucr.get('connector/ldap/server', ucr.get('ldap/master'))

	try:
		port = int(ucr.get('connector/ldap/port', ucr.get('ldap/master/port')))
	except:
		port = 7389

	lo = univention.admin.uldap.access(host=host, port=port, base=ucr['ldap/base'], binddn=binddn, bindpw=bindpw, start_tls=0, follow_referral=True)

	return lo

def operatingSystem_attribute(ucr, samdb):
	msg = samdb.search(base=samdb.domain_dn(), scope=samba.ldb.SCOPE_SUBTREE,
                                expression="(sAMAccountName=%s$)" % ucr["hostname"],
                                attrs=["operatingSystem", "operatingSystemVersion"])
	if msg:
		obj = msg[0]
		if not "operatingSystem" in obj:
			delta = ldb.Message()
			delta.dn = obj.dn
			delta["operatingSystem"] = ldb.MessageElement("Univention Corporate Server", ldb.FLAG_MOD_REPLACE, "operatingSystem")
			samdb.modify(delta)
		if not "operatingSystemVersion" in obj:
			delta = ldb.Message()
			delta.dn = obj.dn
			delta["operatingSystemVersion"] = ldb.MessageElement("3.0", ldb.FLAG_MOD_REPLACE, "operatingSystemVersion")
			samdb.modify(delta)
			
def takeover_DC_Behavior_Version(ucr, remote_samdb, samdb, ad_server_name, sitename):
	## DC Behaviour Version
	msg = remote_samdb.search(base="CN=NTDS Settings,CN=%s,CN=Servers,CN=%s,CN=Sites,CN=Configuration,%s" % (ad_server_name, sitename, samdb.domain_dn()), scope=samba.ldb.SCOPE_BASE,
                                attrs=["msDS-HasMasterNCs", "msDS-HasInstantiatedNCs", "msDS-Behavior-Version"])
	if msg:
		obj = msg[0]
		if "msDS-Behavior-Version" in obj:
			delta = ldb.Message()
			delta.dn = ldb.Dn(samdb, dn="CN=NTDS Settings,CN=%s,CN=Servers,CN=%s,CN=Sites,CN=Configuration,%s" % (ucr["hostname"], sitename, samdb.domain_dn()))
			delta["msDS-Behavior-Version"] = ldb.MessageElement(obj["msDS-Behavior-Version"], ldb.FLAG_MOD_REPLACE, "msDS-Behavior-Version")
			samdb.modify(delta)

def takeover_hasInstantiatedNCs(ucr, samdb, ad_server_name, sitename):
	msg = samdb.search(base="CN=NTDS Settings,CN=%s,CN=Servers,CN=%s,CN=Sites,CN=Configuration,%s" % (ad_server_name, sitename, samdb.domain_dn()), scope=samba.ldb.SCOPE_BASE,
                                attrs=["msDS-hasMasterNCs", "msDS-HasInstantiatedNCs"])
	partitions=[]
	if msg:
		obj = msg[0]
		delta = ldb.Message()
		delta.dn = ldb.Dn(samdb, dn="CN=NTDS Settings,CN=%s,CN=Servers,CN=%s,CN=Sites,CN=Configuration,%s" % (ucr["hostname"], sitename, samdb.domain_dn()))
		if "msDS-HasInstantiatedNCs" in obj:
			for partitionDN in obj["msDS-HasInstantiatedNCs"]:
				delta[partitionDN] = ldb.MessageElement(obj["msDS-HasInstantiatedNCs"], ldb.FLAG_MOD_REPLACE, "msDS-HasInstantiatedNCs")
		if "msDS-HasInstantiatedNCs" in delta:
			samdb.modify(delta)

		## and note the msDS-hasMasterNCs values for fsmo takeover
		if "msDS-hasMasterNCs" in obj:
			for partitionDN in obj["msDS-hasMasterNCs"]:
				partitions.append(partitionDN)
	return partitions

def takeover_hasMasterNCs(ucr, samdb, sitename, partitions):
	msg = samdb.search(base="CN=NTDS Settings,CN=%s,CN=Servers,CN=%s,CN=Sites,CN=Configuration,%s" % (ucr["hostname"], sitename, samdb.domain_dn()), scope=samba.ldb.SCOPE_BASE, attrs=["hasPartialReplicaNCs", "msDS-hasMasterNCs"])
	if msg:
		obj = msg[0]
		for partition in partitions:
			if "hasPartialReplicaNCs" in obj and partition in obj["hasPartialReplicaNCs"]:
				print "Removing hasPartialReplicaNCs on %s for %s" % (ucr["hostname"], partition)
				delta = ldb.Message()
				delta.dn = obj.dn
				delta["hasPartialReplicaNCs"] = ldb.MessageElement(partition, ldb.FLAG_MOD_DELETE, "hasPartialReplicaNCs")
				try:
					samdb.modify(delta)
				except:
					print "Failed to remove hasPartialReplicaNCs %s from %s" % (partition, ucr["hostname"])
					print "Current NTDS object: %s" % obj

			if "msDS-hasMasterNCs" in obj and partition in obj["msDS-hasMasterNCs"]:
				print "Naming context %s already registed in msDS-hasMasterNCs for %s" % (partition, ucr["hostname"])
			else:
				delta = ldb.Message()
				delta.dn = obj.dn
				delta[partition] = ldb.MessageElement(partition, ldb.FLAG_MOD_ADD, "msDS-hasMasterNCs")
				try:
					samdb.modify(delta)
				except:
					print "Failed to add msDS-hasMasterNCs %s to %s" % (partition, ucr["hostname"])
					print "Current NTDS object: %s" % obj

def let_samba4_manage_etc_krb5_keytab(ucr, secretsdb):

	msg = secretsdb.search(base="cn=Primary Domains", scope=samba.ldb.SCOPE_SUBTREE,
                                expression="(flatName=%s)" % ucr["windows/domain"],
                                attrs=["krb5Keytab"])
	if msg:
		obj = msg[0]
		if not "krb5Keytab" in obj or not "/etc/krb5.keytab" in obj["krb5Keytab"]:
			delta = ldb.Message()
			delta.dn = obj.dn
			delta["krb5Keytab"] = ldb.MessageElement("/etc/krb5.keytab", ldb.FLAG_MOD_ADD, "krb5Keytab")
			secretsdb.modify(delta)

def add_servicePrincipals(ucr, secretsdb, spn_list):
	msg = secretsdb.search(base="cn=Primary Domains", scope=samba.ldb.SCOPE_SUBTREE,
                                expression="(flatName=%s)" % ucr["windows/domain"],
                                attrs=["servicePrincipalName"])
	if msg:
		obj = msg[0]
		delta = ldb.Message()
		delta.dn = obj.dn
		for spn in spn_list:
			if not "servicePrincipalName" in obj or not spn in obj["servicePrincipalName"]:
				delta[spn] = ldb.MessageElement(spn, ldb.FLAG_MOD_ADD, "servicePrincipalName")
		secretsdb.modify(delta)

def sync_time(server):
	## source: http://code.activestate.com/recipes/117211-simple-very-sntp-client/
	TIME1970 = 2208988800L      # Thanks to F.Lundh

	client = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
	data = '\x1b' + 47 * '\0'
	client.settimeout(15.0)
	try:
		client.sendto( data, ( server, 123 ))
		data, address = client.recvfrom( 1024 )
		if data:
			print 'NTP Response received from server %s' % server
			t = struct.unpack( '!12I', data )[10]
			t -= TIME1970
			offset = time.time() - t
			print "The local clock differs from the clock on %s by about %s seconds." % (server, int(round(offset)))
			if abs(time.time() - t) < 180:
				print "The offest is less than three minutes, that should be good enough for Kerberos."
			elif time.gmtime(t) >= time.gmtime():
				print "Setting local time: ",
				p = subprocess.Popen(["/bin/date", "-s", time.ctime(t)], stdout=subprocess.PIPE)
				(stdout, stderr) = p.communicate()
				print stdout
			else:
				print "Error: time %s on server %s is earlier than" % (time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.localtime(t)), server)
				print "       time %s on this server!" % time.strftime("%a, %d %b %Y %H:%M:%S %Z", time.localtime())
				print "       Refusing to reset time on this server to avoid SSL certificate problems."
				print "       Please check time on server %s" % server
				sys.exit(1)
	except socket.error:
		print "Warning: Could not retrive time from %s via NTP" % server

def check_for_phase_II(ucr, lp, ad_server_ip):
	## Check if we are in Phase II and the AD server is already switched off:
	if "hosts/static/%s" % ad_server_ip in ucr:
		ad_server_fqdn, ad_server_name = ucr["hosts/static/%s" % ad_server_ip].split()

		## Check if the AD server is already in the local SAM db
		samdb = SamDB(os.path.join(samba_private_dir, "sam.ldb"), session_info=system_session(lp), lp=lp)
		msgs = samdb.search(base=ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_SUBTREE,
					expression="(sAMAccountName=%s$)" % ad_server_name,
					attrs=["objectSid"])
		if msgs:
			return (1, ad_server_fqdn, ad_server_name)
		else:
			return (2, ad_server_fqdn, ad_server_name)
	return (0, None, None)

def sync_position_s4_to_ucs(ucr, udm_type, ucs_object_dn, s4_object_dn):
	rdn_list = ldap.explode_dn(s4_object_dn)
	rdn_list.pop(0)
	new_position = string.replace(','.join(rdn_list).lower(), ucr['connector/s4/ldap/base'].lower(), ucr['ldap/base'].lower())

	rdn_list = ldap.explode_dn(ucs_object_dn)
	rdn_list.pop(0)
	old_position = ','.join(rdn_list)

	if new_position.lower() != old_position.lower():
		p = subprocess.Popen(["/usr/sbin/univention-directory-manager", udm_type, "move", "--dn", ucs_object_dn, "--position", new_position])
		p.wait()

def print_dot():
	sys.stdout.write(".")
	sys.stdout.flush()

def get_stable_last_id(progress_function = None, max_time=20):
	last_id_cached_value = None
	static_count = 0
	t = t_0 = time.time()
	while static_count < 3:
		if last_id_cached_value:
			time.sleep (0.1)
		with file("/var/lib/univention-ldap/last_id") as f:
			last_id = f.read().strip()
		if last_id != last_id_cached_value:
			static_count = 0
			last_id_cached_value = last_id
		elif last_id:
			static_count = static_count + 1
		delta_t = time.time() - t
		t = t + delta_t
		if t - t_0 > max_time:
			print
			return None
		if progress_function and delta_t >= 1:
			progress_function()
	return last_id

def wait_for_listener_replication(progress_function = None, max_time=20):
	notifier_id_cached_value = None
	static_count = 0
	t = t_0 = time.time()
	while static_count < 3:
		if notifier_id_cached_value:
			time.sleep (0.7)
		last_id = get_stable_last_id(progress_function)
		with file("/var/lib/univention-directory-listener/notifier_id") as f:
			notifier_id = f.read().strip()
		if not last_id:
			return False
		elif last_id != notifier_id:
			static_count = 0
			notifier_id_cached_value = notifier_id
		else:
			static_count = static_count + 1
		delta_t = time.time() - t
		t = t + delta_t
		if t - t_0 > max_time:
			print
			print "Warning: Listener ID not yet up to date (last_id=%s, listener ID=%s). Waited for about %s seconds." % (last_id, notifier_id, int(round(t - t_0)))
			return False
		if progress_function and delta_t >= 1:
			progress_function()
	if progress_function and t - t_0 > 3:
		print
	return True

def wait_for_s4_connector_replication(ucr, progress_function = None, max_time=None):
	
	conn = sqlite3.connect('/etc/univention/connector/s4internal.sqlite')
	c = conn.cursor()

	static_count = 0
	cache_S4_rejects = None
	foldername = "/var/lib/univention-connector/s4"
	t = t_0 = time.time()

	ucr.load()	## load current values
	connector_s4_poll_sleep = int(ucr.get("connector/s4/poll/sleep", "5"))
	connector_s4_retryrejected = int(ucr.get("connector/s4/retryrejected", "10"))
	required_static_count = 5 * connector_s4_retryrejected

	if not max_time:
		max_time = 10 * connector_s4_retryrejected * connector_s4_poll_sleep
		print "Waiting for S4 Connector sync (max. %s seconds)" % int(round(max_time))

	while static_count < required_static_count:
		time.sleep (connector_s4_poll_sleep)

		c.execute('select key from "UCS rejected";')
		conn.commit()
		known_files = [ row[0] for row in c.fetchall() ]

		c.execute('select key from "S4 rejected";')
		conn.commit()
		count_S4_rejects = len(c.fetchall())

		if count_S4_rejects != cache_S4_rejects:
			cache_S4_rejects = count_S4_rejects
			static_count = 0
			continue

		for entry in os.listdir(foldername):
			filename = os.path.join(foldername, entry)
			if os.path.isfile(filename):
				if not filename in known_files:
					static_count = 0
					break
		else:
			static_count = static_count + 1
		delta_t = time.time() - t
		t = t + delta_t
		if t - t_0 > max_time:
			print
			print "Warning: S4 Connector not yet up to date. Waited for about %s seconds." % (int(round(t - t_0),))
			return False
		if progress_function and delta_t >= 1:
			progress_function()
	if progress_function and t - t_0 > 3:
		print
	return True

	conn.close()

def check_samba4_started():
	for i in xrange(5):
		time.sleep(1)
		p = subprocess.Popen(["pgrep", "-cxf", "/usr/sbin/samba -D"], stdout=subprocess.PIPE)
		(stdout, stderr) = p.communicate()
		if int(stdout) > 1:
			break
	else:
		if int(stdout) == 1:
			p = subprocess.Popen(["/etc/init.d/samba4", "stop"])
			p.wait()
			p = subprocess.Popen(["pkill", "-9", "-xf", "/usr/sbin/samba -D"], stdout=subprocess.PIPE)
			p.wait()
			p = subprocess.Popen(["pgrep", "-cxf", "/usr/sbin/samba -D"], stdout=subprocess.PIPE)
			(stdout, stderr) = p.communicate()
			if int(stdout) > 0:
				print "ERROR: Stray Processes:", int(stdout)
				p = subprocess.Popen(["pkill", "-9", "-xf", "/usr/sbin/samba -D"], stdout=subprocess.PIPE)
				p.wait()
			p = subprocess.Popen(["/etc/init.d/samba4", "start"])
			p.wait()
			## fallback
			time.sleep(2)
			p = subprocess.Popen(["pgrep", "-cxf", "/usr/sbin/samba -D"], stdout=subprocess.PIPE)
			(stdout, stderr) = p.communicate()
			if int(stdout) == 1:
				print "ERROR: Stray Processes:", int(stdout)
				p = subprocess.Popen(["pkill", "-9", "-xf", "/usr/sbin/samba -D"], stdout=subprocess.PIPE)
				p.wait()
				p = subprocess.Popen(["/etc/init.d/samba4", "start"])
				p.wait()

def run_phaseI(opts, args):

	ad_server_name = None
	if len(args) > 0:
		ad_server_ip = args[0]
	if len(args) == 2:
		ad_server_name = args[1]
	elif len(args) != 1:
		parser.print_usage()
		sys.exit(1)

	devnull = open('/dev/null', 'w')

	ucr = config_registry.ConfigRegistry()
	ucr.load()
	local_fqdn = '.'.join((ucr["hostname"], ucr["domainname"]))

        # lp = LoadParm()
        # lp.load('/etc/samba/smb.conf')
	lp = sambaopts.get_loadparm()

	### First plausibility checks

	## 1.a Check that local domainname matches kerberos realm
	if ucr["domainname"].lower() != ucr["kerberos/realm"].lower():
		print "Mismatching DNS domain and kerberos realm. Please reinstall the server with the same Domain as your AD"
		sys.exit(1)

	## 1.b ping the given AD server IP
	print "Pinging AD IP %s: " % ad_server_ip,
	p1 = subprocess.Popen(["fping", ad_server_ip], stdout=devnull, stderr=devnull)
	rc= p1.poll()
	while rc is None:
		time.sleep(1)
		print_dot()
		rc= p1.poll()
	print
	if rc != 0:
		## Check if we are in Phase II and the AD server is already switched off:
		(rc, tmp_fqdn, tmp_name) = check_for_phase_II(ucr, lp, ad_server_ip)
		if rc == 0:
			print "Error: Server IP %s not reachable" % ad_server_ip
		elif rc == 1:
			print "Note: The AD Server IP %s not reachable" % ad_server_ip
			print "Error: But found the AD DC %s account already in the Samba 4 SAM backend" % tmp_name
			print "       Looks like it was switched of to finalize the migration?"
			print "       If this is true, then restart this script with option --fsmo-takeover"
		elif rc == 2:
			print "Error: Server IP %s not reachable" % ad_server_ip
			print "Error: It seems that this script was run once already for the first migration step,"
			print "       but the server %s cannot be found in the local Samba SAM database." % tmp_name
			print "       Don't know how to continue, giving up at this point."
		sys.exit(1)
	else:
		print "Ok, Server IP %s is online." % ad_server_ip

	## 1.c Check, if the given AD Credentials work
	creds = credopts.get_credentials(lp)
	if creds.get_username() == "root":
		creds.set_username("Administrator")
	ad_join_user = creds.get_username()
	ad_join_password = creds.get_password()

	try:
		remote_samdb = SamDB("ldap://%s" % ad_server_ip, credentials=creds, session_info=system_session(lp), lp=lp)
	except:
		print "Error: Cannot connect to ldap://%s/ as %s\%s" % (ad_server_ip, creds.get_domain(), ad_join_user)
		print "       Please check the given credentials."
		sys.exit(1)

	p = subprocess.Popen(["smbclient", "//%s/sysvol" % ad_server_ip, "-U%s%%%s" % (ad_join_user, ad_join_password), '-c', 'quit'], stdout=devnull, stderr=devnull)
	if p.wait() != 0:
		print "Error: Cannot connect to //%s/sysvol as %s\%s" % (ad_server_ip, creds.get_domain(), ad_join_user)
		print "       Please check the given credentials."
		sys.exit(1)

	## 1.d Check, if a AD DNS domain is given and if it matches the local one
	ad_server_fqdn = None
	if ad_server_name:
		char_idx = ad_server_name.find(".")
		if char_idx == -1:
			ad_server_fqdn = "%s.%s" % (ad_server_name, ucr["domainname"])
		else:
			ad_server_fqdn = ad_server_name
	else:
		try:
			p1 = subprocess.Popen(["dig", "@%s" % ad_server_ip, "SRV", "_kerberos._tcp.dc._msdcs.%s" % ucr["domainname"], "+short"], stdout=subprocess.PIPE)
			(stdout, stderr) = p1.communicate()
		except:
			print "Error: DNS lookup for DC at IP %s failed." % ad_server_ip
			print "Please retry by passing the AD server name as additional command line argument"
			sys.exit(1)

		lines = stdout.rstrip('\n').split('\n')
		if not stdout:
			print "Error: DNS lookup for DC at IP %s failed." % ad_server_ip
			msgs = remote_samdb.search(base="DC=DomainDnsZones,%s" % ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_SUBTREE,
                                		expression="(DC=_kerberos._tcp)",
										attrs=["dn"])
			if msgs:
				obj = msgs[0]
				p = re.compile("DC=_kerberos._tcp,DC=([^,]*),.*")
				m = p.match(obj["dn"].get_linearized())
				if len(m.groups()) == 1:
					remote_domainname = m.group(1)
					if remote_domainname != ucr["domainname"]:
						print "Local machine does not seem to be installed with the same domainname as the AD domain!"
						print "Remote domain lookup returned: %s" % remote_domainname
						print "Local domain: %s" % ucr["domainname"]
					else:
						print "Please retry by passing the AD server name as additional command line argument"
				else:
					print "Please retry by passing the AD server name as additional command line argument"
			else:
				print "Please retry by passing the AD server name as additional command line argument"
			sys.exit(1)
		elif len(lines) > 1:
			print "Warning: Multiple DCs registered for DNS SRV record _kerberos._tcp.dc._msdcs.%s"  % ucr["domainname"]
			local_fqdn_found_in_AD_SRV = False
			for line in lines:
				tmp_fqdn = line.split()[3].rstrip('.')
				if tmp_fqdn == local_fqdn:
					print "Warning: This UCS server is already registered as DC at the DNS server %s" % ad_server_ip
					local_fqdn_found_in_AD_SRV = True
					continue
				else:
					p1 = subprocess.Popen(["dig", "@%s" % ad_server_ip, tmp_fqdn, "+short"], stdout=subprocess.PIPE)
					(stdout, stderr) = p1.communicate()
					if stdout.strip('\n') == ad_server_ip:
						if not ad_server_fqdn:
							ad_server_fqdn = tmp_fqdn
						else:
							print "Error: More than one of the registered DC FQDNs matches the given AD server IP:"
							print "       %s" % ad_server_fqdn
							print "       %s" % tmp_fqdn
							print "Error: Failed to determine DC for IP %s" % ad_server_ip
							print "Please retry by passing the AD server name as additional command line argument"
							sys.exit(1)

			if not ad_server_fqdn:
				print "Error: Failed to determine DC for IP %s" % ad_server_ip
				print "Please retry by passing the AD server name as additional command line argument"
				sys.exit(1)
			else:
				print "Sucessfull determined AD DC FQDN %s for given IP %s" % (ad_server_fqdn, ad_server_ip)

			if local_fqdn_found_in_AD_SRV and ad_server_fqdn:
				## Check if we are in Phase II and the AD server is already switched off:
				(rc, tmp_fqdn, tmp_name) = check_for_phase_II(ucr, lp, ad_server_ip)
				if rc == 0:
					pass
				elif rc == 1:
					print "Error: Account for the AD DC %s is already the Samba 4 SAM backend." % tmp_name
					print "       It seems that this script was run once already for the first migration step."
					print "       If this is true, then go over to the AD DC to migrate the SYSVOL,"
					print "       and switch it off before restarting this script with option --fsmo-takeover"
					sys.exit(1)
				elif rc == 2:
					print "Error: It seems that this script was run once already for the first migration step,"
					print "       but the server %s cannot be found in the local Samba SAM database." % tmp_name
					print "       Don't know how to continue, giving up at this point."
					sys.exit(1)

		else:
			## OK, we have a unique match
			try:
				ad_server_fqdn = lines[0].split()[3]
				ad_server_fqdn = ad_server_fqdn.rstrip('.')
				print "Sucessfull determined AD DC FQDN %s for given IP %s" % (ad_server_fqdn, ad_server_ip)
			except:
				print "Error: Parsing of DNS SRV record failed: '%s'" % lines
				print "Please retry by passing the AD server name as additional command line argument"
				sys.exit(1)

	char_idx = ad_server_fqdn.find(".")
	if char_idx == -1:
		print "Error: AD server did not return FQDN for IP %s" % ad_server_ip
		print "Please retry by passing the AD server name as additional command line argument"
		sys.exit(1)
	elif not ad_server_fqdn[char_idx+1:] == ucr["domainname"]:
		print "Error: local DNS domain %s does not match AD server DNS domain." % ucr["domainname"]
		sys.exit(1)
	else:
		ad_server_name = ad_server_fqdn.split('.', 1)[0]
	
	## 2. Check, if there is a DNS Server running at ad_server_ip which is
	## able to resolve ad_server_fqdn
	p1 = subprocess.Popen(["dig", "@%s" % ad_server_ip, ad_server_fqdn, "+short"], stdout=subprocess.PIPE)
	(stdout, stderr) = p1.communicate()
	if not stdout.strip('\n') == ad_server_ip:
		print "Error: Cannot resolve DNS name %s using DNS server %s" % (ad_server_fqdn, ad_server_ip)
		print "       Please check DNS name, IP or configuration."
		sys.exit(1)

	## 4. Determine Site of given server, important for locale-dependend names like "Standardname-des-ersten-Standorts"
	sitename = None
	msgs = remote_samdb.search(base=ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_SUBTREE,
                                expression="(sAMAccountName=%s$)" % ad_server_name,
                                attrs=["serverReferenceBL"])
	if msgs:
		obj = msgs[0]
		serverReferenceBL = obj["serverReferenceBL"][0]
		serverReferenceBL_RDNs = ldap.explode_dn(serverReferenceBL)
		serverReferenceBL_RDNs.reverse()
		config_partition_index = None
		site_container_index = None
		for i in xrange(len(serverReferenceBL_RDNs)):
			if site_container_index:
				sitename = serverReferenceBL_RDNs[i].split('=', 1)[1]
				break
			elif config_partition_index and serverReferenceBL_RDNs[i] == "CN=Sites":
				site_container_index = i
			elif not site_container_index and serverReferenceBL_RDNs[i] == "CN=Configuration":
				config_partition_index = i
			i = i+1
		print "Located server %s site %s in AD SAM" % (ad_server_fqdn, sitename)

	## OK, we are quite shure that we have the basics right, note the AD server IP and FQDN in UCR for phase II
	config_registry.handler_set(["hosts/static/%s=%s %s" % (ad_server_ip, ad_server_fqdn, ad_server_name) ])

	### Phase I.a: Join to AD

	## Essential: Sync the time
	sync_time(ad_server_ip)

	## Stop the S4 Connector for phase I
	p = subprocess.Popen(["/etc/init.d/univention-s4-connector", "stop"], stdout=devnull, stderr=devnull)
	p.wait()

	## Stop Samba
	p = subprocess.Popen(["/etc/init.d/samba4", "stop"])
	p.wait()

	## Move current Samba directory out of the way
	if os.path.exists(samba_dir):
		backup_samba_dir = "%s.bak" % samba_private_dir
		if not os.path.exists(backup_samba_dir):
			os.rename(samba_private_dir, backup_samba_dir)
			os.makedirs(samba_private_dir)
		else:
			shutil.rmtree(samba_private_dir)
			os.mkdir(samba_private_dir)

	## Adjust some UCR settings
	if "nameserver1/local" in ucr:
		nameserver1_orig = ucr["nameserver1/local"]
	else:
		nameserver1_orig = ucr["nameserver1"]
		config_registry.handler_set(["nameserver1/local=%s" % nameserver1_orig, "nameserver1=%s" % ad_server_ip])

	config_registry.handler_set(["directory/manager/web/modules/users/user/properties/username/syntax=string"])
	config_registry.handler_set(["dns/backend=ldap"])
	ucr.load()

	## Stop the NSCD
	p = subprocess.Popen(["/etc/init.d/nscd", "stop"])
	p.wait()

	## Restart bind9 to use the OpenLDAP backend, just to be sure
	p = subprocess.Popen(["/etc/init.d/bind9", "restart"])
	p.wait()

	## Get machine credentials
	try:
		machine_secret = open('/etc/machine.secret','r').read().strip()
	except IOError, e:
		univention.debug.debug(univention.debug.ADMIN, univention.debug.ERROR, 'Could not read machine credentials: %s', str(e))
		sys.exit(1)

	## Join into the domain
	if sitename:
		p = subprocess.Popen(["/usr/sbin/samba-tool", "domain", "join", ucr["domainname"], "DC", "-U%s%%%s" % (ad_join_user, ad_join_password), "--realm=%s" % ucr["kerberos/realm"], "--machinepass=%s" % machine_secret, "--server=%s" % ad_server_fqdn, "--site=%s" % sitename])
		if p.wait() != 0:
			sys.exit(1)
	else:
		print "Error: Cannot determine site for server %s" % ad_server_fqdn
		sys.exit(1)

	## Fix some attributes in local SamDB
	ad_domainsid = None
        samdb = SamDB(os.path.join(samba_private_dir, "sam.ldb"), session_info=system_session(lp), lp=lp)
	msgs = samdb.search(base=ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_BASE,
				expression="(objectClass=domain)",
				attrs=["objectSid"])
	if msgs:
		obj = msgs[0]
		ad_domainsid = str(ndr_unpack(security.dom_sid, obj["objectSid"][0]))
	if not ad_domainsid:
		print "Error: Could not determine domain SID"
		sys.exit(1)

	old_domainsid = None
	lo = _connect_ucs(ucr)
	ldap_result = lo.search(filter="(&(objectClass=sambaDomain)(sambaDomainName=%s))" % ucr["windows/domain"], attr=["sambaSID"])
	if len(ldap_result) == 1:
		ucs_object_dn = ldap_result[0][0]

		if os.path.exists("/var/tmp/old_sambasid"):
			f = open("/var/tmp/old_sambasid", 'r')
			old_domainsid = f.read()
			f.close()
		else:
			old_domainsid = ldap_result[0][1]["sambaSID"][0]
			f = open("/var/tmp/old_sambasid", 'w')
			f.write("%s" % old_domainsid)
			f.close()
	elif len(ldap_result) > 0:
		print 'ERROR: Found more than one sambaDomain object with sambaDomainName=%s' % ucr["windows/domain"]
	else:
		print 'ERROR: Did not find a sambaDomain object with sambaDomainName=%s' % ucr["windows/domain"]

	print "Replacing OLD sambaSID: %s" % old_domainsid
	if old_domainsid != ad_domainsid:
		ml = [("sambaSID", old_domainsid, ad_domainsid)]
		lo.modify(ucs_object_dn, ml)

	operatingSystem_attribute(ucr, samdb)
	takeover_DC_Behavior_Version(ucr, remote_samdb, samdb, ad_server_name, sitename)

	## Fix some attributes in SecretsDB
        secretsdb = samba.Ldb(os.path.join(samba_private_dir, "secrets.ldb"), session_info=system_session(lp), lp=lp)

	let_samba4_manage_etc_krb5_keytab(ucr, secretsdb)
	fqdn = "%s.%s" % (ucr['hostname'], ucr['domainname'])
	spn_list = ("host/%s" % fqdn, "ldap/%s" % fqdn)
	add_servicePrincipals(ucr, secretsdb, spn_list)

	## Set Samba domain password settings. Note: rotation of passwords will only work with UCS 3.1, so max password age must be disabled for now.
	p = subprocess.Popen(["samba-tool", "domain", "passwordsettings", "set", "--history-length=3", "--min-pwd-age=0", "--max-pwd-age=0"])
	p.wait()
	time.sleep(2)

	## Disable replication from Samba4 to AD
	config_registry.handler_set(["samba4/dcerpc/endpoint/drsuapi=false"])
	## Temporary workaround, until univention-samba4 smb.conf template supports samba4/service/drsuapi
	p = subprocess.Popen(["sed", "-i", '/-drsuapi/!s/\(\s*dcerpc endpoint servers\s*=\s*.*\)$/\\1 -drsuapi/', "/etc/samba/smb.conf"])
	p.wait()

	## Start Samba
	p = subprocess.Popen(["/etc/init.d/samba4", "start"])
	p.wait()
	check_samba4_started()

	### Phase I.b: Pre-Map SIDs (locale adjustment etc.)

	## pre-create containers in UDM
	container_list = []
	msgs = samdb.search(base=ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_SUBTREE,
				expression="(objectClass=organizationalunit)",
				attrs=["dn"])
	if msgs:
		print "Creating OUs in the Univention Directory Manager"
	for obj in msgs:
		container_list.append(obj["dn"].get_linearized())

	container_list.sort( key=len )

	for container_dn in container_list:
		rdn_list = ldap.explode_dn(container_dn)
		(ou_type, ou_name) = rdn_list.pop(0).split('=', 1)
		position = string.replace(','.join(rdn_list).lower(), ucr['connector/s4/ldap/base'].lower(), ucr['ldap/base'].lower())

		udm_type = None
		if ou_type == "OU":
			udm_type="container/ou"
		elif ou_type == "CN":
			udm_type="container/cn"
		else:
			print "Warning: Unmapped container type %s" % container_dn

		if udm_type:
			p = subprocess.Popen(["/usr/sbin/univention-directory-manager", udm_type, "create", "--ignore_exists", "--position", position, "--set" , "name=%s" % ou_name])
			p.wait()
	
	## construct locale mapping
	# univention.admin.modules.update()
	# co				= univention.admin.config.config()
	# position		= univention.admin.uldap.position(ucr['ldap/base'])
	# user_module		= univention.admin.modules.get("users/user")
	ucs_ad_name_map = { }
	for (name, rid) in well_known_domain_rids.items():
		msgs = samdb.search(base=ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_SUBTREE,
					expression="(objectSid=%s-%s)" % (ad_domainsid, rid),
					attrs=["sAMAccountName", "objectClass"])
		if msgs:
			obj = msgs[0]
			ad_object_name = obj["sAMAccountName"][0]

			## Special Mapping for UCS
			if name == "Domain Computers":
				name ="Windows Hosts"

			if ad_object_name.lower() != name.lower():
				oc = obj["objectClass"]
				if "group" in oc:
					ucs_ad_name_map[name] = ad_object_name
					config_registry.handler_set(["connector/s4/mapping/group/table/%s=%s" % (name, ad_object_name)])
				elif "user" in oc:
					ldap_result = lo.search(filter="(&(objectClass=sambaSamAccount)(sambaSID=*)(uid=%s))" % name, attr=["dn"])
					if ldap_result:
						print "Renaming well known user account %s to %s" % (name, ad_object_name)
						p = subprocess.Popen(["/usr/sbin/univention-directory-manager", "users/user", "modify", "--dn", ldap_result[0][0], "--set" , "username=%s" % ad_object_name])
						p.wait()
					# filter = univention.admin.filter.expression('username', name)
					# objs = user_module.lookup(co, lo, filter, scope='domain', base=position.getDomain(), unique=1)
					# if objs:
					# 	obj = objs[0]
					# 	obj['username']=unicode( "%s"%ad_object_name, "utf-8" )
					# 	obj.modify()

	## construct dict of old UCS sambaSIDs
	old_sambaSID_dict = {}
	samba_sid_map = {}
	## Users and Computers
	ldap_result = lo.search(filter="(&(objectClass=sambaSamAccount)(sambaSID=*))", attr=["uid", "sambaSID", "univentionObjectType"])
	for record in ldap_result:
		(ucs_object_dn, ucs_object_dict) = record
		old_sid = ucs_object_dict["sambaSID"][0]
		ucs_name = ucs_object_dict["uid"][0]
		if old_sid.startswith(old_domainsid):
			old_sambaSID_dict[old_sid] = ucs_name

			## lookup new sid
			new_sid = None
			if ucs_name in ucs_ad_name_map:
				lookup_name = ucs_ad_name_map[ucs_name]
			else:
				lookup_name = ucs_name

			msgs = samdb.search(base=ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_SUBTREE,
						expression="(sAMAccountName=%s)" % lookup_name,
						attrs=["dn", "objectSid"])
			if not msgs:
				continue
			else:
				obj = msgs[0]
				new_sid = str(ndr_unpack(security.dom_sid, obj["objectSid"][0]))
				samba_sid_map[old_sid] = new_sid

				if opts.verbose:
					print "Rewriting user %s SID %s to %s" % (old_sambaSID_dict[old_sid], old_sid, new_sid)
				ml = [("sambaSID", old_sid, new_sid)]
				lo.modify(ucs_object_dn, ml)

	## Groups
	ldap_result = lo.search(filter="(&(objectClass=sambaGroupMapping)(sambaSID=*))", attr=["cn", "sambaSID", "univentionObjectType"])
	for record in ldap_result:
		(ucs_object_dn, ucs_object_dict) = record
		old_sid = ucs_object_dict["sambaSID"][0]
		ucs_name = ucs_object_dict["cn"][0]
		if old_sid.startswith(old_domainsid):
			old_sambaSID_dict[old_sid] = ucs_name

			## lookup new sid
			new_sid = None
			if ucs_name in ucs_ad_name_map:
				lookup_name = ucs_ad_name_map[ucs_name]
			else:
				lookup_name = ucs_name

			msgs = samdb.search(base=ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_SUBTREE,
						expression="(sAMAccountName=%s)" % lookup_name,
						attrs=["objectSid"])
			if msgs:
				obj = msgs[0]
				new_sid = str(ndr_unpack(security.dom_sid, obj["objectSid"][0]))
				samba_sid_map[old_sid] = new_sid
			if new_sid:
				if opts.verbose:
					print "Rewriting group '%s' SID %s to %s" % (old_sambaSID_dict[old_sid], old_sid, new_sid)
				ml = [("sambaSID", old_sid, new_sid)]
				lo.modify(ucs_object_dn, ml)

	ldap_result = lo.search(filter="(sambaPrimaryGroupSID=*)", attr=["sambaPrimaryGroupSID"])
	for record in ldap_result:
		(ucs_object_dn, ucs_object_dict) = record
		old_sid = ucs_object_dict["sambaPrimaryGroupSID"][0]
		if old_sid.startswith(old_domainsid):
			if old_sid in samba_sid_map:
				ml = [("sambaPrimaryGroupSID", old_sid, samba_sid_map[old_sid])]
				lo.modify(ucs_object_dn, ml)
			else:
				if old_sid in old_sambaSID_dict:
					# print "Error: Could not find new sambaPrimaryGroupSID for %s" % old_sambaSID_dict[old_sid]
					pass
				else:
					print "Error: Unknown sambaPrimaryGroupSID %s" % old_sid


	### Pre-Create mail domains for all mail and proxyAddresses:
        samdb = SamDB(os.path.join(samba_private_dir, "sam.ldb"), session_info=system_session(lp), lp=lp)
	msgs = samdb.search(base=ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_SUBTREE,
					expression="(|(mail=*)(proxyAddresses=*))",
					attrs=["mail", "proxyAddresses"])
	maildomains = []
	for msg in msgs:
		for attr in ("mail", "proxyAddresses"):
			if attr in msg:
				for address in msg[attr]:
					char_idx = address.find("@")
					if char_idx != -1:
						domainpart = address[char_idx+1:].lower()
						# if not domainpart.endswith(".local"): ## We need to create all the domains. Alternatively set:
						## ucr:directory/manager/web/modules/users/user/properties/mailAlternativeAddress/syntax=emailAddress
						if not domainpart in maildomains:
							maildomains.append(domainpart)
	for maildomain in maildomains:
		p = subprocess.Popen(["/usr/sbin/univention-directory-manager", "mail/domain", "create", "--ignore_exists", "--position", "cn=domain,cn=mail,%s" % ucr["ldap/base"], "--set" , "name=%s" % maildomain])
		p.wait()

	## create DNS SPN
	p = subprocess.Popen(["/usr/share/univention-samba4/scripts/create_dns-host_spn.py"])
	p.wait()

	### Copy UCS Administrator Password to S4 Administrator object
	### (Account is disabled in SBS 2008 by default and the password might be unknown)
	## workaround for samba ndr parsing traceback
	#p = subprocess.Popen(["samba-tool", "user", "setpassword", "Administrator", "--newpassword=DummyPW123"]) ## will be overwritten in the next step
	#p.wait()
	#p = subprocess.Popen(["/usr/sbin/univention-password_sync_ucs_to_s4", "Administrator"])
	#if p.wait() != 0:	## retry logic from 97univention-s4-connector.inst join script
	#	p = subprocess.Popen(["/etc/init.d/samba4", "restart"])
	#	p.wait()
	#	check_samba4_started()
	#	time.sleep(3)
	#	p = subprocess.Popen(["/usr/sbin/univention-password_sync_ucs_to_s4", "Administrator"])
	#	p.wait()

	### Phase I.c: Run S4 Connector

	old_sleep = ucr.get("connector/s4/poll/sleep", "5")
	old_retry = ucr.get("connector/s4/retryrejected", "10")
	config_registry.handler_set(["connector/s4/poll/sleep=1", "connector/s4/retryrejected=2"])
	p = subprocess.Popen(["/usr/share/univention-s4-connector/msgpo.py", "--write2ucs"])
	p.wait()

	# print "Waiting for listener to finish (max. 90 seconds)",
	# t = t_0 = time.time()
	# if not wait_for_listener_replication(print_dot, 90):
	# 	print "Warning: Stopping Listener now anyway."
	print "Waiting for replication to finish (30 seconds)",
	for i in xrange(30):
		time.sleep(1)
		print_dot()
	print

	## Reset S4 Connector and handler state
	p = subprocess.Popen(["/etc/init.d/univention-directory-listener", "stop"])
	p.wait()

	if os.path.exists("/var/lib/univention-directory-listener/handlers/s4-connector"):
		os.unlink("/var/lib/univention-directory-listener/handlers/s4-connector")
	# if os.path.exists("/var/lib/univention-directory-listener/handlers/samba4-idmap"):
	# 	os.unlink("/var/lib/univention-directory-listener/handlers/samba4-idmap")
	if os.path.exists("/etc/univention/connector/s4internal.sqlite"):
		os.unlink("/etc/univention/connector/s4internal.sqlite")
	for foldername in ("/var/lib/univention-connector/s4", "/var/lib/univention-connector/s4/tmp"):
		for entry in os.listdir(foldername):
			filename = os.path.join(foldername, entry)
			try:
				if os.path.isfile(filename):
					os.unlink(filename)
			except Exception, e:
				print "Error removing file: %s" % str(e)

	p = subprocess.Popen(["/etc/init.d/univention-directory-listener", "start"])
	p.wait()

	#print "Waiting for directory listener to finish (10 seconds)",
	#for i in xrange(10):
	#	time.sleep(1)
	#	print_dot()
	#print

	print "Starting S4 Connector"
	p = subprocess.Popen(["/etc/init.d/univention-s4-connector", "start"])
	p.wait()

	print "Waiting for S4 Connector sync (max. 5 minutes)",
	t = t_0 = time.time()
	wait_for_s4_connector_replication(ucr, print_dot, 300)
	delta_t = time.time() - t
	if	delta_t < 3:
		print '>'
		for i in xrange(300):
			time.sleep(1)
			print_dot()
		print

	## Reset normal relication intervals
	config_registry.handler_set(["connector/s4/poll/sleep=%s" % old_sleep, "connector/s4/retryrejected=%s" % old_retry])
	p = subprocess.Popen(["/etc/init.d/univention-s4-connector", "restart"])
	p.wait()

	## rebuild idmap
	p = subprocess.Popen(["/usr/lib/univention-directory-listener/system/samba4-idmap.py", "--direct-resync"], stdout=devnull, stderr=devnull)
	p.wait()

	print "TODO: Determine replication status"

	## Wait for Sync to finish
	# pattern = re.compile(r"(^.+\n-{38}\ntry to sync \d+ changes from UCS\ndone: .+\nChanges from UCS: (\d+) \((\d+) saved rejected\)\n-{38}\n-{38}\ntry to sync \d+ changes from S4\ndone: .+\nChanges from S4:  (\d+) \((\d+) saved rejected\)\n-{38}\n)", re.MULTILINE)

	# changes_from_ucs = changes_from_s4 = 1
	# while changes_from_ucs > 0 or changes_from_s4 > 0:
	#	time.sleep(5)
	#	with open("/var/log/univention/connector-s4-status.log", "r") as f:
	#		status_log = f.read()
	#		m = pattern.match(status_log)
	#		changes_from_ucs = m.group(2)
	#		rejects_from_ucs = m.group(3)
	#		changes_from_s4 = m.group(4)
	#		rejects_from_s4 = m.group(5)

	## Start NSCD again
	p = subprocess.Popen(["/etc/init.d/nscd", "start"])
	p.wait()

	### Phase II: AD-Side Sync 

	print "TODO: Ask user to robocopy sysvol"
	print "TODO: Ask user to robocopy server side homedirs (?)"
	# print "TODO: Profile kopieren: z.B. nach /home/$user/windows-profiles/default.V2"
	print "TODO: Ask user to switch off AD server"
	sys.exit(1)


def run_phaseIII(opts, args):

	ad_server_name = None
	if len(args) > 0:
		ad_server_ip = args[0]
	if len(args) == 2:
		ad_server_name = args[1]
	elif len(args) != 1:
		parser.print_usage()
		sys.exit(1)

	devnull = open('/dev/null', 'w')

	ucr = config_registry.ConfigRegistry()
	ucr.load()
	local_fqdn = '.'.join((ucr["hostname"], ucr["domainname"]))

        # lp = LoadParm()
        # lp.load('/etc/samba/smb.conf')
	lp = sambaopts.get_loadparm()

	### First plausibility checks

	## 1.a check if the given IP was mapped to a host name via UCR in Phase I
	(rc, phaseI_fqdn, phaseI_name) = check_for_phase_II(ucr, lp, ad_server_ip)
	if rc == 0:
		print "Error: given IP %s was not mapped to a hostname in phase I"
		print "       Please complete phase I of the migration before initiating the FSMO takeover"
		sys.exit(1)
	elif rc == 1:
		print "OK, Found the AD DC %s account in the local Samba 4 SAM backend" % phaseI_name
	elif rc == 2:
		print "Error: It seems that this script was run once already for the first migration step,"
		print "       but the server %s cannot be found in the local Samba SAM database." % phaseI_name
		print "       Don't know how to continue, giving up at this point."
		print "       Maybe the steps needed for migration have been finished already?"
		sys.exit(1)

	## 1.b Check, if a AD DNS domain is given and if it matches the one given before
	ad_server_fqdn = None
	if ad_server_name:
		char_idx = ad_server_name.find(".")
		if char_idx == -1:
			ad_server_fqdn = "%s.%s" % (ad_server_name, ucr["domainname"])
		else:
			ad_server_fqdn = ad_server_name
			ad_server_name = ad_server_fqdn.split('.', 1)[0]
		if ad_server_name != phaseI_name:
			print "Error: Given AD server name %s does not match the one recorded for IP %s in phase I: %s" % (ad_server_name, ad_server_ip, phaseI_name)
			print "       Consider not explicetely passing an AD server name."
			sys.exit(1)
	else:
		ad_server_fqdn = phaseI_fqdn
		ad_server_name = phaseI_name

	## 1.c Check that local domainname matches kerberos realm
	if ucr["domainname"].lower() != ucr["kerberos/realm"].lower():
		print "Mismatching DNS domain and kerberos realm. Please reinstall the server with the same Domain as your AD"
		sys.exit(1)

	## 1.d ping the given AD server IP
	print "Pinging AD IP %s: " % ad_server_ip,
	p1 = subprocess.Popen(["fping", ad_server_ip], stdout=devnull, stderr=devnull)
	rc= p1.poll()
	while rc is None:
		sys.stdout.write(".")
		sys.stdout.flush()
		time.sleep(1)
		rc= p1.poll()
	print
	if rc == 0:
		print "Error: The server IP %s is still reachable" % ad_server_ip
		print "       Return to the AD DC to migrate the SYSVOL, and then"
		print "       switch it off before restarting this script with option --fsmo-takeover"
		sys.exit(1)
	else:
		print "Ok, Server IP %s unreachable." % ad_server_ip


	### Phase III: Promote to FSMO master and DNS server

	## 1. Determine Site of local server, important for locale-dependend names like "Standardname-des-ersten-Standorts"
	sitename = None
	samdb = SamDB(os.path.join(samba_private_dir, "sam.ldb"), session_info=system_session(lp), lp=lp)
	msgs = samdb.search(base=ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_SUBTREE,
                                expression="(sAMAccountName=%s$)" % ucr["hostname"],
                                attrs=["serverReferenceBL"])
	if msgs:
		obj = msgs[0]
		serverReferenceBL = obj["serverReferenceBL"][0]
		serverReferenceBL_RDNs = ldap.explode_dn(serverReferenceBL)
		serverReferenceBL_RDNs.reverse()
		config_partition_index = None
		site_container_index = None
		for i in xrange(len(serverReferenceBL_RDNs)):
			if site_container_index:
				sitename = serverReferenceBL_RDNs[i].split('=', 1)[1]
				break
			elif config_partition_index and serverReferenceBL_RDNs[i] == "CN=Sites":
				site_container_index = i
			elif not site_container_index and serverReferenceBL_RDNs[i] == "CN=Configuration":
				config_partition_index = i
			i = i+1
		print "Located server %s site %s in Samba4 SAM" % (ucr["hostname"], sitename)

	## properly register partitions
	partitions = takeover_hasInstantiatedNCs(ucr, samdb, ad_server_name, sitename)

	## Re-Set Defaul NTACLs on sysvol
	p = subprocess.Popen(["/usr/share/univention-samba4/scripts/set_sysvol_ntacl.py", sysvol_path], stdout=devnull, stderr=devnull)
	p.wait()

	## Re-set default fACLs so sysvol-sync can read files and directories
	p = subprocess.Popen(["setfacl", "-R", "-P", "-m", "g:Authenticated Users:r-x,d:g:Authenticated Users:r-x", sysvol_path])
	if p.wait() != 0:
		print "Error: Could not set fACL for %s" % sysvol_path
		print "Warning: Continuing anyway. Please fix later:"
		print "         setfacl -R -P -m 'g:Authenticated Users:r-x,d:g:Authenticated Users:r-x' %s" % sysvol_path

	## Add DNS records to UDM:
	p = subprocess.Popen(["/usr/share/univention-samba4/scripts/setup-dns-in-ucsldap.sh", "--dc", "--pdc", "--gc", "--site=%s" % sitename])
	p.wait()

	## remove local enty for AD DC from /etc/hosts
	config_registry.handler_unset(["hosts/static/%s" % ad_server_ip ])

	## Replace DNS host record for AD Server name by DNS Alias
	p = subprocess.Popen(["univention-directory-manager", "dns/host_record", "delete", "--superordinate", "zoneName=%s,cn=dns,%s" % (ucr["domainname"], ucr["ldap/base"]), "--dn", "relativeDomainName=%s,zoneName=%s,cn=dns,%s" % (ad_server_name, ucr["domainname"], ucr["ldap/base"]) ], stdout=devnull, stderr=devnull)
	p.wait()
	p = subprocess.Popen(["univention-directory-manager", "dns/alias", "create", "--superordinate", "zoneName=%s,cn=dns,%s" % (ucr["domainname"], ucr["ldap/base"]), "--set", "name=%s" % ad_server_name, "--set", "cname=%s" % local_fqdn])
	p.wait()

	## Cleanup necessary to use NETBIOS Alias
	print "Cleaning up:"
	
	print "Removing AD DC account from local Samba4 SAM database"
	p = subprocess.Popen(["/usr/bin/ldbdel", "-r", "-H", os.path.join(samba_private_dir, "sam.ldb"), "CN=%s,CN=Domain System Volume (SYSVOL share),CN=File Replication Service,CN=System,%s" % (ad_server_name, ucr["samba4/ldap/base"])], stdout=devnull, stderr=devnull)
	p.wait()
	p = subprocess.Popen(["/usr/bin/ldbdel", "-r", "-H", os.path.join(samba_private_dir, "sam.ldb"), "CN=%s,CN=Servers,CN=%s,CN=Sites,CN=Configuration,%s" % (ad_server_name, sitename, ucr["samba4/ldap/base"])])
	p.wait()
	p = subprocess.Popen(["/usr/bin/ldbdel", "-r", "-H", os.path.join(samba_private_dir, "sam.ldb"), "CN=%s,OU=Domain Controllers,%s" % (ad_server_name, ucr["samba4/ldap/base"])])
	p.wait()
	## Finally, for consistency remove AD DC object from UDM
	print "Removing AD DC account from local Univention Directory Manager"
	p = subprocess.Popen(["univention-directory-manager", "computers/windows_domaincontroller", "delete", "--dn", "cn=%s,cn=dc,cn=computers,%s" % (ad_server_name, ucr["ldap/base"]) ])
	p.wait()

	## Create NETBIOS Alias
	f = open('/etc/samba/local.conf', 'a')
	f.write('[global]\nnetbios aliases = "%s"\n' % ad_server_name)
	f.close()

	p = subprocess.Popen(["/usr/sbin/univention-config-registry", "commit", "/etc/samba/smb.conf"])
	p.wait()

	## Assign AD IP to a virtual network interface
	## Determine primary network interface, UCS 3.0-2 style:
	ip_addr = None
	try:
		ip_addr = ipaddr.IPAddress(ad_server_ip)
	except ValueError:
		print "Error: Parsing AD server address failed"
		print "       Failed to setup a virtual network interface with the AD IP address."
	if ip_addr:
		new_interface = None
		if ip_addr.version == 4:
			for i in xrange(4):
				if "interfaces/eth%s/address" % i in ucr:
					for j in xrange(4):
						if not "interfaces/eth%s_%s/address" % (i, j) in ucr:
							primary_interface = "eth%s" % i
							new_interface_ucr = "eth%s_%s" % (i, j)
							new_interface = "eth%s:%s" % (i, j)
							break
			
			if new_interface:
				guess_network = ucr["interfaces/%s/network" % primary_interface]
				guess_netmask = ucr["interfaces/%s/netmask" % primary_interface]
				guess_broadcast = ucr["interfaces/%s/broadcast" % primary_interface]
				config_registry.handler_set(["interfaces/%s/address=%s" % (new_interface_ucr, ad_server_ip),
								"interfaces/%s/network=%s" % (new_interface_ucr, guess_network),
								"interfaces/%s/netmask=%s" % (new_interface_ucr, guess_netmask),
								"interfaces/%s/broadcast=%s" % (new_interface_ucr, guess_broadcast)])
				samba_interfaces = ucr.get("samba/interfaces")
				if ucr.is_true("samba/interfaces/bindonly") and samba_interfaces:
					config_registry.handler_set(["samba/interfaces=%s %s" % (samba_interfaces, new_interface)])
			else:
				print "Warning: Could not determine primary IPv4 network interface."
				print "         Failed to setup a virtual IPv4 network interface with the AD IP address."
		elif ip_addr.version == 6:
			for i in xrange(4):
				if "interfaces/eth%s/ipv6/default/address" % i in ucr:
					for j in xrange(4):
						if not "interfaces/eth%s_%s/ipv6/default/address" % (i, j) in ucr:
							primary_interface = "eth%s" % i
							new_interface_ucr = "eth%s_%s" % (i, j)
							new_interface = "eth%s:%s" % (i, j)
							break
			
			if new_interface:
				guess_prefix = ucr["interfaces/%s/ipv6/default/prefix" % primary_interface]
				config_registry.handler_set(["interfaces/%s/ipv6/default/address=%s" % (new_interface_ucr, ad_server_ip),
								"interfaces/%s/ipv6/default/prefix=%s" % (new_interface_ucr, guess_broadcast),
								"interfaces/%s/ipv6/acceptRA=false"])
				samba_interfaces = ucr.get("samba/interfaces")
				if ucr.is_true("samba/interfaces/bindonly") and samba_interfaces:
					config_registry.handler_set(["samba/interfaces=%s %s" % (samba_interfaces, new_interface)])
			else:
				print "Warning: Could not determine primary IPv6 network interface."
				print "         Failed to setup a virtual IPv6 network interface with the AD IP address."

	## Resolve against local Bind9
	## use OpenLDAP backend until the S4 Connector has run
	if "nameserver1/local" in ucr:
		nameserver1_orig = ucr["nameserver1/local"]
		config_registry.handler_set(["nameserver1=%s" % nameserver1_orig])
		## unset temporary variable
		config_registry.handler_unset(["nameserver1/local"])
	else:
		print "Warning: Weird, unable to determine previous nameserver1..."
		print "         Using localhost as fallback, probably that's the right thing to do."
		config_registry.handler_set(["nameserver1=127.0.0.1"])

	## Use Samba4 as DNS backend
	config_registry.handler_set(["dns/backend=samba4"])

	## Re-enable replication from Samba4
	config_registry.handler_unset(["samba4/dcerpc/endpoint/drsuapi"])

	## Claim FSMO roles
	print "Claiming FSMO roles"
	takeover_hasMasterNCs(ucr, samdb, sitename, partitions)
	for fsmo_role in ('rid', 'pdc', 'infrastructure', 'schema', 'naming'):
		p = subprocess.Popen(["samba-tool", "fsmo", "seize", "--role=%s" % fsmo_role, "--force"])
		p.wait()

	## Let things settle
	time.sleep(3)

	## Restart Samba and make shure the rapid restart did not leave the main process blocking
	p = subprocess.Popen(["/etc/init.d/samba4", "restart"])
	p.wait()
	check_samba4_started()

	## Restart bind9 to use the OpenLDAP backend, just to be sure
	p = subprocess.Popen(["/etc/init.d/bind9", "restart"])
	p.wait()

	## re-create /etc/krb5.keytab
	##  https://forge.univention.org/bugzilla/show_bug.cgi?id=27426
	p = subprocess.Popen(["/usr/share/univention-samba4/scripts/create-keytab.sh"])
	p.wait()

	## Enable NTP Signing for Windows SNTP clients
	config_registry.handler_set(["ntp/signed=yes"])
	p = subprocess.Popen(["/etc/init.d/ntp", "restart"])
	p.wait()

if __name__ == '__main__':

	parser = OptionParser("%prog [options] <AD Server IP> [<AD Server Name>]")
	parser.add_option("-v", "--verbose", action="store_true")
	parser.add_option("--fsmo-takeover", action="store_true")

	sambaopts = samba.getopt.SambaOptions(parser)
	parser.add_option_group(sambaopts)
	parser.add_option_group(samba.getopt.VersionOptions(parser))
	# use command line creds if available
	credopts = samba.getopt.CredentialsOptions(parser)
	parser.add_option_group(credopts)
	opts, args = parser.parse_args()

	if not opts.fsmo_takeover:
		run_phaseI(opts, args)
	else:
		run_phaseIII(opts, args)


