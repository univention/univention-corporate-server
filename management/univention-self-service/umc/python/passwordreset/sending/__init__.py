import importlib
import inspect
import os

from univention.management.console.modules.passwordreset.send_plugin import UniventionSelfServiceTokenEmitter


def get_plugins(log):
    plugins = {}

    def find_plugins():
        _plugins = []
        _dir = os.path.dirname(__file__)
        for _file in os.listdir(_dir):
            if _file.endswith(".py") and _file != "__init__.py" and os.path.isfile(os.path.join(_dir, _file)):
                _plugins.append(_file[:-3])
        return _plugins

    def load_plugin(_module):
        res = importlib.import_module(f'univention.management.console.modules.passwordreset.sending.{_module}')
        for possible_plugin_class in inspect.getmembers(res, lambda m: inspect.isclass(m) and m is not UniventionSelfServiceTokenEmitter and issubclass(m, UniventionSelfServiceTokenEmitter)):
            return possible_plugin_class[1]
        return None

    for _plugin in find_plugins():
        plugin_class = load_plugin(_plugin)
        if plugin_class:
            if plugin_class.is_enabled():
                log(f"get_plugins(): Loaded sending plugin class '{plugin_class.__name__}' for sending method '{plugin_class.send_method()}'.")
                plugins[plugin_class.send_method()] = plugin_class(log)
            else:
                log(f"get_plugins(): Plugin class '{plugin_class.__name__}' for sending method '{plugin_class.send_method()}' is disabled.")
    for _name, plugin in plugins.items():
        log(f"get_plugins(): plugin class '{plugin.__class__.__name__}' for sending method '{plugin.send_method()}': udm_property: '{plugin.udm_property}' token_length: '{plugin.token_length}'")
    return plugins
