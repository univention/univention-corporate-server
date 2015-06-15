# -*- coding: utf-8 -*-

import urllib2
from socket import error as SocketError

from univention.appreport.api import ucr
from univention.appreport import provider
# TODO: import univention.debug

PROVIDER_IDENTIFIER = 'appreport/recipient'


class ConnectionManager(object):

	user_agent = 'univention.appreport'
	timeout = 60

	def __init__(self):
		self.opener = self.build_opener()
		self.default_headers()

	def build_opener(self):
		handler = urllib2.BaseHandler()
		proxy_handler = urllib2.ProxyHandler()
		opener = urllib2.build_opener(handler, proxy_handler)
		return opener

	def default_headers(self):
		self.opener.addheaders = [('User-Agent', self.user_agent)]

	def request(self, request):
		try:
			self.opener.open(request.request, timeout=self.timeout)
		except SocketError:
			raise  # TODO
		except (urllib2.HTTPError, urllib2.URLError):
			raise  # TODO


class AppReporting(object):

	def __init__(self):
		self.connection = ConnectionManager()
		provider.load()

	def main(self):
		for provider_ in self.providers():
			try:
				for request in provider_.requests():
					self.connection.request(request)
			except:
				raise  # TODO

	def providers(self):
		yield provider.get('univention')
		for name in ucr.get(PROVIDER_IDENTIFIER, '').split():
			yield provider.get(name)


if __name__ == '__main__':
	AppReporting().main()
