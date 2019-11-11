import subprocess
import socket
import optparse
import time
import glob
import os
import ConfigParser
import logging

if os.path.exists('./windows-scripts'):
	COMMAND_DIR = './windows-scripts/'
else:
	COMMAND_DIR = '/usr/share/ucs-windows-tools/windows-scripts/'

LOG_FILE = '/var/log/univention/ucs-windows-tools.log'


def default_options():
	usage = "usage: %prog [OPTIONS]"
	parser = optparse.OptionParser(usage=usage)
	group = optparse.OptionGroup(parser, "General options")
	group.add_option("--domain", dest="domain", help="the AD domain name")
	group.add_option("--domain-admin", dest="domain_admin", help="the domain administrator account")
	group.add_option("--domain-password", dest="domain_password", help="the domain administrator password")
	group.add_option("--local-admin", dest="local_admin", help="the local administrator account")
	group.add_option("--local-password", dest="local_password", help="the local administrator password")
	group.add_option("--port", dest="port", type="int", default=445, help="winexe port (445)")
	group.add_option("--client", dest="client", help="the windows client")
	group.add_option("--logfile", dest="logfile", default=LOG_FILE, help="log file")
	group.add_option("--loglevel", dest="loglevel", type='int', default=4, help="log level (1,2,3,4)")
	parser.add_option_group(group)

	# get default options from config
	config = ConfigParser.ConfigParser()
	config.read(os.path.join(os.environ['HOME'], ".ucs-windows-tools.ini"))
	if config.has_section("default"):
		if config.has_option("default", "domain"):
			parser.set_defaults(domain=config.get("default", "domain"))
		if config.has_option("default", "domain_admin"):
			parser.set_defaults(domain_admin=config.get("default", "domain_admin"))
		if config.has_option("default", "local_admin"):
			parser.set_defaults(local_admin=config.get("default", "local_admin"))
		if config.has_option("default", "local_password"):
			parser.set_defaults(local_password=config.get("default", "local_password"))
		if config.has_option("default", "client"):
			parser.set_defaults(client=config.get("default", "client"))
		if config.has_option("default", "domain_password"):
			parser.set_defaults(domain_password=config.get("default", "domain_password"))

	return parser


class WinExeFailed(Exception):

	'''ucs_addServiceToLocalhost failed'''


class WinExe(object):

	def __init__(
		self,
		domain=None,
		domain_admin=None,
		domain_password=None,
		local_admin=None,
		local_password=None,
		port=445,
		client=None,
		loglevel=4,
		logfile=LOG_FILE):

		self.command_dir = COMMAND_DIR
		self.domain = domain
		self.domain_admin = domain_admin
		self.domain_password = domain_password
		self.local_admin = local_admin
		self.local_password = local_password
		self.port = port
		self.client = client
		self.scripts_copied = False
		self.__check_default_options()
		# logging
		self.logger = logging.getLogger('winexe')
		formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
		if logfile == '-':
			handler = logging.StreamHandler()
		else:
			handler = logging.FileHandler(logfile)
		handler.setFormatter(formatter)
		self.logger.addHandler(handler)
		if loglevel == 1:
			self.logger.setLevel(logging.ERROR)
		elif loglevel == 2:
			self.logger.setLevel(logging.WARN)
		elif loglevel == 3:
			self.logger.setLevel(logging.INFO)
		elif loglevel == 4:
			self.logger.setLevel(logging.DEBUG)
		else:
			raise ValueError('--loglevel must be one of 1, 2, 3 or 4!')

		self.logger.info('start')

		return

	def __check_default_options(self):

		if not self.domain:
			raise WinExeFailed("--domain needs to be specified")
		if not self.domain_admin:
			raise WinExeFailed("--domain-admin needs to be specified")
		if not self.domain_password:
			raise WinExeFailed("--domain-password needs to be specified")
		if not self.local_admin:
			raise WinExeFailed("--local-admin needs to be specified")
		if not self.local_password:
			raise WinExeFailed("--local-password needs to be specified")
		if not self.port:
			raise WinExeFailed("--port needs to be specified")
		if not self.client:
			raise WinExeFailed("--client needs to be specified")
		return True

	# TODO better check if IPC$ is reachable for client
	def __client_reachable(self, timeout=1):
		for i in range(timeout):
			try:
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				s.settimeout(1)
				s.connect((self.client, self.port))
				return True
			except socket.error:
				time.sleep(1)
				self.logger.info("checking if client %s:%s is reachable" % (self.client, self.port))
		return False

	def __build_winexe_cmd(self, domain_mode=True, runas_user=None, runas_password=None):
		cmd = []
		cmd.append("winexe")
		cmd.append("--interactive=0")
		if self.domain and domain_mode and runas_user and runas_password:
			cmd.append("-U")
			cmd.append(self.domain + "\\" + self.domain_admin + "%" + self.domain_password)
			cmd.append("--runas")
			cmd.append(self.domain + "\\" + runas_user + "%" + runas_password)
		else:
			cmd.append("-U")
			cmd.append(self.local_admin + "%" + self.local_password)

		cmd.append("//" + self.client)
		return cmd

	def __trim_windows_stdout(self, msg):
		new_msg = []
		for i in msg.split("\r"):
			i = i.strip()
			if i.startswith("Microsoft (R) Windows Script Host"):
				continue
			if i.startswith("Copyright (C) Microsoft Corporation"):
				continue
			if i:
				new_msg.append(i)
		return "\n".join(new_msg)

	def __run_command(self, cmd, dont_fail=False):
		self.logger.info("running %s" % " ".join(cmd))
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False)
		stdout, stderr = p.communicate()
		if stderr:
			self.logger.warn("Error running %s" % " ".join(cmd))
		for stream in (stdout, stderr):
			if stream:
				self.logger.warn(stream)
		if p.returncode and not dont_fail:
			raise WinExeFailed("command '%s' failed with: %s %s" % (" ".join(cmd), stdout, stderr))
		stdout = self.__trim_windows_stdout(stdout)
		return p.returncode, stdout, stderr

	def __copy_scripts(self):
		if self.scripts_copied:
			return

		cmd = ["smbclient"]
		cmd.append("//%s/C$" % self.client)
		cmd.append("-U")
		cmd.append(self.local_admin + "%" + self.local_password)
		cmd.extend(["-c", "prompt; lcd %s; mput *; quit" % self.command_dir])
		ret, stdout, stderr = self.__run_command(cmd, dont_fail=True)
		if ret:
			raise WinExeFailed("failed to copy scripts to %s  (%s, %s, %s)" % (self.client, ret, stdout, stderr))

		self.scripts_copied = True

	def __copy_script(self, script=None, domain_mode=True, runas_user=None, runas_password=None):

		extension = script.split(".")[-1]
		cmd = self.__build_winexe_cmd(domain_mode=domain_mode, runas_user=runas_user, runas_password=runas_password)

		# check certutil
		# TODO
		# certutil is required on the client as we need it to decode the
		# base64 encoded scripts, is there a better way?
		certutil = cmd + ['certutil']
		ret, stdout, stderr = self.__run_command(certutil, dont_fail=True)
		if ret:
			raise WinExeFailed("certutil not found on client %s! (%s %s)" % (self.client, stderr, stdout))

		# copy file to client in chunks of 4000 chars
		base64 = open(script, "r").read().encode("base64").replace("\n", "")
		command = os.path.basename(script).split(".")[0]
		overwrite = ">"
		for i in range(0, len(base64), 4000):
			copy = cmd + ["cmd /C echo %s %s c:\\%s.tmp" % (base64[i:i + 4000], overwrite, command)]
			overwrite = ">>"
			ret, stdout, stderr = self.__run_command(copy, dont_fail=True)
			if ret:
				raise WinExeFailed("failed to copy %s.%s (%s, %s, %s)" % (command, extension, ret, stdout, stderr))

		# decode script
		decode = cmd + ["certutil -f -decode c:\\%s.tmp c:\\%s.%s" % (command, command, extension)]
		ret, stdout, stderr = self.__run_command(decode, dont_fail=True)
		if ret:
			raise WinExeFailed("failed to decode %s.%s (%s, %s, %s)" % (command, extension, ret, stdout, stderr))

		return 0

	def winexec(self, *args, **kwarg):
		''' run args via winexe on self.client '''

		domain_mode = kwarg.get("domain_mode", True)
		dont_fail = kwarg.get("dont_fail", False)
		runas_user = kwarg.get("runas_user", self.domain_admin)
		runas_password = kwarg.get("runas_password", self.domain_password)

		if len(args) < 1:
			raise WinExeFailed("no command for winexec")
		command = args[0]
		command_args = []
		if len(args) > 1:
			for i in args[1:]:
				if i:
					command_args.append(str(i))

		if not self.__client_reachable():
			raise WinExeFailed("client %s is not reachable!" % self.client)

		cmd = self.__build_winexe_cmd(domain_mode=domain_mode, runas_user=runas_user, runas_password=runas_password)

		script = glob.glob(self.command_dir + command + ".*")
		if script and len(script) == 1:
			# self.__copy_script(script=script[0], domain_mode=domain_mode, runas_user=runas_user, runas_password=runas_password)
			self.__copy_scripts()
			if script[0].endswith(".bat"):
				cmd.append("cmd /C call c:\\%s.bat %s" % (command, " ".join(command_args)))
			elif script[0].endswith(".vbs"):
				cmd.append("cscript c:\\%s.vbs %s" % (command, " ".join(command_args)))
			elif script[0].endswith(".ps1"):
				cmd.append("PowerShell.exe -inputformat none -Noninteractive -ExecutionPolicy Bypass -File c:\\%s.ps1 %s " % (command, " ".join(command_args)))

			else:
				raise WinExeFailed("script has an unknown file extension: %s" % script[0])
		else:
			if command_args:
				command = "%s %s" % (command, " ".join(command_args))
			cmd.append(command)

		return self.__run_command(cmd, dont_fail=dont_fail)

	def wait_for_client(self, timeout=1, domain_mode=True):
		''' wait timeout seconds until client is reachable and winexe works '''

		# check if client is reachable
		if not self.__client_reachable(timeout=timeout):
			raise WinExeFailed("waiting for client (%s) failed with timeout %s" % (self.client, timeout))
		# check winexe
		for i in range(timeout):
			retval, stdout, stderr = self.winexec("cmd /C dir c:\\", dont_fail=True, domain_mode=domain_mode)
			if retval == 0:
				return 0
			time.sleep(1)
			self.logger.info("waiting for client %s" % self.client)
		# failed to connect
		raise WinExeFailed("waiting for client (%s) failed with timeout %s (can't run winexe)" % (self.client, timeout))

		return True

	def wait_until_client_is_gone(self, timeout=1):
		''' wait until self.client is no longer reachable '''

		for i in range(timeout):
			if not self.__client_reachable(timeout=1):
				return 0
			time.sleep(1)
			self.logger.info("waiting for client %s to disappear" % self.client)
		raise WinExeFailed("waiting until client (%s) is gone failed with timeout %s" % (self.client, timeout))

		return True

	def check_user_login(self, runas_user, runas_password):
		''' run klist with user runas_user '''

		ret, stdout, stderr = self.winexec(
			"klist",
			runas_user=runas_user,
			runas_password=runas_password,
			dont_fail=True,
		)
		if ret != 0:
			raise WinExeFailed("check_user_login for %s failed with %s: %s" % (runas_user, ret, stdout + stderr))

		return True

	def check_name_server(self, dns_server):
		''' check (dig) if dns_server is a DNS server '''
		self.__run_command(["dig", "@%s" % dns_server])

	def domain_join(self, dns_server=None):
		''' join self.client into self.domain '''

		self.check_name_server(dns_server)
		self.winexec("firewall-turn-off", domain_mode=False)
		self.winexec("set-dns-server", dns_server, domain_mode=False)
		self.winexec("domain-join", self.domain, self.domain_admin, self.domain_password, domain_mode=False)
		self.winexec("reboot")
		self.wait_until_client_is_gone(timeout=120)
		self.wait_for_client(timeout=120)
		self.winexec("check-domain", self.domain)
		self.winexec("activate-ts-service")
		self.check_user_login(self.domain_admin, self.domain_password)

		return True

	def list_domain_users(self):
		''' list all the domain users '''

		return self.winexec("ad-users")

	def create_ad_users(self, username, password, users):
		''' creates users users with prefix username and password password '''

		return self.winexec("create-ad-users", username, password, users)

	def create_ad_groups(self, groupname, groups):
		''' creates groups groups with prefix groupname '''

		return self.winexec("create-ad-groups", groupname, groups)

	def add_users_to_group(self, username, users, groupname, groups):
		''' adds users with prefix username to groups with prefix groupname '''

		return self.winexec("add-users-to-group", username, users, groupname, groups)

	def create_user_and_add_to_group(self, username, password, groupname):
		''' create a user with the given username and add the user to the group '''

		return self.winexec("create-user-and-add-to-group", username, password, groupname)

	def force_gpo_update(self):
		''' Runs gpupdate.exe /force '''
		return self.winexec('cmd /C "gpupdate.exe /force"', dont_fail=True)

	def get_gpo_report(self, gpo_name, server=""):
		''' returns gpo report for the self.client on the server in the domain '''

		return self.winexec("univention-get-gpo-report", self.domain, '"%s"' % gpo_name, server, domain_mode=True)

	def create_gpo(self, gpo_name, comment="", server=""):
		''' creates a gpo via the self.client on the server in the domain '''

		return self.winexec("univention-create-gpo", self.domain, '"%s"' % gpo_name, '"%s"' % comment, server, domain_mode=True)

	def Set_GPPermissions(self, gpo_name, permission_level, target_name, target_type, replace="False", server=""):
		'''
		applies a gpo via the self.client on the server in the domain
		permission_level: GpoRead|GpoApply|GpoEdit|GpoEditDeleteModifySecurity|None
		target_type: Computer|User|Group
		replace to overwrite existing GpoPermissions: True|False as a string
		'''

		return self.winexec("univention-Set-GPPermissions", self.domain, '"%s"' % gpo_name, permission_level, '"%s"' % target_name, target_type, replace, server, domain_mode=True)

	def Get_ItemProperty(self, item):

		return self.winexec("univention-Get-ItemProperty", item, domain_mode=True)

	def Set_GPRegistryValue(self, gpo_name, reg_key, value_name, value, value_type, server=""):
		'''
		modifies the gpo_name with reg_key to value_name and value_type with value
		'''

		return self.winexec("univention-Set-GPRegistryValue", self.domain, '"%s"' % gpo_name, reg_key, value_name, value, value_type, server, domain_mode=True)

	def link_gpo(self, gpo_name, link_order, target_container, server=""):
		'''
		links a gpo via the self.client on the server in the domain to the target_container
		'''

		return self.winexec("univention-link-gpo", self.domain, '"%s"' % gpo_name, link_order, target_container, server, domain_mode=True)

	def remove_gpo(self, gpo_name, server=""):
		''' removes a gpo via the self.client on the server in the domain '''

		return self.winexec("univention-remove-gpo", self.domain, '"%s"' % gpo_name, server, domain_mode=True)

	def add_certificate_authority(self):
		''' install and setup certificate authority '''

		# this is a lib needed in univention-add-certificate-authority
		self.__copy_script(self.command_dir + "/univention-install-certification-authority.ps1")

		self.winexec("univention-add-certificate-authority", self.domain)
		self.winexec("reboot")
		self.wait_until_client_is_gone(timeout=120)
		self.wait_for_client(timeout=600)

	def add_gpo_management_console(self):
		''' install GPMC on self.client and reboot '''
		self.winexec("univention-install-gpmc", self.domain)
		self.winexec("reboot")
		self.wait_until_client_is_gone(timeout=120)
		self.wait_for_client(timeout=120)

	def file_exists(self, filename):
		''' check if filename exists, return TRUE or FALSE (if file does not exists) '''

		returncode, stdout, stderr = self.winexec("cmd /C dir %s" % filename, dont_fail=True)
		if returncode == 0:
			return True
		return False

	def get_file(self, filename, destination=None):
		''' get contents of a file and optional save the contents in destination'''

		self.winexec("certutil -f -encode %s c:\\winexe.tmp.b64" % filename)
		returncode, stdout, stderr = self.winexec('cmd /C more c:\\winexe.tmp.b64')
		self.winexec("cmd /C del c:\\winexe.tmp.b64", dont_fail=True)
		stdout = stdout.replace('-----BEGIN CERTIFICATE-----', '')
		stdout = stdout.replace('-----END CERTIFICATE-----', '')
		content = stdout.decode("base64")
		if destination:
			with open(destination, 'w') as f:
				f.write(content)
		return content

	def get_root_certificate(self, filename="/tmp/ad-cert.cer"):
		''' export root certificate to filename (/tmp/ad-cert.cer) '''

		cert = 'c:\\ad-cert.crt'
		self.winexec("cmd /C del %s" % cert, dont_fail=True)
		for i in range(0, 20):
			self.winexec("certutil -store -enterprise CA 0 %s" % cert)
			time.sleep(1)
			if self.file_exists(cert):
				break
		self.get_file("%s" % cert, destination=filename)

	def promote_ad(self, dmode, forest_mode, install_root_ca=True):
		''' create AD domain on windows server '''

		self.set_local_user_password(self.domain_admin, self.domain_password)
		# TODO, why change to password here?
		self.wait_for_client(timeout=120, domain_mode=False)
		self.winexec("firewall-turn-off", domain_mode=False)
		self.winexec("univention-install-ad-ps-features", domain_mode=False, dont_fail=True)
		self.winexec("reboot", domain_mode=False)
		self.wait_until_client_is_gone(timeout=120)
		self.wait_for_client(timeout=600, domain_mode=False)
		self.winexec("univention-promote-ad", self.domain, dmode, forest_mode, domain_mode=False)
		self.wait_until_client_is_gone(timeout=120)
		self.wait_for_client(timeout=600)
		if install_root_ca:
			self.add_certificate_authority()
			self.get_root_certificate()

	def set_local_user_password(self, user, password):
		''' Changes the password of a local windows user '''
		self.winexec("cmd /C net user %s" % (user + " " + password), domain_mode=False)

	def reboot_remote_win_host(self):
		''' Reboots this windows host'''
		return self.winexec("reboot", domain_mode=False)

	def shutdown_remote_win_host(self, domain_mode=False):
		''' Shuts down this windows host'''
		self.winexec("shutdown", domain_mode=domain_mode)

	def set_gateway(self, gateway, domain_mode=True):
		''' Sets the gateway on windows host'''
		self.winexec("set-gateway", gateway, domain_mode=domain_mode)
