#!/usr/bin/python
import subprocess
import time

from univention.config_registry import ConfigRegistry


def main():
	print('Make sure to restart apache if necessary')
	ucr = ConfigRegistry()
	ucr.load()
	parallel_instances = int(ucr.get('umc/parallel', 0))
	if parallel_instances < 1:
		raise ValueError('Please set umc/parallel correct')
	start_port_umcws = int(ucr.get('umc/parallel/start-port', 18090))
	start_port_umcs = 16070
	process_list = []
	for i in range(parallel_instances):
		umcs_process = subprocess.Popen(['univention-management-console-server', '--port', str(start_port_umcs + i)])
		umcws_process = subprocess.Popen(['univention-management-console-web-server', '--port', str(start_port_umcws + i), '--umc-port', str(start_port_umcs + i)])
	print('Running')

if __name__ == '__main__':
	main()
