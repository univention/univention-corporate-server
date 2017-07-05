#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import os
import ast
import glob
from subprocess import call


def main():
	services = []
	for patch in glob.glob('patches/*.patch'):
		with open(patch) as fd:
			try:
				params = ast.literal_eval(fd.readline().strip())
				assert isinstance(params, dict)
			except (SyntaxError, ValueError, AssertionError):
				params = {}
		call(['patch', '-p%s' % params.get('p', 0), '-d', params.get('d', '/'), '-i', os.path.join(os.getcwd(), patch)])
		services.extend(params.get('restart_service', []))

	for service in set(services):
		call(['invoke-rc.d', service, 'restart'])


if __name__ == '__main__':
	main()
