import subprocess
import socket
import sys
import optparse
import time
import os
import base64
import ConfigParser

COMMAND_DIR="./vbs"

class WinExe:

	def __init__(self) :

		self.usage = "usage: %prog [OPTIONS]"
		self.parser = optparse.OptionParser(usage=self.usage)
		group = optparse.OptionGroup(self.parser, "General options")

		group.add_option("--domain", dest="domain", help="the AD domain name")
		group.add_option("--domain-admin", dest="domain_admin", help="the domain administrator account")
		group.add_option("--domain-password", dest="domain_password", help="the domain administrator password")
		group.add_option("--local-admin", dest="local_admin", help="the local administrator account")
		group.add_option("--local-password", dest="local_password", help="the local administrator password")
		group.add_option("--port", dest="port", type="int", default=445, help="winexe port (445)")
		group.add_option("--client", dest="client", help="the windows client")
		
		self.parser.add_option_group(group)

		self.options = optparse.OptionGroup(self.parser, "More options")
		self.parser.add_option_group(self.options)

		self.command_dir = COMMAND_DIR

		return

	def error(self, msg):
		print >> sys.stderr, "%s" % msg

	def error_and_exit(self, msg):
		self.error(msg)
		sys.exit(1)
		
	def check_options(self):


		self.opts, self.args = self.parser.parse_args()

		config = ConfigParser.ConfigParser()
		config.read(os.path.join(os.environ['HOME'], ".winexe.ini"))
		for i in ["domain", "domain_admin", "local_admin", "local_password", "client", "domain_password"]:
			if config.has_section("default") and config.has_option("default", i):
				self.opts.ensure_value(i, config.get("default", i))

		if not self.opts.domain:
			self.error_and_exit("option --domain is required")
		if not self.opts.domain_admin:
			self.error_and_exit("option --domain-admin is required")
		if not self.opts.domain_password:
			self.error_and_exit("option --domain-password is required")
		if not self.opts.local_admin:
			self.error_and_exit("option --local-admin is required")
		if not self.opts.local_password:
			self.error_and_exit("option --local-password is required")
		if not self.opts.client:
			self.error_and_exit("option --client is required")

		return

	# TODO better check if IPC$ is reachable for client
	def client_reachable(self, timeout=1):

		for i in range(timeout):
			try:
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				s.settimeout(1)
				s.connect((self.opts.client, self.opts.port))
				return True
			except socket.error, e:
				time.sleep(1)
		return False

	def copy_script(self, vbs, domain=True, debug=False, dont_fail=False):

		cmd = []
		cmd.append("winexe")
		cmd.append("--interactive=0")
		if domain:
			cmd.append("-U")
			cmd.append(self.opts.domain + "\\" + self.opts.domain_admin + "%" + self.opts.domain_password)
			cmd.append("--runas")
			cmd.append(self.opts.domain + "\\" + self.opts.domain_admin + "%" + self.opts.domain_password)
		else:
			cmd.append("-U")
			cmd.append(self.opts.local_admin + "%" + self.opts.local_password)
		
		cmd.append("//" + self.opts.client)

		# copy file to client in chunks of 4000 chars
		base64 = open(vbs, "r").read().encode("base64").replace("\n", "")
		command = os.path.basename(vbs).split(".")[0]
		overwrite = ">"
		for i in range(0, len(base64), 4000):
			copy = cmd + ["cmd /C echo %s %s c:\\%s.tmp" % (base64[i:i+4000], overwrite, command)]
			overwrite = ">>"
			if debug:
				print copy
			p = subprocess.Popen(copy, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			so, se = p.communicate()
			if p.returncode:
				self.error_and_exit("failed to copy %s.vbs (%s, %s, %s)" % (command, p.returncode, so, se))

		# decode script
		decode = cmd + ["certutil -f -decode c:\\%s.tmp c:\\%s.vbs" % (command, command)]
		if debug:
			print decode
		p = subprocess.Popen(decode, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		so, se = p.communicate()
		if p.returncode:
			self.error_and_exit("failed to copy %s.vbs (%s, %s, %s)" % (command, p.returncode, so, se))

		return 0

	def winexec(self, *args, **kwarg):

		domain = kwarg.get("domain", True)
		quiet = kwarg.get("quiet", False)
		dont_fail = kwarg.get("dont_fail", False)
		debug = kwarg.get("debug", False)
		runas_user = kwarg.get("runas_user", self.opts.domain_admin)
		runas_password = kwarg.get("runas_password", self.opts.domain_password)

		if len(args) < 1:
			self.error_and_exit("no command for winexec")
		command = args[0]
		command_args = []
		if len(args) > 1:
			for i in args[1:]:
				if i:
					command_args.append(str(i))

		if not self.client_reachable():
			 self.error_and_exit("client %s is not reachable" % self.opts.client)

		cmd = []
		cmd.append("winexe")
		cmd.append("--interactive=0")
		if domain:
			cmd.append("-U")
			cmd.append(self.opts.domain + "\\" + self.opts.domain_admin + "%" + self.opts.domain_password)
			cmd.append("--runas")
			cmd.append(self.opts.domain + "\\" + runas_user + "%" + runas_password)
		else:
			cmd.append("-U")
			cmd.append(self.opts.local_admin + "%" + self.opts.local_password)

		cmd.append("//" + self.opts.client)

		# check if command is a vbs script and copy command
		vbs = os.path.join(self.command_dir, command + ".vbs")
		if os.path.isfile(vbs):
			self.copy_script(vbs, domain=domain, dont_fail=dont_fail, debug=debug)
			cmd.append("cscript c:\\%s.vbs %s" % (command, " ".join(command_args)))
		else:
			if command_args:
				command = "%s %s" % (command, " ".join(command_args))
			cmd.append(command)

		if debug:
			print cmd

		# run the command
		process = subprocess.Popen(
			cmd,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			shell=False)
		(stdout, stderr) = process.communicate()


		# print command output
		mystdout = []
		mystderr = []
		for i in stdout.split("\r"):
			i = i.strip()
			if i.startswith("Microsoft (R) Windows Script Host"):
				continue
			if i.startswith("Copyright (C) Microsoft Corporation"):
				continue
			if i:
				mystdout.append(i)
		for i in stderr.split("\r"):
			i = i.strip()
			if i:
				mystderr.append(i) 

		if not quiet:
			for i in mystdout:
				print i
			for i in mystderr:
				print i

		# check if command was susccessfull
		if process.returncode != 0 and not dont_fail:
			self.error_and_exit("command %s failed with %s" % (command, process.returncode))

		return process.returncode, mystdout, mystderr

	def wait_for_client(self, timeout=1, domain=True):

		# check if client is reachable
		if not self.client_reachable(timeout=timeout):
			self.error_and_exit("wait_for_client failed (client %s is not reachable)" % self.opts.client)

		# check winexe
		for i in range(timeout):
			retval, stdout, stderr = self.winexec("cmd /C dir", quiet=True, dont_fail=True)
			if retval == 0:
				return 0
			time.sleep(1)

		self.error_and_exit("wait_for_client failed (winexe to %s failed)" % self.opts.client)

	def wait_until_client_is_gone(self, timeout=1):

		for i in range(timeout):
			if not self.client_reachable(timeout=1):
				return 0
			time.sleep(1)

		self.error_and_exit("wait_until_client_is_gone failed, client %s still reachable after %s attempts" % (self.opts.client, timeout))

	def check_user_login(self, runas_user, runas_password):
		ret, stdout, stderr = self.winexec(
			"klist",
			runas_user=runas_user,
			runas_password=runas_password,
			quiet=True,
			dont_fail=True)
		if ret != 0:
			self.error_and_exit("check_user_login for %s failed with %s (%s)" % (runas_user, ret, stdout + stderr))
