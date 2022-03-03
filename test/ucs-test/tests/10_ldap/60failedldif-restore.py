#!/usr/share/ucs-test/runner pytest-3 -s
## desc: Checking whether failed.ldif will be restored.
## tags:
##  - replication
## roles:
##  - domaincontroller_backup
##  - domaincontroller_slave
## exposure: dangerous

import os
import subprocess
import time
from contextlib import contextmanager

import ldap
import pytest

from univention.config_registry import handler_set
from univention.testing import utils
from univention.testing.strings import random_name
from univention.testing.ucr import UCSTestConfigRegistry
from univention.testing.udm import UCSTestUDM

LDIF_TIMEOUT = 5
ldif_folder = '/var/lib/univention-directory-replication'
failed_ldif = os.path.join(ldif_folder, 'failed.ldif')


@pytest.fixture(scope="module", autouse=True)
def activate_quick_ldif_mode():
	with UCSTestConfigRegistry() as ucr:
		handler_set(['listener/ldap/retries=0', 'replication/ldap/retries=0'])
		subprocess.check_call(['systemctl', 'restart', 'univention-directory-listener'])
		yield ucr
	subprocess.check_call(['systemctl', 'restart', 'univention-directory-listener'])


@pytest.fixture
def udm():
	with UCSTestUDM() as udm:
		yield udm


@contextmanager
def local_ldap_down():
	subprocess.check_call(['systemctl', 'stop', 'slapd'])
	try:
		time.sleep(1)
		yield
	finally:
		subprocess.check_call(['systemctl', 'start', 'slapd'])
	time.sleep(1)


def __check_action_failure(udm, verify_args):
	ldif_timer = 0
	while not os.path.isfile(failed_ldif):
		time.sleep(1)
		ldif_timer += 1
		if ldif_timer > LDIF_TIMEOUT:
			pytest.fail('no failed.ldif created')
	try:
		udm.verify_udm_object(*verify_args)
	except ldap.SERVER_DOWN:
		pass
	else:
		pytest.fail('wrong ldap server or not down?')


def test_modify_ldif(udm, name=random_name()):
	dn = udm.create_object('container/cn', name=random_name(), description='will be modified')
	with local_ldap_down():
		udm.modify_object('container/cn', dn=dn, description='has been modified', wait_for_replication=False)
		verify_args = ('container/cn', dn, {'description': 'has been modified'})
		__check_action_failure(udm, verify_args)
	utils.wait_for_replication()
	udm.verify_udm_object(*verify_args)


def test_modify_utf8_ldif(udm):
	test_modify_ldif(udm, random_name() + '☃')


def test_remove_ldif(udm):
	dn = udm.create_object('container/cn', name=random_name(), description='will be removed')
	with local_ldap_down():
		udm.remove_object('container/cn', dn=dn, wait_for_replication=False)
		verify_args = ('container/cn', dn, None)
		__check_action_failure(udm, verify_args)
	utils.wait_for_replication()
	udm.verify_udm_object(*verify_args)


def test_create_ldif(udm):
	with local_ldap_down():
		dn = udm.create_object('container/cn', name=random_name(), description='has been created', wait_for_replication=False)
		verify_args = ('container/cn', dn, {'description': 'has been created'})
		__check_action_failure(udm, verify_args)
	utils.wait_for_replication()
	udm.verify_udm_object(*verify_args)
