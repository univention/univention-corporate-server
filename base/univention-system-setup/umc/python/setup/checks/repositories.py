from os import environ
from subprocess import Popen, PIPE, STDOUT

from univention.management.console.log import MODULE
from univention.config_registry import ConfigRegistry
try:
	from typing import Iterator, List, Sequence, Tuple  # noqa F401
except ImportError:
	pass


UCR = ConfigRegistry()


def get_unreachable_repository_servers():
	# type: () -> List[str]
	"""
	Start a process to check the reachability of important servers:
	* UCS repository server (`repository/online/server`)
	* App server (`repository/app_center/server`)
	* `docker.software-univention.de`

	:returns: List of URLs.
	"""
	UCR.load()

	servers = [
		UCR.get('repository/online/server'),
		UCR.get('repository/app_center/server'),
		'docker.software-univention.de'
	]

	processes = list(start_curl_processes(servers))
	wait_for_processes_to_finish(processes)
	log_warnings_about_unreachable_repository_servers(zip(servers, processes))
	return [server for server, process in zip(servers, processes) if process.returncode != 0]


def start_curl_processes(servers):
	# type: (Sequence[str]) -> Iterator[Popen]
	"""
	Start a :command:`curl` process to check the reachability of important servers.process

	:param servers: List of URLs to check.
	:returns: List of processes.
	"""
	env = dict(environ)
	env.update(dict(
		(var, UCR[ucr])
		for ucr, var in [('proxy/http', 'http_proxy'), ('proxy/https', 'https_proxy'), ('proxy/no_proxy', 'no_proxy')]
		if ucr in UCR
	))

	for server in servers:
		cmd = ['curl', '--max-time', '10', '--silent', '--show-error', '--head', server]
		yield Popen(cmd, stdout=PIPE, stderr=STDOUT, env=env)


def wait_for_processes_to_finish(processes):
	# type: (Sequence[Popen]) -> None
	"""
	Wait until all processes have finished.

	:param processes: List of processes.
	"""
	for process in processes:
		process.wait()


def log_warnings_about_unreachable_repository_servers(servers_with_curl_processes):
	# type: (Sequence[Tuple[str, Popen]]) -> None
	"""
	Load a message for all failed processes.

	:param processes: List of 2-tuples (URL, process)
	"""
	for server, process in servers_with_curl_processes:
		if process.returncode != 0:
			stdout, strerr = process.communicate()
			MODULE.warn(
				# FIXME: When changing to Python 3 use process.args here.
				"'curl --max-time 10 %s' exited with returncode %s: %s" %
				(server, process.returncode, stdout)
			)
