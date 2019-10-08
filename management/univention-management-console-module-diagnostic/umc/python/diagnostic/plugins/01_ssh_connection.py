#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from univention.management.console.config import ucr
from univention.management.console.modules.diagnostic import Critical
from univention.management.console.modules.diagnostic import Warning
from univention.admin import uldap
from univention.admin import modules
from univention.management.console.log import MODULE
import paramiko
import logging
import socket
import re

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('SSH connection to UCS server failed!')

ucr.load()
fqdn = ".".join((ucr['hostname'], ucr['domainname']))
run_descr = ['This can be checked by running:  univention-ssh /etc/machine.secret "%s$@%s" echo OK' % (ucr["hostname"], fqdn)]


class IgnorePolicy(paramiko.MissingHostKeyPolicy):

	def missing_host_key(self, client, hostname, key):
		pass


def run(_umc_instance):
	# Now a workaround for paramico logging to connector-s4.log
	# because one of the diagnostic plugins instantiates s4connector.s4.s4()
	# which initializes univention.debug2, which initializes logging.basicConfig
	logger = paramiko.util.logging.getLogger()
	logger.setLevel(logging.CRITICAL)

	try:
		lo, position = uldap.getMachineConnection(ldap_master=False)
	except Exception as err:
		raise Warning(str(err))

	modules.update()
	ucs_hosts = []
	roles = [
		'computers/domaincontroller_backup',
		'computers/domaincontroller_master',
		'computers/domaincontroller_slave',
		'computers/memberserver']
	for role in roles:
		udm_obj = modules.get(role)
		modules.init(lo, position, udm_obj)
		for host in udm_obj.lookup(None, lo, 'cn=*'):
			if 'docker' in host.oldattr.get('univentionObjectFlag', []):
				continue
			if not host.get('ip'):
				continue
			host.open()
			ucs_hosts.append(host['name'])

	with open('/etc/machine.secret', 'rb') as fd:
		password = fd.read().strip()

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

		fqdn = host + '.' + ucr['domainname']
		try:
			client.connect(fqdn, port=22, username=ucr['hostname'] + '$', password=password, timeout=2, banner_timeout=2, allow_agent=False)
			client.close()
		except paramiko.BadHostKeyException as err:
			bad[fqdn] = key_msg + '!'
			key_failed = True
		except paramiko.BadAuthenticationType as err:
			bad[fqdn] = auth_msg + '!'
			auth_failed = True
		except (paramiko.SSHException, socket.timeout) as err:
			# ignore if host is not reachable and other ssh errors
			pass
		except Exception as err:
			bad[fqdn] = str(err)
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
		log_msg = msg.splitlines()
		for line in log_msg:
			if not re.match(r'^\s*$', line):
				MODULE.error("%s" % line)
		MODULE.error("%s" % data)
		raise Critical(msg % data)


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
