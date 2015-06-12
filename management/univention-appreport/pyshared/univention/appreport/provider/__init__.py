# -*- coding: utf-8 -*-

import os.path
import inspect

from univention.appreport.api import UniventionServer, ServerInterface

provider = {}


def load():
	# TODO: we don't need to import all files
	provider.clear()
	errors = []
	for module in os.listdir(os.path.dirname(__file__)):
		if not module.endswith('.py'):
			continue
		try:
			module = __import__('univention.appreport.provider.%s' % (module[:-3],))
		except ImportError as exc:
			errors.append(exc)
			continue

		for member in inspect.getmembers(module, inspect.isclass):
			if isinstance(member, ServerInterface) and member is not ServerInterface:
				provider[module.__name__] = member
	provider['univention'] = UniventionServer
	for exc in errors:
		raise exc


def get(name, *args, **kwargs):
	class_ = provider.get(name, ServerInterface)
	return class_(*args, **kwargs)
