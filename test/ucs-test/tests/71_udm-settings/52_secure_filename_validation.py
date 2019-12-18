#!/usr/share/ucs-test/runner /usr/bin/py.test -s
## desc: Creates Schema and ACL extensions in invalid paths
## bugs: [41780]
## roles:
##  - domaincontroller_master
## packages:
##   - univention-config
## exposure: dangerous

from __future__ import print_function

import bz2
import os.path

import pytest
import ldap.dn

import univention.testing.udm as udm_test
from univention.testing import utils, strings


# TODO: add a test case for subdirectories
@pytest.mark.parametrize('modify', [False, True])
@pytest.mark.parametrize('prefix', ['/', '../../../../../../../../../'])
@pytest.mark.parametrize('path,position,attr,ocs', [
	('/var/lib/univention-ldap/local-schema', 'cn=ldapschema,cn=univention', 'univentionLDAPSchemaFilename', 'univentionLDAPExtensionSchema'),
	('/etc/univention/templates/files/etc/ldap/slapd.conf.d/', 'cn=ldapacl,cn=univention', 'univentionLDAPACLFilename', 'univentionLDAPExtensionACL')
])
@pytest.mark.parametrize('name', ['etc/passwd3'])
def test_filename_validation(modify, prefix, path, position, attr, ocs, name):
	lo = utils.get_ldap_connection()
	with udm_test.UCSTestUDM() as udm:
		pos = '%s,%s' % (position, udm.LDAP_BASE,)
		filename = filename_modify = '%s%s%s' % (prefix, name, strings.random_string())
		if modify:
			dn_modify = '%s=%s,%s' % (attr, ldap.dn.escape_dn_chars(filename), pos)
			filename = filename.replace('/', '').replace('.', '')
		dn = '%s=%s,%s' % (attr, ldap.dn.escape_dn_chars(filename), pos)
		fullpath = os.path.join(path, filename)
		fullpath_modify = os.path.join(path, filename_modify)
		attrs = {
			attr: [filename],
			'cn': [filename],
			'objectClass': ['top', 'univentionObjectMetadata', ocs],
			'univentionOwnedByPackage': ['foo'],
			'univentionOwnedByPackageVersion': ['1'],
			attr.replace('Filename', 'Data'): [bz2.compress('\n' if modify else 'root:$6$5cAInBgG$7rdZuEujGK1QFoprcNspXsXHsymW3Txp0kDyHFsE.omI.3T0xek3KIneFPZ99Z8dwZnZ2I2O/Tk8x4mNNGSE4.:16965:0:99999:7:::')],
			attr.replace('Filename', 'Active'): ['TRUE'],
		}
		al = [(key, [v for v in val]) for key, val in attrs.items()]
		print(('Creating', dn))
		dn = lo.add(dn, al) or dn
		try:
			utils.wait_for_replication_and_postrun()
			if modify:
				assert os.path.exists(fullpath)
				if ocs == 'univentionLDAPExtensionACL':
					assert os.path.exists(fullpath + '.info')

				print(('Modifying into', dn_modify))
				dn = lo.modify(dn, [
					(attr, filename, filename_modify),
					('cn', filename, filename_modify),
				]) or dn
				print(('Modified', dn))
				assert dn == dn_modify
				utils.wait_for_replication_and_postrun()

			# object was renamed (if modify). make sure the old files do not exists anymore.
			assert not os.path.exists(fullpath_modify), err(fullpath_modify)
			assert not os.path.exists(fullpath), err(fullpath)
			if ocs == 'univentionLDAPExtensionACL':
				assert not os.path.exists(fullpath + '.info'), err(fullpath + '.info')
				assert not os.path.exists(fullpath_modify + '.info'), err(fullpath_modify + '.info')

			# create fake files and see if the listener would remove them.
			with open(fullpath_modify, 'w') as fd:
				fd.write('TEMP')
			if ocs == 'univentionLDAPExtensionACL':
				with open(fullpath_modify + '.info', 'w') as fd:
					fd.write('TEMP')
		finally:
			lo.delete(dn)

		utils.wait_for_replication_and_postrun()
		assert os.path.exists(fullpath_modify), err(fullpath_modify)
		assert 'TEMP' in err(fullpath_modify)
		os.unlink(fullpath_modify)
		if ocs == 'univentionLDAPExtensionACL':
			assert os.path.exists(fullpath_modify + '.info'), err(fullpath_modify)
			assert 'TEMP' in err(fullpath_modify + '.info')
			os.unlink(fullpath_modify + '.info')


def err(filename):
	return '%r exists (content=%r)' % (filename, open(filename).read())
