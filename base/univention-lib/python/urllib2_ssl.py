import re
import httplib
import socket
import ssl
import urllib2


class CertificateError(ValueError):
	pass

# The following method has been backported from Python 3.3.2. Additionally the
# official fix for CVE-2013-2099 has been added.
# Please check http://docs.python.org/3/license.html for license information.
#


def _dnsname_to_pat(dn, max_wildcards=1):
	pats = []
	for frag in dn.split(r'.'):
		if frag.count('*') > max_wildcards:
			# Issue #17980: avoid denials of service by refusing more [#17980]
			# than one wildcard per fragment.  A survery of established
			# policy among SSL implementations showed it to be a
			# reasonable choice.
			raise CertificateError(
				"too many wildcards in certificate DNS name: " + repr(dn))
		if frag == '*':
			# When '*' is a fragment by itself, it matches a non-empty dotless
			# fragment.
			pats.append('[^.]+')
		else:
			# Otherwise, '*' matches any dotless fragment.
			frag = re.escape(frag)
			pats.append(frag.replace(r'\*', '[^.]*'))
	return re.compile(r'\A' + r'\.'.join(pats) + r'\Z', re.IGNORECASE)

# The following method has been backported from Python 3.3.2.
# Please check http://docs.python.org/3/license.html for license information.
#


def match_hostname(cert, hostname):
	"""Verify that *cert* (in decoded format as returned by
	SSLSocket.getpeercert()) matches the *hostname*.  RFC 2818 rules
	are mostly followed, but IP addresses are not accepted for *hostname*.

	CertificateError is raised on failure. On success, the function
	returns nothing.
	"""
	if not cert:
		raise ValueError("empty or no certificate")
	dnsnames = []
	san = cert.get('subjectAltName', ())
	for key, value in san:
		if key == 'DNS':
			if _dnsname_to_pat(value).match(hostname):
				return
			dnsnames.append(value)
	if not san:
		# The subject is only checked when subjectAltName is empty
		for sub in cert.get('subject', ()):
			for key, value in sub:
				# XXX according to RFC 2818, the most specific Common Name
				# must be used.
				if key == 'commonName':
					if _dnsname_to_pat(value).match(hostname):
						return
					dnsnames.append(value)
	if len(dnsnames) > 1:
		raise CertificateError("hostname %r "
			"doesn't match either of %s"
			% (hostname, ', '.join(map(repr, dnsnames))))
	elif len(dnsnames) == 1:
		raise CertificateError("hostname %r "
			"doesn't match %r"
			% (hostname, dnsnames[0]))
	else:
		raise CertificateError("no appropriate commonName or "
			"subjectAltName fields were found")


#
# New wrapper classes for HTTPSConnection in python 2.6 to be able
# to verify the certificate against a CA and to verify the
# certificate's hostname.
#
class VerifiedHTTPSConnection(httplib.HTTPSConnection):

	def __init__(self, host, **kwargs):
		self._ca_certs_file = kwargs.pop('ca_certs_file', None)
		self._check_hostname = kwargs.pop('check_hostname', True)
		httplib.HTTPSConnection.__init__(self, host, **kwargs)

	def connect(self):
		"Connect to a host on a given (SSL) port."

		sock = socket.create_connection((self.host, self.port), self.timeout)

		if self._tunnel_host:
			self.sock = sock
			self._tunnel()

		kwargs = {}
		if self._ca_certs_file is not None:
			kwargs.update(cert_reqs=ssl.CERT_REQUIRED, ca_certs=self._ca_certs_file)
		self.sock = ssl.wrap_socket(sock,
									keyfile=self.key_file,
									certfile=self.cert_file,
									**kwargs)
		try:
			if self._check_hostname:
				match_hostname(self.sock.getpeercert(), self.host)
		except Exception:
			self.sock.shutdown(socket.SHUT_RDWR)
			self.sock.close()
			raise


class VerifiedHTTPSHandler(urllib2.HTTPSHandler):

	"""
    Possible keyword arguments:
      cert_file:       (see httplib.HTTPSConnection)
      key_file:        (see httplib.HTTPSConnection)
      ca_certs_file:   (string, see VerifiedHTTPSConnection) filename of CA certs file
      check_hostname:  (boolean, see VerifiedHTTPSConnection) checks certificate hostname against given hostname

    Code example:
	  import urllib
	  import univention.urllib2_ssl
	  opener = urllib2.build_opener(
		  univention.urllib2_ssl.VerifiedHTTPSHandler(
			  key_file='/etc/univention/ssl/%s/private.key' % ucr.get('hostname'),
			  cert_file='/etc/univention/ssl/%s/cert.key' % ucr.get('hostname'),
			  ca_certs_file='/etc/univention/ssl/ucsCA/CAcert.pem',
			  ))
	  response = opener.open(url, body).read()

	"""

	def __init__(self, **kwargs):
		urllib2.HTTPSHandler.__init__(self, kwargs.pop('debuglevel', 0))  # always pass debuglevel to HTTPSHandler
		self._httpcon_kwargs = kwargs

	def https_open(self, req):
		# instead of passing a class name to do_open() the method _getVerifiedHTTPSConnectionInstance
		# is passed. The method has the same signature as the class constructor and returns an instance
		# of our new wrapper class VerifiedHTTPSConnection.
		return self.do_open(self._getVerifiedHTTPSConnectionInstance, req)

	def _getVerifiedHTTPSConnectionInstance(self, host, **kwargs):
		conn_kwargs = self._httpcon_kwargs.copy()
		conn_kwargs.update(kwargs)
		return VerifiedHTTPSConnection(host, **conn_kwargs)
