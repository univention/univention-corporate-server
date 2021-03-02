#!/usr/share/ucs-test/runner /usr/bin/pytest -l -v
## desc: Test unionmap
## tags: [udm,apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-config
##   - univention-directory-manager-tools
##   - univention-mail-server

# pylint: disable=attribute-defined-outside-init

from __future__ import print_function

import pytest
import univention.testing.strings as uts
import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test
import univention.testing.utils as utils
from essential.mail import send_mail, check_delivery, create_shared_mailfolder, imap_search_mail, random_email, make_token, set_mail_forward_copy_to_self_ucrv

with ucr_test.UCSTestConfigRegistry() as ucr:
	DOMAIN = ucr.get("domainname").lower()
	HOSTNAME = ucr.get("hostname")
	FQDN = "%s.%s" % (HOSTNAME, DOMAIN)

DEBUG_LEVEL = 1
set_mail_forward_copy_to_self_ucrv('yes')


class Bunch(object):
	def __init__(self, **kwargs):
		self.__dict__.update(kwargs)

	def __str__(self):
		result = []
		for key, value in self.__dict__.items():
			result.append("%s=%r" % (key, value))
		return "Bunch(" + ", ".join(result) + ")"

	def __repr__(self):
		return str(self)


def random_mail_user(udm, mail_alternative_address=None):
	if mail_alternative_address is None:
		mail_alternative_address = random_email()
	user = Bunch()
	user.mailPrimaryAddress = random_email()
	user.mailAlternativeAddress = mail_alternative_address
	user.mailHomeServer = FQDN
	user.dn, user.username = udm.create_user(set={
		"mailHomeServer": user.mailHomeServer,
		"mailPrimaryAddress": user.mailPrimaryAddress,
		"mailAlternativeAddress": user.mailAlternativeAddress,
	})
	return user


def test_user_b_mail_alt_equal_user_a_mail_primary():
	print("### user_b's mail_alternative_address is equal to user_a's primary mail address")
	with udm_test.UCSTestUDM() as udm:
		a_user = random_mail_user(udm=udm)
		b_user = random_mail_user(udm=udm, mail_alternative_address=a_user.mailPrimaryAddress)
		token = make_token()
		send_mail(recipients=a_user.mailPrimaryAddress, msg=token, debuglevel=DEBUG_LEVEL)
		check_delivery(token, a_user.mailPrimaryAddress, True)
		check_delivery(token, b_user.mailPrimaryAddress, True)


@pytest.mark.parametrize("mail_forward_copy_to_self,delivered", [("1", True), ("0", False)])
def test_user_b_mail_alt_equal_user_a_mail_primary_with_mail_copy_to_self(mail_forward_copy_to_self, delivered):
	print("### user_b's mail_alternative_address is equal to user_a's mail forward address")
	with udm_test.UCSTestUDM() as udm:
		a_user = Bunch()
		a_user.mailPrimaryAddress = random_email()
		a_user.mailHomeServer = FQDN
		a_user.mailForwardAddress = random_email()
		a_user.dn, a_user.username = udm.create_user(set={
			"mailHomeServer": a_user.mailHomeServer,
			"mailPrimaryAddress": a_user.mailPrimaryAddress,
			"mailForwardAddress": a_user.mailForwardAddress,
			"mailForwardCopyToSelf": mail_forward_copy_to_self,
		})
		b_user = Bunch()
		b_user.mailPrimaryAddress = random_email()
		b_user.mailHomeServer = FQDN
		b_user.dn, a_user.username = udm.create_user(set={
			"mailHomeServer": b_user.mailHomeServer,
			"mailPrimaryAddress": b_user.mailPrimaryAddress,
			"mailAlternativeAddress": a_user.mailPrimaryAddress,
		})
		token = make_token()
		send_mail(recipients=a_user.mailPrimaryAddress, msg=token, debuglevel=DEBUG_LEVEL)
		check_delivery(token, a_user.mailPrimaryAddress, delivered)
		check_delivery(token, b_user.mailPrimaryAddress, True)


@pytest.mark.parametrize("mail_forward_copy_to_self,delivered", [("1", True), ("0", False)])
def test_user_b_mail_alt_equal_user_a_mail_forward(mail_forward_copy_to_self, delivered):
	print("### user_b's mail_alternative_address is equal to user_a's mail forward address")
	with udm_test.UCSTestUDM() as udm:
		a_user = Bunch()
		a_user.mailPrimaryAddress = random_email()
		a_user.mailHomeServer = FQDN
		a_user.mailForwardAddress = random_email()
		a_user.dn, a_user.username = udm.create_user(set={
			"mailHomeServer": a_user.mailHomeServer,
			"mailPrimaryAddress": a_user.mailPrimaryAddress,
			"mailForwardAddress": a_user.mailForwardAddress,
			"mailForwardCopyToSelf": mail_forward_copy_to_self,
		})
		b_user = Bunch()
		b_user.mailPrimaryAddress = random_email()
		b_user.mailHomeServer = FQDN
		b_user.dn, a_user.username = udm.create_user(set={
			"mailHomeServer": b_user.mailHomeServer,
			"mailPrimaryAddress": b_user.mailPrimaryAddress,
			"mailAlternativeAddress": a_user.mailForwardAddress,
		})
		token = make_token()
		send_mail(recipients=a_user.mailPrimaryAddress, msg=token, debuglevel=DEBUG_LEVEL)
		check_delivery(token, a_user.mailPrimaryAddress, delivered)
		check_delivery(token, b_user.mailPrimaryAddress, True)


def test_group_mail_equal_user_mail_alt():
	print("### The group's mail is identical to a users mail_alternative_address")
	with udm_test.UCSTestUDM() as udm:
		group_mail = random_email()
		user_a = random_mail_user(udm=udm, mail_alternative_address=group_mail)
		user_b = random_mail_user(udm=udm)
		udm.create_group(
			set={
				"mailAddress": group_mail,
				"users": [user_b.dn]
			}
		)
		token = make_token()
		send_mail(recipients=group_mail, msg=token, debuglevel=DEBUG_LEVEL)
		check_delivery(token, user_a.mailPrimaryAddress, True)
		check_delivery(token, user_b.mailPrimaryAddress, True)


def test_mail_list_equal_user_mail_alt():
	print("### A mailing list's mail is identical with a users mail_alternative_address")
	with udm_test.UCSTestUDM() as udm:
		list_name = uts.random_name()
		mailing_list_mail = "%s@%s" % (list_name, DOMAIN)
		user_a = random_mail_user(udm=udm, mail_alternative_address=mailing_list_mail)
		user_b = random_mail_user(udm=udm)
		udm.create_object(
			"mail/lists",
			set={
				"name": list_name,
				"mailAddress": mailing_list_mail,
				"members": [user_b.mailPrimaryAddress],
			}
		)
		token = make_token()
		send_mail(recipients=mailing_list_mail, msg=token, debuglevel=DEBUG_LEVEL)
		check_delivery(token, user_a.mailPrimaryAddress, True)
		check_delivery(token, user_b.mailPrimaryAddress, True)


def test_user_mail_alt_equals_shared_folder_mail_address():
	print("### A user has mail@shared_folder as mail_alternative_address address")
	with udm_test.UCSTestUDM() as udm:
		folder_name = uts.random_name()
		shared_folder_mail = "%s@%s" % (folder_name, DOMAIN)
		user = random_mail_user(udm=udm, mail_alternative_address=shared_folder_mail)
		token = make_token()
		msgid = uts.random_name()
		folder_dn, folder_name, folder_mailaddress = create_shared_mailfolder(
			udm, FQDN, mailAddress=shared_folder_mail,
			user_permission=['"%s" "%s"' % ("anyone", "all")]
		)
		send_mail(recipients=shared_folder_mail, msg=token, debuglevel=DEBUG_LEVEL, messageid=msgid)
		check_delivery(token, user.mailPrimaryAddress, True)
		found = imap_search_mail(
			messageid=msgid, server=FQDN,
			imap_user=user.mailPrimaryAddress,
			imap_folder=folder_name, use_ssl=True
		)
		if not found:
			utils.fail("Mail sent with token = %r to %s un-expectedly".format(token, folder_name))


def test_group_mail_in_mailing_list():
	with udm_test.UCSTestUDM() as udm:
		group_members = []
		group_mails = []
		for i in range(2):
			user = random_mail_user(udm=udm)
			group_members.append(user.dn)
			group_mails.append(user.mailPrimaryAddress)
		group_mail = random_email()
		udm.create_group(
			set={
				"mailAddress": group_mail,
				"users": group_members
			}
		)
		list_name = uts.random_name()
		list_mail = "%s@%s" % (list_name, DOMAIN)
		udm.create_object(
			"mail/lists",
			set={
				"name": list_name,
				"mailAddress": list_mail,
				"members": [group_mail]
			},
			wait_for_drs_replication=True
		)
		token = make_token()
		send_mail(recipients=list_mail, msg=token, debuglevel=DEBUG_LEVEL)
		for mail in group_mails:
			check_delivery(token, mail, True)
