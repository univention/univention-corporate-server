#!/usr/bin/python3
import json
import cgitb
cgitb.enable()


def application(environ, start_response):
	status, _, reason = environ.get('REDIRECT_STATUS', '200 OK').partition(' ')
	status = int(status)
	reason = reason or {502: 'Proxy Error', 503: 'Service Unavailable'}.get(status, reason)
	url = environ.get('REDIRECT_URL', '')
	service = 'it'
	service_name = 'Service'
	if url.startswith('/univention/udm'):
		service_name = 'Univention Directory Manager REST API'
		service = 'univention-directory-manager-rest'
		if status == 503:
			reason = 'UDM REST Unavailable'
	elif url.startswith('/univention/portal'):
		service = 'univention-portal-server'
		service_name = 'Portal Server'
		if status == 503:
			reason = 'Portal Service Unavailable'
	elif url.startswith('/univention/'):
		service_name = 'Univention Management Console Web Server'
		service = 'univention-management-console-web-server'
		if status == 503:
			reason = 'UMC-Web-Server Unavailable'

	message = "The %s could not be reached. Please restart %s or try again later." % (service_name, service)
	if status == 502:
		message += ' %s' % (environ.get('REDIRECT_ERROR_NOTES', ''),)
		message = message.rstrip()
	data = {
		"status": status,
		"message": message,
		# DEBUG: "environ": dict((key, val) for key, val in environ.items() if not key.startswith('wsgi.') and not key.startswith('mod_wsgi.')),
	}
	response_header = [('Content-type', 'application/json')]  # TODO: give HTML when json is not accepable
	start_response('%d %s' % (status, reason), response_header)
	return [json.dumps(data).encode('UTF-8')]
