# -*- coding: utf-8 -*-

from typing import List, Tuple

import pytest

from univention.testing.ucr import UCSTestConfigRegistry
import univention.testing.utils as utils
from univention.udm import NoObject, NotYetSavedError, UDM


@pytest.fixture
def ldap_base(ucr):  # type: () -> str
	return ucr["ldap/base"]


@pytest.fixture
def ucr():  # type: () -> UCSTestConfigRegistry
	with UCSTestConfigRegistry() as ucr_test:
		yield ucr_test


@pytest.fixture
def simple_udm(ucr):  # type: () -> UDM
	account = utils.UCSTestDomainAdminCredentials()
	return UDM.credentials(
		account.binddn,
		account.bindpw,
		ucr["ldap/base"],
		ucr["ldap/master"],
		ucr["ldap/master/port"],
	).version(1)


@pytest.fixture
def schedule_delete_udm_obj(simple_udm):
	objs = []  # type: List[Tuple[str, str]]

	def _func(dn, udm_mod):  # type: (str, str) -> None
		objs.append((dn, udm_mod))

	yield _func

	for dn, udm_mod_name in objs:
		mod = simple_udm.get(udm_mod_name)
		try:
			udm_obj = mod.get(dn)
		except NoObject:
			print("UDM {!r} object {!r} does not exist (anymore).".format(udm_mod_name, dn))
			continue
		try:
			udm_obj.delete(remove_childs=True)
			print("Deleted UDM {!r} object {!r} through UDM.".format(udm_mod_name, dn))
		except NotYetSavedError:
			print("UDM {!r} object {!r} not deleted, it had not been saved.".format(udm_mod_name, dn))
