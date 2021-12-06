#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
install/remove/update apps via umc
"""

import optparse
import os
import sys
import time
from tempfile import gettempdir
from requests import get

import univention.config_registry
import univention.lib.umc
from univention.appcenter.app_cache import Apps as FindApps
from univention.appcenter.utils import call_process, get_local_fqdn


class Apps(object):

	def __init__(self):
		usage = '''%prog [options] '''
		description = sys.modules[__name__].__doc__
		parser = optparse.OptionParser(usage=usage, description=description)
		parser.add_option("-U", "--username", action="store", dest="username", help="username")
		parser.add_option("-p", "--password", action="store", dest="password", help="password")
		parser.add_option("-a", "--app", action="store", dest="app", help="app id")
		parser.add_option("-r", "--remove", action="store_true", dest="remove", default=False, help="remove app")
		parser.add_option("-u", "--update", action="store_true", dest="update", default=False, help="upgrade app")
		parser.add_option(
			"-i", "--ignore-no-update", action="store_true", dest="ignore_no_update", default=False,
			help="normally -u fails if no update is available, with this switch just return in that case")
		(self.options, self.args) = parser.parse_args()
		assert self.options.username is not None
		assert self.options.password is not None
		assert self.options.app is not None
		self.client = None
		self.ucr = univention.config_registry.ConfigRegistry()
		self.ucr.load()
		print(self.options)

	def umc(self, path, data):
		print('-> invoke {path} with options {data}'.format(path=path, data=data))
		if self.client is None:
			self.client = univention.lib.umc.Client(username=self.options.username, password=self.options.password)
		print('-> headers: {headers}'.format(headers=self.client._headers))
		resp = self.client.umc_command(path, data)
		assert resp.status == 200
		result = resp.result
		print('<- {res}'.format(res=result))
		return result

	def wait(self, result, app):
		pid = result['id']
		path = 'appcenter/progress'
		data = dict(progress_id=pid)
		waited = 0
		while waited <= 720:
			time.sleep(10)
			waited += 1
			try:
				result = self.umc(path, data)
			except univention.lib.umc.ConnectionError:
				print('... Apache down? Ignoring...')
				continue
			for message in result.get('intermediate', []):
				print('   {msg}'.format(msg=message.get('message')))
			if result.get('finished', False):
				break
		else:
			raise Exception("wait timeout")
		print(result)
		assert result['result'][get_local_fqdn()][app]['success'] is True

	def run_script(self, app, script):
		app = FindApps().find(app)
		url = os.path.join('http://appcenter-test.software-univention.de', 'univention-repository', app.get_ucs_version(), 'maintained', 'component', app.component_id, 'test_%s' % script)
		print(url)
		response = get(url)
		if response.ok is not True:
			print(' no %s script found for app %s: %s' % (script, app.id, response.content))
			return
		fname = os.path.join(gettempdir(), '%s.%s' % (app.id, script))
		with open(fname, 'wb') as f:
			f.write(response.content)
		os.chmod(fname, 0o755)
		bind_dn = self.ucr.get('tests/domainadmin/account')
		if bind_dn is None:
			bind_dn = 'uid=Administrator,%s' % self.ucr.get('ldap/base')
		pwd_file = self.ucr.get('tests/domainadmin/pwdfile')
		unlink_pwd_file = False
		if pwd_file is None:
			pwd_file = '/tmp/app-installation.pwd'
			with open(pwd_file, 'w') as fd:
				fd.write('univention')
			unlink_pwd_file = True
		try:
			cmd = [fname, '--binddn', bind_dn, '--bindpwdfile', pwd_file]
			print('running ', cmd)
			return call_process(cmd).returncode
		finally:
			if unlink_pwd_file:
				os.unlink(pwd_file)

	def make_args(self, action, app):
		host = get_local_fqdn()
		settings = {}
		return {
			"action": action,
			"auto_installed": [],
			"hosts": {host: app},
			"apps": [app],
			"dry_run": False,
			"settings": {app: settings},
		}

	def run_action(self, action, app):
		data = self.make_args(action, app)
		resp = self.umc("appcenter/run", data)
		self.wait(resp, app)

	def install(self):
		self.run_script(self.options.app, 'preinstall')
		self.run_action("install", self.options.app)

	def uninstall(self):
		self.run_script(self.options.app, 'preremove')
		self.run_action("remove", self.options.app)

	def update(self):
		self.run_script(self.options.app, 'preupgrade')
		result = self.umc('appcenter/get', {"application": self.options.app})
		update_available = False
		for host in result.get('installations'):
			if host == self.ucr['hostname']:
				print('-> installations: {inst}'.format(inst=result['installations']))
				if result['installations'][host]['update_available']:
					update_available = True
					break
		if self.options.ignore_no_update is True and update_available is False:
			return
		assert update_available is True
		self.run_action("upgrade", self.options.app)

	def main(self):
		if self.options.remove:
			self.uninstall()
		elif self.options.update:
			self.update()
		else:
			self.install()


if __name__ == '__main__':
	apps = Apps()
	apps.main()
