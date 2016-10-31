"""
.. module:: randomdomain
	:platform: Unix

.. moduleauthor:: Ammar Najjar <najjar@univention.de>
"""
import pycurl
import StringIO
import time
import univention.testing.utils as utils
from tempfile import NamedTemporaryFile


class SimpleCurl(object):

	"""pycurl simple class implementation\n
	:param proxy: proxy for the http requests
	:type proxy: str
	:param username: to use for http requests
	:type username: str
	:param password: password for the user provided
	:type password: str
	:param bFollowLocation:
	:type bFollowLocation: bool
	:param maxReDirs:
	:type maxReDirs: int
	:param connectTimeout:
	:type connectTimeout: int
	:param port:
	:type port: int
	:param auth: authentication type
	:type auth: int
	:param cookies:
	:type cookies:
	:param user_agent: user agent <=> agent string
	:type user_agent: string
	"""

	def __init__(
		self,
		proxy,
		username=None,
		password=None,
		bFollowLocation=1,
		maxReDirs=5,
		connectTimout=10,
		timeOut=10,
		port=3128,
		auth=pycurl.HTTPAUTH_BASIC,
		cookie=None,
		user_agent=None,
	):
			# Perform basic authentication by default
		self.curl = pycurl.Curl()
		self.curl.setopt(pycurl.FOLLOWLOCATION, bFollowLocation)
		self.curl.setopt(pycurl.MAXREDIRS, maxReDirs)
		self.curl.setopt(pycurl.CONNECTTIMEOUT, connectTimout)
		self.curl.setopt(pycurl.TIMEOUT, timeOut)
		self.curl.setopt(pycurl.PROXY, proxy)
		self.curl.setopt(pycurl.PROXYPORT, port)
		if auth:
			self.curl.setopt(pycurl.PROXYAUTH, auth)
			account = utils.UCSTestDomainAdminCredentials()
			self.curl.setopt(pycurl.PROXYUSERPWD, "%s:%s" % (
				username or account.username,
				password or account.bindpw,
			)
			)
		if user_agent:
			self.curl.setopt(pycurl.USERAGENT, user_agent)

		self.cookiefile = NamedTemporaryFile()
		self.curl.setopt(pycurl.COOKIEJAR, self.cookiefile.name)
		self.curl.setopt(pycurl.COOKIEFILE, self.cookiefile.name)

	def cookies(self):
		return self.curl.getinfo(pycurl.INFO_COOKIELIST)

	def getPage(self, url, bVerbose=False, postData=None):
		"""Gets a http page
		this method keep trying to fetch the page for 60secs then stops
		raising and exception if not succeeded.\n
		:param url: url
		:type url: str
		:param bVerbose: if verbose
		:type bVerbose: bool
		:param postData:
		:type postData:
		:returns: html page
		"""
		self.curl.setopt(pycurl.URL, url)
		self.curl.setopt(pycurl.VERBOSE, bVerbose)
		if postData:
			self.curl.setopt(pycurl.HTTPPOST, postData)
		buf = StringIO.StringIO()
		self.curl.setopt(pycurl.WRITEFUNCTION, buf.write)
		print 'getting page:', url
		for i in xrange(60):
			try:
				self.curl.perform()
				break
			except pycurl.error:
				print '.'
				time.sleep(1)
		else:
			print 'Requested page could not be fetched'
			raise
		page = buf.getvalue()
		# print page[1:400]
		buf.close()
		return page

	def httpCode(self):
		"""HTTP status code\n
		:returns: int - http_status_code
		"""
		return self.curl.getinfo(pycurl.HTTP_CODE)

	def response(self, url):
		"""HTTP status code\n
		:param url: url
		:type url: str
		:returns: int - HTTP status code
		"""
		self.getPage(url)
		return self.httpCode()

	def close(self):
		"""Close the curl connection"""
		self.curl.close()

	def __del__(self):
		self.curl.close()
