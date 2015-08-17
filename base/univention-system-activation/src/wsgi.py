# coding: UTF-8

import cgi
import subprocess
import json
import re
from univention.config_registry import ConfigRegistry

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


def application(environ, start_response):
	"""WSGI entry point"""

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
		try:
			out = subprocess.check_output(['/usr/bin/sudo', '/usr/bin/univention-ldapsearch', '-LLL', 'objectClass=univentionLicense'])
			return _finish(data=out)
		except subprocess.CalledProcessError as exc:
			_log('Failed to read license data from LDAP:\n%s' % exc)
			return _finish('400 Bad Request', 'Failed to read license data from LDAP:\n%s' % exc)

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
	if not 'license' in formdata:
		# no license has been uploaded :(
		return _finish('400 Bad Request', {
			'success': False,
			'message': 'No license information specified in request'
		})

	# the program logic bellow is oriented at the import function of the
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

	# disable system activation service (stop is executed with a small delay)
	# and answer request
	ucr.load()
	apps = get_installed_apps()
	subprocess.Popen(['/usr/bin/sudo', '/usr/sbin/univention-system-activation', 'stop'], stderr=subprocess.STDOUT)
	return _finish('200 OK', {
		'success': True,
		'uuid': ucr.get('uuid/license', ''),
		'apps': apps,
	})


if __name__ == '__main__':
	from wsgiref.simple_server import make_server
	srv = make_server('localhost', 8398, application)
	srv.serve_forever()

