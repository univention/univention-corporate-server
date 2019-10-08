#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from univention.management.console.config import ucr
from univention.management.console.modules.diagnostic import Warning, MODULE

import dns.resolver
from dns.exception import DNSException, Timeout

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Nameserver(s) are not responsive')
description = '\n'.join([
	_('%d of the configured nameservers are not responding to DNS queries.'),
	_('Please make sure the DNS settings in the {setup:network} are correctly set up.'),
	_('If the problem persists make sure the nameserver is connected to the network and the forwarders are able to reach the internet (www.univention.de).'),

])
umc_modules = [{
	'module': 'setup',
	'flavor': 'network'
}]
run_descr = ['Checks if all nameservers are responsive']


def run(_umc_instance):
	ucr.load()
	failed = []
	fqdn = ".".join((ucr['hostname'], ucr['domainname']))
	hostnames = {
		'www.univention.de': ('dns/forwarder1', 'dns/forwarder2', 'dns/forwarder3'),
		fqdn: ('nameserver1', 'nameserver2', 'nameserver3')
	}
	for hostname, nameservers in hostnames.items():
		for nameserver in nameservers:
			if not ucr.get(nameserver):
				continue

			MODULE.process("Trying %s to resolve %s" % (ucr[nameserver], hostname))
			MODULE.process("Similar to running: dig +short %s @%s" % (hostname, ucr[nameserver]))
			try:
				query_dns_server(ucr[nameserver], hostname)
			except DNSException as exc:
				msgs = ['\n', _('The nameserver %(nameserver)s (UCR variable %(var)r) is not responsive:') % {'nameserver': ucr[nameserver], 'var': nameserver}]

				if isinstance(exc, Timeout):
					msgs.append(_('A timeout occurred while reaching the nameserver (is it online?).'))
				else:
					msgs.append('%s' % (exc,))
				failed.append('\n'.join(msgs))

	if failed:
		MODULE.error('%s%s' % (description % (len(failed),), '\n'.join(failed)))
		raise Warning('%s%s' % (description % (len(failed),), '\n'.join(failed)))


def query_dns_server(nameserver, hostname):
	resolver = dns.resolver.Resolver()
	resolver.lifetime = 10
	resolver.nameservers = [nameserver]

	# perform a reverse lookup
	try:
		resolver.query(hostname)
	except dns.resolver.NXDOMAIN:
		# it's not a problem
		pass


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
