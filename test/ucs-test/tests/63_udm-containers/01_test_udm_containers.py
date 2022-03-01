#!/usr/share/ucs-test/runner /usr/bin/pytest-3 -s -l -vv
# -*- coding: utf-8 -*-
## desc: Create container/ou
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools

import ldap.dn
import ldap.filter
import pytest

import univention.testing.strings as uts
import univention.testing.udm as udm_test
import univention.testing.utils as utils
from univention.testing.ucs_samba import wait_for_drs_replication


class Test_ContainerOU(object):

	def test_container_ou_creation(self, udm):
		"""Create container/ou"""
		ou = udm.create_object('container/ou', name=uts.random_name())
		utils.verify_ldap_object(ou)

	def test_container_ou_creation_with_special_characters(self, udm):
		"""Create container/ou with specials characters"""
		ou = udm.create_object('container/ou', name=uts.random_name_special_characters())
		utils.verify_ldap_object(ou)

	def test_container_ou_modification_set_description(self, udm):
		"""Set description during container/ou modification"""
		description = uts.random_string()

		ou = udm.create_object('container/ou', name=uts.random_name())

		udm.modify_object('container/ou', dn=ou, description=description)
		utils.verify_ldap_object(ou, {'description': [description]})

	def test_container_ou_modification_set_description_with_special_characters(self, udm):
		"""Set description during container/ou modification with special characters"""
		description = uts.random_string()

		ou = udm.create_object('container/ou', name=uts.random_name_special_characters())

		udm.modify_object('container/ou', dn=ou, description=description)
		utils.verify_ldap_object(ou, {'description': [description]})

	def test_container_ou_creation_set_description(self, udm):
		"""Set description during container/ou creation"""
		description = uts.random_string()

		ou = udm.create_object('container/ou', name=uts.random_name(), description=description)
		utils.verify_ldap_object(ou, {'description': [description]})

	def test_container_ou_creation_set_description_with_special_characters(self, udm):
		"""Set description during container/ou creation with special characters"""
		description = uts.random_string()

		ou = udm.create_object('container/ou', name=uts.random_name_special_characters(), description=description)
		utils.verify_ldap_object(ou, {'description': [description]})

	def test_container_ou_relocation(self, udm):
		"""Move container/ou into another container/ou"""
		ou_name = uts.random_name()

		ou = udm.create_object('container/ou', name=ou_name)
		ou2 = udm.create_object('container/ou', name=uts.random_name())

		udm.move_object('container/ou', dn=ou, position=ou2)
		utils.verify_ldap_object('ou=%s,%s' % (ldap.dn.escape_dn_chars(ou_name), ou2))

	def test_container_ou_relocation_with_special_characters(self, udm):
		"""Move container/ou into another container/ou  with special characters"""
		ou_name = uts.random_name_special_characters()

		ou = udm.create_object('container/ou', name=ou_name)
		ou2 = udm.create_object('container/ou', name=uts.random_name_special_characters())

		udm.move_object('container/ou', dn=ou, position=ou2)
		utils.verify_ldap_object('ou=%s,%s' % (ldap.dn.escape_dn_chars(ou_name), ou2))

	def test_container_ou_recursive_relocation(self, udm):
		"""Move container/ou into another container/ou and the latter one into another container/ou"""
		ou_name = uts.random_string()
		ou2_name = uts.random_string()

		ou = udm.create_object('container/ou', name=ou_name)
		ou2 = udm.create_object('container/ou', name=ou2_name)
		ou3 = udm.create_object('container/ou', name=uts.random_name())

		udm.move_object('container/ou', dn=ou, position=ou2)
		udm.move_object('container/ou', dn=ou2, position=ou3)
		utils.verify_ldap_object('ou=%s,ou=%s,%s' % (ldap.dn.escape_dn_chars(ou_name), ldap.dn.escape_dn_chars(ou2_name), ou3))

	def test_container_ou_recursive_relocation_with_special_characters(self, udm):
		"""Move container/ou into another container/ou and the latter one into another container/ou  with special characters"""
		ou_name = uts.random_name_special_characters()
		ou2_name = uts.random_name_special_characters()

		ou = udm.create_object('container/ou', name=ou_name)
		ou2 = udm.create_object('container/ou', name=ou2_name)
		ou3 = udm.create_object('container/ou', name=uts.random_name_special_characters())

		udm.move_object('container/ou', dn=ou, position=ou2)
		udm.move_object('container/ou', dn=ou2, position=ou3)
		utils.verify_ldap_object('ou=%s,ou=%s,%s' % (ldap.dn.escape_dn_chars(ou_name), ldap.dn.escape_dn_chars(ou2_name), ou3))

	def test_container_ou_recursive_removal(self, udm):
		"""Remove an container/ou recursively"""
		ou_name = uts.random_string()
		ou2_name = uts.random_string()

		ou = udm.create_object('container/ou', name=ou_name)
		ou2 = udm.create_object('container/ou', name=ou2_name)
		ou3 = udm.create_object('container/ou', name=uts.random_name())

		udm.move_object('container/ou', dn=ou, position=ou2)
		udm.move_object('container/ou', dn=ou2, position=ou3)
		ou = 'ou=%s,ou=%s,%s' % (ldap.dn.escape_dn_chars(ou_name), ldap.dn.escape_dn_chars(ou2_name), ou3)
		udm.remove_object('container/ou', dn=ou3)
		utils.verify_ldap_object(ou, should_exist=False)

	def test_container_ou_recursive_removal_with_special_characters(self, udm):
		"""Remove an container/ou recursively  with special characters"""
		ou_name = uts.random_name_special_characters()
		ou2_name = uts.random_name_special_characters()

		ou = udm.create_object('container/ou', name=ou_name)
		ou2 = udm.create_object('container/ou', name=ou2_name)
		ou3 = udm.create_object('container/ou', name=uts.random_name_special_characters())

		utils.wait_for_replication_and_postrun()

		udm.move_object('container/ou', dn=ou, position=ou2)
		udm.move_object('container/ou', dn=ou2, position=ou3)

		ou = 'ou=%s,ou=%s,%s' % (ldap.dn.escape_dn_chars(ou_name), ldap.dn.escape_dn_chars(ou2_name), ou3)
		udm.remove_object('container/ou', dn=ou3)
		utils.verify_ldap_object(ou, should_exist=False)

	@pytest.mark.tags('apptest')
	def test_container_ou_rename(self, udm, ucr):
		"""Rename a container/ou with subobjects"""
		user_name = uts.random_string()

		ou_name = uts.random_string()
		ou_name_new = uts.random_string()

		ou = udm.create_object('container/ou', name=ou_name)
		user = udm.create_user(position=ou, username=user_name)

		udm.modify_object('container/ou', dn=ou, name=ou_name_new)
		utils.verify_ldap_object(ou, should_exist=False)
		utils.verify_ldap_object(user[0], should_exist=False)

		new_ou = 'ou=%s,%s' % (ldap.dn.escape_dn_chars(ou_name_new), ucr.get('ldap/base'))
		new_user = 'uid=%s,ou=%s,%s' % (ldap.dn.escape_dn_chars(user_name), ldap.dn.escape_dn_chars(ou_name_new), ucr.get('ldap/base'))
		utils.verify_ldap_object(new_ou, should_exist=True)
		utils.verify_ldap_object(new_user, should_exist=True)

	@pytest.mark.tags('apptest')
	def test_container_ou_rename_with_special_characters(self, udm, ucr):
		"""Rename a container/ou with subobjects with special characters"""
		# bugs: [35959]
		user_name = uts.random_string()

		ou_name = uts.random_name_special_characters()
		ou_name_new = uts.random_name_special_characters()

		ou = udm.create_object('container/ou', name=ou_name)
		user = udm.create_user(position=ou, username=user_name)

		udm.modify_object('container/ou', dn=ou, name=ou_name_new)
		utils.verify_ldap_object(ou, should_exist=False)
		utils.verify_ldap_object(user[0], should_exist=False)

		new_ou = 'ou=%s,%s' % (ldap.dn.escape_dn_chars(ou_name_new), ucr.get('ldap/base'))
		new_user = 'uid=%s,ou=%s,%s' % (ldap.dn.escape_dn_chars(user_name), ldap.dn.escape_dn_chars(ou_name_new), ucr.get('ldap/base'))
		utils.verify_ldap_object(new_ou, should_exist=True)
		utils.verify_ldap_object(new_user, should_exist=True)

	@pytest.mark.tags('apptest')
	def test_container_ou_rename_uppercase(self, udm, ucr):
		"""Rename a container/ou with subobjects from lower to upper case"""
		lo = utils.get_ldap_connection()
		existing_temporary_ous = lo.searchDn(filter='ou=temporary_move_container_*')

		def test_organizational_unit(parent, add_user):
			if parent is None:
				parent = ucr.get('ldap/base')
			user_name = 'X' + uts.random_string()  # test preserving name (case sensitivity)

			ou_name = uts.random_string()
			ou_name_new = ou_name.encode('UTF-8').upper().decode('UTF-8')  # warning: u'ß'.upper() == u'SS'

			ou = udm.create_object('container/ou', position=parent, name=ou_name, wait_for=True)
			if add_user:
				udm.create_user(position=ou, username=user_name)

			try:
				udm.modify_object('container/ou', dn=ou, name=ou_name_new, wait_for=True)
			except AssertionError:
				pass
			for dn, entry in lo.search(filter='ou=temporary_move_container_*'):
				if dn not in existing_temporary_ous:
					to_be_removed = udm._cleanup.setdefault('container/ou', [])
					to_be_removed.append(dn)
				assert dn in existing_temporary_ous, 'ou = %s remained' % dn

			new_ou = 'ou=%s,%s' % (ldap.dn.escape_dn_chars(ou_name_new), parent)
			new_user = 'uid=%s,%s' % (ldap.dn.escape_dn_chars(user_name), new_ou)

			utils.verify_ldap_object(new_ou, {'ou': [ou_name_new]}, should_exist=True)
			if add_user:
				for dn, entry in lo.search(filter=ldap.filter.filter_format('uid=%s', [user_name])):
					assert entry.get('uid')[0] == user_name.encode('UTF-8'), 'CASE SENSITIVITY: uid = %s; expected: %s' % (entry.get('uid')[0], user_name)
				utils.verify_ldap_object(new_user, should_exist=True)

			return new_ou

		# EMPTY
		# FIRST LEVEL
		first_level_unit = test_organizational_unit(parent=None, add_user=False)

		# SECOND LEVEL
		test_organizational_unit(parent=first_level_unit, add_user=False)

		# WITH USER
		# FIRST LEVEL
		first_level_unit = test_organizational_unit(parent=None, add_user=True)

		# SECOND LEVEL
		test_organizational_unit(parent=first_level_unit, add_user=True)

	@pytest.mark.tags('apptest')
	def test_container_ou_rename_uppercase_with_special_characters(self, udm, ucr):
		"""Rename a container/ou with subobjects from lower to upper case with special characters"""
		# bugs: [35959]
		lo = utils.get_ldap_connection()
		existing_temporary_ous = lo.searchDn(filter='ou=temporary_move_container_*')

		def test_organizational_unit(parent, add_user):
			if parent is None:
				parent = ucr.get('ldap/base')
			user_name = 'X' + uts.random_string()  # test preserving name (case sensitivity)

			ou_name = uts.random_name_special_characters()
			ou_name_new = ou_name.encode('UTF-8').upper().decode('UTF-8')  # warning: u'ß'.upper() == u'SS'

			ou = udm.create_object('container/ou', position=parent, name=ou_name, wait_for=True)
			if add_user:
				udm.create_user(position=ou, username=user_name)

			try:
				udm.modify_object('container/ou', dn=ou, name=ou_name_new, wait_for=True)
			except AssertionError:
				pass
			for dn, entry in lo.search(filter='ou=temporary_move_container_*'):
				if dn not in existing_temporary_ous:
					to_be_removed = udm._cleanup.setdefault('container/ou', [])
					to_be_removed.append(dn)
				assert dn in existing_temporary_ous, 'ou = %s remained' % dn

			new_ou = 'ou=%s,%s' % (ldap.dn.escape_dn_chars(ou_name_new), parent)
			new_user = 'uid=%s,%s' % (ldap.dn.escape_dn_chars(user_name), new_ou)

			utils.verify_ldap_object(new_ou, {'ou': [ou_name_new]}, should_exist=True)
			if add_user:
				for dn, entry in lo.search(filter=ldap.filter.filter_format('uid=%s', [user_name])):
					assert entry.get('uid')[0] == user_name.encode('UTF-8'), 'CASE SENSITIVITY: uid = %s; expected: %s' % (entry.get('uid')[0], user_name)
				utils.verify_ldap_object(new_user, should_exist=True)

			return new_ou

		# EMPTY
		# FIRST LEVEL
		first_level_unit = test_organizational_unit(parent=None, add_user=False)

		# SECOND LEVEL
		test_organizational_unit(parent=first_level_unit, add_user=False)

		# WITH USER
		# FIRST LEVEL
		first_level_unit = test_organizational_unit(parent=None, add_user=True)

		# SECOND LEVEL
		test_organizational_unit(parent=first_level_unit, add_user=True)

	def test_container_ou_rename_uppercase_rollback(self, udm, ucr):
		"""Rename a container/ou with un-moveable subobjects from lower to upper case"""
		user_name = uts.random_string()
		network_name = uts.random_string()

		ou_name = uts.random_string()
		ou_name_new = ou_name.encode('UTF-8').upper().decode('UTF-8')  # warning: u'ß'.upper() == u'SS'

		ou = udm.create_object('container/ou', name=ou_name)
		wait_for_drs_replication('ou=%s' % ou_name)
		udm.create_user(position=ou, username=user_name)
		udm.create_object('networks/network', position=ou, name=network_name, network='1.1.1.1', netmask='24')

		with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed) as exc:
			udm.modify_object('container/ou', dn=ou, name=ou_name_new)
		# This operation is not allowed on this object: Unable to move object ayj9blkm9k (networks/network) in subtree, trying to revert changes.
		assert 'Unable to move object' in str(exc.value)

		new_ou = 'ou=%s,%s' % (ldap.dn.escape_dn_chars(ou_name_new), ucr.get('ldap/base'))
		new_user = 'uid=%s,ou=%s,%s' % (ldap.dn.escape_dn_chars(user_name), ldap.dn.escape_dn_chars(ou_name_new), ucr.get('ldap/base'))
		utils.verify_ldap_object(new_ou, should_exist=True)
		utils.verify_ldap_object(new_user, should_exist=True)

		lo = utils.get_ldap_connection()
		for dn, entry in lo.search(filter=ldap.filter.filter_format('ou=%s', [ou_name])):
			assert entry.get('ou')[0] == ou_name.encode('UTF-8'), 'ou = %s; expected: %s' % (entry.get('ou')[0], ou_name)

	def test_container_ou_rename_uppercase_rollback_with_special_characters(self, udm, ucr):
		"""Rename a container/ou with un-moveable subobjects from lower to upper case with special characters"""
		user_name = uts.random_string()
		network_name = uts.random_string()

		ou_name = uts.random_name_special_characters()
		ou_name_new = ou_name.encode('UTF-8').upper().decode('UTF-8')  # warning: u'ß'.upper() == u'SS'

		ou = udm.create_object('container/ou', name=ou_name)
		wait_for_drs_replication(ldap.filter.filter_format('ou=%s', [ou_name]))
		udm.create_user(position=ou, username=user_name)
		udm.create_object('networks/network', position=ou, name=network_name, network='1.1.1.1', netmask='24')

		with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed) as exc:
			udm.modify_object('container/ou', dn=ou, name=ou_name_new)
		# This operation is not allowed on this object: Unable to move object ayj9blkm9k (networks/network) in subtree, trying to revert changes.
		assert 'Unable to move object' in str(exc.value)

		new_ou = 'ou=%s,%s' % (ldap.dn.escape_dn_chars(ou_name_new), ucr.get('ldap/base'))
		new_user = 'uid=%s,ou=%s,%s' % (ldap.dn.escape_dn_chars(user_name), ldap.dn.escape_dn_chars(ou_name_new), ucr.get('ldap/base'))
		utils.verify_ldap_object(new_ou, should_exist=True)
		utils.verify_ldap_object(new_user, should_exist=True)

		lo = utils.get_ldap_connection()
		for dn, entry in lo.search(filter=ldap.filter.filter_format('ou=%s', (ou_name,))):
			assert entry.get('ou')[0] == ou_name.encode('UTF-8'), 'ou = %s; expected: %s' % (entry.get('ou')[0], ou_name)


class Test_ContainerCN(object):

	def test_container_cn_creation(self, udm):
		"""Create container/cn"""
		cn = udm.create_object('container/cn', name=uts.random_name())
		utils.verify_ldap_object(cn)

	def test_container_cn_creation_with_special_characters(self, udm):
		"""Create container/cn"""
		cn = udm.create_object('container/cn', name=uts.random_name_special_characters())
		utils.verify_ldap_object(cn)

	def test_container_cn_modification_set_description(self, udm):
		"""Set description during container/cn modification"""
		description = uts.random_string()

		cn_name = uts.random_name()
		cn = udm.create_object('container/cn', name=cn_name)
		wait_for_drs_replication('cn=%s' % cn_name)

		udm.modify_object('container/cn', dn=cn, description=description)
		utils.verify_ldap_object(cn, {'description': [description]})

	def test_container_cn_modification_set_description_with_special_characters(self, udm):
		"""Set description during container/cn modification special characters"""
		description = uts.random_string()

		cn_name = uts.random_name_special_characters()
		cn = udm.create_object('container/cn', name=cn_name)
		wait_for_drs_replication(ldap.filter.filter_format('cn=%s', [cn_name]))

		udm.modify_object('container/cn', dn=cn, description=description)
		utils.verify_ldap_object(cn, {'description': [description]})

	def test_container_cn_creation_set_description(self, udm):
		"""Set description during container/cn creation"""
		description = uts.random_string()

		cn = udm.create_object('container/cn', name=uts.random_name(), description=description)
		utils.verify_ldap_object(cn, {'description': [description]})

	def test_container_cn_creation_set_description_with_special_characters(self, udm):
		"""Set description during container/cn creation special characters"""
		description = uts.random_string()

		cn = udm.create_object('container/cn', name=uts.random_name_special_characters(), description=description)
		utils.verify_ldap_object(cn, {'description': [description]})

	def test_container_cn_relocation(self, udm):
		"""Move container/cn into another container/cn"""
		cn_name = uts.random_name()

		cn = udm.create_object('container/cn', name=cn_name)
		cn2 = udm.create_object('container/cn', name=uts.random_name())

		udm.move_object('container/cn', dn=cn, position=cn2)
		utils.verify_ldap_object('cn=%s,%s' % (ldap.dn.escape_dn_chars(cn_name), cn2))

	def test_container_cn_relocation_with_special_characters(self, udm):
		"""Move container/cn into another container/cn special characters"""
		cn_name = uts.random_name_special_characters()

		cn = udm.create_object('container/cn', name=cn_name)
		cn2 = udm.create_object('container/cn', name=uts.random_name_special_characters())

		udm.move_object('container/cn', dn=cn, position=cn2)
		utils.verify_ldap_object('cn=%s,%s' % (ldap.dn.escape_dn_chars(cn_name), cn2))

	@pytest.mark.tags('apptest')
	def test_container_cn_recursive_relocation(self, udm):
		"""Move container/cn into another container/cn and the latter one into another container/cn"""
		cn_name = uts.random_string()
		cn2_name = uts.random_string()

		cn = udm.create_object('container/cn', name=cn_name)
		cn2 = udm.create_object('container/cn', name=cn2_name)
		cn3 = udm.create_object('container/cn', name=uts.random_name())

		udm.move_object('container/cn', dn=cn, position=cn2)
		udm.move_object('container/cn', dn=cn2, position=cn3)
		utils.verify_ldap_object('cn=%s,cn=%s,%s' % (ldap.dn.escape_dn_chars(cn_name), ldap.dn.escape_dn_chars(cn2_name), cn3))

	def test_container_cn_recursive_relocation_with_special_characters(self, udm):
		"""Move container/cn into another container/cn and the latter one into another container/cn special characters"""
		cn_name = uts.random_name_special_characters()
		cn2_name = uts.random_name_special_characters()

		cn = udm.create_object('container/cn', name=cn_name)
		cn2 = udm.create_object('container/cn', name=cn2_name)
		cn3 = udm.create_object('container/cn', name=uts.random_name_special_characters())

		udm.move_object('container/cn', dn=cn, position=cn2)
		udm.move_object('container/cn', dn=cn2, position=cn3)
		utils.verify_ldap_object('cn=%s,cn=%s,%s' % (ldap.dn.escape_dn_chars(cn_name), ldap.dn.escape_dn_chars(cn2_name), cn3))

	def test_container_cn_recursive_removal(self, udm):
		"""Remove container/cn recursively"""
		cn_name = uts.random_string()
		cn2_name = uts.random_string()

		cn = udm.create_object('container/cn', name=cn_name)
		cn2 = udm.create_object('container/cn', name=cn2_name)
		cn3 = udm.create_object('container/cn', name=uts.random_name())

		udm.move_object('container/cn', dn=cn, position=cn2)
		udm.move_object('container/cn', dn=cn2, position=cn3)
		cn = 'cn=%s,cn=%s,%s' % (ldap.dn.escape_dn_chars(cn_name), ldap.dn.escape_dn_chars(cn2_name), cn3)

		udm.remove_object('container/cn', dn=cn3)
		utils.verify_ldap_object(cn, should_exist=False)

	def test_container_cn_recursive_removal_with_special_characters(self, udm):
		"""Remove container/cn recursively special characters"""
		cn_name = uts.random_name_special_characters()
		cn2_name = uts.random_name_special_characters()

		cn = udm.create_object('container/cn', name=cn_name)
		cn2 = udm.create_object('container/cn', name=cn2_name)
		cn3 = udm.create_object('container/cn', name=uts.random_name_special_characters())

		udm.move_object('container/cn', dn=cn, position=cn2)
		udm.move_object('container/cn', dn=cn2, position=cn3)
		cn = 'cn=%s,cn=%s,%s' % (ldap.dn.escape_dn_chars(cn_name), ldap.dn.escape_dn_chars(cn2_name), cn3)

		udm.remove_object('container/cn', dn=cn3)
		utils.verify_ldap_object(cn, should_exist=False)

	@pytest.mark.tags('apptest')
	def test_container_cn_rename(self, udm, ucr):
		"""Rename a container/cn with subobjects"""
		user_name = uts.random_string()

		cn_name = uts.random_string()
		cn_name_new = uts.random_string()

		cn = udm.create_object('container/cn', name=cn_name)
		user = udm.create_user(position=cn, username=user_name)

		udm.modify_object('container/cn', dn=cn, name=cn_name_new)
		utils.verify_ldap_object(cn, should_exist=False)
		utils.verify_ldap_object(user[0], should_exist=False)

		new_cn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(cn_name_new), ucr.get('ldap/base'))
		new_user = 'uid=%s,cn=%s,%s' % (user_name, cn_name_new, ucr.get('ldap/base'))
		utils.verify_ldap_object(new_cn, should_exist=True)
		utils.verify_ldap_object(new_user, should_exist=True)

	@pytest.mark.tags('apptest')
	def test_container_cn_rename_with_special_characters(self, udm, ucr):
		"""Rename a container/cn with subobjects"""
		user_name = uts.random_string()

		cn_name = uts.random_name_special_characters()
		cn_name_new = uts.random_name_special_characters()

		cn = udm.create_object('container/cn', name=cn_name)
		user = udm.create_user(position=cn, username=user_name)

		udm.modify_object('container/cn', dn=cn, name=cn_name_new)
		utils.verify_ldap_object(cn, should_exist=False)
		utils.verify_ldap_object(user[0], should_exist=False)

		new_cn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(cn_name_new), ucr.get('ldap/base'))
		new_user = 'uid=%s,cn=%s,%s' % (ldap.dn.escape_dn_chars(user_name), ldap.dn.escape_dn_chars(cn_name_new), ucr.get('ldap/base'))
		utils.verify_ldap_object(new_cn, should_exist=True)
		utils.verify_ldap_object(new_user, should_exist=True)

	@pytest.mark.tags('apptest')
	def test_container_cn_rename_uppercase(self, udm, ucr):
		"""Rename a container/cn with subobjects from lower to upper case"""
		def test_container(parent, add_user):
			if parent is None:
				parent = ucr.get('ldap/base')
			user_name = 'X' + uts.random_string()  # test preserving name (case sensitivity)

			cn_name = uts.random_string()
			cn_name_new = cn_name.encode('UTF-8').upper().decode('UTF-8')  # warning: u'ß'.upper() == u'SS'

			cn = udm.create_object('container/cn', position=parent, name=cn_name)
			if add_user:
				udm.create_user(position=cn, username=user_name)

			try:
				udm.modify_object('container/cn', dn=cn, name=cn_name_new)
			except AssertionError:
				pass
			lo = utils.get_ldap_connection()
			for dn, entry in lo.search(filter='ou=temporary_move_container_*'):
				to_be_removed = udm._cleanup.setdefault('container/ou', [])
				to_be_removed.append(dn)
				assert False, 'ou = %s remained' % dn

			new_cn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(cn_name_new), parent)
			new_user = 'uid=%s,%s' % (ldap.dn.escape_dn_chars(user_name), new_cn)

			utils.verify_ldap_object(new_cn, should_exist=True)
			if add_user:
				for dn, entry in lo.search(filter=ldap.filter.filter_format('uid=%s', [user_name, ])):
					assert entry.get('uid')[0] == user_name.encode('UTF-8'), 'CASE SENSITIVITY: uid = %s; expected: %s' % (entry.get('uid')[0], user_name)
				utils.verify_ldap_object(new_user, should_exist=True)

			for dn, entry in lo.search(filter=ldap.filter.filter_format('cn=%s', [cn_name_new])):
				assert entry.get('cn')[0] == cn_name_new.encode('UTF-8'), 'cn = %s; expected: %s' % (entry.get('cn')[0], cn_name_new)
			return new_cn

		# EMPTY
		# FIRST LEVEL
		first_level_container = test_container(parent=None, add_user=False)

		# SECOND LEVEL
		test_container(parent=first_level_container, add_user=False)

		# WITH USER
		# FIRST LEVEL
		first_level_container = test_container(parent=None, add_user=True)

		# SECOND LEVEL
		test_container(parent=first_level_container, add_user=True)

	@pytest.mark.tags('apptest')
	def test_container_cn_rename_uppercase_with_special_characters(self, udm, ucr):
		"""Rename a container/cn with subobjects from lower to upper case"""
		if utils.package_installed('univention-s4-connector'):
			# this test is not stable with the s4-connector
			# somehow we end up with
			#
			# Creating container/cn object with /usr/sbin/udm-test container/cn create --position dc=four,dc=four --set 'name=ĝkn}_>ä%\6'
			# Waiting for connector replication
			# Modifying container/cn object with /usr/sbin/udm-test container/cn modify --dn 'cn=ĝkn}_\>ä%\\6,dc=four,dc=four' --set 'name=ĝKN}_>ä%\6'
			# modrdn detected: 'cn=\xc4\x9dkn}_\\>\xc3\xa4%\\\\6,dc=four,dc=four' ==> 'cn=\xc4\x9dKN}_\\>\xc3\xa4%\\\\6,dc=four,dc=four'
			# Waiting for connector replication
			# ### FAIL ###
			# #cn = ĝkn}_>ä%\6; expected: ĝKN}_>ä%\6
			pytest.skip('S4-Connector')

		def test_container(parent, add_user):
			if parent is None:
				parent = ucr.get('ldap/base')
			user_name = 'X' + uts.random_string()  # test preserving name (case sensitivity)

			cn_name = uts.random_name_special_characters()
			cn_name_new = cn_name.encode('UTF-8').upper().decode('UTF-8')  # warning: u'ß'.upper() == u'SS'

			cn = udm.create_object('container/cn', position=parent, name=cn_name)
			if add_user:
				udm.create_user(position=cn, username=user_name)

			try:
				udm.modify_object('container/cn', dn=cn, name=cn_name_new)
			except AssertionError:
				pass
			lo = utils.get_ldap_connection()
			for dn, entry in lo.search(filter='ou=temporary_move_container_*'):
				to_be_removed = udm._cleanup.setdefault('container/ou', [])
				to_be_removed.append(dn)
				assert False, 'ou = %s remained' % dn

			new_cn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(cn_name_new), parent)
			new_user = 'uid=%s,%s' % (ldap.dn.escape_dn_chars(user_name), new_cn)

			utils.verify_ldap_object(new_cn, should_exist=True)
			if add_user:
				for dn, entry in lo.search(filter=ldap.filter.filter_format('uid=%s', [user_name])):
					assert entry.get('uid')[0] == user_name.encode('UTF-8'), 'CASE SENSITIVITY: uid = %s; expected: %s' % (entry.get('uid')[0], user_name)
				utils.verify_ldap_object(new_user, should_exist=True)

			for dn, entry in lo.search(filter=ldap.filter.filter_format('cn=%s', [cn_name_new])):
				assert entry.get('cn')[0] == cn_name_new.encode('UTF-8'), 'cn = %s; expected: %s' % (entry.get('cn')[0], cn_name_new)
			return new_cn

		# EMPTY
		# FIRST LEVEL
		first_level_container = test_container(parent=None, add_user=False)

		# SECOND LEVEL
		test_container(parent=first_level_container, add_user=False)

		# WITH USER
		# FIRST LEVEL
		first_level_container = test_container(parent=None, add_user=True)

		# SECOND LEVEL
		test_container(parent=first_level_container, add_user=True)

	def test_container_cn_rename_uppercase_rollback(self, udm, ucr):
		"""Rename a container/cn with un-moveable subobjects from lower to upper case"""
		user_name = uts.random_string()
		network_name = uts.random_string()

		cn_name = uts.random_string()
		cn_name_new = cn_name.encode('UTF-8').upper().decode('UTF-8')  # warning: u'ß'.upper() == u'SS'

		cn = udm.create_object('container/cn', name=cn_name)
		wait_for_drs_replication('cn=%s' % cn_name)
		udm.create_user(position=cn, username=user_name)
		udm.create_object('networks/network', position=cn, name=network_name, network='1.1.1.1', netmask='24')

		with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
			udm.modify_object('container/cn', dn=cn, name=cn_name_new)

		new_cn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(cn_name_new), ucr.get('ldap/base'))
		new_user = 'uid=%s,cn=%s,%s' % (ldap.dn.escape_dn_chars(user_name), ldap.dn.escape_dn_chars(cn_name_new), ucr.get('ldap/base'))
		utils.verify_ldap_object(new_cn, should_exist=True)
		utils.verify_ldap_object(new_user, should_exist=True)

		lo = utils.get_ldap_connection()
		for dn, entry in lo.search(filter=ldap.filter.filter_format('cn=%s', [cn_name])):
			assert entry.get('cn')[0] == cn_name.encode('UTF-8'), 'cn = %s; expected: %s' % (entry.get('cn')[0], cn_name)

	def test_container_cn_rename_uppercase_rollback_with_special_characters(self, udm, ucr):
		"""Rename a container/cn with un-moveable subobjects from lower to upper case special characters"""
		user_name = uts.random_string()
		network_name = uts.random_string()

		cn_name = uts.random_name_special_characters()
		cn_name_new = cn_name.encode('UTF-8').upper().decode('UTF-8')  # warning: u'ß'.upper() == u'SS'

		cn = udm.create_object('container/cn', name=cn_name)
		wait_for_drs_replication(ldap.filter.filter_format('cn=%s', [cn_name]))
		udm.create_user(position=cn, username=user_name)
		udm.create_object('networks/network', position=cn, name=network_name, network='1.1.1.1', netmask='24')

		with pytest.raises(udm_test.UCSTestUDM_ModifyUDMObjectFailed):
			udm.modify_object('container/cn', dn=cn, name=cn_name_new)

		utils.wait_for_replication_and_postrun()
		new_cn = 'cn=%s,%s' % (ldap.dn.escape_dn_chars(cn_name_new), ucr.get('ldap/base'))
		new_user = 'uid=%s,cn=%s,%s' % (ldap.dn.escape_dn_chars(user_name), ldap.dn.escape_dn_chars(cn_name_new), ucr.get('ldap/base'))
		utils.verify_ldap_object(new_cn, should_exist=True)
		utils.verify_ldap_object(new_user, should_exist=True)

		lo = utils.get_ldap_connection()
		for dn, entry in lo.search(filter=ldap.filter.filter_format('cn=%s', [cn_name])):
			assert entry.get('cn')[0] == cn_name.encode('UTF-8'), 'cn = %s; expected: %s' % (entry.get('cn')[0], cn_name)


class Test_StandardContainer(object):

	@pytest.mark.dangerous
	def test_object_move_and_standard_container_modify(self, udm):
		"""move the object and modify the standard container flag at the same time"""
		# bugs: [41694]
		# exposure: dangerous

		lo = utils.get_ldap_connection()

		for object_type in ('container/cn', 'container/ou'):
			defalt_containers = 'cn=default containers,%s' % (udm.UNIVENTION_CONTAINER,)
			print('testing', object_type)
			computerPath = lo.getAttr(defalt_containers, 'univentionComputersObject')
			userPath = lo.getAttr(defalt_containers, 'univentionUsersObject')

			utils.verify_ldap_object(defalt_containers, {'univentionUsersObject': userPath, 'univentionComputersObject': computerPath})
			old_dn = udm.create_object(object_type, **{'name': uts.random_string(), 'computerPath': '1'})
			computerPath.append(old_dn)

			utils.verify_ldap_object(defalt_containers, {'univentionUsersObject': userPath, 'univentionComputersObject': computerPath})

			new_dn = udm.modify_object(object_type, **{'name': uts.random_string(), 'dn': old_dn, 'computerPath': '0', 'userPath': '1'})
			computerPath.remove(old_dn)
			userPath.append(new_dn)
			utils.verify_ldap_object(defalt_containers, {'univentionUsersObject': userPath, 'univentionComputersObject': computerPath})
