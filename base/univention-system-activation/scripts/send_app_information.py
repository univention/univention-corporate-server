#!/usr/bin/env python


import urllib
import urllib2
from univention.management.console.log import MODULE
from univention.management.console.modules.appcenter.util import urlopen
from univention.config_registry import ConfigRegistry


ucr = ConfigRegistry()
ucr.load()


def main():
	apps = get_installed_apps()
	send_information(apps)


def get_installed_apps():
	apps = {}
	for key, value in ucr.items():
		if 'appliance/apps/' in key:
			appliance, app, app_id, app_attr = key.split('/')
			apps.setdefault(app_id, {})[app_attr] = value
	return apps


def send_information(apps, action='install', status=200):
	query_params = {
		'uuid' : ucr.get('uuid/license'),
		'action': action,
		'status': status,
		'role': ucr.get('server/role')
	}
	
	for app in apps.iterkeys():
		current_app = apps[app]
		if current_app['notifyVendor']:
			query_params['app'] = app
			query_params['version'] = current_app['version']
			try:
				request_data = urllib.urlencode(query_params)
				server = get_server(with_sheme=True)
				url = '%s/postinst' % (server, )
				request = urllib2.Request(url, request_data)
				foo = urlopen(request)
			except:
				MODULE.warn(traceback.format_exc())


def get_server(with_sheme=False):
	server = ucr.get('repository/app_center/server', 'appcenter.software-univention.de')
	if with_sheme:
		if not server.startswith('http'):
			server = 'https://%s' %server
	else:
		server = re.sub('https?://', '', server)
	return server


if __name__ == '__main__':
	main()
