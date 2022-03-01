#!/usr/share/ucs-test/runner pytest-3 -s -l -v
# -*- coding: utf-8 -*-
## desc: Test ticket lifetime are changed successfully
## exposure: safe
## roles:
##  - domaincontroller_master
## tags: []
## packages:
##  - univention-config
## bugs: [52987]

import os

import pytest

from univention.config_registry import ConfigRegistry
from univention.config_registry.frontend import ucr_update
from univention.testing.utils import package_installed

KRB5_PATH = "/etc/krb5.conf"
SMB_PATH = "/etc/samba/smb.conf"
VALUE = "50"
key = "kerberos/defaults/ticket-lifetime"


def file_contain(file: str, text: str, no_exist_ignore: bool = True):
	if os.path.exists(file):
		with open(file, "r") as f:
			if text not in f.read():
				return -1
	elif not no_exist_ignore:
		return -2
	return 0


@pytest.fixture()
def myucr():
	# type: () -> Iterator[ConfigRegistry]
	"""
	Per `function` auto-reverting UCR instance.
	"""
	with ConfigRegistry() as ucr:
		yield ucr


def test_kerberos_lifetime(myucr):
	old_value = myucr.get(key, None)
	value = -3
	try:
		ucr_update(myucr, {
			key: VALUE,
		})
		value = file_contain(KRB5_PATH, f"ticket_lifetime = { VALUE }h")
	finally:
		ucr_update(myucr, {
			key: old_value,
		})
	assert value == 0


@pytest.mark.skipif(not package_installed('univention-samba4'), reason='Missing software: univention-samba4')
def test_samba_lifetime(myucr):
	old_value = myucr.get(key, None)
	value = -3
	try:
		ucr_update(myucr, {
			key: VALUE,
		})
		value = file_contain(SMB_PATH, f"kdc:user ticket lifetime = { VALUE }")
	finally:
		ucr_update(myucr, {
			key: old_value,
		})
	assert value == 0
