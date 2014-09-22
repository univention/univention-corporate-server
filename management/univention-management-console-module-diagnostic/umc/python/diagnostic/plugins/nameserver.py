#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from univention.management.console.config import ucr
from univention.management.console.modules.diagnostic import Conflict

import dns.resolver
import dns.exception

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Nameserver(s) are not responsive')
description = _('Some of the configured nameservers are not responding to DNS-Queries. Please make sure the DNS settings in the {networks} module are correctly set up.')
umc_modules = [('setup', 'network', {})]


def run():
	ucr.load()
	stdout = ''
	stderr = ''
	success = True

	hostnames = {
		'www.univention.de': ('dns/forwarder1', 'dns/forwarder2', 'dns/forwarder3'),
		ucr.get('hostname', ''): ('nameserver1', 'nameserver2', 'nameserver3')
	}

	for hostname, nameservers in hostnames.iteritems():
		for nameserver in nameservers:
			if not ucr.get(nameserver):
				continue

			answers = query_dns_server(ucr[nameserver], hostname)
			success = success and answers
			if not answers:
				stderr += _('The nameserver %r(%r) is not responsive.') % (nameserver, ucr[nameserver])

	return success, stdout, stderr


def query_dns_server(nameserver, hostname):
	resolver = dns.resolver.Resolver()
	resolver.lifetime = 10
	resolver.nameservers = [nameserver]

	# perform a SRV lookup
	try:
		resolver.query(hostname)
	except dns.resolver.NXDOMAIN:
		pass
	except dns.exception.Timeout:
		return False
	except dns.exception.DNSException:
		# any other exception is ....
		raise
		return False
	return True
