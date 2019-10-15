import subprocess

from univention.management.console.log import MODULE
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
	log_warnings_about_unreachable_repository_servers(zip(servers, processes))
	return [server for server, process in zip(servers, processes) if process.returncode != 0]


def start_curl_processes(servers):
	return [subprocess.Popen(['curl', '--max-time', '10', server]) for server in servers]


def wait_for_processes_to_finish(processes):
	for process in processes:
		process.wait()


def log_warnings_about_unreachable_repository_servers(servers_with_curl_processes):
	for server, process in servers_with_curl_processes:
		if process.returncode != 0:
			MODULE.warn(
				# FIXME: When changing to Python 3 use process.args here.
				"'curl --max-time 10 %s' exited with returncode %s." %
				(server, process.returncode)
			)
