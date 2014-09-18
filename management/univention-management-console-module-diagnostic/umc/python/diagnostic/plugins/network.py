#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Network')
description = _('Checks if the network is correctly configured')

from subprocess import Popen, PIPE
from univention.management.console.config import ucr
import dns.resolver
import dns.exception
from urlparse import urlparse
import pycurl
import StringIO
import traceback


def run():
	stdout = ''
	stderr = ''
	success = True

	stdout += _('Checking if gateway is reachable\n')
	reachable, _stdout, _stderr = gateway_reachable()
	stdout += _stdout
	stderr += _stderr
	if reachable != 0:
		success = False

	stdout += _('Checking for responding nameservers\n')
	responding, _stdout, _stderr = dns_settings()
	stdout += _stdout
	stderr += _stderr
	if not responding:
		success = False

	stdout += _('Checking proxy server\n')
	proxy_works, _stdout, _stderr = http_proxy()
	stdout += _stdout
	stderr += _stderr
	if not proxy_works:
		success = False

	# module should redirect to the system setup network module
	if not success:
		stdout += _('.... <a href="javascript:function() {require("umc/app").openModule("setup", "network");}">use system setup network to repair...</a>')

	return success, stdout, stderr


def gateway_reachable():
	ucr.load()
	gateway = ucr.get('gateway')
	process = Popen(['/bin/ping', '-c1', '-w100', gateway], stdout=PIPE, stderr=PIPE)
	stdout, stderr = process.communicate()

	return process.returncode, stdout, stderr


def dns_settings():
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


def http_proxy():
	ucr.load()
	success = True
	stdout = ''
	stderr = ''

	proxy = ucr.get('proxy/http')
	if proxy:
		proxy = urlparse(proxy)
		stdout += _('The proxy is configured, using host=%r, port=%r') % (proxy.hostname, proxy.port)
		curl = pycurl.Curl()
		curl.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_HTTP)
		curl.setopt(pycurl.PROXYAUTH, pycurl.PROXYAUTH_AVAIL)
		curl.setopt(pycurl.PROXY, proxy.hostname)
		curl.setopt(pycurl.PROXYPORT, proxy.port)
		#curl.setopt(pycurl.FOLLOWLOCATION, bFollowLocation)
		#curl.setopt(pycurl.MAXREDIRS, maxReDirs)
		#curl.setopt(pycurl.CONNECTTIMEOUT, connectTimout)
		#curl.setopt(pycurl.TIMEOUT, timeOut)
		if proxy.username and proxy.password:
			curl.setopt(pycurl.PROXYUSERPWD, '%s:%s' % (proxy.username, proxy.password))

		curl.setopt(pycurl.URL, 'http://univention.de/')
		#curl.setopt(pycurl.VERBOSE, bVerbose)

		buf = StringIO.StringIO()
		curl.setopt(pycurl.WRITEFUNCTION, buf.write)
		try:
			curl.perform()
		except pycurl.error:
			success = False
			stderr += traceback.format_exc()
		else:
			page = buf.getvalue()
			buf.close()
			curl.getinfo(pycurl.HTTP_CODE)
			stdout = page[:100]
		finally:
			curl.close()

	return success, stdout, stderr
