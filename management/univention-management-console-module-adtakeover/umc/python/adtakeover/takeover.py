#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Univention AD takeover script
#  Migrates an AD server to the local UCS Samba 4 DC
#
# Copyright 2012-2021 Univention GmbH
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

import os
import re
import sys
import time
import locale
import shutil
import logging
import traceback
import subprocess
import configparser
from datetime import datetime, timedelta

import ldb
import samba
import samba.getopt
from samba import Ldb
from samba.samdb import SamDB
from samba.auth import system_session
from samba.param import LoadParm
from samba.ndr import ndr_unpack
from samba.dcerpc import security
# from samba.netcmd.common import netcmd_get_domain_infos_via_cldap
from samba.dcerpc import nbt
from samba.net import Net
from samba.credentials import Credentials, DONT_USE_KERBEROS

import ldap
import sqlite3
import ipaddress
from ldap.filter import filter_format
from ldap.dn import escape_dn_chars, str2dn, dn2str

import univention.admin.uldap
import univention.admin.uexceptions as uexceptions
import univention.admin.modules as udm_modules
import univention.admin.filter as udm_filter
import univention.admin.objects
from univention.admincli import license_check
import univention.lib
import univention.lib.s4
import univention.config_registry
import univention.lib.admember
from univention.config_registry.interfaces import Interfaces
from univention.management.console.log import MODULE
from univention.management.console import Translation
from univention.uldap import parentDn


ucr = univention.config_registry.ConfigRegistry()
ucr.load()

# load UDM modules
udm_modules.update()

LOGFILE_NAME = "/var/log/univention/ad-takeover.log"
JOIN_LOGFILE_NAME = "/var/log/univention/join.log"
BACKUP_DIR = "/var/univention-backup/ad-takeover"
SAMBA_DIR = '/var/lib/samba'
SAMBA_PRIVATE_DIR = os.path.join(SAMBA_DIR, 'private')
SYSVOL_PATH = os.path.join(SAMBA_DIR, 'sysvol')

logging.basicConfig(filename=LOGFILE_NAME, format='%(asctime)s %(message)s', level=logging.DEBUG)
log = logging.getLogger()

try:
	univention.admin.handlers.disable_ad_restrictions(disable=False)
except AttributeError:
	log.info('univention.admin.handlers.disable_ad_restrictions is not available')

DEVNULL = open(os.devnull, 'w')

_ = Translation('univention-management-console-module-adtakeover').translate


class Progress(object):

	'''Progress information. reset() and error() are set by the UMC module.
	progress.warning can be used when something went wrong which is not
	raise-worthy
	'''

	def __init__(self):
		self._headline = None
		self._message = None
		self._percentage = 'Infinity'
		self._errors = []
		self._critical = False
		self._finished = False

	def reset(self):
		self._headline = None
		self._message = None
		self._percentage = 'Infinity'
		self._errors = []
		self._critical = False
		self._finished = False

	def set(self, headline=None, message=None, percentage=None):
		if headline is not None:
			self.headline(headline)
		if message is not None:
			self.message(message)
		if percentage is not None:
			self.percentage(percentage)

	def headline(self, headline):
		MODULE.process('### %s ###' % headline)
		self._headline = headline
		self._message = None

	def message(self, message):
		MODULE.process('  %s' % message)
		self._message = str(message)

	def percentage(self, percentage):
		if percentage < 0:
			percentage = 'Infinity'
		self._percentage = percentage

	def percentage_increment_scaled(self, fraction):
		self.percentage(self._percentage + self._scale * fraction)
		self._scale = self._scale * (1 - fraction)

	def warning(self, error):
		MODULE.warn(' %s' % error)
		self._errors.append(str(error))

	def error(self, error):
		self._errors.append(str(error))
		self._critical = True

	def finish(self):
		self._finished = True

	def poll(self):
		return {
			'component': self._headline,
			'info': self._message,
			'steps': self._percentage,
			'errors': self._errors,
			'critical': self._critical,
			'finished': self._finished,
		}


class TakeoverError(Exception):

	'''AD Takeover Error'''

	def __init__(self, errormessage=None, detail=None):
		if errormessage:
			self.errormessage = errormessage
		else:
			self.errormessage = self.default_error_message
		self.detail = detail
		log.error(self)

	def __str__(self):
		if self.errormessage and self.detail:
			return '%s (%s)' % (self.errormessage, self.detail)
		else:
			return self.errormessage or self.detail or ''


class ComputerUnreachable(TakeoverError):
	default_error_message = _('The computer is not reachable.')


class AuthenticationFailed(TakeoverError):
	default_error_message = _('Authentication failed.')


class DomainJoinFailed(TakeoverError):
	default_error_message = _('Domain join failed.')


class SysvolGPOMissing(TakeoverError):
	default_error_message = _('At least one GPO is still missing in SYSVOL.')


class SysvolGPOVersionTooLow(TakeoverError):
	default_error_message = _('At least one GPO in SYSVOL is not up to date yet.')


class SysvolGPOVersionMismatch(TakeoverError):
	default_error_message = _('At least one GPO in SYSVOL is newer than the Group Policy Container version.')


class SysvolError(TakeoverError):
	default_error_message = _('Something is wrong with the SYSVOL.')


class ADServerRunning(TakeoverError):
	default_error_message = _('The Active Directory server seems to be running. It must be shut off.')


class TimeSynchronizationFailed(TakeoverError):
	default_error_message = _('Time synchronization failed.')


class ManualTimeSynchronizationRequired(TimeSynchronizationFailed):
	default_error_message = _('Time difference critical for Kerberos but synchronization aborted.')


class LicenseInsufficient(TakeoverError):
	default_error_message = _('Insufficient License.')


def count_domain_objects_on_server(hostname_or_ip, username, password, progress):
	'''Connects to the hostname_or_ip with username/password credentials
	Expects to find a Windows Domain Controller.
	Gets str, str, str, Progress
	Returns {
		'ad_hostname' : hostname,
		'ad_ip' : hostname_or_ip,
		'ad_os' : version_of_the_ad, # "Windows 2008 R2"
		'ad_domain' : domain_of_the_ad, # "mydomain.local"
		'users' : number_of_users_in_domain,
		'groups' : number_of_groups_in_domain,
		'computers' : number_of_computers_in_domain,
		'license_error' : error_message_from_validating_license,
	}
	Raises ComputerUnreachable, AuthenticationFailed
	'''

	ucs_license = UCS_License_detection(ucr)

	progress.headline(_('Connecting to %s') % hostname_or_ip)
	ad = AD_Connection(hostname_or_ip)

	progress.message(_('Authenticating'))
	ad.authenticate(username, password)

	progress.message(_('Retrieving information from AD DC'))
	domain_info = ad.count_objects(ucs_license.ignored_users_list)
	try:
		ucs_license.check_license(domain_info)
	except LicenseInsufficient as e:
		domain_info['license_error'] = str(e) + ' ' + _('You may proceed with the takeover, but the domain management may be limited afterwards until a new license is installed.')
	else:
		domain_info['license_error'] = ''

	return domain_info


def join_to_domain_and_copy_domain_data(hostname_or_ip, username, password, progress):
	'''Connects to the hostname_or_ip with username/password credentials
	Expects to find a Windows Domain Controller.
	Gets str, str, str, Progress
	Raises ComputerUnreachable, AuthenticationFailed, DomainJoinFailed
	'''
	state = AD_Takeover_State()
	state.set_start()

	progress.headline(_('Connecting to %s') % hostname_or_ip)
	progress.percentage(0.5)
	ad = AD_Connection(hostname_or_ip)

	progress.headline(_('Authenticating'))
	progress.percentage(0.7)
	ad.authenticate(username, password)

	progress.headline(_('Synchronizing system clock'))
	progress.percentage(1)
	takeover = AD_Takeover(ucr, ad)
	takeover.time_sync()

	progress.headline(_('Joining the domain'))
	takeover.disable_admember_mode(progress)
	progress.percentage(2)
	progress._scale = 18 - progress._percentage
	takeover.join_AD(progress)
	state.set_joined()
	progress.headline(_('Starting Samba'))
	progress.percentage(18)
	takeover.post_join_tasks_and_start_samba_without_drsuapi()
	progress.headline(_('Rewriting SIDs in the UCS directory service'))
	progress.percentage(22)
	takeover.rewrite_sambaSIDs_in_OpenLDAP()
	progress.headline(_('Checking group policies'))
	takeover.remove_conflicting_msgpo_objects()
	progress.headline(_('Initializing the S4 Connector listener'))
	progress.percentage(23)
	progress._scale = 70 - progress._percentage
	takeover.resync_s4connector_listener(progress)
	progress.headline(_('Starting the S4 Connector'))
	progress.percentage(70)
	progress._scale = 98 - progress._percentage
	takeover.start_s4_connector(progress)
	progress.headline(_('Rebuilding IDMAP'))
	progress.percentage(98)
	takeover.rebuild_idmap()
	progress.message(_('Reset SYSVOL ACLs'))
	progress.percentage(99)
	takeover.reset_sysvol_ntacls()
	takeover.set_nameserver1_to_local_default_ip()
	progress.percentage(100)
	state.set_sysvol()


def take_over_domain(progress):
	'''Actually takes control of the domain, deletes old AD server, takes
	its IP, etc.
	Gets Progress
	Raises AuthenticationFailed, DomainJoinFailed, ADServerRunning
	'''
	state = AD_Takeover_State()
	state.check_takeover()

	takeover_final = AD_Takeover_Finalize(ucr)
	progress.headline(_('Search for %s in network') % takeover_final.ad_server_ip)
	progress.percentage(0)
	progress._scale = 5
	takeover_final.ping_AD(progress)

	progress.headline(_('Taking over Active Directory domain controller roles'))
	progress.message(_('Adjusting settings in Samba directory service'))
	progress.percentage(5)
	takeover_final.post_join_fix_samDB()
	takeover_final.fix_sysvol_acls()
	progress.message(_('Claiming FSMO roles'))
	progress.percentage(15)
	takeover_final.claim_FSMO_roles()
	progress.message(_('Removing the previous AD server account'))
	progress.percentage(20)
	takeover_final.remove_AD_server_account_from_samdb()
	takeover_final.remove_AD_server_account_from_UDM()
	progress.message(_('Taking over DNS address'))
	progress.percentage(22)
	takeover_final.create_DNS_alias_for_AD_hostname()
	progress.message(_('Taking over NETBIOS address'))
	progress.percentage(28)
	takeover_final.create_NETBIOS_alias_for_AD_hostname()
	progress.message(_('Taking over IP address'))
	progress.percentage(35)
	takeover_final.create_virtual_IP_alias()
	progress.message(_('Registering IP in DNS'))
	progress.percentage(42)
	takeover_final.create_reverse_DNS_records()
	progress.message(_('Reconfiguring nameserver'))
	progress.percentage(52)
	takeover_final.reconfigure_nameserver_for_samba_backend()
	progress.message(_('Finalizing'))
	progress.percentage(69)
	takeover_final.configure_SNTP()
	progress.percentage(80)
	takeover_final.finalize()
	progress.percentage(100)
	state.set_finished()


def check_status():
	'''Where are we in the process of AD takeover?
	Returns one of:
	'start' -> nothing happened yet
	'sysvol' -> we copied domain data, sysvol was not yet copied'
	'takeover' -> sysvol was copied. we can now take over the domain
	'finished' -> already finished
	'''
	state = AD_Takeover_State()
	return state.current()


def check_sysvol(progress):
	'''Whether the AD sysvol is already copied to the local system
	Gets Progress
	Raises SysvolError
	'''
	state = AD_Takeover_State()
	state.check_sysvol()

	progress.message(_('Checking GPOs in SYSVOL'))
	check_gpo_presence()

	state.set_takeover()


def set_status_done():
	'''Set status to "done", indicating the module has been run once successfully
	and may be started again.
	'''
	state = AD_Takeover_State()
	return state.set_done()


class AD_Takeover_State(object):

	def __init__(self):
		self.statefile = os.path.join(SAMBA_PRIVATE_DIR, ".adtakeover")
		self.stateorder = ("start", "joined", "sysvol", "takeover", "finished", "done")

	def _set_persistent_state(self, state):
		with open(self.statefile, "w") as f:
			f.write(state)

	def _save_state(self, new_state):
		try:
			i = self.stateorder.index(new_state)
		except ValueError:
			raise TakeoverError(_("Internal module error: Refusing to set invalid state '%s'.") % new_state)

		current_state = self.current()

		if new_state == "start":
			self.check_start()
			if current_state == "start":
				self._set_persistent_state(new_state)
			elif current_state == "done":
				log.info("Starting another takover.")
				timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
				statefile_backup = "%s.previous-ad-takeover-%s" % (self.statefile, timestamp)
				os.rename(self.statefile, statefile_backup)
				self._set_persistent_state(new_state)
		elif current_state == self.stateorder[i - 1]:
			self._set_persistent_state(new_state)
		else:
			raise TakeoverError(_("Internal module error: Cannot go from state '%(current)s' to state '%(new)s'.") % {'current': current_state, 'new': new_state})

	def check_sysvol(self):
		current_state = self.current()
		if current_state != "sysvol":
			raise TakeoverError(_("Internal module error: Expected to be in state 'sysvol', but found '%s'.") % (current_state,))

	def check_takeover(self):
		current_state = self.current()
		if current_state != "takeover":
			raise TakeoverError(_("Internal module error: Expected to be in state 'takeover', but found '%s'.") % (current_state,))

	def check_start(self):
		current_state = self.current()
		if current_state not in ("done", "start"):
			raise TakeoverError(_("Internal module error: Takeover running, aborting attempt to restart."))

	def set_start(self):
		self._save_state("start")

	def set_joined(self):
		self._save_state("joined")

	def set_sysvol(self):
		self._save_state("sysvol")

	def set_takeover(self):
		self._save_state("takeover")

	def set_finished(self):
		self._save_state("finished")

	def set_done(self):
		self._save_state("done")

	def current(self):
		if os.path.exists(self.statefile):
			with open(self.statefile) as f:
				state = f.read().strip()
				if state in self.stateorder:
					return state
				else:
					raise TakeoverError(_("Invalid state in file %s") % self.statefile)
		else:
			return "start"


AD_IP_HOSTNAME = [None, None]


def get_ip_and_hostname_of_ad():
	ucr.load()
	ad_server_ip = ucr.get("univention/ad/takeover/ad/server/ip")
	if ad_server_ip:
		if "hosts/static/%s" % ad_server_ip in ucr:
			ad_server_fqdn, ad_server_name = ucr["hosts/static/%s" % ad_server_ip].split()
			return [ad_server_ip, ad_server_name]
	else:
		return AD_IP_HOSTNAME

# def set_ip_and_hostname_of_ad(ip, hostname):
#	AD_IP_HOSTNAME[:] = [ip, hostname]


def get_ad_hostname():
	'''The hostname of the AD to be specified in robocopy'''
	return get_ip_and_hostname_of_ad()[1]


def sysvol_info():
	'''The info needed for the "Copy SYSVOL"-page, i.e.
	"ad_hostname" and "ucs_hostname"'''
	return {
		'ucs_hostname': ucr.get('hostname'),
		'ad_hostname': get_ad_hostname(),
	}


class UCS_License_detection(object):

	def __init__(self, ucr):
		self.ucr = ucr

		import univention.admin.license
		self.License = univention.admin.license.License
		self._license = univention.admin.license._license
		self.ignored_users_list = self._license.sysAccountNames

	def determine_license(self, lo, dn):
		def mylen(xs):
			if xs is None:
				return 0
			return len(xs)
		v = self._license.version
		types = self._license.licenses[v]
		if dn is None:
			max = [self._license.licenses[v][type] for type in types]
		else:
			max = [lo.get(dn)[self._license.keys[v][type]][0] for type in types]

		objs = [lo.searchDn(filter=self._license.filters[v][type]) for type in types]
		num = [mylen(obj) for obj in objs]
		self._license.checkObjectCounts(max, num)
		result = []
		for i in list(types.keys()):
			types[i]
			m = max[i]
			n = num[i]
			objs[i]
			if i == self.License.USERS or i == self.License.ACCOUNT:
				n -= self._license.sysAccountsFound
				if n < 0:
					n = 0
			li = self._license.names[v][i]
			if m:
				if i == self.License.USERS or i == self.License.ACCOUNT:
					log.debug("determine_license for current UCS %s: %s of %s" % (li, n, m))
					log.debug("  %s Systemaccounts are ignored." % self._license.sysAccountsFound)
					result.append((li, n, m))
		return result

	def check_license(self, domain_info):

		binddn = self.ucr['ldap/hostdn']
		with open('/etc/machine.secret', 'r') as pwfile:
			bindpw = pwfile.readline().strip()

		try:
			lo = univention.admin.uldap.access(
				host=self.ucr['ldap/master'],
				port=int(self.ucr.get('ldap/master/port', '7389')),
				base=self.ucr['ldap/base'],
				binddn=binddn,
				bindpw=bindpw
			)
		except uexceptions.authFail:
			raise LicenseInsufficient(_("Internal Error: License check failed."))

		try:
			self._license.init_select(lo, 'admin')
			check_array = self.determine_license(lo, None)
		except uexceptions.base:
			dns = license_check.find_licenses(lo, self.ucr['ldap/base'], 'admin')
			dn, expired = license_check.choose_license(lo, dns)
			check_array = self.determine_license(lo, dn)

		# some name translation
		object_displayname_for_licensetype = {'Accounts': _('users'), 'Users': _('users')}
		ad_object_count_for_licensetype = {'Accounts': domain_info["users"], 'Users': domain_info["users"]}

		license_sufficient = True
		error_msg = None
		for object_type, num, max_objs in check_array:
			object_displayname = object_displayname_for_licensetype.get(object_type, object_type)
			log.info("Found %s %s objects on the remote server." % (ad_object_count_for_licensetype[object_type], object_displayname))
			sum_objs = num + ad_object_count_for_licensetype[object_type]
			domain_info["licensed_%s" % (object_displayname,)] = max_objs
			domain_info["estimated_%s" % (object_displayname,)] = sum_objs
			if self._license.compare(sum_objs, max_objs) > 0:
				license_sufficient = False
				error_msg = _("Number of %(object_name)s after takeover would be %(sum)s. This would exceed the number of licensed objects (%(max)s).") % {
					'object_name': object_displayname,
					'sum': sum_objs,
					'max': max_objs,
				}
				log.warn(error_msg)

		if not license_sufficient:
			raise LicenseInsufficient(error_msg)


class AD_Connection(object):

	def __init__(self, hostname_or_ip, lp=None):

		self.hostname_or_ip = hostname_or_ip
		self.ldap_uri = ldap_uri_for_host(hostname_or_ip)

		if lp:
			self.lp = lp
		else:
			self.lp = LoadParm()
			self.lp.load('/etc/samba/smb.conf')

		ping(hostname_or_ip)

		# To reduce authentication delays first check if an AD is present at all
		try:
			Ldb(url=self.ldap_uri, lp=self.lp)
		except ldb.LdbError:
			raise ComputerUnreachable(_("Active Directory services not detected at %s.") % hostname_or_ip)

	def authenticate(self, username, password, lp=None):
		self.username = username
		self.password = password

		self.creds = Credentials()
		# creds.guess(lp)
		self.creds.set_domain("")
		self.creds.set_workstation("")
		self.creds.set_kerberos_state(DONT_USE_KERBEROS)
		self.creds.set_username(self.username)
		self.creds.set_password(self.password)

		try:
			self.samdb = SamDB(self.ldap_uri, credentials=self.creds, session_info=system_session(self.lp), lp=self.lp)
		except ldb.LdbError:
			raise AuthenticationFailed()

		# Sanity check: are we talking to the AD on the local system?
		ntds_guid = self.samdb.get_ntds_GUID()
		local_ntds_guid = None
		try:
			local_samdb = SamDB("ldap://127.0.0.1", credentials=self.creds, session_info=system_session(self.lp), lp=self.lp)
			local_ntds_guid = local_samdb.get_ntds_GUID()
		except ldb.LdbError:
			pass
		if ntds_guid == local_ntds_guid:
			raise TakeoverError(_("The selected Active Directory server has the same NTDS GUID as this UCS server."))

		self.domain_dn = self.samdb.get_root_basedn()
		if self.domain_dn.get_linearized().lower() != ucr["ldap/base"].lower():
			raise TakeoverError(_("The LDAP base of this UCS domain differs from the LDAP base of the selected Active Directory domain."))

		self.domain_sid = None
		msgs = self.samdb.search(
			base=self.domain_dn, scope=samba.ldb.SCOPE_BASE,
			expression="(objectClass=domain)",
			attrs=["objectSid", "msDS-Behavior-Version"]
		)
		if msgs:
			obj = msgs[0]
			self.domain_sid = str(ndr_unpack(security.dom_sid, obj["objectSid"][0]))
			if "msDS-Behavior-Version" in obj:
				try:
					msds_behavior_version = int(obj["msDS-Behavior-Version"][0])
				except ValueError:
					log.error("Cannot parse msDS-Behavior-Version: %s" % (obj["msDS-Behavior-Version"][0],))
				if msds_behavior_version > 4:
					raise TakeoverError(_("The Active Directory domain has a function level of Windows Server 2012 or newer, Samba currently only supports up to Windows 2008R2: %s") % (msds_behavior_version))
			else:
				log.error("msDS-Behavior-Version missing in AD.")
		if not self.domain_sid:
			raise TakeoverError(_("Failed to determine AD domain SID."))

		self.domain_info = lookup_adds_dc(self.hostname_or_ip)
		self.domain_info['ad_os'] = self.operatingSystem(self.domain_info["ad_netbios_name"])

	def reconnect(self):
		try:
			self.samdb = SamDB(self.ldap_uri, credentials=self.creds, session_info=system_session(self.lp), lp=self.lp)
		except ldb.LdbError:
			raise AuthenticationFailed()

	def operatingSystem(self, netbios_name):
		msg = self.samdb.search(
			base=self.samdb.domain_dn(), scope=samba.ldb.SCOPE_SUBTREE,
			expression=filter_format("(sAMAccountName=%s$)", [netbios_name]),
			attrs=["operatingSystem", "operatingSystemVersion", "operatingSystemServicePack"])
		if msg:
			obj = msg[0]
			if "operatingSystem" in obj:
				return obj["operatingSystem"][0]
			else:
				return ""

	def count_objects(self, ignored_users_list):

		ignored_user_objects = 0
		ad_user_objects = 0
		ad_group_objects = 0
		ad_computer_objects = 0

		# page results
		PAGE_SIZE = 1000
		controls = ['paged_results:1:%s' % PAGE_SIZE]

		# Count user objects
		msgs = self.samdb.search(
			base=self.domain_dn, scope=samba.ldb.SCOPE_SUBTREE,
			expression="(&(objectCategory=user)(objectClass=user))",
			attrs=["sAMAccountName", "objectSid"], controls=controls)
		for obj in msgs:
			sAMAccountName = obj["sAMAccountName"][0]

			# identify well known names, abstracting from locale
			sambaSID = str(ndr_unpack(security.dom_sid, obj["objectSid"][0]))
			sambaRID = sambaSID[len(self.domain_sid) + 1:]
			for (_rid, _name) in list(univention.lib.s4.well_known_domain_rids.items()):
				if _rid == sambaRID:
					log.debug("Found account %s with well known RID %s (%s)" % (sAMAccountName, sambaRID, _name))
					sAMAccountName = _name
					break

			for ignored_account in ignored_users_list:
				if sAMAccountName.lower() == ignored_account.lower():
					ignored_user_objects = ignored_user_objects + 1
					break
			else:
				ad_user_objects = ad_user_objects + 1

		# Count group objects
		msgs = self.samdb.search(
			base=self.domain_dn, scope=samba.ldb.SCOPE_SUBTREE,
			expression="(objectCategory=group)",
			attrs=["sAMAccountName", "objectSid"], controls=controls)
		for obj in msgs:
			sAMAccountName = obj["sAMAccountName"][0]

			# identify well known names, abstracting from locale
			sambaSID = str(ndr_unpack(security.dom_sid, obj["objectSid"][0]))
			sambaRID = sambaSID[len(self.domain_sid) + 1:]
			for (_rid, _name) in list(univention.lib.s4.well_known_domain_rids.items()):
				if _rid == sambaRID:
					log.debug("Found group %s with well known RID %s (%s)" % (sAMAccountName, sambaRID, _name))
					sAMAccountName = _name
					break

			ad_group_objects = ad_group_objects + 1

		# Count computer objects
		msgs = self.samdb.search(
			base=self.domain_dn, scope=samba.ldb.SCOPE_SUBTREE,
			expression="(objectCategory=computer)",
			attrs=["sAMAccountName", "objectSid"], controls=controls)
		for obj in msgs:
			sAMAccountName = obj["sAMAccountName"][0]

			# identify well known names, abstracting from locale
			sambaSID = str(ndr_unpack(security.dom_sid, obj["objectSid"][0]))
			sambaRID = sambaSID[len(self.domain_sid) + 1:]
			for (_rid, _name) in list(univention.lib.s4.well_known_domain_rids.items()):
				if _rid == sambaRID:
					log.debug("Found computer %s with well known RID %s (%s)" % (sAMAccountName, sambaRID, _name))
					sAMAccountName = _name
					break

			else:
				ad_computer_objects = ad_computer_objects + 1

		self.domain_info['users'] = ad_user_objects
		self.domain_info['groups'] = ad_group_objects
		self.domain_info['computers'] = ad_computer_objects

		return self.domain_info


class AD_Takeover(object):

	def __init__(self, ucr, ad_connection):
		self.ucr = ucr
		self.AD = ad_connection
		self.ad_server_ip = self.AD.domain_info["ad_ip"]
		self.ad_server_fqdn = self.AD.domain_info["ad_hostname"]
		self.ad_server_name = self.AD.domain_info["ad_netbios_name"]
		self.ad_netbios_domain = self.AD.domain_info["ad_netbios_domain"]

		self.lp = LoadParm()
		try:
			self.lp.load('/etc/samba/smb.conf')
		except:
			self.lp.load('/dev/null')

		self.local_fqdn = '.'.join((self.ucr["hostname"], self.ucr["domainname"]))

	def time_sync(self, tolerance=180, critical_difference=360):
		'''Try to sync the local time with an AD server'''

		env = os.environ.copy()
		env["LC_ALL"] = "C"
		try:
			p1 = subprocess.Popen(["rdate", "-p", "-n", self.ad_server_ip], close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
			stdout, stderr = p1.communicate()
		except OSError as ex:
			log.error("ERROR: rdate -p -n %s: %s" % (self.ad_server_ip, ex.args[1]))
			return False

		if p1.returncode:
			log.error("ERROR: rdate failed (%d)" % (p1.returncode,))
			return False

		TIME_FORMAT = "%a %b %d %H:%M:%S %Z %Y"
		time_string = stdout.strip()
		old_locale = locale.getlocale(locale.LC_TIME)
		try:
			locale.setlocale(locale.LC_TIME, (None, None))  # 'C' as env['LC_ALL'] some lines earlier
			remote_datetime = datetime.strptime(time_string, TIME_FORMAT)
		except ValueError as ex:
			raise TimeSynchronizationFailed(_("AD Server did not return proper time string: %s.") % (time_string,))
		finally:
			locale.setlocale(locale.LC_TIME, old_locale)

		local_datetime = datetime.today()
		delta_t = local_datetime - remote_datetime
		if abs(delta_t) < timedelta(0, tolerance):
			log.info("INFO: Time difference is less than %d seconds, skipping reset of local time" % (tolerance,))
		elif local_datetime > remote_datetime:
			if abs(delta_t) >= timedelta(0, critical_difference):
				raise ManualTimeSynchronizationRequired(_("Remote clock is behind local clock by more than %s seconds, refusing to turn back time. Please advance the clock of the Active Directory DC.") % (critical_difference,))
			else:
				log.info("INFO: Remote clock is behind local clock by more than %s seconds, refusing to turn back time. Please advance the clock of the Active Directory DC." % (tolerance,))
				return False
		else:
			log.info("INFO: Synchronizing time to %s" % self.ad_server_ip)
			p1 = subprocess.Popen(["rdate", "-s", "-n", self.ad_server_ip], close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			stdout, stderr = p1.communicate()
			if p1.returncode:
				log.error("ERROR: rdate -s -p failed (%d)" % (p1.returncode,))
				raise TimeSynchronizationFailed(_("Internal Error: rdate -s -p failed (%d).") % (p1.returncode,))
		return True

	def disable_admember_mode(self, progress):
		if univention.lib.admember.is_domain_in_admember_mode():
			univention.lib.admember.remove_admember_service_from_localhost()
			univention.lib.admember.revert_ucr_settings()
			univention.lib.admember.revert_connector_settings()
			run_and_output_to_log(["univention-config-registry", "unset", "connector/s4/listener/disabled", ], log.debug)
			run_and_output_to_log([
				"univention-config-registry", "set",
				"connector/ad/autostart=no",
				"connector/s4/autostart=yes",
				"samba4/ignore/mixsetup=yes",
			], log.debug)
			run_and_output_to_log(["/etc/init.d/univention-ad-connector", "stop"], log.debug)
			run_and_output_to_log(["/usr/bin/systemctl", "try-restart", "univention-directory-listener"], log.debug)
			# And now run 96univention-samba4.inst pre-provision setup (.adtakeover status is "start"), to disable slapd on port 389, and 97uinvention-s4-connector.inst
			# Due to Bug #35561 the script needs to be run directly to determine its exit status.
			returncode = run_and_output_to_log(["/usr/lib/univention-install/96univention-samba4.inst"], log.debug)
			if returncode:
				log.error("ERROR: Initial univention-run-join-scripts --run-scripts 96univention-samba4.inst failed (%d)" % (returncode,))
				univention.lib.admember.add_admember_service_to_localhost()
				raise DomainJoinFailed(_("The domain join failed. See %s for details.") % JOIN_LOGFILE_NAME)
			returncode = run_and_output_to_log(["univention-run-join-scripts", "--run-scripts", "97univention-s4-connector.inst"], log.debug)

	def join_AD(self, progress):
		log.info("Starting phase I of the takeover process.")

		# OK, we are quite sure that we have the basics right, note the AD server IP and FQDN in UCR for phase II
		run_and_output_to_log(["univention-config-registry", "set", "hosts/static/%s=%s %s" % (self.ad_server_ip, self.ad_server_fqdn, self.ad_server_name)], log.debug)

		run_and_output_to_log(["/etc/init.d/univention-s4-connector", "stop"], log.debug)
		run_and_output_to_log(["/etc/init.d/samba-ad-dc", "stop"], log.debug)
		progress.percentage_increment_scaled(1.0 / 32)

		# Move current Samba directory out of the way
		timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
		self.backup_samba_dir = "%s.before-ad-takeover-%s" % (SAMBA_PRIVATE_DIR, timestamp)
		if os.path.exists(SAMBA_PRIVATE_DIR):
			if os.path.exists(self.backup_samba_dir):  # practically impossible, but none the less
				shutil.rmtree(self.backup_samba_dir)
			os.rename(SAMBA_PRIVATE_DIR, self.backup_samba_dir)
			os.makedirs(SAMBA_PRIVATE_DIR)
			statefile = os.path.join(self.backup_samba_dir, ".adtakeover")
			shutil.copy(statefile, SAMBA_PRIVATE_DIR)

		# Adjust some UCR settings
		if "nameserver1/local" in self.ucr:
			nameserver1_orig = self.ucr["nameserver1/local"]
		else:
			nameserver1_orig = self.ucr["nameserver1"]
			run_and_output_to_log(
				[
					"univention-config-registry", "set",
					"nameserver1/local=%s" % nameserver1_orig,
					"nameserver1=%s" % self.ad_server_ip,
					"directory/manager/web/modules/users/user/properties/username/syntax=string",
					"directory/manager/web/modules/groups/group/properties/name/syntax=string",
					"dns/backend=ldap"
				],
				log.debug
			)

		self.ucr.load()
		univention.admin.configRegistry.load()  # otherwise the modules do not use the new syntax

		# Stop the NSCD
		run_and_output_to_log(["/etc/init.d/nscd", "stop"], log.debug)
		progress.percentage_increment_scaled(1.0 / 32)

		# Restart bind9 to use the OpenLDAP backend, just to be sure
		run_and_output_to_log(["/etc/init.d/bind9", "restart"], log.debug)
		progress.percentage_increment_scaled(1.0 / 16)

		# Get machine credentials
		try:
			machine_secret = open('/etc/machine.secret', 'r').read().strip()
		except IOError as e:
			raise TakeoverError(_("Could not read local machine password: %s") % str(e))

		# Join into the domain
		log.info("Starting Samba domain join.")
		t = time.time()
		p = subprocess.Popen(["samba-tool", "domain", "join", self.ucr["domainname"], "DC", "-U%s%%%s" % (self.AD.username, self.AD.password), "--realm=%s" % self.ucr["kerberos/realm"], "--machinepass=%s" % machine_secret, "--server=%s" % self.ad_server_fqdn, "--site=%s" % self.AD.domain_info["ad_server_site"]], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		RE_SCHEMA = re.compile("^Schema-DN\[(?P<partition_dn>[^\]]+)\] objects\[([^\]]+)\] linked_values\[([^\]]+)\]$")
		RE_PARTITION = re.compile("^Partition\[(?P<partition_dn>[^\]]+)\] objects\[([^\]]+)\] linked_values\[([^\]]+)\]$")
		domain_dn = self.AD.samdb.domain_dn()
		part_started = ''
		while p.poll() is None:
			log_line = p.stdout.readline().rstrip()
			if log_line:
				log.debug(log_line)
				if not part_started:
					m = RE_SCHEMA.match(log_line)
					if m:
						part_started = "Schema partition"
						progress.message(_("Copying %s") % part_started)
						progress.percentage_increment_scaled(1.0 / 16)
				else:
					m = RE_PARTITION.match(log_line)
					if m:
						g = m.groups()
						part = g[0][:-len(domain_dn) - 1]
						if not part:
							part = domain_dn
						if part != part_started:
							progress.message(_("Copying %s") % part)
							progress.percentage_increment_scaled(1.0 / 16)
							part_started = part
			t1 = time.time()
			if t1 - t >= 1:
				progress.percentage_increment_scaled(1.0 / 32)
				t = t1
		if p.returncode == 0:
			log.info("Samba domain join successful.")
		else:
			self.cleanup_failed_join()
			raise DomainJoinFailed(_("The domain join failed. See %s for details.") % LOGFILE_NAME)

	def cleanup_failed_join(self):
		self.ucr.load()

		run_and_output_to_log(["univention-config-registry", "unset", "hosts/static/%s" % (self.ad_server_ip,)], log.debug)

		# Restore backup Samba directory
		if os.path.exists(self.backup_samba_dir):
			shutil.rmtree(SAMBA_PRIVATE_DIR)
			os.rename(self.backup_samba_dir, SAMBA_PRIVATE_DIR)
			# shutil.copytree(self.backup_samba_dir, SAMBA_PRIVATE_DIR, symlinks=True)

		# Start Samba again
		run_and_output_to_log(["/etc/init.d/samba-ad-dc", "start"], log.debug)

		# Start S4 Connector again
		run_and_output_to_log(["/etc/init.d/univention-s4-connector", "start"], log.debug)

		# Adjust some UCR settings back
		if "nameserver1/local" in self.ucr:
			nameserver1_orig = self.ucr["nameserver1/local"]
			run_and_output_to_log(["univention-config-registry", "set", "nameserver1=%s" % nameserver1_orig], log.debug)
			# unset temporary variable
			run_and_output_to_log(["univention-config-registry", "unset", "nameserver1/local"], log.debug)
		else:
			msg = []
			msg.append("Warning: Weird, unable to determine previous nameserver1...")
			msg.append("         Using localhost as fallback, probably that's the right thing to do.")
			log.warn("\n".join(msg))
			run_and_output_to_log(["univention-config-registry", "set", "nameserver1=127.0.0.1"], log.debug)

		# Use Samba4 as DNS backend
		run_and_output_to_log(["univention-config-registry", "set", "dns/backend=samba4"], log.debug)

		# Restart bind9 to use the Samba4 backend, just to be sure
		run_and_output_to_log(["/etc/init.d/bind9", "restart"], log.debug)

		# Start the NSCD again
		run_and_output_to_log(["/etc/init.d/nscd", "restart"], log.debug)

	def post_join_tasks_and_start_samba_without_drsuapi(self):

		# Now run the Joinscript again (AD Member starts at VERSION=1, regular UCS is done already)
		returncode = run_and_output_to_log(["univention-run-join-scripts", "--run-scripts", "96univention-samba4.inst"], log.debug)
		if returncode:
			log.error("ERROR: Final univention-run-join-scripts --run-scripts 96univention-samba4.inst failed (%d)" % (returncode,))
			raise DomainJoinFailed(_("The domain join failed. See %s for details.") % JOIN_LOGFILE_NAME)

		# create backup dir
		if not os.path.exists(BACKUP_DIR):
			os.mkdir(BACKUP_DIR)
		elif not os.path.isdir(BACKUP_DIR):
			log.debug('%s is a file, renaming to %s.bak' % (BACKUP_DIR, BACKUP_DIR))
			os.rename(BACKUP_DIR, "%s.bak" % BACKUP_DIR)
			os.mkdir(BACKUP_DIR)

		# Rewrite domain SID in OpenLDAP sambaDomain object
		self.ad_domainsid = None
		self.samdb = SamDB(os.path.join(SAMBA_PRIVATE_DIR, "sam.ldb"), session_info=system_session(self.lp), lp=self.lp)
		msgs = self.samdb.search(
			base=self.ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_BASE,
			expression="(objectClass=domain)",
			attrs=["objectSid"])
		if msgs:
			obj = msgs[0]
			self.ad_domainsid = str(ndr_unpack(security.dom_sid, obj["objectSid"][0]))
		if not self.ad_domainsid:
			raise TakeoverError(_("Failed to determine new domain SID."))

		self.old_domainsid = None
		self.lo = _connect_ucs(self.ucr)
		ldap_result = self.lo.search(filter=filter_format("(&(objectClass=sambaDomain)(sambaDomainName=%s))", [self.ucr["windows/domain"]]), attr=["sambaSID"])
		if len(ldap_result) == 1:
			sambadomain_object_dn = ldap_result[0][0]

			old_ucs_sambasid_backup_file = "%s/old_sambasid" % BACKUP_DIR
			if os.path.exists(old_ucs_sambasid_backup_file):
				f = open(old_ucs_sambasid_backup_file, 'r')
				self.old_domainsid = f.read()
				f.close()
			else:
				self.old_domainsid = ldap_result[0][1]["sambaSID"][0]
				f = open(old_ucs_sambasid_backup_file, 'w')
				f.write("%s" % self.old_domainsid)
				f.close()
		elif len(ldap_result) > 0:
			log.error('Error: Found more than one sambaDomain object with sambaDomainName=%s' % self.ucr["windows/domain"])
			# FIXME: probably sys.exit()?
		else:
			log.error('Error: Did not find a sambaDomain object with sambaDomainName=%s' % self.ucr["windows/domain"])
			sambadomain_object_dn = None
			# FIXME: probably sys.exit()?

		if self.ucr["windows/domain"] != self.ad_netbios_domain or not sambadomain_object_dn:
			ldap_result = self.lo.search(filter=filter_format("(&(objectClass=sambaDomain)(sambaDomainName=%s))", [self.ad_netbios_domain]), attr=["sambaSID"])
			if len(ldap_result) == 1:
				sambadomain_object_dn = ldap_result[0][0]
			elif len(ldap_result) > 0:
				log.error('Error: Found more than one sambaDomain object with sambaDomainName=%s' % self.ad_netbios_domain)
				# FIXME: probably sys.exit()?
			else:
				if sambadomain_object_dn:
					position = univention.admin.uldap.position(self.lo.base)
					module_settings_sambadomain = udm_modules.get('settings/sambadomain')
					udm_modules.init(self.lo, position, module_settings_sambadomain)

					try:
						sambadomain_object = module_settings_sambadomain.object(None, self.lo, position, sambadomain_object_dn)
						sambadomain_object.open()
					except uexceptions.ldapError as exc:
						log.debug("Opening '%s' failed: %s." % (sambadomain_object_dn, exc,))

					try:
						log.debug("Renaming '%s' to '%s' in UCS LDAP." % (sambadomain_object_dn, self.ad_netbios_domain))
						sambadomain_object['name'] = self.ad_netbios_domain
						sambadomain_object.modify()
					except uexceptions.ldapError as exc:
						log.debug("Renaming of '%s' failed: %s." % (sambadomain_object_dn, exc,))
					else:
						x = str2dn(sambadomain_object_dn)
						x[0] = [(x[0][0][0], self.ad_netbios_domain, ldap.AVA_STRING)]
						sambadomain_object_dn = dn2str(x)
				else:
					# FIXME: in this peculiar case we should create one.
					pass

			run_and_output_to_log(["univention-config-registry", "set", "windows/domain=%s" % self.ad_netbios_domain, ], log.debug)

		if sambadomain_object_dn:
			log.debug("Replacing old UCS sambaSID (%s) by AD domain SID (%s)." % (self.old_domainsid, self.ad_domainsid))
			if self.old_domainsid != self.ad_domainsid:
				ml = [("sambaSID", self.old_domainsid, self.ad_domainsid)]
				self.lo.modify(sambadomain_object_dn, ml)
		else:
			log.error("Error: Identification of Samba domain object failed")

		# Fix some attributes in local SamDB
		operatingSystem_attribute(self.ucr, self.samdb)
		try:
			takeover_DC_Behavior_Version(self.ucr, self.AD.samdb, self.samdb, self.ad_server_name, self.AD.domain_info["ad_server_site"])
		except ldb.LdbError as ex:
			log.debug('Exception during LDAP search of remote LDAP: %s' % (ex.args[0],))
			log.debug('Might be due to a timeout, attempting to reconnect.')
			self.AD.reconnect()
			takeover_DC_Behavior_Version(self.ucr, self.AD.samdb, self.samdb, self.ad_server_name, self.AD.domain_info["ad_server_site"])

		# Fix some attributes in SecretsDB
		secretsdb = samba.Ldb(os.path.join(SAMBA_PRIVATE_DIR, "secrets.ldb"), session_info=system_session(self.lp), lp=self.lp)

		let_samba4_manage_etc_krb5_keytab(self.ucr, secretsdb)
		spn_list = ("host/%s" % self.local_fqdn, "ldap/%s" % self.local_fqdn)
		add_servicePrincipals(self.ucr, secretsdb, spn_list)

		# Avoid password expiry for DCs:
		run_and_output_to_log(["samba-tool", "user", "setexpiry", "--noexpiry", "--filter", '(&(objectclass=computer)(serverReferenceBL=*))'], log.debug)
		time.sleep(2)

		# Disable replication from Samba4 to AD
		run_and_output_to_log(["univention-config-registry", "set", "samba4/dcerpc/endpoint/drsuapi=false"], log.debug)

		# Start Samba
		run_and_output_to_log(["/etc/init.d/samba-ad-dc", "start"], log.debug)
		check_samba4_started()

	def remove_conflicting_msgpo_objects(self):
		'''The S4 Connector prefers OpenLDAP objects, so we must remove conflicting ones'''

		sysvol_dir = "/var/lib/samba/sysvol"
		samdb_domain_dns_name = self.samdb.domain_dns_name()
		sam_sysvol_dom_dir = os.path.join(sysvol_dir, samdb_domain_dns_name)
		ucs_sysvol_dom_dir = os.path.join(sysvol_dir, ucr["domainname"])
		if samdb_domain_dns_name != ucr["domainname"]:
			if os.path.isdir(ucs_sysvol_dom_dir) and not os.path.isdir(sam_sysvol_dom_dir):
				os.rename(ucs_sysvol_dom_dir, sam_sysvol_dom_dir)

		msgs = self.samdb.search(
			base=self.samdb.domain_dn(), scope=samba.ldb.SCOPE_SUBTREE,
			expression="(objectClass=groupPolicyContainer)",
			attrs=["cn"])

		for obj in msgs:
			name = obj["cn"][0]
			run_and_output_to_log(["/usr/sbin/univention-directory-manager", "container/msgpo", "delete", "--filter", filter_format("name=%s", [name])], log.debug)
			gpo_path = '%s/Policies/%s' % (sam_sysvol_dom_dir, name,)
			if os.path.exists(gpo_path):
				log.info("Removing associated conflicting GPO directory %s." % (gpo_path,))
				shutil.rmtree(gpo_path, ignore_errors=True)

			if name.upper() == name:
				continue

			run_and_output_to_log(["/usr/sbin/univention-directory-manager", "container/msgpo", "delete", "--filter", filter_format("name=%s", [name.upper()])], log.debug)
			gpo_path = '%s/Policies/%s' % (sam_sysvol_dom_dir, name.upper(),)
			if os.path.exists(gpo_path):
				log.info("Removing associated conflicting GPO directory %s." % (gpo_path,))
				shutil.rmtree(gpo_path, ignore_errors=True)
		run_and_output_to_log(["/usr/share/univention-s4-connector/msgpo.py", "--write2ucs"], log.debug)

	def rewrite_sambaSIDs_in_OpenLDAP(self):
		# Phase I.b: Pre-Map SIDs (locale adjustment etc.)

		# pre-create containers in UDM
		container_list = []
		msgs = self.samdb.search(
			base=self.ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_SUBTREE,
			expression="(objectClass=organizationalunit)",
			attrs=["dn"])
		if msgs:
			log.debug("Creating OUs in the Univention Directory Manager")
		for obj in msgs:
			container_list.append(obj["dn"].get_linearized())

		container_list.sort(key=len)

		for container_dn in container_list:
			(ou_type, ou_name) = ldap.dn.str2dn(container_dn)[0][0][:2]
			position = parentDn(container_dn).lower().replace(self.ucr['samba4/ldap/base'].lower(), self.ucr['ldap/base'].lower())

			udm_type = None
			if ou_type.upper() == "OU":
				udm_type = "container/ou"
			elif ou_type.upper() == "CN":
				udm_type = "container/cn"
			else:
				log.warn("Warning: Unmapped container type %s" % container_dn)

			if udm_type:
				run_and_output_to_log(["/usr/sbin/univention-directory-manager", udm_type, "create", "--ignore_exists", "--position", position, "--set", "name=%s" % ou_name], log.debug)

		# Identify and rename UCS group names to match Samba4 (localized) group names
		AD_well_known_sids = {}
		for (rid, name) in list(univention.lib.s4.well_known_domain_rids.items()):
			AD_well_known_sids["%s-%s" % (self.ad_domainsid, rid)] = name
		AD_well_known_sids.update(univention.lib.s4.well_known_sids)

		groupRenameHandler = GroupRenameHandler(self.lo)
		userRenameHandler = UserRenameHandler(self.lo)

		for (sid, canonical_name) in list(AD_well_known_sids.items()):

			msgs = self.samdb.search(
				base=self.ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_SUBTREE,
				expression=filter_format("(&(objectSid=%s)(sAMAccountName=*))", (sid,)),
				attrs=["sAMAccountName", "objectClass"])
			if not msgs:
				log.debug("Name of Well known SID %s not found in Samba" % (sid,))
				continue

			obj = msgs[0]
			ad_object_name = obj.get("sAMAccountName", [None])[0]
			oc = obj["objectClass"]

			if not ad_object_name:
				continue

			if sid == "S-1-5-32-550":  # Special: Printer-Admins / Print Operators / Opérateurs d’impression
				# don't rename, adjust group name mapping for S4 connector instead.
				run_and_output_to_log(["univention-config-registry", "set", "connector/s4/mapping/group/table/Printer-Admins=%s" % (ad_object_name,)], log.debug)
				continue

			ucsldap_object_name = canonical_name  # default
			# lookup canonical_name in UCSLDAP, for cases like "Replicator/Replicators" and "Server Operators"/"System Operators" that changed in UCS 3.2, see Bug #32461#c2
			ucssid = sid.replace(self.ad_domainsid, self.old_domainsid, 1)
			ldap_result = self.lo.search(filter=filter_format("(sambaSID=%s)", (ucssid,)), attr=["sambaSID", "uid", "cn"])
			if len(ldap_result) == 1:
				if "group" in oc or "foreignSecurityPrincipal" in oc:
					ucsldap_object_name = ldap_result[0][1].get("cn", [None])[0]
				elif "user" in oc:
					ucsldap_object_name = ldap_result[0][1].get("uid", [None])[0]
			elif len(ldap_result) > 0:
				log.error('Error: Found more than one object with sambaSID=%s' % (sid,))
			else:
				log.debug('Info: Did not find an object with sambaSID=%s' % (sid,))

			if not ucsldap_object_name:
				continue

			if ad_object_name.lower() != ucsldap_object_name.lower():
				if "group" in oc or "foreignSecurityPrincipal" in oc:
					groupRenameHandler.rename_ucs_group(ucsldap_object_name, ad_object_name)
				elif "user" in oc:
					userRenameHandler.rename_ucs_user(ucsldap_object_name, ad_object_name)

		# construct dict of old UCS sambaSIDs
		old_sambaSID_dict = {}
		samba_sid_map = {}
		# Users and Computers
		ldap_result = self.lo.search(filter="(&(objectClass=sambaSamAccount)(sambaSID=*))", attr=["uid", "sambaSID", "univentionObjectType"])
		for record in ldap_result:
			(ucs_object_dn, ucs_object_dict) = record
			old_sid = ucs_object_dict["sambaSID"][0]
			ucs_name = ucs_object_dict["uid"][0]
			if old_sid.startswith(self.old_domainsid):
				old_sambaSID_dict[old_sid] = ucs_name

				msgs = self.samdb.search(
					base=self.ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_SUBTREE,
					expression=filter_format("(sAMAccountName=%s)", (ucs_name,)),
					attrs=["dn", "objectSid"])
				if not msgs:
					continue
				else:
					obj = msgs[0]
					new_sid = str(ndr_unpack(security.dom_sid, obj["objectSid"][0]))
					samba_sid_map[old_sid] = new_sid

					log.debug("Rewriting user %s SID %s to %s" % (old_sambaSID_dict[old_sid], old_sid, new_sid))
					ml = [("sambaSID", old_sid, new_sid)]
					self.lo.modify(ucs_object_dn, ml)

		# Groups
		ldap_result = self.lo.search(filter="(&(objectClass=sambaGroupMapping)(sambaSID=*))", attr=["cn", "sambaSID", "univentionObjectType"])
		for record in ldap_result:
			(ucs_object_dn, ucs_object_dict) = record
			old_sid = ucs_object_dict["sambaSID"][0]
			ucs_name = ucs_object_dict["cn"][0]
			if old_sid.startswith(self.old_domainsid):
				old_sambaSID_dict[old_sid] = ucs_name

				msgs = self.samdb.search(
					base=self.ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_SUBTREE,
					expression=filter_format("(sAMAccountName=%s)", (ucs_name,)),
					attrs=["objectSid"])
				if not msgs:
					continue
				else:
					obj = msgs[0]
					new_sid = str(ndr_unpack(security.dom_sid, obj["objectSid"][0]))
					samba_sid_map[old_sid] = new_sid

					log.debug("Rewriting group '%s' SID %s to %s" % (old_sambaSID_dict[old_sid], old_sid, new_sid))
					ml = [("sambaSID", old_sid, new_sid)]
					self.lo.modify(ucs_object_dn, ml)

		ldap_result = self.lo.search(filter="(sambaPrimaryGroupSID=*)", attr=["sambaPrimaryGroupSID"])
		for record in ldap_result:
			(ucs_object_dn, ucs_object_dict) = record
			old_sid = ucs_object_dict["sambaPrimaryGroupSID"][0]
			if old_sid.startswith(self.old_domainsid):
				if old_sid in samba_sid_map:
					ml = [("sambaPrimaryGroupSID", old_sid, samba_sid_map[old_sid])]
					self.lo.modify(ucs_object_dn, ml)
				else:
					if old_sid in old_sambaSID_dict:
						# log.error("Error: Could not find new sambaPrimaryGroupSID for %s" % old_sambaSID_dict[old_sid])
						pass
					else:
						log.debug("Warning: Unknown sambaPrimaryGroupSID %s" % old_sid)

		# Pre-Create mail domains for all mail and proxyAddresses:
		msgs = self.samdb.search(
			base=self.ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_SUBTREE,
			expression="(|(mail=*)(proxyAddresses=*))",
			attrs=["mail", "proxyAddresses"])
		maildomains = []
		for msg in msgs:
			for attr in ("mail", "proxyAddresses"):
				if attr in msg:
					for address in msg[attr]:
						char_idx = address.find("@")
						if char_idx != -1:
							domainpart = address[char_idx + 1:].lower()
							# if not domainpart.endswith(".local"): ## We need to create all the domains. Alternatively set:
							# ucr:directory/manager/web/modules/users/user/properties/mailAlternativeAddress/syntax=emailAddress
							if domainpart not in maildomains:
								maildomains.append(domainpart)
		for maildomain in maildomains:
			returncode = run_and_output_to_log(["univention-directory-manager", "mail/domain", "create", "--ignore_exists", "--position", "cn=domain,cn=mail,%s" % self.ucr["ldap/base"], "--set", "name=%s" % maildomain], log.debug)
			if returncode != 0:
				log.error("Creation of UCS mail/domain %s failed. See %s for details." % (maildomain, LOGFILE_NAME,))

		# re-create DNS SPN account
		log.debug("Attempting removal of DNS SPN account in UCS-LDAP, will be recreated later with new password.")
		run_and_output_to_log(["univention-directory-manager", "users/user", "delete", "--dn", "uid=dns-%s,cn=users,%s" % (escape_dn_chars(self.ucr["hostname"]), self.ucr["ldap/base"])], log.debug)

		# remove zarafa and univention-squid-kerberos SPN accounts, recreated later in phaseIII by running the respective joinscripts again
		log.debug("Attempting removal of Zarafa and Squid SPN accounts in UCS-LDAP, will be recreated later with new password.")
		for service in ("zarafa", "http", "http-proxy"):
			run_and_output_to_log(["univention-directory-manager", "users/user", "delete", "--dn", "uid=%s-%s,cn=users,%s" % (escape_dn_chars(service), escape_dn_chars(self.ucr["hostname"]), self.ucr["ldap/base"])], log.debug)

		# Remove logonHours restrictions from Administrator account, was set in one test environment..
		msgs = self.samdb.search(
			base=self.ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_SUBTREE,
			expression="(samaccountname=Administrator)",
			attrs=["logonHours"])
		if msgs:
			obj = msgs[0]
			if "logonHours" in obj:
				log.debug("Removing logonHours restriction from Administrator account")
				delta = ldb.Message()
				delta.dn = obj.dn
				delta["logonHours"] = ldb.MessageElement([], ldb.FLAG_MOD_DELETE, "logonHours")
				self.samdb.modify(delta)

	def resync_s4connector_listener(self, progress):
		log.info("Waiting for listener to finish (max. 30 minutes)")
		if not wait_for_listener_replication(progress, 1800):
			log.warn("Warning: Stopping Listener now anyway.")

		# Restart Univention Directory Listener for S4 Connector
		log.info("Restarting Univention Directory Listener")

		# Reset S4 Connector and handler state
		run_and_output_to_log(["systemctl", "stop", "univention-directory-listener"], log.debug)

		for i in range(30):
			time.sleep(1)
			# progress.percentage_increment_scaled(1.0/100)
			progress.percentage_increment_scaled(1.0 / 32)

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
				except Exception as e:
					log.error("Error removing file: %s" % str(e))

		returncode = run_and_output_to_log(["systemctl", "start", "univention-directory-listener"], log.debug)
		if returncode != 0:
			log.error("Start of univention-directory-listener failed. See %s for details." % (LOGFILE_NAME,))

		# print "Waiting for directory listener to start up (10 seconds)",
		# for i in xrange(10):
		#	time.sleep(1)
		#	print_progress()
		# print

	def start_s4_connector(self, progress):
		old_sleep = self.ucr.get("connector/s4/poll/sleep", "5")
		old_retry = self.ucr.get("connector/s4/retryrejected", "10")
		run_and_output_to_log(["univention-config-registry", "set", "connector/s4/poll/sleep=1", "connector/s4/retryrejected=2"], log.debug)

		# turn off the legacy position_mapping:
		run_and_output_to_log(["univention-config-registry", "unset", "connector/s4/mapping/dns/position"], log.debug)

		# rotate S4 connector log and start the S4 Connector
		# careful: the postrotate task used to "restart" the connector!
		run_and_output_to_log(["logrotate", "-f", "/etc/logrotate.d/univention-s4-connector"], log.debug)

		# Just in case, start the Connector explicitly
		log.info("Starting S4 Connector")
		returncode = run_and_output_to_log(["/etc/init.d/univention-s4-connector", "start"], log.debug)
		if returncode != 0:
			log.error("Start of univention-s4-connector failed. See %s for details." % (LOGFILE_NAME,))

		log.info("Waiting for S4 Connector sync")
		wait_for_s4_connector_replication(self.ucr, self.lp, progress)
		# Reset normal relication intervals
		run_and_output_to_log(["univention-config-registry", "set", "connector/s4/poll/sleep=%s" % old_sleep, "connector/s4/retryrejected=%s" % old_retry], log.debug)
		returncode = run_and_output_to_log(["/etc/init.d/univention-s4-connector", "restart"], log.debug)
		if returncode != 0:
			log.error("Restart of univention-s4-connector failed. See %s for details." % (LOGFILE_NAME,))

	def rebuild_idmap(self):
		# rebuild idmap
		returncode = run_and_output_to_log(["/usr/lib/univention-directory-listener/system/samba4-idmap.py", "--direct-resync"], log.debug)
		if returncode != 0:
			log.error("Resync of samba4-idmap failed. See %s for details." % (LOGFILE_NAME,))

		# Start NSCD again
		returncode = run_and_output_to_log(["/etc/init.d/nscd", "start"], log.debug)
		if returncode != 0:
			log.error("Start of nscd failed. See %s for details." % (LOGFILE_NAME,))

		# Save AD server IP for Phase III
		run_and_output_to_log(["univention-config-registry", "set", "univention/ad/takeover/ad/server/ip=%s" % (self.ad_server_ip)], log.debug)

	def set_nameserver1_to_local_default_ip(self):
		default_ip = Interfaces().get_default_ip_address().ip
		if default_ip:
			run_and_output_to_log(["univention-config-registry", "set", "nameserver1=%s" % default_ip], log.debug)
		else:
			msg = []
			msg.append("Warning: get_default_ip_address failed, using 127.0.0.1 as fallback")
			log.warn("\n".join(msg))
			run_and_output_to_log(["univention-config-registry", "set", "nameserver1=127.0.0.1"], log.debug)

	def reset_sysvol_ntacls(self):
		# Re-Set NTACLs from nTSecurityDescriptor on sysvol policy directories
		# This is necessary as 96univention-samba4.inst hasn't run yet at this point in AD Member mode
		# It's required for robocopy access
		subprocess.call(["net", "cache", "flush"], stdout=DEVNULL, stderr=DEVNULL)
		subprocess.call(["samba-tool", "ntacl", "sysvolreset"], stdout=DEVNULL, stderr=DEVNULL)


class AD_Takeover_Finalize(object):

	def __init__(self, ucr):
		self.lp = LoadParm()
		try:
			self.lp.load('/etc/samba/smb.conf')
		except:
			self.lp.load('/dev/null')

		# check if an IP address was recorded in UCR during Phase I
		self.ucr = ucr
		self.ucr.load()
		self.ad_server_ip = ucr.get("univention/ad/takeover/ad/server/ip")
		if not self.ad_server_ip:
			log.error("Error: AD server IP not found in UCR. This indicates that phase I was not completed successfully yet.")
			raise TakeoverError(_("The Active Directory domain join was not completed successfully yet."))

		if not "hosts/static/%s" % self.ad_server_ip in self.ucr:
			msg = []
			msg.append("")
			msg.append("Error: given IP %s was not mapped to a hostname in phase I." % (self.ad_server_ip,))
			msg.append("       Please complete phase I of the takeover before initiating the FSMO takeover.")
			log.error("\n".join(msg))
			raise TakeoverError(_("The Active Directory domain join was not completed successfully yet."))

		self.ad_server_fqdn, self.ad_server_name = self.ucr["hosts/static/%s" % self.ad_server_ip].split(None, 1)

		# Check if the AD server is already in the local SAM db
		samdb = SamDB(os.path.join(SAMBA_PRIVATE_DIR, "sam.ldb"), session_info=system_session(self.lp), lp=self.lp)
		msgs = samdb.search(
			base=self.ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_SUBTREE,
			expression=filter_format("(sAMAccountName=%s$)", [self.ad_server_name]),
			attrs=["objectSid"])
		if msgs:
			log.info("OK, Found the AD DC %s account in the local Samba 4 SAM database." % self.ad_server_name)
		else:
			msg = []
			msg.append("")
			msg.append("Error: It seems that this script was run once already for the first takeover step,")
			msg.append("       but the server %s cannot be found in the local Samba SAM database." % self.ad_server_name)
			msg.append("       Don't know how to continue, giving up at this point.")
			msg.append("       Maybe the steps needed for takeover have been finished already?")
			log.error("\n".join(msg))
			raise TakeoverError(_("Active Directory takeover finished already."))

		self.local_fqdn = '.'.join((self.ucr["hostname"], self.ucr["domainname"]))
		self.primary_interface = None

	def ping_AD(self, progress):
		# Ping the IP
		ip_version = determine_IP_version(self.ad_server_ip)

		if ip_version == 6:
			cmd = ["fping6", self.ad_server_ip]
		else:
			cmd = ["fping", self.ad_server_ip]

		p1 = subprocess.Popen(cmd, stdout=DEVNULL, stderr=DEVNULL)
		rc = p1.poll()
		while rc is None:
			progress.percentage_increment_scaled(1.0 / 16)
			time.sleep(1)
			rc = p1.poll()

		if rc == 0:
			msg = []
			msg.append("")
			msg.append("Error: The server IP %s is still reachable." % self.ad_server_ip)
			log.error("\n".join(msg))
			raise ADServerRunning(_("The Server IP %s is still online, please shut down the machine.") % (self.ad_server_ip,))
		else:
			log.info("Ok, Server IP %s unreachable.\n" % self.ad_server_ip)

	def post_join_fix_samDB(self):
		# Restart Samba and make sure the rapid restart did not leave the main process blocking
		run_and_output_to_log(["/etc/init.d/samba-ad-dc", "restart"], log.debug)
		check_samba4_started()

		# 1. Determine Site of local server, important for locale-dependend names like "Standardname-des-ersten-Standorts"
		self.sitename = None
		self.samdb = SamDB(os.path.join(SAMBA_PRIVATE_DIR, "sam.ldb"), session_info=system_session(self.lp), lp=self.lp)
		msgs = self.samdb.search(
			base=self.ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_SUBTREE,
			expression=filter_format("(sAMAccountName=%s$)", (self.ucr["hostname"],)),
			attrs=["serverReferenceBL"])
		if msgs:
			obj = msgs[0]
			serverReferenceBL = obj["serverReferenceBL"][0]
			serverReferenceBL_RDNs = ldap.explode_dn(serverReferenceBL)
			serverReferenceBL_RDNs.reverse()
			config_partition_index = None
			site_container_index = None
			for i in range(len(serverReferenceBL_RDNs)):
				if site_container_index:
					self.sitename = serverReferenceBL_RDNs[i].split('=', 1)[1]
					break
				elif config_partition_index and serverReferenceBL_RDNs[i] == "CN=Sites":
					site_container_index = i
				elif not site_container_index and serverReferenceBL_RDNs[i] == "CN=Configuration":
					config_partition_index = i
				i = i + 1
			log.info("Located server %s in AD site %s in Samba4 SAM database." % (self.ucr["hostname"], self.sitename))

		# properly register partitions
		self.partitions = takeover_hasInstantiatedNCs(self.ucr, self.samdb, self.ad_server_name, self.sitename)

	def fix_sysvol_acls(self):

		# Backup current NTACLs on sysvol
		p = subprocess.Popen(["getfattr", "-m", "-", "-d", "-R", SYSVOL_PATH], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(stdout, stderr) = p.communicate()
		if stdout:
			now = time.localtime()
			timestamp = time.strftime("%Y%m%d%H%M%S", now)
			f = open('%s/sysvol_attr_backup.log-%s' % (BACKUP_DIR, timestamp), 'a')
			f.write("### getfattr output %s\n%s" % (time.strftime("%Y-%m-%d %H:%M:%S", now), stdout))
			f.close()
		else:
			log.debug("getfattr did not produce any output")
		if len(stderr.rstrip().split('\n')) > 1:
			log.debug(stderr)

		# Re-Set NTACLs from nTSecurityDescriptor on sysvol policy directories
		subprocess.call(["net", "cache", "flush"], stdout=DEVNULL, stderr=DEVNULL)
		run_and_output_to_log(["samba-tool", "ntacl", "sysvolreset"], log.debug)

		# Re-set default fACLs so sysvol-sync can read files and directories (See Bug#29065)
		returncode = run_and_output_to_log(["setfacl", "-R", "-P", "-m", "g:Authenticated Users:r-x,d:g:Authenticated Users:r-x", SYSVOL_PATH], log.debug)
		if returncode != 0:
			log.error("Error: Could not set fACL for %s" % SYSVOL_PATH)
			msg = []
			msg.append("Warning: Continuing anyway. Please fix later by running:")
			msg.append("         setfacl -R -P -m 'g:Authenticated Users:r-x,d:g:Authenticated Users:r-x' %s" % SYSVOL_PATH)
			log.warn("\n".join(msg))

	def create_DNS_alias_for_AD_hostname(self):
		# Add DNS records to UDM:
		run_and_output_to_log(["/usr/share/univention-samba4/scripts/setup-dns-in-ucsldap.sh", "--dc", "--pdc", "--gc", "--site=%s" % self.sitename], log.info)

		# wait_for_s4_connector_replication hangs forever in the sqlite query
		# #wait_for_s4_connector_replication(self.ucr, self.lp)
		# # Let samba_dnsupdate check DNS records
		#run_and_output_to_log(["/usr/sbin/samba_dnsupdate", ], log.info)

		# remove local entry for AD DC from /etc/hosts
		run_and_output_to_log(["univention-config-registry", "unset", "hosts/static/%s" % self.ad_server_ip], log.debug)

		# Replace DNS host record for AD Server name by DNS Alias
		run_and_output_to_log(["univention-directory-manager", "dns/host_record", "delete", "--superordinate", "zoneName=%s,cn=dns,%s" % (escape_dn_chars(self.ucr["domainname"]), self.ucr["ldap/base"]), "--dn", "relativeDomainName=%s,zoneName=%s,cn=dns,%s" % (escape_dn_chars(self.ad_server_name), escape_dn_chars(self.ucr["domainname"]), self.ucr["ldap/base"])], log.debug)

		returncode = run_and_output_to_log(["univention-directory-manager", "dns/alias", "create", "--superordinate", "zoneName=%s,cn=dns,%s" % (escape_dn_chars(self.ucr["domainname"]), self.ucr["ldap/base"]), "--set", "name=%s" % self.ad_server_name, "--set", "cname=%s" % self.local_fqdn], log.debug)
		if returncode != 0:
			log.error("Creation of dns/alias %s for %s failed. See %s for details." % (self.ad_server_name, self.local_fqdn, LOGFILE_NAME,))

	def remove_AD_server_account_from_samdb(self):
		# Cleanup necessary to use NETBIOS Alias
		backlink_attribute_list = ["serverReferenceBL", "frsComputerReferenceBL", "msDFSR-ComputerReferenceBL"]
		msgs = self.samdb.search(
			base=self.ucr["samba4/ldap/base"], scope=samba.ldb.SCOPE_SUBTREE,
			expression=filter_format("(sAMAccountName=%s$)", [self.ad_server_name]),
			attrs=backlink_attribute_list)
		if msgs:
			obj = msgs[0]
			for backlink_attribute in backlink_attribute_list:
				if backlink_attribute in obj:
					backlink_object = obj[backlink_attribute][0]
					try:
						log.info("Removing %s from SAM database." % (backlink_object,))
						self.samdb.delete(backlink_object, ["tree_delete:0"])
					except:
						log.debug("Removal of AD %s objects %s from Samba4 SAM database failed. See %s for details." % (backlink_attribute, backlink_object, LOGFILE_NAME,))
						log.debug(traceback.format_exc())

			# Now delete the AD DC account and sub-objects
			# Cannot use tree_delete on isCriticalSystemObject, perform recursive delete like ldbdel code does it:
			msgs = self.samdb.search(base=obj.dn, scope=samba.ldb.SCOPE_SUBTREE, attrs=["dn"])
			obj_dn_list = [o.dn for o in msgs]
			obj_dn_list.sort(key=len)
			obj_dn_list.reverse()
			for obj_dn in obj_dn_list:
				try:
					log.info("Removing %s from SAM database." % (obj_dn,))
					self.samdb.delete(obj_dn)
				except:
					log.error("Removal of AD DC account object %s from Samba4 SAM database failed. See %s for details." % (obj_dn, LOGFILE_NAME,))
					log.debug(traceback.format_exc())

	def remove_AD_server_account_from_UDM(self):
		# Finally, for consistency remove AD DC object from UDM
		log.debug("Removing AD DC account from local Univention Directory Manager")
		returncode = run_and_output_to_log(["univention-directory-manager", "computers/windows_domaincontroller", "delete", "--dn", "cn=%s,cn=dc,cn=computers,%s" % (escape_dn_chars(self.ad_server_name), self.ucr["ldap/base"])], log.debug)
		if returncode != 0:
			log.error("Removal of DC account %s via UDM failed. See %s for details." % (self.ad_server_name, LOGFILE_NAME,))

	def create_NETBIOS_alias_for_AD_hostname(self):
		# Create NETBIOS Alias
		f = open('/etc/samba/local.conf', 'a')
		f.write('[global]\nnetbios aliases = "%s"\n' % self.ad_server_name)
		f.close()

		run_and_output_to_log(["univention-config-registry", "commit", "/etc/samba/smb.conf"], log.debug)

	def _get_primary_interface(self, ipv4=True):
		# from dedicated ucs var
		if self.ucr.get('adtakeover/interface', None):
			primary_interface = self.ucr['adtakeover/interface']
			log.info('got primary interface %s from ucr adtakeover/interface' % primary_interface)
			return primary_interface
		# from routing
		primary_interface = None
		p = subprocess.Popen(['ip', 'route', 'get', self.ad_server_ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(stdout, stderr) = p.communicate()
		if stdout:
			for line in stdout.splitlines():
				if 'dev ' in line:
					try:
						primary_interface = line.split('dev')[1].split()[0]
						if primary_interface != 'lo':
							log.info('got primary interface %s from ip route' % primary_interface)
							return primary_interface
					except IndexError:
						pass
		# from ucr primary
		if self.ucr.get('interfaces/primary', None):
			primary_interface = self.ucr['interfaces/primary']
			log.info('got primary interface %s from ucr interfaces/primary' % primary_interface)
			return primary_interface
		# from ucr interfaces
		ipv4_interfaces = list()
		ipv6_interfaces = list()
		for k in list(self.ucr.keys()):
			m = re.match('interfaces/([^/]+)/address', k)
			if m:
				ipv4_interfaces.append(m.group(1))
			m = re.match('interfaces/([^/]+)/ipv6/default/address', k)
			if m:
				ipv6_interfaces.append(m.group(1))
		if ipv4 and ipv4_interfaces:
			primary_interface = sorted(ipv4_interfaces)[0]
			log.info('got primary interface %s from ucr interfaces/.*/address' % primary_interface)
			return primary_interface
		elif not ipv4 and ipv6_interfaces:
			primary_interface = sorted(ipv6_interfaces)[0]
			log.info('got primary interface %s from ucr interfaces/.*/ipv6/default/address' % primary_interface)
			return primary_interface
		else:
			log.error('could not find primary interface, using eth0, check interfaces/primary or adtakeover/interface ucr variables!')
			return 'eth0'

	def create_virtual_IP_alias(self):
		# Assign AD IP to a virtual network interface
		# Determine primary network interface, UCS 3.0-2 style:
		ip_version = determine_IP_version(self.ad_server_ip)

		new_interface = None
		if not ip_version:
			msg = []
			msg.append("Error: Parsing AD server address failed")
			msg.append("       Failed to setup a virtual network interface with the AD IP address.")
			log.error("\n".join(msg))
		elif ip_version == 4:
			self.primary_interface = self._get_primary_interface(ipv4=True)
			for j in range(1, 6):
				if not "interfaces/%s_%s/address" % (self.primary_interface, j) in self.ucr:
					new_interface_ucr = "%s_%s" % (self.primary_interface, j)
					new_interface = "%s:%s" % (self.primary_interface, j)
					break
			if new_interface:
				guess_network = self.ucr["interfaces/%s/network" % self.primary_interface]
				guess_netmask = self.ucr["interfaces/%s/netmask" % self.primary_interface]
				guess_broadcast = self.ucr["interfaces/%s/broadcast" % self.primary_interface]
				run_and_output_to_log(["/usr/share/univention-updater/disable-apache2-umc"], log.debug)
				run_and_output_to_log([
					"univention-config-registry", "set",
					"interfaces/%s/address=%s" % (new_interface_ucr, self.ad_server_ip),
					"interfaces/%s/network=%s" % (new_interface_ucr, guess_network),
					"interfaces/%s/netmask=%s" % (new_interface_ucr, guess_netmask),
					"interfaces/%s/broadcast=%s" % (new_interface_ucr, guess_broadcast)], log.debug)
				samba_interfaces = self.ucr.get("samba/interfaces")
				if self.ucr.is_true("samba/interfaces/bindonly") and samba_interfaces:
					run_and_output_to_log(["univention-config-registry", "set", "samba/interfaces=%s %s" % (samba_interfaces, new_interface)], log.debug)
				run_and_output_to_log(["/usr/share/univention-updater/enable-apache2-umc", "--no-restart"], log.debug)
			else:
				msg = []
				msg.append("Warning: Could not determine primary IPv4 network interface.")
				msg.append("         Failed to setup a virtual IPv4 network interface with the AD IP address.")
				log.warn("\n".join(msg))
		elif ip_version == 6:
			self.primary_interface = self._get_primary_interface(ipv4=False)
			for j in range(1, 6):
				if not "interfaces/eth%s_%s/ipv6/default/address" % (self.primary_interface, j) in self.ucr:
					new_interface_ucr = "%s_%s" % (self.primary_interface, j)
					new_interface = "%s:%s" % (self.primary_interface, j)
					break

			if new_interface:
				run_and_output_to_log(["/usr/share/univention-updater/disable-apache2-umc"], log.debug)
				run_and_output_to_log([
					"univention-config-registry", "set",
					"interfaces/%s/ipv6/default/address=%s" % (new_interface_ucr, self.ad_server_ip),
					"interfaces/%s/ipv6/default/prefix=%s" % (new_interface_ucr, guess_broadcast),
					"interfaces/%s/ipv6/acceptRA=false"], log.debug)
				samba_interfaces = self.ucr.get("samba/interfaces")
				if self.ucr.is_true("samba/interfaces/bindonly") and samba_interfaces:
					run_and_output_to_log(["univention-config-registry", "set", "samba/interfaces=%s %s" % (samba_interfaces, new_interface)], log.debug)
				run_and_output_to_log(["/usr/share/univention-updater/enable-apache2-umc", "--no-restart"], log.debug)
			else:
				msg = []
				msg.append("Warning: Could not determine primary IPv6 network interface.")
				msg.append("         Failed to setup a virtual IPv6 network interface with the AD IP address.")
				log.warn("\n".join(msg))

	def create_reverse_DNS_records(self):
		# Add record in reverse zone as well, to make nslookup $domainname on XP clients happy..
		p = subprocess.Popen(["univention-ipcalc6", "--ip", self.ad_server_ip, "--netmask", self.ucr["interfaces/%s/netmask" % self.primary_interface], "--output", "pointer", "--calcdns"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(stdout, stderr) = p.communicate()
		if stdout.rstrip():
			ptr_address = stdout.rstrip()

		p = subprocess.Popen(["univention-ipcalc6", "--ip", self.ad_server_ip, "--netmask", self.ucr["interfaces/%s/netmask" % self.primary_interface], "--output", "reverse", "--calcdns"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		(stdout, stderr) = p.communicate()
		if stdout.rstrip():
			subnet_parts = stdout.rstrip().split('.')
			subnet_parts.reverse()
			ptr_zone = "%s.in-addr.arpa" % '.'.join(subnet_parts)

		if ptr_zone and ptr_address:
			# check for an existing record.
			p = subprocess.Popen(["univention-directory-manager", "dns/ptr_record", "list", "--superordinate", "zoneName=%s,cn=dns,%s" % (escape_dn_chars(ptr_zone), self.ucr["ldap/base"]), "--filter", filter_format("address=%s", [ptr_address])], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			(stdout, stderr) = p.communicate()
			if len(stdout.rstrip().split('\n')) > 1:
				# modify existing record.
				returncode = run_and_output_to_log(["univention-directory-manager", "dns/ptr_record", "modify", "--superordinate", "zoneName=%s,cn=dns,%s" % (escape_dn_chars(ptr_zone), self.ucr["ldap/base"]), "--dn", "relativeDomainName=%s,zoneName=%s,cn=dns,%s" % (escape_dn_chars(ptr_address), escape_dn_chars(ptr_zone), self.ucr["ldap/base"]), "--set", "ptr_record=%s." % self.local_fqdn], log.debug)
				if returncode != 0:
					log.warn("Warning: Update of reverse DNS record %s for %s failed. See %s for details." % (self.ad_server_ip, self.local_fqdn, LOGFILE_NAME,))
			else:
				# add new record.
				returncode = run_and_output_to_log(["univention-directory-manager", "dns/ptr_record", "create", "--superordinate", "zoneName=%s,cn=dns,%s" % (escape_dn_chars(ptr_zone), self.ucr["ldap/base"]), "--set", "address=%s" % ptr_address, "--set", "ptr_record=%s." % self.local_fqdn], log.debug)
				if returncode != 0:
					log.warn("Warning: Creation of reverse DNS record %s for %s failed. See %s for details." % (self.ad_server_ip, self.local_fqdn, LOGFILE_NAME,))
		else:
			log.warn("Warning: Calculation of reverse DNS record %s for %s failed. See %s for details." % (self.ad_server_ip, self.local_fqdn, LOGFILE_NAME,))

	def reconfigure_nameserver_for_samba_backend(self):
		# Resolve against local Bind9
		if "nameserver1/local" in self.ucr:
			nameserver1_orig = self.ucr["nameserver1/local"]
			run_and_output_to_log(["univention-config-registry", "set", "nameserver1=%s" % nameserver1_orig], log.debug)
			# unset temporary variable
			run_and_output_to_log(["univention-config-registry", "unset", "nameserver1/local"], log.debug)
		else:
			msg = []
			msg.append("Warning: Weird, unable to determine previous nameserver1...")
			msg.append("         Using localhost as fallback, probably that's the right thing to do.")
			log.warn("\n".join(msg))
			run_and_output_to_log(["univention-config-registry", "set", "nameserver1=127.0.0.1"], log.debug)

		# Use Samba4 as DNS backend
		run_and_output_to_log(["univention-config-registry", "set", "dns/backend=samba4"], log.debug)

	def claim_FSMO_roles(self):
		# Re-enable replication from Samba4
		run_and_output_to_log(["univention-config-registry", "unset", "samba4/dcerpc/endpoint/drsuapi"], log.debug)

		# Claim FSMO roles
		log.info("Claiming FSMO roles")
		takeover_hasMasterNCs(self.ucr, self.samdb, self.sitename, self.partitions)
		for fsmo_role in ('pdc', 'rid', 'infrastructure', 'schema', 'naming', 'domaindns', 'forestdns'):
			for attempt in range(3):
				if attempt > 0:
					time.sleep(1)
					log.debug("trying samba-tool fsmo seize --role=%s --force again:" % fsmo_role)
				returncode = run_and_output_to_log(["samba-tool", "fsmo", "seize", "--role=%s" % fsmo_role, "--force"], log.debug)
				if returncode == 0:
					break
			else:
				msg = []
				msg.append("Claiming FSMO role %s failed." % fsmo_role)
				msg.append("Warning: Continuing anyway. Please fix later by running:")
				msg.append("         samba-tool fsmo seize --role=%s --force" % fsmo_role)
				log.error("\n".join(msg))

		# Let things settle
		time.sleep(3)

		# Restart Samba and make sure the rapid restart did not leave the main process blocking
		run_and_output_to_log(["/etc/init.d/samba-ad-dc", "restart"], log.debug)
		check_samba4_started()

	def configure_SNTP(self):
		# re-create /etc/krb5.keytab
		# https://forge.univention.org/bugzilla/show_bug.cgi?id=27426
		run_and_output_to_log(["/usr/share/univention-samba4/scripts/create-keytab.sh"], log.debug)

		# Enable NTP Signing for Windows SNTP clients
		run_and_output_to_log(["univention-config-registry", "set", "ntp/signed=yes"], log.debug)
		returncode = run_and_output_to_log(["/etc/init.d/ntp", "restart"], log.debug)
		if returncode != 0:
			log.error("Start of NTP daemon failed. See %s for details." % (LOGFILE_NAME,))

	def finalize(self):
		# Re-run joinscripts that create an SPN account (lost in old secrets.ldb)
		for joinscript_name in ("zarafa4ucs-sso", "univention-squid-samba4", "univention-samba4-dns"):
			run_and_output_to_log(["sed", "-i", "/^%s v[0-9]* successful/d" % joinscript_name, "/var/univention-join/status"], log.debug)
		returncode = run_and_output_to_log(["univention-run-join-scripts"], log.debug)
		if returncode != 0:
			log.error("univention-run-join-scripts failed, please run univention-run-join-scripts manually after the script finished")

		run_and_output_to_log(["univention-config-registry", "set", "univention/ad/takeover/completed=yes"], log.debug)
		run_and_output_to_log(["univention-config-registry", "unset", "univention/ad/takeover/ad/server/ip"], log.debug)
		run_and_output_to_log(["samba-tool", "dbcheck", "--fix", "--yes"], log.debug)
		run_and_output_to_log(["/etc/init.d/bind9", "restart"], log.debug)


def check_gpo_presence():
	lp = LoadParm()
	try:
		lp.load('/etc/samba/smb.conf')
	except:
		lp.load('/dev/null')

	samdb = SamDB(os.path.join(SAMBA_PRIVATE_DIR, "sam.ldb"), session_info=system_session(lp), lp=lp)

	# check versions
	msgs = samdb.search(
		base=samdb.domain_dn(), scope=samba.ldb.SCOPE_SUBTREE,
		expression="(objectClass=groupPolicyContainer)",
		attrs=["cn", "gPCFileSysPath", "versionNumber"])

	sysvol_dir = "/var/lib/samba/sysvol"
	default_policies_dir = os.path.join(sysvol_dir, samdb.domain_dns_name(), "Policies")
	for obj in msgs:
		name = obj["cn"][0]
		if "gPCFileSysPath" in obj:
			try:
				[server, share, subdir] = parse_unc(obj["gPCFileSysPath"][0])
				gpo_path = os.path.join(sysvol_dir, subdir.replace('\\', '/'))
			except ValueError as ex:
				log.error(ex.args[0])
				gpo_path = os.path.join(default_policies_dir, name)
		else:
			gpo_path = os.path.join(default_policies_dir, name)
		if not os.path.isdir(gpo_path):
			log.error("GPO missing in SYSVOL: %s" % name)
			raise SysvolGPOMissing()

		if "versionNumber" in obj:
			gpcversion = obj["versionNumber"][0]
			config = configparser.ConfigParser()
			try:
				with open(os.path.join(gpo_path, 'GPT.INI')) as f:
					try:
						config.readfp(f)
						fileversion = config.get('General', 'version')
						if fileversion < gpcversion:
							log.error("File version %s of GPO %s is lower than GPO container versionNumber (%s)" % (fileversion, name, gpcversion))
							raise SysvolGPOVersionTooLow(_("At least one GPO in SYSVOL is not up to date yet."))
						if fileversion != gpcversion:
							log.error("File version %s of GPO %s differs from GPO container versionNumber (%s)" % (fileversion, name, gpcversion))
							# TODO: Imrpove error reporting
					except configparser.Error as ex:
						log.error(ex.args[0])
			except IOError as ex:
				log.error(ex.args[0])

	return True

# HELPER FUNCTIONS: ###########################


class Timer(object):

	def __init__(self):
		self.timetable = []

	def start(self, label):
		self.timetable = [(label, time.time()), ]

	def timestamp(self, label):
		self.timetable.append((label, time.time()))

	def log_stats(self):
		(label0, t0) = self.timetable[0]
		(label1, t1) = self.timetable[-1]
		total = t1 - t0
		ti = t0
		percent = [(label0, 0)]
		fraction = [(label0, 0)]
		log.debug("============ timing progress: ===================")
		log.debug("%s: %s" % (label0, 0))
		for (label, t) in self.timetable:
			delta = t - ti
			if not delta:
				continue
			percent.append((label, 100 * (t - t0) // total))
			log.debug("%s: %s%%" % percent[-1])
			fraction.append((label, 100 * delta // total))
			ti = t

		log.debug("============ timing fractions: ===================")
		for (label, f) in fraction:
			log.debug("%s: %s%%" % (label, f))


def determine_IP_version(address):
	try:
		ip_version = ipaddress.ip_address(u'%s' % (address,)).version
	except ValueError:
		ip_version = None

	return ip_version


def ldap_uri_for_host(hostname_or_ip):
	ip_version = determine_IP_version(hostname_or_ip)

	if ip_version == 6:
		return "ldap://[%s]" % hostname_or_ip  # For some reason the ldb-clients do not support this currently.
	else:
		return "ldap://%s" % hostname_or_ip


def ping(hostname_or_ip):
	ip_version = determine_IP_version(hostname_or_ip)

	if ip_version == 6:
		cmd = ["fping6", "-r2", "-t200", hostname_or_ip]
	else:
		cmd = ["fping", "-r2", "-t200", hostname_or_ip]

	try:
		p1 = subprocess.Popen(cmd, close_fds=True, stdout=DEVNULL, stderr=DEVNULL)
		rc = p1.wait()
	except OSError as ex:
		# i18n: The program "fping" failed.
		raise TakeoverError(" ".join(cmd) + _(" failed"), ex.args[1])

	if rc != 0:
		raise ComputerUnreachable(_("Network connection to %s failed.") % hostname_or_ip)


def lookup_adds_dc(hostname_or_ip=None, realm=None, ucr=None):
	'''CLDAP lookup'''

	domain_info = {}

	if not hostname_or_ip and not realm:
		if not ucr:
			ucr = univention.config_registry.ConfigRegistry()
			ucr.load()

		realm = ucr.get("kerberos/realm")

	if not hostname_or_ip and not realm:
		return domain_info

	lp = LoadParm()
	lp.load('/dev/null')

	ip_address = None
	if hostname_or_ip:
		try:
			ipaddress.ip_address(u'%s' % (hostname_or_ip,))
			ip_address = hostname_or_ip
		except ValueError as ex:
			pass

		try:
			net = Net(creds=None, lp=lp)
			cldap_res = net.finddc(address=hostname_or_ip, flags=nbt.NBT_SERVER_LDAP | nbt.NBT_SERVER_DS | nbt.NBT_SERVER_WRITABLE)
		except RuntimeError as ex:
			raise ComputerUnreachable(_("Connection to Active Directory server %s failed.") % (hostname_or_ip,), ex.args[0])

	elif realm:
		try:
			net = Net(creds=None, lp=lp)
			cldap_res = net.finddc(domain=realm, flags=nbt.NBT_SERVER_LDAP | nbt.NBT_SERVER_DS | nbt.NBT_SERVER_WRITABLE)
			hostname_or_ip = cldap_res.pdc_dns_name
		except RuntimeError as ex:
			raise TakeoverError(_("The automatic search for an Active Directory server for realm %s did not yield any results.") % (realm,))

	if not ip_address:
		if cldap_res.pdc_dns_name:
			try:
				p1 = subprocess.Popen(['net', 'lookup', cldap_res.pdc_dns_name], close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				stdout, stderr = p1.communicate()
				ip_address = stdout.strip()
			except OSError as ex:
				log.warn("WARNING: net lookup %s failed: %s" % (cldap_res.pdc_dns_name, ex.args[1]))

	domain_info = {
		"ad_forrest": cldap_res.forest,
		"ad_domain": cldap_res.dns_domain,
		"ad_netbios_domain": cldap_res.domain_name,
		"ad_hostname": cldap_res.pdc_dns_name,
		"ad_netbios_name": cldap_res.pdc_name,
		"ad_server_site": cldap_res.server_site,
		"ad_client_site": cldap_res.client_site,
		"ad_ip": ip_address,
	}

	if not domain_info["ad_server_site"]:
		raise TakeoverError(_("Failed to detect the Active Directory site of the server."))

	return domain_info


def run_and_output_to_log(cmd, log_function, print_commandline=True):
	if print_commandline and log_function == log.debug:
		log_function("Calling: %s" % ' '.join(cmd))
	p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	while p.poll() is None:
		log_line = p.stdout.readline().rstrip()
		if log_line:
			log_function(log_line)
	return p.returncode


def get_stable_last_id(progress=None, max_time=20):
	last_id_cached_value = None
	static_count = 0
	t = t_0 = time.time()
	while static_count < 3:
		if last_id_cached_value:
			time.sleep(0.1)
		with open("/var/lib/univention-ldap/last_id") as f:
			last_id = f.read().strip()
		if last_id != last_id_cached_value:
			static_count = 0
			last_id_cached_value = last_id
		elif last_id:
			static_count = static_count + 1
		delta_t = time.time() - t
		t = t + delta_t
		if t - t_0 > max_time:
			return None
		if progress and delta_t >= 1:
			progress.percentage_increment_scaled(1.0 / 32)
	return last_id


def wait_for_listener_replication(progress=None, max_time=None):
	notifier_id_cached_value = None
	static_count = 0
	t_last_feedback = t_1 = t_0 = time.time()
	while static_count < 5:
		if notifier_id_cached_value:
			time.sleep(0.7)
		last_id = get_stable_last_id(progress)
		with open("/var/lib/univention-directory-listener/notifier_id") as f:
			notifier_id = f.read().strip()
		if not last_id:
			return False
		elif last_id != notifier_id:
			static_count = 0
			notifier_id_cached_value = notifier_id
		else:
			static_count = static_count + 1

		delta_t = time.time() - t_1
		t_1 = t_1 + delta_t
		if max_time:
			if t_1 - t_0 > max_time:
				log.debug("Warning: Listener ID not yet up to date (last_id=%s, listener ID=%s). Waited for about %s seconds." % (last_id, notifier_id, int(round(t_1 - t_0))))
				return False
		delta_t_last_feedback = t_1 - t_last_feedback
		if progress and delta_t_last_feedback >= 1:
			t_last_feedback = t_last_feedback + delta_t_last_feedback
			progress.percentage_increment_scaled(0.6 / 32)

	return True


def wait_for_s4_connector_replication(ucr, lp, progress=None, max_time=None):

	conn = sqlite3.connect('/etc/univention/connector/s4internal.sqlite')
	c = conn.cursor()

	static_count = 0
	t_last_feedback = t_1 = t_0 = time.time()

	ucr.load()  # load current values
	connector_s4_poll_sleep = int(ucr.get("connector/s4/poll/sleep", "5"))
	connector_s4_retryrejected = int(ucr.get("connector/s4/retryrejected", "10"))
	required_static_count = 5 * connector_s4_retryrejected

	if max_time == "scale10":
		max_time = 10 * connector_s4_retryrejected * connector_s4_poll_sleep
		log.info("Waiting for S4 Connector sync (max. %s seconds)" % int(round(max_time)))

	highestCommittedUSN = -1
	lastUSN = -1
	while static_count < required_static_count:
		time.sleep(connector_s4_poll_sleep)

		previous_highestCommittedUSN = highestCommittedUSN
		samdb = SamDB(os.path.join(SAMBA_PRIVATE_DIR, "sam.ldb"), session_info=system_session(lp), lp=lp)
		msgs = samdb.search(base="", scope=samba.ldb.SCOPE_BASE, attrs=["highestCommittedUSN"])
		highestCommittedUSN = msgs[0]["highestCommittedUSN"][0]

		previous_lastUSN = lastUSN
		try:
			c.execute('select value from S4 where key=="lastUSN"')
		except sqlite3.OperationalError as ex:
			log.debug(str(ex))
		else:
			conn.commit()
			lastUSN = c.fetchone()[0]

		if not (lastUSN == highestCommittedUSN and lastUSN == previous_lastUSN and highestCommittedUSN == previous_highestCommittedUSN):
			static_count = 0
		else:
			static_count = static_count + 1

		delta_t = time.time() - t_1
		t_1 = t_1 + delta_t
		if max_time:
			if t_1 - t_0 > max_time:
				log.debug("Warning: S4 Connector synchronization did not finish yet. Waited for about %s seconds." % (int(round(t_1 - t_0),)))
				conn.close()
				return False
		delta_t_last_feedback = t_1 - t_last_feedback
		if progress and delta_t_last_feedback >= 1:
			t_last_feedback = t_last_feedback + delta_t_last_feedback
			progress.percentage_increment_scaled(1.0 / 32)

	conn.close()
	return True


def check_samba4_started():
	attempt = 1
	for i in range(5):
		time.sleep(1)
		p = subprocess.Popen(["pgrep", "-cxf", "/usr/sbin/samba -D"], stdout=subprocess.PIPE)
		(stdout, stderr) = p.communicate()
		if int(stdout) > 1:
			break
	else:
		if int(stdout) == 1:
			attempt = 2
			run_and_output_to_log(["/etc/init.d/samba-ad-dc", "stop"], log.debug)
			run_and_output_to_log(["pkill", "-9", "-xf", "/usr/sbin/samba -D"], log.debug)
			p = subprocess.Popen(["pgrep", "-cxf", "/usr/sbin/samba -D"], stdout=subprocess.PIPE)
			(stdout, stderr) = p.communicate()
			if int(stdout) > 0:
				log.debug("ERROR: Stray Processes:", int(stdout))
				run_and_output_to_log(["pkill", "-9", "-xf", "/usr/sbin/samba -D"], log.debug)
			run_and_output_to_log(["/etc/init.d/samba-ad-dc", "start"], log.debug)
			# fallback
			time.sleep(2)
			p = subprocess.Popen(["pgrep", "-cxf", "/usr/sbin/samba -D"], stdout=subprocess.PIPE)
			(stdout, stderr) = p.communicate()
			if int(stdout) == 1:
				attempt = 3
				log.debug("ERROR: Stray Processes:", int(stdout))
				run_and_output_to_log(["pkill", "-9", "-xf", "/usr/sbin/samba -D"], log.debug)
				run_and_output_to_log(["/etc/init.d/samba-ad-dc", "start"], log.debug)
				# and log
				time.sleep(2)
				p = subprocess.Popen(["pgrep", "-cxf", "/usr/sbin/samba -D"], stdout=subprocess.PIPE)
				(stdout, stderr) = p.communicate()
		log.debug("Number of Samba 4 processes after %s start/restart attempts: %s" % (attempt, stdout))


class UserRenameHandler(object):

	''' Provides methods for renaming users in UDM
	'''

	def __init__(self, lo):
		self.lo = lo
		self.position = univention.admin.uldap.position(self.lo.base)

		self.module_users_user = udm_modules.get('users/user')
		udm_modules.init(self.lo, self.position, self.module_users_user)

	def udm_rename_ucs_user(self, userdn, new_name):
		try:
			user = self.module_users_user.object(None, self.lo, self.position, userdn)
			user.open()
		except uexceptions.ldapError as exc:
			log.debug("Opening user '%s' failed: %s." % (userdn, exc,))

		try:
			log.debug("Renaming '%s' to '%s' in UCS LDAP." % (user.dn, new_name))
			user['username'] = new_name
			return user.modify()
		except uexceptions.ldapError as exc:
			log.debug("Renaming of user '%s' failed: %s." % (userdn, exc,))
			return

	def rename_ucs_user(self, ucsldap_object_name, ad_object_name):
		userdns = self.lo.searchDn(
			filter=filter_format("(&(objectClass=sambaSamAccount)(uid=%s))", (ucsldap_object_name, )),
			base=self.lo.base)

		if len(userdns) > 1:
			log.warn("Warning: Found more than one Samba user with name '%s' in UCS LDAP." % (ucsldap_object_name,))

		for userdn in userdns:
			self.udm_rename_ucs_user(userdn, ad_object_name)


class GroupRenameHandler(object):

	''' Provides methods for renaming groups in UDM
	'''

	_SETTINGS_DEFAULT_UDM_PROPERTIES = (
		"defaultGroup",
		"defaultComputerGroup",
		"defaultDomainControllerGroup",
		"defaultDomainControllerMBGroup",
		"defaultClientGroup",
		"defaultMemberServerGroup",
	)

	def __init__(self, lo):
		self.lo = lo
		self.position = univention.admin.uldap.position(self.lo.base)

		self.module_groups_group = udm_modules.get('groups/group')
		udm_modules.init(self.lo, self.position, self.module_groups_group)

		self.module_settings_default = udm_modules.get('settings/default')
		udm_modules.init(self.lo, self.position, self.module_settings_default)

	def udm_rename_ucs_group(self, groupdn, new_name):
		try:
			group = self.module_groups_group.object(None, self.lo, self.position, groupdn)
			group.open()
		except uexceptions.ldapError as exc:
			log.debug("Opening group '%s' failed: %s." % (groupdn, exc,))

		try:
			log.debug("Renaming '%s' to '%s' in UCS LDAP." % (group.dn, new_name))
			group['name'] = new_name
			dn = group.modify()
			dn2 = ldap.dn.str2dn(dn)
			if new_name != dn2[0][0][1]:  # TODO: remove when fixed in UDM
				dn2.insert(0, [(dn2.pop(0)[0][0], new_name, ldap.AVA_STRING)])
				dn = ldap.dn.dn2str(dn2)
			return dn
		except uexceptions.ldapError as exc:
			log.debug("Renaming of group '%s' failed: %s." % (groupdn, exc,))
			return

	def udm_rename_ucs_defaultGroup(self, groupdn, new_groupdn):
		if not new_groupdn:
			return

		if not groupdn:
			return

		lookup_filter = udm_filter.conjunction('|', [
			udm_filter.expression(propertyname, groupdn)
			for propertyname in GroupRenameHandler._SETTINGS_DEFAULT_UDM_PROPERTIES
		])

		referring_objects = udm_modules.lookup('settings/default', None, self.lo, scope='sub', base=self.lo.base, filter=lookup_filter)
		for referring_object in referring_objects:
			changed = False
			for propertyname in GroupRenameHandler._SETTINGS_DEFAULT_UDM_PROPERTIES:
				if groupdn in referring_object[propertyname]:
					referring_object[propertyname] = new_groupdn
					changed = True
			if changed:
				log.debug("Modifying '%s' in UCS LDAP." % (referring_object.dn,))
				referring_object.modify()

	def rename_ucs_group(self, ucsldap_object_name, ad_object_name):
		groupdns = self.lo.searchDn(
			filter=filter_format("(&(objectClass=sambaGroupMapping)(cn=%s))", (ucsldap_object_name, )),
			base=self.lo.base)

		if len(groupdns) > 1:
			log.warn("Warning: Found more than one Samba group with name '%s' in UCS LDAP." % (ucsldap_object_name,))

		for groupdn in groupdns:
			new_groupdn = self.udm_rename_ucs_group(groupdn, ad_object_name)
			self.udm_rename_ucs_defaultGroup(groupdn, new_groupdn)


def _connect_ucs(ucr, binddn=None, bindpwd=None):
	''' Connect to OpenLDAP '''

	if binddn and bindpwd:
		bindpw = bindpwd
	else:
		bindpw_file = ucr.get('connector/ldap/bindpw', '/etc/ldap.secret')
		binddn = ucr.get('connector/ldap/binddn', 'cn=admin,' + ucr['ldap/base'])
		bindpw = open(bindpw_file).read()
		if bindpw[-1] == '\n':
			bindpw = bindpw[0:-1]

	host = ucr.get('connector/ldap/server', ucr.get('ldap/master'))

	try:
		port = int(ucr.get('connector/ldap/port', ucr.get('ldap/master/port')))
	except:
		port = 7389

	lo = univention.admin.uldap.access(host=host, port=port, base=ucr['ldap/base'], binddn=binddn, bindpw=bindpw, start_tls=0, follow_referral=True)

	return lo


def operatingSystem_attribute(ucr, samdb):
	msg = samdb.search(base=samdb.domain_dn(), scope=samba.ldb.SCOPE_SUBTREE, expression=filter_format("(sAMAccountName=%s$)", (ucr["hostname"],)), attrs=["operatingSystem", "operatingSystemVersion"])
	if msg:
		obj = msg[0]
		if "operatingSystem" not in obj:
			delta = ldb.Message()
			delta.dn = obj.dn
			delta["operatingSystem"] = ldb.MessageElement("Univention Corporate Server", ldb.FLAG_MOD_REPLACE, "operatingSystem")
			samdb.modify(delta)
		if "operatingSystemVersion" not in obj:
			delta = ldb.Message()
			delta.dn = obj.dn
			delta["operatingSystemVersion"] = ldb.MessageElement("3.0", ldb.FLAG_MOD_REPLACE, "operatingSystemVersion")
			samdb.modify(delta)


def takeover_DC_Behavior_Version(ucr, remote_samdb, samdb, ad_server_name, sitename):
	# DC Behavior Version
	msg = remote_samdb.search(
		base="CN=NTDS Settings,CN=%s,CN=Servers,CN=%s,CN=Sites,CN=Configuration,%s" % (escape_dn_chars(ad_server_name), escape_dn_chars(sitename), samdb.domain_dn()),
		scope=samba.ldb.SCOPE_BASE,
		attrs=["msDS-HasMasterNCs", "msDS-HasInstantiatedNCs", "msDS-Behavior-Version"]
	)
	if msg:
		obj = msg[0]
		if "msDS-Behavior-Version" in obj:
			delta = ldb.Message()
			delta.dn = ldb.Dn(samdb, dn="CN=NTDS Settings,CN=%s,CN=Servers,CN=%s,CN=Sites,CN=Configuration,%s" % (escape_dn_chars(ucr["hostname"]), escape_dn_chars(sitename), samdb.domain_dn()))
			delta["msDS-Behavior-Version"] = ldb.MessageElement(obj["msDS-Behavior-Version"], ldb.FLAG_MOD_REPLACE, "msDS-Behavior-Version")
			samdb.modify(delta)


def takeover_hasInstantiatedNCs(ucr, samdb, ad_server_name, sitename):
	partitions = []
	try:
		msg = samdb.search(
			base="CN=NTDS Settings,CN=%s,CN=Servers,CN=%s,CN=Sites,CN=Configuration,%s" % (escape_dn_chars(ad_server_name), escape_dn_chars(sitename), samdb.domain_dn()),
			scope=samba.ldb.SCOPE_BASE,
			attrs=["msDS-hasMasterNCs", "msDS-HasInstantiatedNCs"])
	except ldb.LdbError as ex:
		log.debug(ex.args[1])
		return partitions

	if msg:
		obj = msg[0]
		delta = ldb.Message()
		delta.dn = ldb.Dn(samdb, dn="CN=NTDS Settings,CN=%s,CN=Servers,CN=%s,CN=Sites,CN=Configuration,%s" % (escape_dn_chars(ucr["hostname"]), escape_dn_chars(sitename), samdb.domain_dn()))
		if "msDS-HasInstantiatedNCs" in obj:
			for partitionDN in obj["msDS-HasInstantiatedNCs"]:
				delta[partitionDN] = ldb.MessageElement(obj["msDS-HasInstantiatedNCs"], ldb.FLAG_MOD_REPLACE, "msDS-HasInstantiatedNCs")
		if "msDS-HasInstantiatedNCs" in delta:
			samdb.modify(delta)

		# and note the msDS-hasMasterNCs values for fsmo takeover
		if "msDS-hasMasterNCs" in obj:
			for partitionDN in obj["msDS-hasMasterNCs"]:
				partitions.append(partitionDN)
	return partitions


def takeover_hasMasterNCs(ucr, samdb, sitename, partitions):
	msg = samdb.search(base="CN=NTDS Settings,CN=%s,CN=Servers,CN=%s,CN=Sites,CN=Configuration,%s" % (escape_dn_chars(ucr["hostname"]), escape_dn_chars(sitename), samdb.domain_dn()), scope=samba.ldb.SCOPE_BASE, attrs=["hasPartialReplicaNCs", "msDS-hasMasterNCs"])
	if msg:
		obj = msg[0]
		for partition in partitions:
			if "hasPartialReplicaNCs" in obj and partition in obj["hasPartialReplicaNCs"]:
				log.debug("Removing hasPartialReplicaNCs on %s for %s" % (ucr["hostname"], partition))
				delta = ldb.Message()
				delta.dn = obj.dn
				delta["hasPartialReplicaNCs"] = ldb.MessageElement(partition, ldb.FLAG_MOD_DELETE, "hasPartialReplicaNCs")
				try:
					samdb.modify(delta)
				except:
					log.debug("Failed to remove hasPartialReplicaNCs %s from %s" % (partition, ucr["hostname"]))
					log.debug("Current NTDS object: %s" % obj)

			if "msDS-hasMasterNCs" in obj and partition in obj["msDS-hasMasterNCs"]:
				log.debug("Naming context %s already registered in msDS-hasMasterNCs for %s" % (partition, ucr["hostname"]))
			else:
				delta = ldb.Message()
				delta.dn = obj.dn
				delta[partition] = ldb.MessageElement(partition, ldb.FLAG_MOD_ADD, "msDS-hasMasterNCs")
				try:
					samdb.modify(delta)
				except:
					log.debug("Failed to add msDS-hasMasterNCs %s to %s" % (partition, ucr["hostname"]))
					log.debug("Current NTDS object: %s" % obj)


def let_samba4_manage_etc_krb5_keytab(ucr, secretsdb):

	msg = secretsdb.search(
		base="cn=Primary Domains",
		scope=samba.ldb.SCOPE_SUBTREE,
		expression=filter_format("(flatName=%s)", (ucr["windows/domain"],)),
		attrs=["krb5Keytab"]
	)
	if msg:
		obj = msg[0]
		if "krb5Keytab" not in obj or "/etc/krb5.keytab" not in obj["krb5Keytab"]:
			delta = ldb.Message()
			delta.dn = obj.dn
			delta["krb5Keytab"] = ldb.MessageElement("/etc/krb5.keytab", ldb.FLAG_MOD_ADD, "krb5Keytab")
			secretsdb.modify(delta)


def add_servicePrincipals(ucr, secretsdb, spn_list):
	msg = secretsdb.search(
		base="cn=Primary Domains",
		scope=samba.ldb.SCOPE_SUBTREE,
		expression=filter_format("(flatName=%s)", (ucr["windows/domain"],)),
		attrs=["servicePrincipalName"]
	)
	if msg:
		obj = msg[0]
		delta = ldb.Message()
		delta.dn = obj.dn
		for spn in spn_list:
			if "servicePrincipalName" not in obj or spn not in obj["servicePrincipalName"]:
				delta[spn] = ldb.MessageElement(spn, ldb.FLAG_MOD_ADD, "servicePrincipalName")
		secretsdb.modify(delta)


def sync_position_s4_to_ucs(ucr, udm_type, ucs_object_dn, s4_object_dn):
	new_position = parentDn(s4_object_dn).lower().replace(ucr['connector/s4/ldap/base'].lower(), ucr['ldap/base'].lower())
	old_position = parentDn(ucs_object_dn)

	if new_position.lower() != old_position.lower():
		run_and_output_to_log(["/usr/sbin/univention-directory-manager", udm_type, "move", "--dn", ucs_object_dn, "--position", new_position], log.debug)


def parse_unc(unc):  # fixed function from samba/netcmd/gpo.py
	'''Parse UNC string into a hostname, a service, and a filepath'''
	if not (unc.startswith('\\\\') or unc.startswith('//')):
		raise ValueError(_("UNC doesn't start with \\\\ or //"))
	tmp = unc[2:].split('/', 2)
	if len(tmp) == 3:
		return tmp
	tmp = unc[2:].split('\\', 2)
	if len(tmp) == 3:
		return tmp
	raise ValueError(_("Invalid UNC string: %s") % unc)

# END LIB. HERE COMES THE OLD CODE: ###########################


def run_phaseI(ucr, lp, opts, args, parser, creds, always_answer_with=None):

	# First plausibility checks
	# 1.a Check that local domainname matches kerberos realm
	if ucr["domainname"].lower() != ucr["kerberos/realm"].lower():
		log.error("Mismatching DNS domain and kerberos realm. Please reinstall the server with the same Domain as your AD.")
		sys.exit(1)
	# Check, if we can reverse resolve ad_server_ip locally
	# Check if the script was run before
	backup_samba_dir = "%s.before-ad-takeover" % SAMBA_PRIVATE_DIR
	if os.path.exists(backup_samba_dir):
		msg = []
		msg.append("Error: Found Samba backup of a previous run of univention-ad-takeover.")
		msg.append("       The AD takeover procedure should only be completed once.")
		msg.append("       Move the directory %s to a safe place to continue anyway." % backup_samba_dir)
		log.error("\n".join(msg))
		sys.exit(1)
	# Check, if there is a DNS Server running at ad_server_ip which is able to resolve ad_server_fqdn
	# 2. Determine Site of given server, important for locale-dependend names like "Standardname-des-ersten-Standorts"
	# 3. Essential: Sync the time
	# 4. Check AD Object Numbers

	# Phase I.a: Join to AD

	# Stop the S4 Connector for phase I
	# Stop Samba
	# Move current Samba directory out of the way
	# Adjust some UCR settings
	# Stop the NSCD
	# Restart bind9 to use the OpenLDAP backend, just to be sure
	# Get machine credentials
	# Join into the domain
	# create backup dir
	# Fix some attributes in local SamDB
	# Set operatingSystem attribute
	# Takeover DC Behavior Version
	# Fix some attributes in SecretsDB
	# Set Samba domain password settings. Note: rotation of passwords will only work with UCS 3.1, so max password age must be disabled for now.
	# Avoid password expiry for DCs:
	# Disable replication from Samba4 to AD
	# Start Samba
	# Phase I.b: Pre-Map SIDs (locale adjustment etc.)

	# pre-create containers in UDM
	# Identify and rename UCS group names to match Samba4 (localized) group names
	# construct dict of old UCS sambaSIDs
	# Rewrite SIDs for Users and Computers
	# Rewrite SIDs for Groups
	# Pre-Create mail domains for all mail and proxyAddresses:
	# re-create DNS SPN account
	# remove zarafa and univention-squid-kerberos SPN accounts, recreated later in phaseIII by running the respective joinscripts again
	# Remove logonHours restrictions from Administrator account, was set in one test environment..

	# Phase I.c: Run S4 Connector
	# Restart Univention Directory Listener for S4 Connector
	# Reset S4 Connector and handler state
	# rotate S4 connector log and start the S4 Connector
	# Ok, just in case, start the Connector explicitly
	# Reset normal relication intervals
	# rebuild idmap
	# Start NSCD again
	# Save AD server IP for Phase III


def run_phaseIII(ucr, lp, ad_server_ip, ad_server_fqdn, ad_server_name):

	# Phase III: Promote to FSMO master and DNS server
	# Restart Samba and make sure the rapid restart did not leave the main process blocking
	# 1. Determine Site of local server, important for locale-dependend names like "Standardname-des-ersten-Standorts"
	# properly register partitions
	# Backup current NTACLs on sysvol
	# Re-Set NTACLs from nTSecurityDescriptor on sysvol policy directories
	# Re-set default fACLs so sysvol-sync can read files and directories (See Bug#29065)
	# Add DNS records to UDM:
	# remove local entry for AD DC from /etc/hosts
	# Replace DNS host record for AD Server name by DNS Alias
	# Cleanup necessary to use NETBIOS Alias
	# Now delete the AD DC account and sub-objects
	# Finally, for consistency remove AD DC object from UDM
	# Create NETBIOS Alias
	# Assign AD IP to a virtual network interface
	# Resolve against local Bind9
	# Use Samba4 as DNS backend
	# Re-enable replication from Samba4
	# Claim FSMO roles
	# Let things settle
	time.sleep(3)
	# Restart Samba and make sure the rapid restart did not leave the main process blocking
	# Create new DNS SPN account in Samba4
	# Restart bind9 to use the OpenLDAP backend, just to be sure
	# re-create /etc/krb5.keytab
	# Enable NTP Signing for Windows SNTP clients
	# Re-run joinscripts that create an SPN account (lost in old secrets.ldb)
