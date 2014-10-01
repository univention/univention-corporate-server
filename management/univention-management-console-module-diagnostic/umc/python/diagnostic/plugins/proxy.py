#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from univention.management.console.config import ucr
from univention.management.console.modules.diagnostic import Conflict, ProblemFixed, MODULE
from univention.config_registry import handler_unset

from urlparse import urlparse
import pycurl
import StringIO
import traceback

from univention.lib.i18n import Translation
_ = Translation('univention-management-console-module-diagnostic').translate

title = _('Proxy server')
description = _('The proxy server can currently not be used. Make sure it is correctly configured using the {setup:network}.\n')
umc_modules = [{
	'module': 'setup',
	'flavor': 'network'
}]
buttons = [{
	'label': _('Disable proxy'),
	'action': 'disable'
}]
actions = {}


def disable_proxy():
	handler_unset(['proxy/http'])
	raise ProblemFixed(_('The proxy has been disabled.'))
actions['disable'] = disable_proxy


def run():
	ucr.load()

	proxy = ucr.get('proxy/http')
	if proxy:
		proxy = urlparse(proxy)
		MODULE.info('The proxy is configured, using host=%r, port=%r' % (proxy.hostname, proxy.port))
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
			raise Conflict('%s\n\n%s' (description, traceback.format_exc()))
		else:
			page = buf.getvalue()
			buf.close()
			curl.getinfo(pycurl.HTTP_CODE)
			MODULE.info(page[:100])
		finally:
			curl.close()


if __name__ == '__main__':
	from univention.management.console.modules.diagnostic import main
	main()
