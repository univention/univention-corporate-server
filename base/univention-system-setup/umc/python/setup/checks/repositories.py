import subprocess

import univention.config_registry

UCR = univention.config_registry.ConfigRegistry()
UCR.load()


def check_if_repository_servers_are_reachable():
	UCR.load()
	for server in [UCR.get('repository/online/server'), UCR.get('repository/app_center/server')]:
		try:
			subprocess.check_call(['curl', server])
		except subprocess.CalledProcessError:
			return False
	return True
