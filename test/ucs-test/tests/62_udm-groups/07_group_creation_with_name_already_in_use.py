#!/usr/share/ucs-test/runner /usr/bin/pytest-3
## desc: Create groups/group with name which is already in use
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools


import pytest

import univention.admin.objects as udm_objects
import univention.admin.modules as udm_modules
import univention.admin.uexceptions as udm_exceptions


@pytest.fixture
def ldap_database_file():
	return '07.ldif'


def test_unique_groupname_create(lo, pos):
	udm_modules.update()
	mod = udm_modules.get('groups/group')
	udm_modules.init(lo, pos, mod)

	pos.setDn('%s,%s' % ('cn=groups1', pos.getBase()))
	g1 = udm_objects.get(mod, None, lo, pos, '')
	udm_objects.open(g1)
	g1['name'] = 'group-one'
	g1.create()

	pos.setDn('%s,%s' % ('cn=groups2', pos.getBase()))
	g2 = udm_objects.get(mod, None, lo, pos, '')
	udm_objects.open(g2)
	g2['name'] = 'group-one'
	with pytest.raises(udm_exceptions.groupNameAlreadyUsed):
		g2.create()


def test_unique_groupname_modify(lo, pos):
	udm_modules.update()
	mod = udm_modules.get('groups/group')
	udm_modules.init(lo, pos, mod)

	pos.setDn('%s,%s' % ('cn=groups1', pos.getBase()))
	g1 = udm_objects.get(mod, None, lo, pos, '')
	udm_objects.open(g1)
	g1['name'] = 'group-one'
	g1.create()

	pos.setDn('%s,%s' % ('cn=groups2', pos.getBase()))
	g2 = udm_objects.get(mod, None, lo, pos, '')
	udm_objects.open(g2)
	g2['name'] = 'group-two'
	g2.create()

	g2 = mod.lookup(None, lo, 'cn=group-two')[0]
	g2['name'] = 'group-one'
	with pytest.raises(udm_exceptions.groupNameAlreadyUsed):
		g2.modify()
