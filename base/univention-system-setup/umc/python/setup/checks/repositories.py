import subprocess

import univention.config_registry

UCR = univention.config_registry.ConfigRegistry()
UCR.load()


def get_unreachable_repository_servers():
	UCR.load()

	servers = [
		UCR.get('repository/online/server'),
		UCR.get('repository/app_center/server'),
		'docker.software-univention.de'
	]

	processes = start_curl_processes(servers)
	wait_for_processes_to_finish(processes)
	return [server for server, process in zip(servers, processes) if process.returncode != 0]

def start_curl_processes(servers):
	return [subprocess.Popen(['curl', '--max-time', '10', server]) for server in servers]

def wait_for_processes_to_finish(processes):
	for process in processes:
		process.wait()
