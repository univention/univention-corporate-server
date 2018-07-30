import subprocess

import univention.config_registry

UCR = univention.config_registry.ConfigRegistry()
UCR.load()


def get_unreachable_repository_servers():
	unreachable_servers = []
	UCR.load()
	for server in [
		UCR.get('repository/online/server'),
		UCR.get('repository/app_center/server'),
		'docker.software-univention.de'
	]:
		try:
			subprocess.check_call(['curl', server])
		except subprocess.CalledProcessError:
			unreachable_servers.append(server)
	return unreachable_servers
