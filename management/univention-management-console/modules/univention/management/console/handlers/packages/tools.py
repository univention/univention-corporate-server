#!/usr/bin/python2.4
# -*- coding: utf-8 -*-

import univention.debug as ud

import apt, re, copy, os
import subprocess

def get_sections():
	sections = []
	cache = apt.Cache()
	for package in cache.keys():
		section = cache[package].section
		if not section in sections:
			sections.append(section)
	return sections


def search_packages(category, pattern, installed, key):
	ud.debug(ud.ADMIN, ud.INFO, 'search_packages: %s ' % key)
	cache = apt.Cache()
	if  key == 'name':
		_re=re.compile( '^%s$' % pattern.replace('*','.*') )
	elif key == 'description':
		_re=re.compile( '%s' % pattern.replace('*','.*').lower() )
	infos = []

	for package in cache.keys():
		if category == 'all' or cache[package].section == category:
			if not installed or installed == cache[package].isInstalled:
				if key == 'name':
					if pattern == '*' or _re.match(package):
						ud.debug(ud.ADMIN, ud.INFO, 'found package %s' % package )
						infos.append(cache[package])
				else:
					if pattern == '*' or _re.search(cache[package].rawDescription.lower()):
						ud.debug(ud.ADMIN, ud.INFO, 'found package %s' % package )
						infos.append(cache[package])

	return infos


def get_package_info(package):
	ud.debug( ud.ADMIN, ud.INFO, 'get package information for [%s]' % package)

	cache = apt.Cache()

	if cache.has_key(package):
		return cache[package]
	else:
		return None


def install_package(package):
	os.environ['DEBIAN_FRONTEND'] = 'noninteractive'
	p1 = subprocess.Popen(["apt-get", "install", "-o", "DPkg::Options::=--force-confold", "-y", "--force-yes", package], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(stdout,stderr) = p1.communicate()
	ud.debug( ud.ADMIN, ud.WARN, 'install stderr=%s' % stderr)
	ud.debug( ud.ADMIN, ud.INFO, 'install stdout=%s' % stdout)
	if p1.returncode != 0:
		return (p1.returncode,stderr)
	else:
		return (p1.returncode,stdout)

	
def upgrade_package(package):
	p1 = subprocess.Popen(["apt-get", "install", "-o", "DPkg::Options::=--force-confold", "-y", "--force-yes", package], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(stdout,stderr) = p1.communicate()
	ud.debug( ud.ADMIN, ud.WARN, 'upgrade stderr=%s' % stderr)
	ud.debug( ud.ADMIN, ud.INFO, 'upgrade stdout=%s' % stdout)
	if p1.returncode != 0:
		return (p1.returncode,stderr)
	else:
		return (p1.returncode,stdout)


def uninstall_package(package):
	p1 = subprocess.Popen(["apt-get", "remove", "-o", "DPkg::Options::=--force-confold", "-y", "--force-yes", package], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(stdout,stderr) = p1.communicate()
	ud.debug( ud.ADMIN, ud.WARN, 'remove stderr=%s' % stderr)
	ud.debug( ud.ADMIN, ud.INFO, 'remove stdout=%s' % stdout)
	if p1.returncode != 0:
		return (p1.returncode,stderr)
	else:
		return (p1.returncode,stdout)

