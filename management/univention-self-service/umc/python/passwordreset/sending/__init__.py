import os
import imp
import inspect

from univention.management.console.modules.passwordreset.send_plugin import UniventionSelfServiceTokenEmitter


def get_plugins(log):
	plugins = dict()

	def find_plugins():
		_plugins = list()
		_dir = os.path.dirname(__file__)
		for _file in os.listdir(_dir):
			if _file.endswith(".py") and not _file == "__init__.py" and os.path.isfile(os.path.join(_dir, _file)):
				info = imp.find_module(_file[:-3], [_dir])
				_plugins.append({"name": _file[:-3], "info": info})
		return _plugins

	def load_plugin(_module):
		res = imp.load_module(_module["name"], *_module["info"])
		for thing in dir(res):
			possible_plugin_class = getattr(res, thing)
			if inspect.isclass(possible_plugin_class) and issubclass(possible_plugin_class, UniventionSelfServiceTokenEmitter):
				return possible_plugin_class
		return None

	for _plugin in find_plugins():
		plugin_class = load_plugin(_plugin)
		if plugin_class:
			if plugin_class.is_enabled():
				log("get_plugins(): Loaded sending plugin class '{}' for sending method '{}'.".format(plugin_class.__name__, plugin_class.send_method()))
				plugins[plugin_class.send_method()] = plugin_class(log)
			else:
				log("get_plugins(): Plugin class '{}' for sending method '{}' is disabled.".format(plugin_class.__name__, plugin_class.send_method()))
	for name, plugin in plugins.items():
		log("get_plugins(): plugin class '{}' for sending method '{}': udm_property: '{}' token_length: '{}'".format(plugin.__class__.__name__, plugin.send_method(), plugin.udm_property, plugin.token_length))
	return plugins
