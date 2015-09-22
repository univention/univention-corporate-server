#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from univention.management.console.config import ucr
from univention.management.console.modules.diagnostic import Critical
from univention.admin import uldap
from univention.admin import modules

import paramiko
import socket

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('SSH connection to UCS server failed!')

class IgnorePolicy(paramiko.MissingHostKeyPolicy):
	def missing_host_key(self, client, hostname, key):
		pass

def run():
	ucr.load()
	lo, position = uldap.getMachineConnection(ldap_master=False)
	modules.update()
	ucs_hosts = []
	roles = ['computers/domaincontroller_backup',
		'computers/domaincontroller_master',
		'computers/domaincontroller_slave',
		'computers/memberserver']
	for role in roles:
		udm_obj = modules.get(role)
		modules.init(lo, position, udm_obj)
		for host in udm_obj.lookup(None, lo, 'cn=*'):
			host.open()
			ucs_hosts.append(host['name'])

	password = open('/etc/machine.secret').read()
	if password[-1] == '\n':
		password = password[0:-1]

	gen_msg = _('The ssh connection to at least one other UCS server failed. ')
	gen_msg += _('The following list shows the affected remote servers and the reason for the failed ssh connection:')

	key_msg = _('Host key for server does not match')
	key_info = _('The ssh host key of the remote server has changed (maybe the host was reinstalled). ')
	key_info += _('Please repair the host key of the remote server in /root/.ssh/known_hosts on %(fqdn)s.')

	auth_msg = _('Machine authentication failed')
	auth_info = _('Login to the remote server with the uid %(uid)s and the password from /etc/machine.secret failed. ')
	auth_info += _('Please check /var/log/auth.log on the remote server for further information.')

	bad = dict()
	key_failed = False
	auth_failed = False
	data = dict(
		fqdn=ucr['hostname'] + '.' + ucr['domainname'],
		uid=ucr['hostname'] + '$',
		hostname=ucr['hostname'])
	for host in ucs_hosts:
		client = paramiko.SSHClient()
		client.load_system_host_keys()
		client.set_missing_host_key_policy(IgnorePolicy())
		dest = None

		# check both, hostname and fqdn
		for dest in [host, host + '.' + ucr['domainname']]:
			try:
				client.connect(dest, port=22, username=ucr['hostname'] + '$', password=password, timeout=1, allow_agent=False)
				client.close()
			except paramiko.BadHostKeyException as err:
				if dest:
					bad[dest] = key_msg + '!'
					key_failed = True
			except paramiko.BadAuthenticationType as err:
				if dest:
					bad[dest] = auth_msg + '!'
					auth_failed = True
			except (paramiko.SSHException, socket.timeout) as err:
				# ignore if host is not reachable and other ssh errors
				pass
			except Exception as err:
				bad[dest] = str(err)
	if bad:
		msg = gen_msg
		msg += '\n\n'
		for host in bad:
			msg += '%s - %s\n' % (host, bad[host])
		if key_failed:
			msg += '\n' + key_msg + ' - ' + key_info + '\n'
		if auth_failed:
			msg += '\n' + auth_msg + ' - ' + auth_info + '\n'
		msg += '\n'
		raise Critical(msg % data)

if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
