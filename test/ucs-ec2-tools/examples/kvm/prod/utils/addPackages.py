#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse


def main():
	desc = "This is a little parser to add univention-packages to kvm-files"
	parser = argparse.ArgumentParser(description=desc)
	parser.add_argument('--url', '-u', help='the url to the corresponding file', required=True)

	parser.add_argument('--packages', '-p', nargs='*', default=['empty'])

	args = vars(parser.parse_args())

	path = args['url']

	print(len(args['packages']))

	with open(path, 'r') as f:
		listFile = f.readlines()

	# if args['packages'] or len(args['packages']) == 0:
	packages = args['packages']
	newListFile = [checkPackages(item, packages) for item in listFile]

	with open(path, 'w') as f:
		for elem in newListFile:
			f.write(elem)


"""
Check if item which represents a line from the imported kvm-file represents
the line with the additional packages that have to be installed.
In case that no packages where given as arguments the list of packages
will be empty
"""


def checkPackages(item, packagesList=None):
	# print(packagesList)
	if packagesList and (packagesList[0] != "empty" and "packages_install=" in item):
		packages = packagesList
		packagesStr = " packages_install=\""

		for package in packages[:-1]:
			packagesStr = packagesStr + package + " "

		packagesStr = packagesStr + packages[-1] + "\"\n"

		return packagesStr
	elif packagesList and (packagesList[0] == "empty" and "packages_install=" in item):
		return " packages_install=\"\"\n"
	elif not packagesList and "packages_install=" in item:
		return " packages_install=\"\"\n"
	else:
		return item


if __name__ == '__main__':
	main()
