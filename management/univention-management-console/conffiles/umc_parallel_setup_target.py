import os
import subprocess

def handler(ucr, changes):
	try:
		umc_parallel = int(ucr.get('umc/parallel', 0))
	except ValueError:
		umc_parallel = 0
	try:
		start_port_web = int(ucr.get('umc/parallel/start-port-web', 18090))
	except ValueError:
		start_port_web = 18090
	try:
		start_port = int(ucr.get('umc/parallel/start-port', 16070))
	except ValueError:
		start_port = 16070

	systemd_target_dir = '/etc/systemd/system/umc_parallel.target.wants/'

	if os.path.isdir(systemd_target_dir):
		for service in os.listdir(systemd_target_dir):
			subprocess.call(['systemctl', 'disable', service])

	if umc_parallel >= 2:
		for i in range(umc_parallel):
			subprocess.call(['systemctl', 'enable', 'univention-management-console-server@{}'.format(i + start_port)])
			subprocess.call(['systemctl', 'enable', 'univention-management-console-web-server@{}'.format(i + start_port_web)])
