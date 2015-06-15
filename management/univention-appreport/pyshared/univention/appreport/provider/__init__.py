# -*- coding: utf-8 -*-

import os.path
import inspect

from univention.appreport.api import UniventionServer, ServerInterface, ucr

provider = {}


def load():
	# TODO: we don't need to import all files
	provider.clear()
	_load_from_ucr()
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


def _load_from_ucr():
	_provider = {}
	# get all data
	for key, value in ((k, v) for k, v in ucr.items() if k.startswith('appreport/provider/')):
		key = key[len('appreport/provider/'):]
		try:
			prov, key = key.split('/', 1)
		except ValueError:
			continue

		if key in ('url', ):
			_provider.setdefault(prov, {})[key] = value
			continue

		try:
			app, key = key.split('/', 1)
		except ValueError:
			continue

		if key in ('url', 'ldap_filter_user_count'):
			_provider.setdefault(prov, {}).setdefault('apps', {}).setdefault(app, {})
			_provider[prov]['apps'][app][key] = value

	# register all CSP's
	for prov, prov_values in _provider.iteritems():
		app_classes = {}
		apps = prov_values['apps']
		apps = dict((ak, av) for ak, av in apps.iteritems() if av.get('url', prov_values.get('url')))
		for app, values in apps.iteritems():
			class App(Application):
				id = app
				user_filter = values.get('ldap_filter_user_count', Application.user_filter)
			app_classes[app] = App

		if not apps:
			continue

		class CSP(CloudServiceProvider):

			apps = tuple(apps.keys())

			def url(self, app):
				return apps[app.id].get('url', prov_values.get('url'))

			def application(self, app):
				return app_classes[app.id](app)
		provider[prov] = CSP


def get(name, *args, **kwargs):
	class_ = provider.get(name, ServerInterface)
	return class_(*args, **kwargs)
