import contextlib
import subprocess
from time import sleep

import ldap

import univention.admin.modules
import univention.admin.objects
import univention.admin.uldap
import univention.config_registry
import univention.connector.ad as ad
import univention.testing.connector_common as tcommon
import univention.testing.ucr as testing_ucr
from univention.config_registry import handler_set as ucr_set
from univention.testing import ldap_glue

configRegistry = univention.config_registry.ConfigRegistry()
configRegistry.load()


class ADConnection(ldap_glue.ADConnection):
	'''helper functions to modify AD-objects'''

	decode_sid = ad.decode_sid

	def __init__(self, configbase='connector'):
		self.configbase = configbase
		self.adldapbase = configRegistry['%s/ad/ldap/base' % configbase]
		self.addomain = self.adldapbase.replace(',DC=', '.').replace('DC=', '')
		self.kerberos = configRegistry.is_true('%s/ad/ldap/kerberos' % configbase)
		if self.kerberos:  # i.e. if UCR ad/member=true
			# Note: tests/domainadmin/account is an OpenLDAP DN but
			#       we only extract the username from it in ldap_glue
			self.login_dn = configRegistry['tests/domainadmin/account']
			self.principal = ldap.dn.str2dn(self.login_dn)[0][0][1]
			self.pw_file = configRegistry['tests/domainadmin/pwdfile']
		else:
			self.login_dn = configRegistry['%s/ad/ldap/binddn' % configbase]
			self.pw_file = configRegistry['%s/ad/ldap/bindpw' % configbase]
		self.host = configRegistry['%s/ad/ldap/host' % configbase]
		self.port = configRegistry['%s/ad/ldap/port' % configbase]
		self.ca_file = configRegistry['%s/ad/ldap/certificate' % configbase]
		no_starttls = configRegistry.is_false('%s/ad/ldap/ssl' % configbase)
		self.connect(no_starttls)


def connector_running_on_this_host():
	return configRegistry.is_true("connector/ad/autostart")


def restart_adconnector():
	print("Restarting AD-Connector")
	subprocess.check_call(["service", "univention-ad-connector", "restart"])


def ad_in_sync_mode(sync_mode, configbase='connector'):
	"""
	Set the AD-Connector into the given `sync_mode` restart.
	"""
	ucr_set(['{}/ad/mapping/syncmode={}'.format(configbase, sync_mode)])
	restart_adconnector()


def wait_for_sync(min_wait_time=0):
	synctime = int(configRegistry.get("connector/ad/poll/sleep", 5))
	synctime = ((synctime + 3) * 2)
	if min_wait_time > synctime:
		synctime = min_wait_time
	print("Waiting {0} seconds for sync...".format(synctime))
	sleep(synctime)


@contextlib.contextmanager
def connector_setup(sync_mode):
	user_syntax = "directory/manager/web/modules/users/user/properties/username/syntax=string"
	group_syntax = "directory/manager/web/modules/groups/group/properties/name/syntax=string"
	with testing_ucr.UCSTestConfigRegistry():
		ucr_set([user_syntax, group_syntax])
		tcommon.restart_univention_cli_server()
		ad_in_sync_mode(sync_mode)
		yield
