# -*- coding: utf-8 -*-
#
# Univention Self Service UI base module
#
# Copyright 2015 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

import sys
sys.stdout = sys.stderr

import atexit
import cherrypy
import json
import imp
import os

from univention.lib.umc_connection import UMCConnection


PluginFolder = "/usr/share/univention-self-service/plugins"
MainModule = "__init__"


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


def load_selfservice_plugins():
	selfservice_plugins = list()

	def find_plugins():
		plugins = list()
		plugin_dirs = os.listdir(PluginFolder)
		for dir in plugin_dirs:
			location = os.path.join(PluginFolder, dir)
			if not os.path.isdir(location) or not "%s.py" % MainModule in os.listdir(location):
				cherrypy.log("No %s.py in plugin_dir %r, ignoring." % (MainModule, dir))
				continue
			info = imp.find_module(MainModule, [location])
			plugins.append({"name": dir, "info": info})
		return plugins

	def load_plugin(plugin):
		return imp.load_module(MainModule, *plugin["info"])

	for pluginf in find_plugins():
		cherrypy.log("Loading plugin %r..." % pluginf["name"])
		plugin = load_plugin(pluginf)
		obj = plugin.get_obj()
		cherrypy.log("obj.get_cherrypy_conf(): %r" % obj.get_cherrypy_conf())
		selfservice_plugins.append(obj)

	return selfservice_plugins

cherrypy.config.update({'environment': 'embedded'})

cherrypy.config.update(
	{"log.access_file": "/var/log/univention/self-service-access.log",
	"log.error_file": "/var/log/univention/self-service-error.log"})

cherrypy.log("Going to load plugins...")
selfservice_plugins = load_selfservice_plugins()


if cherrypy.__version__.startswith('3.0') and cherrypy.engine.state == 0:
	cherrypy.engine.start()
	atexit.register(cherrypy.engine.stop)
	cherrypy.server.unsubscribe()

application = cherrypy.Application(Root(), script_name=None, config=None)
