#!/usr/share/ucs-test/runner python3
## desc: Register and deregister UDM extension via joinscript
## tags: [udm-extensions,apptest]
## roles: [domaincontroller_master,domaincontroller_backup,domaincontroller_slave,memberserver]
## exposure: dangerous
## packages:
##   - univention-config
##   - univention-directory-manager-tools
##   - shell-univention-lib

import difflib
import hashlib
import os

from univention.testing.debian_package import DebianPackage
from univention.testing.udm_extensions import (
	call_join_script, call_unjoin_script, get_absolute_extension_filename, get_dn_of_extension_by_name,
	get_extension_buffer, get_extension_filename, get_extension_name, get_join_script_buffer,
	get_package_name, get_package_version, get_unjoin_script_buffer, remove_extension_by_name,
)
from univention.testing.utils import fail, wait_for_replication

TEST_DATA = (
	('umcregistration', '32_file_integrity_udm_module.xml', '/usr/share/univention-management-console/modules/udm-%s.xml'),
	('icon', '32_file_integrity_udm_module-16.png', '/usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons/16x16/udm-%s.png'),
	('icon', '32_file_integrity_udm_module-50.png', '/usr/share/univention-management-console-frontend/js/dijit/themes/umc/icons/50x50/udm-%s.png'),
	('messagecatalog', 'it.mo', '/usr/share/locale/it/LC_MESSAGES/univention-admin-handlers-%s.mo'),
	('messagecatalog', 'de.mo', '/usr/share/locale/de/LC_MESSAGES/univention-admin-handlers-%s.mo'),
	('messagecatalog', 'es.mo', '/usr/share/locale/es/LC_MESSAGES/univention-admin-handlers-%s.mo'),
)


def test_module():
	extension_type = 'module'
	package_name = get_package_name()
	package_version = get_package_version()
	extension_name = get_extension_name(extension_type)
	extension_filename = get_extension_filename(extension_type, extension_name)

	options = {}
	buffers = {}
	for option_type, filename, target_filename in TEST_DATA:
		buffers[filename] = open('/usr/share/ucs-test/72_udm-extensions/%s' % filename, 'rb').read()
		options.setdefault(option_type, []).append('/usr/share/%s/%s' % (package_name, filename))

	joinscript_buffer = get_join_script_buffer(extension_type, '/usr/share/%s/%s' % (package_name, extension_filename), options=options, version_start='5.0-0')
	unjoinscript_buffer = get_unjoin_script_buffer(extension_type, extension_name, package_name)
	extension_buffer = get_extension_buffer(extension_type, extension_name)

	print(joinscript_buffer)

	package = DebianPackage(name=package_name, version=package_version)
	try:
		# create package and install it
		package.create_join_script_from_buffer('66%s.inst' % package_name, joinscript_buffer)
		package.create_unjoin_script_from_buffer('66%s-uninstall.uinst' % package_name, unjoinscript_buffer)
		package.create_usr_share_file_from_buffer(extension_filename, extension_buffer)
		for fn, data in buffers.items():
			package.create_usr_share_file_from_buffer(fn, data, 'wb')
		package.build()
		package.install()

		call_join_script('66%s.inst' % package_name)

		# wait until removed object has been handled by the listener
		wait_for_replication()

		dnlist = get_dn_of_extension_by_name(extension_type, extension_name)
		if not dnlist:
			fail('ERROR: cannot find UDM extension object with cn=%s in LDAP' % extension_name)

		# check if registered file has been replicated to local system
		target_fn = get_absolute_extension_filename(extension_type, extension_filename)
		if os.path.exists(target_fn):
			print('FILE REPLICATED: %r' % target_fn)
		else:
			fail('ERROR: target file %s does not exist' % target_fn)

		# check if sha1(buffer) == sha1(file)
		hash_buffer = hashlib.sha1(extension_buffer.encode('UTf-8')).hexdigest()
		hash_file = hashlib.sha1(open(target_fn, 'rb').read()).hexdigest()
		print('HASH BUFFER: %r' % hash_buffer)
		print('HASH FILE: %r' % hash_file)
		if hash_buffer != hash_file:
			print('\n'.join(difflib.context_diff(open(target_fn).read(), extension_buffer, fromfile='filename', tofile='buffer')))
			fail('ERROR: sha1 sums of file and BUFFER DIffer (fn=%s ; file=%s ; buffer=%s)' % (target_fn, hash_file, hash_buffer))

		for option_type, src_fn, filename in TEST_DATA:
			filename = filename % extension_name.replace('/', '-')
			if not os.path.exists(filename):
				fail('ERROR: file %r of type %r does not exist' % (filename, option_type))
			hash_buffer = hashlib.sha1(buffers[src_fn]).hexdigest()
			hash_file = hashlib.sha1(open(filename, 'rb').read()).hexdigest()
			if hash_buffer != hash_file:
				print('\n'.join(difflib.context_diff(open(filename).read(), buffers[src_fn], fromfile='filename', tofile='buffer')))
				fail('ERROR: sha1 sums of file and buffer differ (fn=%s ; file=%s ; buffer=%s)' % (filename, hash_file, hash_buffer))

		call_unjoin_script('66%s-uninstall.uinst' % package_name)

		# wait until removed object has been handled by the listener
		wait_for_replication()

		dnlist = get_dn_of_extension_by_name(extension_type, extension_name)
		if dnlist:
			fail('ERROR: UDM extension object with cn=%s is still present in LDAP' % extension_name)

		# check if registered file has been removed from local system
		if os.path.exists(target_fn):
			fail('ERROR: target file %s is still present' % target_fn)
		else:
			print('FILE HAS BEEN REMOVED: %r' % target_fn)

	finally:
		print('Removing UDM extension from LDAP')
		remove_extension_by_name(extension_type, extension_name, fail_on_error=False)

		print('Uninstalling binary package %r' % package_name)
		package.uninstall()

		print('Removing source package')
		package.remove()


if __name__ == '__main__':
	test_module()
