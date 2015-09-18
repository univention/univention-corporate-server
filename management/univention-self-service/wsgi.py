# -*- coding: utf-8 -*-
import sys
sys.stdout = sys.stderr

import atexit
import cherrypy
import json

from univention.lib.umc_connection import UMCConnection


class Root(object):

    @cherrypy.expose
    def index(self):
		cherrypy.response.headers['Content-Type'] = 'application/json'
        return json.dumps('Hello World!')


def request_token(username, mailaddress):
	connection = UMCConnection.get_machine_connection()  # uses the machine.secret, must run as root then, ... (replace?)
	try:
		result = connection.request('passwordreset/reset', {
			'username': username,
			'mailaddress': mailaddress,
		})
	except (ValueError, NotImplementedError, HTTPException):
		raise  # the lib is completely broken ...
	return result


def submit_token(token):
	connection = UMCConnection.get_machine_connection()
	try:
		result = connection.request('passwordreset/submit', {
			'token': token,
		})
	except (ValueError, NotImplementedError, HTTPException):
		raise  # the lib is completely broken ...
	return result


if cherrypy.engine.state == 0:
	cherrypy.engine.start(blocking=False)
	atexit.register(cherrypy.engine.stop)

cherrypy.config.update({'environment': 'embedded'})
application = cherrypy.Application(Root(), script_name=None, config=None)
