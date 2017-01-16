import os
import sys
import shutil

import json
from time import sleep
from httplib import HTTPException

from univention.config_registry import ConfigRegistry
from univention.testing.codes import TestCodes
import univention.testing.utils as utils
from univention.testing.umc import UMCConnection


class UMCBase(object):
	"""
	A base class for testing UMC-system
	"""

	def __init__(self):
		"""Test Class constructor"""
		self.username = None
		self.password = None
		self.hostname = None
		self.connection = None
		self.ldap_base = ''
		self.test_network_dn = ''

		self.ucr = ConfigRegistry()

		# for getting the default English names of users/groups:
		self.default_names = {
			'domainadmins': "Domain Admins",
			'domainusers': "Domain Users",
			'windowshosts': "Windows Hosts",
			'dcbackuphosts': "DC Backup Hosts",
			'dcslavehosts': "DC Slave Hosts",
			'computers': "Computers",
			'printoperators': "Printer-Admins",
			'administrator': "Administrator"
		}

	def reload_ucr(self):
		"""Reload the UCR variables """
		self.ucr.load()

	def get_ucr_credentials(self):
		"""Get credentials from the registry"""
		self.reload_ucr()
		self.username = self.ucr['tests/domainadmin/account']
		self.password = self.ucr['tests/domainadmin/pwd']
		self.hostname = self.ucr['hostname']

		# extracting the 'uid' value of the username string
		self.username = self.username.split(',')[0][len('uid='):]

	def request(self, *args, **kwargs):
		return self.connection.request(*args, **kwargs)

	def create_connection_authenticate(self):
		"""Create UMC connection and authenticate"""
		try:
			self.connection = UMCConnection(self.hostname)
			self.connection.auth(self.username, self.password)
		except HTTPException as exc:
			print("An HTTPException while trying to authenticate to UMC: %r" % exc)
			print "Waiting 5 seconds and making another attempt"
			sleep(5)
			self.connection.auth(self.username, self.password)

	def get_translation(self, obj_type, obj_name):
		"""
		Returns the translation taken from UCR for given 'obj_name' and
		'obj_type'. If not translation found -> returns default English
		name. If no English name availabe -> prints a messge, returns None.
		"""
		translated = self.ucr.get(obj_type + '/default/' + obj_name, self.default_names.get(obj_name))
		if not translated:
			print("\nNo translation and no default English name can be found for object %s of %s type" % (obj_name, obj_type))

		return translated

	def get_groupname_translation(self, groupname):
		"""
		Returns the localized translation for the given 'groupname'.
		Groupname should be the UCR variable name (e.g. domainadmins).
		"""
		return self.get_translation('groups', groupname)

	def get_username_translation(self, username):
		"""
		Returns the localized translation for the given 'username'.
		Username should be the UCR variable name (e.g. administrator).
		"""
		return self.get_translation('users', username)

	def check_obj_exists(self, name, obj_type):
		"""
		Checks if user, group or policy object with provided 'name' exists
		via UMC 'udm/query' request, returns True when exists.
		Object type selected by 'obj_type' argument.
		"""
		options = {
			"container": "all",
			"objectType": obj_type,
			"objectProperty": "None",
			"objectPropertyValue": "",
			"hidden": True
		}
		for result in self.request('udm/query', options, obj_type):
			if result['name'] == name:
				return True

	def get_object(self, options, flavor):
		"""
		Returns the request result of the 'udm/get' UMC connection,
		made with provided 'options' and 'flavor'
		"""
		request_result = self.connection.request('udm/get', options, flavor)
		if request_result is None:
			utils.fail("Request 'udm/get' with options '%s' failed, hostname '%s'" % (options, self.hostname))
		return request_result

	def modify_object(self, options, flavor):
		"""
		Modifies the 'flavor' object as given in 'options' by making a
		UMC request 'udm/put', checks for 'success' in the response
		"""
		request_result = self.connection.request('udm/put', options, flavor)
		if not request_result:
			utils.fail("Request 'udm/put' to modify an object with options '%s' failed, hostname %s" % (options, self.hostname))
		if not request_result[0].get('success'):
			utils.fail("Request 'udm/put' to modify an object with options '%s' failed, no success = True in response, hostname %s, response '%s'" % (options, self.hostname, request_result))

	def delete_obj(self, name, obj_type, flavor):
		"""
		Deletes object with a 'name' by making UMC-request 'udm/remove'
		with relevant options and flavor depending on 'obj_type'
		Supported types are: users, groups, policies, extended attributes,
		networks and computers.
		"""
		print "Deleting test object '%s' with a name: '%s'" % (obj_type, name)

		if obj_type == 'users':
			obj_identifier = "uid=" + name + ",cn=" + obj_type + ","
		elif obj_type == 'policies':
			obj_identifier = "cn=" + name + ",cn=UMC,cn=" + obj_type + ","
		elif obj_type == 'custom attributes':
			obj_identifier = "cn=" + name + ",cn=" + obj_type + ",cn=univention,"
		elif obj_type in ('groups', 'networks', 'computers'):
			obj_identifier = "cn=" + name + ",cn=" + obj_type + ","
		else:
			utils.fail("The object identifier format is unknown for the provided object type '%s'" % obj_type)

		obj_identifier = obj_identifier + self.ldap_base
		options = [{
			"object": obj_identifier,
			"options": {
				"cleanup": True,
				"recursive": True
			}
		}]
		request_result = self.connection.request('udm/remove', options, flavor)
		if not request_result:
			utils.fail("Request 'udm/remove' to delete object with options '%s' failed, hostname %s" % (options, self.hostname))
		if not request_result[0].get('success'):
			utils.fail("Request 'udm/remove' to delete object with options '%s' failed, no success = True in response, hostname '%s', response '%s'" % (options, self.hostname, request_result))

	def return_code_result_skip(self):
		"""Method to stop the test with the code 77, RESULT_SKIP """
		sys.exit(TestCodes.RESULT_SKIP)


class ServiceModule(UMCBase):

	def query(self):
		return self.request('services/query')

	def check_service_presence(self, request_result, service_name):
		"""
		Check if the service with 'service_name' was listed in the response
		'request_result'. Returns 'missing software' code 137 when missing.
		"""
		for result in request_result:
			if result['service'] == service_name:
				break
		else:
			print("The '%s' service is missing in the UMC response: %s" % (service_name, request_result))
			sys.exit(TestCodes.REASON_INSTALL)


class TopModule(UMCBase):
	pass


class JoinModule(UMCBase):

	def query_joinscripts(self):
		return self.request('join/scripts/query', {"*": "*"})

	def join(self, hostname):
		options = {
			"hostname": hostname,
			"username": self.username,
			"password": self.password,
		}
		return self._join('join/join', options)

	def run_scripts(self, script_names, force=False):
		options = {
			"scripts": script_names,
			"force": force,
			"username": self.username,
			"password": self.password,
		}
		return self._join('join/run', options)

	def _join(self, path, options):
		options = {"options": options}
		options = json.dumps(options)
		# defining request explicitly, since UMCConnection raises
		# Exceptions for anything other than response with status 200
		umc_connection = self.connection.get_connection()
		umc_connection.request('POST', '/umcp/command/' + path, options, self.connection._headers)
		request_result = umc_connection.getresponse()
		request_result = request_result.read()
		if not request_result:
			utils.fail("Request 'join/%s' with options '%s' failed, hostname '%s'" % (path, options, self.hostname))

		request_result = json.loads(request_result)
		if request_result.get('status') != 202:
			utils.fail("Request 'join/%s' did not return status 202, hostname: '%s', response '%s'" % (path, self.hostname, request_result))
		if not request_result.get('result')['success']:
			utils.fail("Request 'join/%s' did not return success=True in the response: '%s',hostname '%s'" % (path, request_result, self.hostname))

	def wait_rejoin_to_complete(self, poll_attempts):
		"""
		Polls the join process via UMC 'join/running' request to make
		sure joining is still going on, sleeps 10 secs after every poll
		attempt, fails in case process still going after the given
		'poll_attempts'. Returns when process is not reported as running.
		"""
		for attempt in range(poll_attempts):
			request_result = self.connection.request('join/running')
			if request_result is None:
				utils.fail("No response on UMC 'join/running' request")
			elif request_result is False:
				return
			print "Waiting 10 seconds before next poll request..."
			sleep(10)
		utils.fail("Failed to wait for join script(-s) to finish")

	def copy_file(self, src, dst):
		"""
		Makes a copy of the 'src' file to 'dst' file if 'src' exists
		"""
		try:
			if os.path.exists(src):
				shutil.copy2(src, dst)
				if not os.path.exists(dst):
					utils.fail("The 'shutil' did not copy file '%s' to '%s'" % (src, dst))
			else:
				utils.fail("Failed to find the file at the provided " "path '%s'" % src)
		except (OSError, shutil.Error) as exc:
			utils.fail("An exception while coping the file from '%s', to '%s', error '%s'" % (src, dst, exc))

	def delete_file(self, path):
		"""
		Checks if 'path' file exists and deletes it
		"""
		try:
			if os.path.exists(path):
				os.remove(path)
			else:
				print("Failed to find the file at the provided path '%s'" % path)
		except OSError as exc:
			utils.fail("An exception occured while deleting a file located at '%s': '%s'" % (path, exc))


class UDMModule(UMCBase):

	def create_computer(self, computer_name, ip_address, dns_forward, dns_reverse):
		"""
		Creates a computer with given arguments and self.ldap_base,
		self.test_network_dn via 'udm/add' UMC request
		"""
		options = [{
			"object": {
				"ip": ip_address,
				"network": self.test_network_dn,
				"unixhome": "/dev/null",
				"ntCompatibility": False,
				"shell": "/bin/false",
				"primaryGroup": "cn=Windows Hosts,cn=groups," + self.ldap_base,
				"dnsEntryZoneForward": dns_forward,
				"name": computer_name,
				"dnsEntryZoneReverse": dns_reverse,
				"$options$": {
					"samba": True,
					"kerberos": True,
					"posix": True,
					"nagios": False
				},
				"$policies$": {}
			},
			"options": {"container": "cn=computers," + self.ldap_base, "objectType": "computers/windows"}
		}]
		return self.request("udm/add", options, "computers/computer")
