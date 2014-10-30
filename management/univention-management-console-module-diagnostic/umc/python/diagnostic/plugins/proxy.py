#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from univention.management.console.config import ucr
from univention.management.console.modules.diagnostic import Warning, Conflict, MODULE

from urlparse import urlparse
import pycurl
import StringIO
import traceback

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Proxy server failure')
description = _('There was an error using the proxy server. The {setup:network} can be used to change the proxy configuration.\n')
umc_modules = [{
	'module': 'setup',
	'flavor': 'network'
}]
actions = {}


def run(url='http://www.univention.de/', connecttimeout=30, timeout=30):
	ucr.load()

	proxy = ucr.get('proxy/http')
	if not proxy:
		return

	proxy = urlparse(proxy)
	MODULE.info('The proxy is configured, using host=%r, port=%r' % (proxy.hostname, proxy.port))
	curl = pycurl.Curl()
	curl.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_HTTP)
	curl.setopt(pycurl.PROXY, proxy.hostname)
	curl.setopt(pycurl.PROXYPORT, proxy.port)
	curl.setopt(pycurl.FOLLOWLOCATION, True)
	curl.setopt(pycurl.MAXREDIRS, 5)
	curl.setopt(pycurl.CONNECTTIMEOUT, connecttimeout)
	curl.setopt(pycurl.TIMEOUT, 30)
	if proxy.username:
		curl.setopt(pycurl.PROXYAUTH, pycurl.HTTPAUTH_ANY)
		credentials = '%s' % (proxy.username,)
		if proxy.password:
			credentials = '%s:%s' % (proxy.username, proxy.password)
		curl.setopt(pycurl.PROXYUSERPWD, credentials)

	curl.setopt(pycurl.URL, url)
	#curl.setopt(pycurl.VERBOSE, bVerbose)

	buf = StringIO.StringIO()
	curl.setopt(pycurl.WRITEFUNCTION, buf.write)
	try:
		curl.perform()
	except pycurl.error as exc:
		try:
			code, msg = exc.args
			msg = '%s (code=%s)' % (msg, code)
			MODULE.info(msg)
		except ValueError:
			MODULE.error(traceback.format_exc())
			code = 0
			msg = str(exc)
		if code == pycurl.E_COULDNT_CONNECT:
			msg = _('The proxy host could not be reached. Make sure that hostname (%r) and port (%r) are correctly set up.') % (proxy.hostname, proxy.port,)
		elif code == pycurl.E_COULDNT_RESOLVE_PROXY:
			msg = _('The hostname of the proxy could not be resolved. May check your DNS configuration.')
		elif code == pycurl.E_OPERATION_TIMEOUTED:
			msg = _('The server did not respond within %d seconds. Please check your network configuration.') % (timeout,)
		elif code == 0:
			MODULE.error(traceback.format_exc())

		raise Conflict('\n'.join([description, msg]))
	else:
		#page = buf.getvalue()
		#MODULE.info(page[:100])
		buf.close()
		http_status = curl.getinfo(pycurl.HTTP_CODE)
		if http_status >= 400:
			raise Warning('\n'.join([
				description,
				_('The proxy server is reachable but the HTTP response status code (%d) does not indicate success.') % (http_status,),
				_('This warning might be harmless. Nevertheless make sure the authentication credentials (if any) are correct and the proxy server ACLs do not forbid requests to %s.') % (url,)
			]))
	finally:
		curl.close()


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
