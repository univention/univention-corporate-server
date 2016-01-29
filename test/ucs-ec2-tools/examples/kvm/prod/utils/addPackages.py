#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse

def main():
	desc = "This is a little parser to add univention-packages to kvm-files"
	parser = argparse.ArgumentParser(description=desc)
	parser.add_argument('--url','-u',help='the url to the corresponding file',required=True)
	
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('--packages','-p', nargs='*')
	group.add_argument('--empty','-e',help='this is used if no additional packages should be installed', action="store_true")
	
	args = vars(parser.parse_args())

	path = args['url']

	with open(path, 'r') as f:
		listFile = f.readlines()

	if args['packages']:
		packages = args['packages']
		#print("packages übergeben")
		#print(len(packages))
		newListFile = [checkPackages(item, packages, empty=False) for item in listFile]
	elif args['empty']:
		#print("empty übergeben")
		newListFile = [checkPackages(item, empty=True) for item in listFile]

	with open(path, 'w') as f:
		for elem in newListFile:
			f.write(elem)

	



def checkPackages(item, packagesList=None, empty=False):
	if empty==False and packagesList and "packages_install=" in item:
		packages = packagesList
		#print(len(packages))
		packagesStr = " packages_install=\""

		for package in packages[:-1]:
			packagesStr = packagesStr + package + " "

		packagesStr = packagesStr + packages[-1] + "\"\n"

		return packagesStr
	elif empty==True and not packagesList and "packages_install=" in item:
		#print("angekommen")
		return " packages_install=\"\"\n"
	else:
		return item


if __name__ == '__main__':
	main()
