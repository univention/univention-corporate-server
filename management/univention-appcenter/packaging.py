from distutils.core import setup as orig_setup

from debian.deb822 import Deb822
from debian.changelog import Changelog

def _get_version():
	changelog = Changelog(open('debian/changelog'))
	return changelog.full_version

def _get_description(name):
	contents = open('debian/control').read().split('\n\n')
	for content in contents:
		package = Deb822(content)
		if 'Package' in package and package['Package'] == name:
			if 'Description' in package:
				description = package['Description']
				if '\n .\n' in description:
					return description.split('\n .\n')[0]
				return description
			return None

def setup(name, **attrs):
	if 'name' not in attrs:
		attrs['name'] = name
	if 'license' not in attrs:
		attrs['license'] = 'AGPL'
	if 'author_email' not in attrs:
		attrs['author_email'] = 'packages@univention.de'
	if 'author' not in attrs:
		attrs['author'] = 'Univention GmbH'
	if 'url' not in attrs:
		attrs['url'] = 'http://www.univention.de/'
	if 'version' not in attrs:
		attrs['version'] = _get_version()
	if 'description' not in attrs:
		attrs['description'] = _get_description(name)
	print attrs
	return orig_setup(**attrs)
