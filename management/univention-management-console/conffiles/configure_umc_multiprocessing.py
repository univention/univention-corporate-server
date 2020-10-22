import os
import subprocess


def handler(ucr, changes):
	try:
		processes = int(ucr.get('umc/http/processes', 1))
	except ValueError:
		processes = 1
	try:
		start_port = int(ucr.get('umc/http/processes/start-port', 18090))
	except ValueError:
		start_port = 18090

	systemd_target_dir = '/etc/systemd/system/univention-management-console-web-server-multiprocessing.target.wants/'

	if os.path.isdir(systemd_target_dir):
		for service in os.listdir(systemd_target_dir):
			subprocess.call(['systemctl', 'disable', service])

	if processes > 1:
		for i in range(processes):
			subprocess.call(['systemctl', 'enable', 'univention-management-console-web-server@{}'.format(i + start_port)])
