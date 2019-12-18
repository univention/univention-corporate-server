#!/usr/share/ucs-test/runner /usr/bin/py.test -s
# coding: utf-8
## desc: "Test the UCS<->AD sync in {read,write,sync} mode for `con_other_attribute`s."
## exposure: dangerous
## packages:
## - univention-s4-connector
## bugs:
##  - 35903
##  - 36480
##  - 45252
## versions:
##  4.2-2: skip

# We skip this since 4.2-2, as the corresponding implementation is not yet committed.
# See https://forge.univention.org/bugzilla/show_bug.cgi?id=45252.

from __future__ import print_function

import pytest

from univention.testing.udm import UCSTestUDM
import univention.testing.connector_common as tcommon
from univention.testing.connector_common import (NormalUser, create_udm_user,
	delete_udm_user, create_con_user, delete_con_user)

import s4connector
from s4connector import (connector_running_on_this_host, connector_setup)

MAPPINGS = (
	# ucs_attribute, con_attribute, con_other_attribute
	('phone', 'telephoneNumber', 'otherTelephone'),
	('homeTelephoneNumber', 'homePhone', 'otherHomePhone'),
	('mobileTelephoneNumber', 'mobile', 'otherMobile'),
	('pagerTelephoneNumber', 'pager', 'otherPager'),
)


def random_number():
	return tcommon.random_string(numeric=True)


# General Information: In Active Directory, for attributes that are split in
# two (e.g. `telephoneNumber` and `otherTelephone`), the administrator is
# responsible for keeping a value in `telephoneNumber`. Imagine the following:
# (a) telephoneNumber = '123', otherTelephone = ['123', '456']
# In this case, if the administrator deletes the value of `telephoneNumber`,
# Active Directory does NOT automatically pull a new value from `otherTelephone`.
#
# This is impossible to support with the connector. Imagine again case (a). If
# we delete `123` from `phone` via UDM, AD would be synced into the following
# state: (b) telephoneNumber = [], otherTelephone = ['456']
# From now on, whenever we add a new value to `phone` via UDM, for example:
# (c) phone = ['456', '789'] it MUST be synced as
# (d) telephoneNumber = [], otherTelephone = ['456', '789'] as '456' came
# before '789' and '456' is definitely in `otherTelephone`.
#
# These tests enforce, that `telephoneNumber` is never empty, as long as there
# are values in `otherTelephone`. If a modification would delete the value of
# `telephoneNumber` and at least one value exists in `otherTelephone`, the
# connector duplicates the first entry of `otherTelephone` into
# `telephoneNumber`.


@pytest.mark.parametrize("attribute", MAPPINGS)
@pytest.mark.parametrize("sync_mode", ["write", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_attribute_sync_from_udm_to_s4(attribute, sync_mode):
	(ucs_attribute, con_attribute, con_other_attribute) = attribute
	udm_user = NormalUser(selection=("username", "lastname", ucs_attribute))
	primary_value = udm_user.basic.get(ucs_attribute)
	all_values = (primary_value, random_number(), random_number())
	secondary_values = all_values[1:]

	with connector_setup(sync_mode) as s4, UCSTestUDM() as udm:
		# A single `phone` number must be synced to `telephoneNumber` in AD.
		(udm_user_dn, s4_user_dn) = create_udm_user(udm, s4, udm_user, s4connector.wait_for_sync)

		# Additional `phone` values must be synced to `otherTelephone`,
		# `telephoneNumber` must keep its value.
		print("\nModifying UDM user: {}={}\n".format(ucs_attribute, all_values))
		udm.modify_object('users/user', dn=udm_user_dn, set={ucs_attribute: all_values})
		s4connector.wait_for_sync()
		s4.verify_object(s4_user_dn,
			{con_attribute: primary_value, con_other_attribute: secondary_values})
		tcommon.verify_udm_object("users/user", udm_user_dn, {ucs_attribute: all_values})

		# If we delete the first `phone` value via UDM, we want to duplicate
		# the first value of `otherTelephone` into `telephoneNumber`.
		(new_primary, next_primary) = secondary_values
		print("\nModifying UDM user: {}={}\n".format(ucs_attribute, secondary_values))
		udm.modify_object('users/user', dn=udm_user_dn, set={ucs_attribute: secondary_values})
		s4connector.wait_for_sync()
		s4.verify_object(s4_user_dn,
			{con_attribute: new_primary, con_other_attribute: secondary_values})
		tcommon.verify_udm_object("users/user", udm_user_dn, {ucs_attribute: secondary_values})

		# If we delete a `phone` value via UDM that is duplicated in AD, we want
		# it to be deleted from `telephoneNumber` and `otherTelephone`.
		print("\nModifying UDM user: {}={}\n".format(ucs_attribute, next_primary))
		udm.modify_object('users/user', dn=udm_user_dn, set={ucs_attribute: next_primary})
		s4connector.wait_for_sync()
		s4.verify_object(s4_user_dn,
			{con_attribute: next_primary, con_other_attribute: next_primary})
		tcommon.verify_udm_object("users/user", udm_user_dn, {ucs_attribute: next_primary})

		# Setting a completely new `phone` value via UDM, this must be synced
		# to `telephoneNumber` and `otherTelephone` must be empty.
		new_phone_who_dis = random_number()
		print("\nModifying UDM user: {}={}\n".format(ucs_attribute, new_phone_who_dis))
		udm.modify_object('users/user', dn=udm_user_dn, set={ucs_attribute: new_phone_who_dis})
		s4connector.wait_for_sync()
		s4.verify_object(s4_user_dn, {con_attribute: new_phone_who_dis, con_other_attribute: []})
		tcommon.verify_udm_object("users/user", udm_user_dn, {ucs_attribute: new_phone_who_dis})

		# No `phone` value via UDM, must result in an empty `telephoneNumber`
		# and `otherTelephone`.
		print("\nModifying UDM user: {}={}\n".format(ucs_attribute, []))
		udm.modify_object('users/user', dn=udm_user_dn, set={ucs_attribute: ''})
		s4connector.wait_for_sync()
		s4.verify_object(s4_user_dn, {con_attribute: [], con_other_attribute: []})
		tcommon.verify_udm_object("users/user", udm_user_dn, {ucs_attribute: []})

		delete_udm_user(udm, s4, udm_user_dn, s4_user_dn, s4connector.wait_for_sync)


@pytest.mark.parametrize("attribute", MAPPINGS)
@pytest.mark.parametrize("sync_mode", ["read", "sync"])
@pytest.mark.skipif(not connector_running_on_this_host(),
	reason="Univention S4 Connector not configured.")
def test_attribute_sync_from_s4_to_udm(attribute, sync_mode):
	(ucs_attribute, con_attribute, con_other_attribute) = attribute
	udm_user = NormalUser(selection=("username", "lastname", ucs_attribute))
	primary_value = udm_user.basic.get(ucs_attribute)
	all_values = (primary_value, random_number(), random_number())
	secondary_values = all_values[1:]

	with connector_setup(sync_mode) as s4:
		# A single `telephoneNumber` must be synced to `phone` in UDM.
		(basic_s4_user, s4_user_dn, udm_user_dn) = create_con_user(s4,
			udm_user, s4connector.wait_for_sync)

		# Additional values in `otherTelephone` must be appended to `phone`.
		print("\nModifying S4 user: {}={}, {}={}\n".format(con_attribute,
			primary_value, con_other_attribute, secondary_values))
		s4.set_attributes(s4_user_dn,
			**{con_attribute: primary_value, con_other_attribute: secondary_values})
		s4connector.wait_for_sync()
		tcommon.verify_udm_object("users/user", udm_user_dn, {ucs_attribute: all_values})
		s4.verify_object(s4_user_dn,
			{con_attribute: primary_value, con_other_attribute: secondary_values})

		if sync_mode == "sync":  # otherwise the connector can't write into AD
			# If we delete the value of `telephoneNumber` from AD, we expect to get
			# the first value of `otherTelephone` duplicated into
			# `telephoneNumber`.
			(new_primary, _) = secondary_values
			print("\nModifying S4 user: {}={}\n".format(con_attribute, []))
			s4.set_attributes(s4_user_dn, **{con_attribute: []})
			s4connector.wait_for_sync()
			tcommon.verify_udm_object("users/user", udm_user_dn, {ucs_attribute: secondary_values})
			s4.verify_object(s4_user_dn,
				{con_attribute: new_primary, con_other_attribute: secondary_values})

			# Deleting the duplicate from `otherTelephone` must retain the value of
			# `telephoneNumber` and `phone` in UDM.
			print("\nModifying S4 user: {}={}\n".format(con_other_attribute, []))
			s4.set_attributes(s4_user_dn, **{con_other_attribute: []})
			s4connector.wait_for_sync()
			tcommon.verify_udm_object("users/user", udm_user_dn, {ucs_attribute: new_primary})
			s4.verify_object(s4_user_dn,
				{con_attribute: new_primary, con_other_attribute: []})

		# Setting a new `telephoneNumber` and no `otherTelephone` in AD must
		# result in a single new value in `phone`.
		new_phone_who_dis = random_number()
		print("\nModifying S4 user: {}={}\n".format(con_attribute, new_phone_who_dis))
		s4.set_attributes(s4_user_dn, **{con_attribute: new_phone_who_dis, con_other_attribute: []})
		s4connector.wait_for_sync()
		tcommon.verify_udm_object("users/user", udm_user_dn, {ucs_attribute: new_phone_who_dis})
		s4.verify_object(s4_user_dn,
			{con_attribute: new_phone_who_dis, con_other_attribute: []})

		# Setting no `telephoneNumber` and no `otherTelephone` in AD must
		# result in no value in `phone`.
		print("\nModifying S4 user: {}={}\n".format(con_attribute, []))
		s4.set_attributes(s4_user_dn, **{con_attribute: [], con_other_attribute: []})
		s4connector.wait_for_sync()
		tcommon.verify_udm_object("users/user", udm_user_dn, {ucs_attribute: []})
		s4.verify_object(s4_user_dn, {con_attribute: [], con_other_attribute: []})

		delete_con_user(s4, s4_user_dn, udm_user_dn, s4connector.wait_for_sync)
