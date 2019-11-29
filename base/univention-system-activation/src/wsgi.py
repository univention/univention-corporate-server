# coding: UTF-8

import cgi
import subprocess
import traceback
import json
import re
from ldif import LDIFParser
from univention.config_registry import ConfigRegistry


class LicenseLDIF(LDIFParser):

	def __init__(self, input, ucr):
		LDIFParser.__init__(self, input)
		self.ucr = ucr
		self.uuid = '00000000-0000-0000-0000-000000000000'

	@property
	def uuid(self):
		return self.uuid

	def handle(self, dn, entry):
		if dn == 'cn=admin,cn=license,cn=univention,%s' % self.ucr.get('ldap/base'):
			if 'univentionLicenseKeyID' in entry and len(entry['univentionLicenseKeyID']) > 0:
				self.uuid = entry['univentionLicenseKeyID'][0]


class LdapLicenseFetchError(Exception):
	pass


ucr = ConfigRegistry()
ucr.load()

LICENSE_UPLOAD_PATH = '/var/cache/univention-system-activation/license.ldif'

reg_exp_app_key = re.compile(r'^appliance/apps/(?P<id>[^/]*)/(?P<key>.*)$')


def get_installed_apps():
	notify_apps = set()
	apps = []
	for key, value in ucr.items():
		m = reg_exp_app_key.match(key)
		if m:
			ucr_key = m.group('key')
			app_id = m.group('id')
			if ucr_key == 'notifyVendor' and ucr.is_true(key):
				notify_apps.add(app_id)
			elif ucr_key == 'version':
				apps.append([app_id, value])

	# only return apps that will notify the vendor
	apps = [iapp for iapp in apps if iapp[0] in notify_apps]
	return apps


def clean_license_output(out):
	# the output might contain the message of the day, as well
	# ... let's clean up that!
	ldif = []
	for line in out.split('\n'):
		if ldif and not line:
			# first empty line after the LDIF -> stop
			break
		matchesLdifStart = line.startswith('dn:')
		if not ldif and not matchesLdifStart:
			# we have not yet found the beginning of the LDIF -> inspect next line
			continue
		# this line is part of the LDIF -> append to LDIF ldifput
		ldif.append(line)
	return '\n'.join(ldif)


def application(environ, start_response):
	def _error(message, trace=None):
		return {
			'status': 500,
			'message': message,
			'traceback': trace,
			'location': '',
		}

	def _log(msg):
		print >> environ['wsgi.errors'], msg

	def _finish(status='200 OK', data=''):
		data = json.dumps(data)
		headers = [
			('Content-Type', 'application/json'),
			('Content-Length', str(len(data))),
		]
		start_response(status, headers)
		return [data]

	# output the license upon GET request
	if environ.get('REQUEST_METHOD') == 'GET':
		cmd = ['usr/bin/sudo', '/usr/bin/univention-ldapsearch', '-LLL', 'objectClass=univentionLicense']
		proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		try:
			out, _err = proc.communicate()
			if proc.returncode:
				raise LdapLicenseFetchError('{} exited with {}:\n{}'.format(' '.join(cmd), proc.returncode, out))
			out = clean_license_output(out)
			return _finish(data=out)
		except subprocess.CalledProcessError as exc:
			_log('Failed to read license data from LDAP:\n%s' % exc)
			return _finish('500 Internal Server Error', _error('Failed to read license data from LDAP:\n%s' % exc))
		except Exception as exc:
			return _finish('500 Internal Server Error', data=_error(str(exc), traceback.format_exc()))

	# block uploads that are larger than 1MB
	try:
		request_body_size = int(environ.get('CONTENT_LENGTH', '0'))
	except (ValueError):
		request_body_size = -1
	if request_body_size < 0:
		return _finish('411 Length Required', {
			'success': False,
			'message': 'The content length was not specified.'
		})
	if request_body_size > 1024 * 100:
		return _finish('413 Request Entity Too Large', {
			'success': False,
			'message': 'The uploaded data is too large for a license file.'
		})

	# make sure the 'license' field exists in the request
	formdata = cgi.FieldStorage(environ=environ, fp=environ['wsgi.input'])
	if 'license' not in formdata:
		# no license has been uploaded :(
		return _finish('400 Bad Request', {
			'success': False,
			'message': 'No license information specified in request'
		})

	# the program logic below is oriented at the import function of the
	# UMC's UDM module
	with open(LICENSE_UPLOAD_PATH, 'wb') as license_file:
		# Replace non-breaking space with a normal space
		# https://forge.univention.org/bugzilla/show_bug.cgi?id=30098
		license_data = formdata.getvalue('license', '').replace(chr(160), ' ')
		license_file.write(license_data)

	# import the uploaded license file
	try:
		subprocess.check_output(['/usr/bin/sudo', '/usr/sbin/univention-license-import', LICENSE_UPLOAD_PATH], stderr=subprocess.STDOUT)
	except subprocess.CalledProcessError as exc:
		_log('Failed to import the license:\n%s\n%s' % (exc.output, exc))
		return _finish('400 Bad Request', {
			'success': False,
			'message': exc.output
		})

	ucr.load()

	# get uuid from ldif file, ucr['uuid/license'] is not yet up-to-date at this point
	license_ldif = LicenseLDIF(open(LICENSE_UPLOAD_PATH, 'rb'), ucr)
	license_ldif.parse()

	system_uuid = ucr.get('uuid/system')

	# disable system activation service (stop is executed with a small delay)
	# and answer request
	apps = get_installed_apps()
	subprocess.Popen(['/usr/bin/sudo', '/usr/sbin/univention-system-activation', 'stop'], stderr=subprocess.STDOUT)
	return _finish('200 OK', {
		'success': True,
		'uuid': license_ldif.uuid,
		'systemUUID': system_uuid,
		'apps': apps,
	})


if __name__ == '__main__':
	from wsgiref.simple_server import make_server
	srv = make_server('localhost', 8398, application)
	srv.serve_forever()
