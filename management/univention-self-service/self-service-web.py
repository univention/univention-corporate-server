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

import cherrypy
import json
import os
import imp
import inspect

from univention.selfservice.frontend import UniventionSelfServiceFrontend


URL_ROOT = "/"
PLUGIN_FOLDER = "/usr/share/univention-self-service/plugins"
MAIN_MODULE = "__init__"


class Root(object):

	def __init__(self, plugins):
		self.plugins = plugins

	@cherrypy.expose
	def index(self):
		return """<html>
	<head></head>
	<body>
%s
	</body>
</html>""" % "\n".join(['		<p><a href="{url}">{name}</a></p>'.format(url=plugin.url, name=plugin.name)
		for plugin in self.plugins])


def load_selfservice_plugins():
	selfservice_plugins = list()

	def find_plugins():
		_plugins = list()
		plugin_dirs = os.listdir(PLUGIN_FOLDER)
		for dir_ in plugin_dirs:
			location = os.path.join(PLUGIN_FOLDER, dir_)
			if not os.path.isdir(location) or not "%s.py" % MAIN_MODULE in os.listdir(location):
				cherrypy.log("uss-web.find_plugins(): No %s.py in plugin_dir %r, ignoring." % (MAIN_MODULE, dir_))
				continue
			info = imp.find_module(MAIN_MODULE, [location])
			_plugins.append({"name": dir_, "info": info})
		return _plugins

	def load_plugin(module):
		res = imp.load_module(MAIN_MODULE, *module["info"])
		for thing in dir(res):
			if thing.lower() == module["name"].lower():
				possible_plugin_class = getattr(res, thing)
				if inspect.isclass(possible_plugin_class) and issubclass(possible_plugin_class, UniventionSelfServiceFrontend):
					return possible_plugin_class
		cherrypy.log("uss-web.load_plugin(): Not a UniventionSelfServiceFrontend class: %r" % module["name"])
		return None

	for module in find_plugins():
		cherrypy.log("uss-web.load_selfservice_plugins(): Loading plugin %r..." % module["name"])
		plugin_class = load_plugin(module)
		if plugin_class:
			selfservice_plugins.append(plugin_class)
	return selfservice_plugins


cherrypy.config.update({
	"log.access_file": "/var/log/univention/self-service-access.log",
	"log.error_file": "/var/log/univention/self-service-error.log",
	"server.socket_port": 8099,
	"engine.autoreload_on": False})

cherrypy.log("uss-web: Going to load plugins...")
plugin_classes = load_selfservice_plugins()
plugins = list()
for plugin_class in plugin_classes:
	pl_obj = plugin_class()
	name = pl_obj.name
	plugins.append(pl_obj)

root = Root(plugins)
cherrypy.tree.mount(root, URL_ROOT, None)
for plugin in plugins:
	cherrypy.tree.mount(plugin, URL_ROOT + plugin.url, plugin.cherrypy_conf)
	cherrypy.log("uss-web: started serving plugin '{}' at '{}'.".format(plugin.name, URL_ROOT + plugin.url))
	cherrypy.log("uss-web: plugin '{}' provided conf '{}'.".format(plugin.name, plugin.cherrypy_conf))

cherrypy.engine.start()
cherrypy.engine.block()
