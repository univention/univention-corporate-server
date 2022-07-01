#!/usr/share/ucs-test/runner pytest-3
# coding=utf-8
## desc: Test umlauts for usertemplate object
## roles: [domaincontroller_master]
## exposure: careful
## bugs: [52878]

import pytest
import unidecode

import univention.admin.modules as udm_modules
import univention.testing.utils as utils
from univention.admin.uldap import getAdminConnection
from univention.testing.strings import random_int, random_name

PASSWORD = 'Univention@99'
MOD_TMPL = 'settings/usertemplate'
MOD_USER = 'users/user'
MAIL_DOMAIN = '%s.%s' % (random_name(), random_name())


def test_replacements():
	previously_hard_coded_umlauts = {
		'À': 'A',
		'Á': 'A',
		'Â': 'A',
		'Ã': 'A',
		'Å': 'A',
		'Æ': 'AE',
		'Ç': 'C',
		'È': 'E',
		'É': 'E',
		'Ê': 'E',
		'Ë': 'E',
		'Ì': 'I',
		'Í': 'I',
		'Î': 'I',
		'Ï': 'I',
		'Ð': 'D',
		'Ñ': 'N',
		'Ò': 'O',
		'Ó': 'O',
		'Ô': 'O',
		'Õ': 'O',
		'Ø': 'O',
		'Ù': 'U',
		'Ú': 'U',
		'Û': 'U',
		'Ý': 'Y',
		'ß': 'ss',
		'à': 'a',
		'á': 'a',
		'â': 'a',
		'ã': 'a',
		'å': 'a',
		'æ': 'ae',
		'ç': 'c',
		'è': 'e',
		'é': 'e',
		'ê': 'e',
		'ë': 'e',
		'ì': 'i',
		'í': 'i',
		'î': 'i',
		'ï': 'i',
		'ñ': 'n',
		'ò': 'o',
		'ó': 'o',
		'ô': 'o',
		'õ': 'o',
		'ø': 'o',
		'ù': 'u',
		'ú': 'u',
		'û': 'u',
		'ý': 'y',
		'ÿ': 'y'
	}
	for umlaut, expected in previously_hard_coded_umlauts.items():
		if isinstance(umlaut, bytes):
			umlaut = umlaut.decode('UTF-8')
		assert unidecode.unidecode(umlaut) == expected


def create_template(udm, host, path):
	template_name = random_name()
	udm.create_object('mail/domain', wait_for_replication=False, name=MAIL_DOMAIN)
	dn_share = udm.create_object('shares/share', wait_for_replication=False, name=random_name(), path=path, host=host)
	properties = dict(
		name=template_name,
		mailPrimaryAddress='<:umlauts><firstname>.<lastname><:lower>@%s' % (MAIL_DOMAIN,),
		mailAlternativeAddress=['<:umlauts><username><:lower>@%s' % (MAIL_DOMAIN,), '<:umlauts><lastname><:lower>@%s' % (MAIL_DOMAIN,)],
		displayName='<:umlauts><lastname>, <:umlauts><firstname>',
		organisation=random_name(),
		sambahome='//%s/<:umlauts><username>' % (host,),
		scriptpath='//%s/scripts/<:umlauts><username>' % (host,),
		profilepath='//%s/profile/<:umlauts><username>' % (host,),
		unixhome='/home/<username>[0]/<:umlauts><username>',
		homeShare=dn_share,
		homeSharePath='<:umlauts><username>[0]/<username>',
		departmentNumber=random_int(),
	)
	dn_template = udm.create_object(MOD_TMPL, wait_for_replication=False, **properties)
	print("verify that template was created as expected.")
	utils.verify_ldap_object(dn_template, {
		'univentionObjectType': [MOD_TMPL],
		'cn': [template_name],
		'o': [properties['organisation']],
		'displayName': [properties['displayName']],
		'homeDirectory': [properties['unixhome']],
		'sambaHomePath': [properties['sambahome']],
		'sambaLogonScript': [properties['scriptpath']],
		'sambaProfilePath': [properties['profilepath']],
		'departmentNumber': [properties['departmentNumber']],
		'userHomeSharePreset': [properties['homeShare']],
		'userHomeSharePathPreset': [properties['homeSharePath']],
		'mailPrimaryAddress': [properties['mailPrimaryAddress']],
		'mailAlternativeAddress': properties['mailAlternativeAddress'],
	})
	return properties, dn_template


@pytest.mark.tags()
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
# @pytest.mark.bugs(52878)
def test_use_usertemplate_umlauts(udm):
	"""Test umlauts for usertemplate object"""
	host = random_name()
	path = '/%s' % (random_name(),)
	properties, dn_template = create_template(udm, host, path)
	co = None
	lo, po = getAdminConnection()
	udm_modules.update()
	# get udm module settings/usertemplate
	mod_tmpl = udm_modules.get(MOD_TMPL)
	# the mod_tmpl module is being initialized here
	udm_modules.init(lo, po, mod_tmpl)
	obj_tmpl = mod_tmpl.object(co, lo, po, dn=dn_template)
	mod_user = udm_modules.get(MOD_USER)
	udm_modules.init(lo, po, mod_user, template_object=obj_tmpl)
	usernames = [
		(u"Pınar", u"Ağrı", "pinar", "agri"),
		(u"ÇçĞğ", u"İıŞş", "ccgg", "iiss"),
		(u"Fryderyk", u"Krępa", "fryderyk", "krepa"),
		(u"Kübra", u"Gümuşay", "kuebra", "guemusay"),
		(u"Зиновьев Селиверст", u"Терентьевич", "zinov'ev seliverst", "terent'evich"),
		(u"Ýlang", u"Müstèrmánn", "ylang", "muestermann"),
		(u"Öle", u"Mästèrmànn", "oele", "maestermann"),
		(u"Nînä", u"Müstèrfräú", "ninae", "muesterfraeu"),
		(u"Ǹanâ", u"Mästérfrâü", "nana", "maesterfraue"),
		(u"Daniel", "Groß", "daniel", "gross"),
		(u"Üwe", "Äpfelmann", "uewe", "aepfelmann"),
	]
	for firstname, lastname, expected_firstname, expected_lastname in usernames:
		user_properties = {
			'lastname': lastname,
			'firstname': firstname,
			'password': PASSWORD,
			'username': random_name(),
		}
		obj_user = mod_user.object(None, lo, po)
		obj_user.open()
		obj_user.info.update(user_properties)
		dn_user = obj_user.create()
		udm._cleanup.setdefault(MOD_USER, []).append(dn_user)
		print('verify that email attributes of dn_user=%s are set as expected' % (dn_user,))
		utils.verify_ldap_object(dn_user, {
			'mailPrimaryAddress': ['%s.%s@%s' % (expected_firstname, expected_lastname, MAIL_DOMAIN)],
			'mailAlternativeAddress': ['%s@%s' % (user_properties['username'], MAIL_DOMAIN), '%s@%s' % (expected_lastname, MAIL_DOMAIN)],
		})
