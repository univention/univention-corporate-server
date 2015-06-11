# coding: UTF-8

import cgi
import tempfile

from ldap import LDAPError
from univention.management.console.modules.udm.tools import LicenseImport, LicenseError
from univention.config_registry import ConfigRegistry

#import cgitb
#cgitb.enable(display=2, logdir="/var/log/univention/system-activation.log")

def read_ldap_secret():
	secret = ''
	with open('/etc/ldap.secret') as secret_file:
		secret = secret_file.read()
		if secret[-1] == '\n':
			secret = secret[:-1]
	return secret

def application(environ, start_response):
	"""WSGI entry point"""

	def _log(msg):
		print >> environ['wsgi.errors'], msg

	def _finish(status='200 OK', response=''):
		headers = [
			('Content-Type', 'text/plain'),
			('Content-Length', str(len(response))),
		]
		start_response(status, headers)
		return [response]

	# block uploads that are larger than 1MB
	try:
		request_body_size = int(environ.get('CONTENT_LENGTH', '0'))
	except (ValueError):
		request_body_size = -1
	if request_body_size < 0:
		return _finish('411 Length Required', 'The content length was not specified.')
	if request_body_size > 1024 * 100:
		return _finish('413 Request Entity Too Large', 'The uploaded data is too large for a license file.')

	# make sure the 'license' field exists in the request
	formdata = cgi.FieldStorage(environ=environ, fp=environ['wsgi.input'])
	if not 'license' in formdata:
		# no license has been uploaded :(
		return _finish('400 Bad Request', 'No license information specified in request')

	# the program logic bellow is oriented at the import function of the
	# UMC's UDM module
	with tempfile.NamedTemporaryFile() as license_file:
		# Replace non-breaking space with a normal space
		# https://forge.univention.org/bugzilla/show_bug.cgi?id=30098
		license_data = formdata.getvalue('license', '').replace(unichr(160), ' ')
		license_file.write(license_data)
		license_file.flush()

		try:
			with open(license_file.name, 'rb') as fd:
				# check license and write it to LDAP
				ucr = ConfigRegistry()
				ucr.load()
				importer = LicenseImport(fd)
				importer.check(ucr.get('ldap/base', ''))
				importer.write('cn=admin,%s' % ucr.get('ldap/base', ''), read_ldap_secret())

		except (ValueError, AttributeError, LDAPError) as exc:
			# AttributeError: missing univentionLicenseBaseDN
			# ValueError raised by ldif.LDIFParser when e.g. dn is duplicated
			# LDAPError e.g. LDIF contained non existing attributes
			if isinstance(exc, LDAPError) and len(exc.args) and isinstance(exc.args[0], dict) and exc.args[0].get('info'):
				return _finish('400 Bad Request', 'LDAP error: %s' % exc.args[0].get('info'))
			return _finish('400 Bad Request', 'License import failed: %s' % exc)
		except LicenseError as exc:
			return _finish('400 Bad Request', 'The license data format is invalid: %s' % (exc, ))

		return _finish('200 OK', 'Successfully imported the license data')


if __name__ == '__main__':
	from wsgiref.simple_server import make_server
	srv = make_server('localhost', 8398, application)
	srv.serve_forever()

