#!/usr/share/ucs-test/runner pytest-3
## desc: Create a usertemplate object and remove it
## tags: [udm,udm-settings,apptest]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-directory-manager-tools

import pytest
import unidecode

import univention.admin.modules as udm_modules
import univention.testing.strings as uts
import univention.testing.utils as utils
from univention.admin.uldap import getAdminConnection
from univention.testing.strings import random_int, random_name
from univention.testing.umc import Client

PASSWORD = 'Univention@99'
MOD_TMPL = 'settings/usertemplate'
MOD_USER = 'users/user'

MAIL_DOMAIN = '%s.%s' % (random_name(), random_name())


def email():
	return '%s.%s' % (random_name(), MAIL_DOMAIN)


@pytest.mark.tags('udm-ldapextensions', 'apptest')
@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('dangerous')
def test_create_usertemplate(udm):
	"""Create a usertemplate object and remove it"""
	template_name = uts.random_name()
	template = udm.create_object('settings/usertemplate', name=template_name)
	utils.verify_ldap_object(template, {'cn': [template_name]})

	udm.remove_object('settings/usertemplate', dn=template)
	utils.verify_ldap_object(template, should_exist=False)


@pytest.mark.roles('domaincontroller_master')
@pytest.mark.exposure('careful')
# @pytest.mark.bugs(42765,43428,29672)
def test_use_usertemplate(udm):
	"""Use a usertemplate object"""
	template_name = random_name()

	udm.create_object('mail/domain', wait_for_replication=False, name=MAIL_DOMAIN)

	dn_secretary = udm.create_user(wait_for_replication=False)[0]

	dn_group = udm.create_group(wait_for_replication=False)[0]
	dn_group1 = udm.create_group(wait_for_replication=False)[0]
	dn_group2 = udm.create_group(wait_for_replication=False)[0]

	host = random_name()
	path = '/%s' % (random_name(),)
	dn_share = udm.create_object('shares/share', wait_for_replication=False, name=random_name(), path=path, host=host)

	properties = dict(
		name=template_name,
		_options=['pki'],
		title=random_name(),
		description=random_name(),
		mailPrimaryAddress='<firstname>.<lastname>@%s' % (MAIL_DOMAIN,),
		mailAlternativeAddress=['<username>@%s' % (MAIL_DOMAIN,), '<lastname>@%s' % (MAIL_DOMAIN,)],
		displayName='<lastname>, <firstname>',
		organisation=random_name(),
		employeeNumber=random_int(),
		employeeType=random_name(),
		secretary=dn_secretary,
		primaryGroup=dn_group,
		groups=[dn_group1, dn_group2],
		disabled='1',
		pwdChangeNextLogin='1',
		homedrive='H:',
		sambahome='//%s/<username>' % (host,),
		scriptpath='//%s/scripts/<username>' % (host,),
		profilepath='//%s/profile/<username>' % (host,),
		unixhome='/home/<username>[0]/<username>',
		shell='/bin/false',
		homeShare=dn_share,
		homeSharePath='<username>[0]/<username>',
		# serviceprovider=FIXME,
		phone='+49-421-22232-0',
		roomNumber=random_int(),
		departmentNumber=random_int(),
		street=random_name(),
		postcode=random_int(),
		city=random_name(),
		country='DE',
		# FIXME: CTX...
	)
	properties['e-mail'] = email()
	dn_template = udm.create_object(MOD_TMPL, wait_for_replication=False, **properties)
	utils.verify_ldap_object(dn_template, {
		'univentionObjectType': [MOD_TMPL],
		'cn': [template_name],
		'title': [properties['title']],
		'description': [properties['description']],
		'o': [properties['organisation']],
		'displayName': [properties['displayName']],
		'postalCode': [properties['postcode']],
		# 'shadowMax': [properties['userexpiry']],  # BUG: no prop
		# 'shadowExpire': [properties['passwordexpiry']],  # BUG: no prop
		'mail': [properties['e-mail']],
		'homeDirectory': [properties['unixhome']],
		'loginShell': [properties['shell']],
		'sambaHomePath': [properties['sambahome']],
		'sambaLogonScript': [properties['scriptpath']],
		'sambaProfilePath': [properties['profilepath']],
		'sambaHomeDrive': [properties['homedrive']],
		'st': [properties['country']],
		'telephoneNumber': [properties['phone']],
		'roomNumber': [properties['roomNumber']],
		'employeeNumber': [properties['employeeNumber']],
		'employeeType': [properties['employeeType']],
		'secretary': [properties['secretary']],
		'departmentNumber': [properties['departmentNumber']],
		'street': [properties['street']],
		'l': [properties['city']],
		'userDisabledPreset': [properties['disabled']],
		'userPwdMustChangePreset': [properties['pwdChangeNextLogin']],
		'userHomeSharePreset': [properties['homeShare']],
		'userHomeSharePathPreset': [properties['homeSharePath']],
		'userPrimaryGroupPreset': [properties['primaryGroup']],
		'userGroupsPreset': properties['groups'],
		'mailPrimaryAddress': [properties['mailPrimaryAddress']],
		'mailAlternativeAddress': properties['mailAlternativeAddress'],
		'userOptionsPreset': properties['_options'],
	})

	user_properties = {
		'lastname': random_name(),
		'firstname': random_name(),
		'password': PASSWORD,
		'username': random_name(),
	}
	if False:  # FIXME: UMC does the template in JS at the frontend
		umc = Client.get_test_connection()
		options = [{
			'object': user_properties,
			'options': {
				'container': 'cn=users,' + udm.LDAP_BASE,
				'objectType': MOD_USER,
				'objectTemplate': dn_template,
			},
		}]
		request = umc.umc_command('udm/add', options, MOD_USER)
		dn_user = request.result[0]['$dn$']
	else:
		co = None
		lo, po = getAdminConnection()

		udm_modules.update()
		mod_tmpl = udm_modules.get(MOD_TMPL)
		udm_modules.init(lo, po, mod_tmpl)
		obj_tmpl = mod_tmpl.object(co, lo, po, dn=dn_template)

		mod_user = udm_modules.get(MOD_USER)
		udm_modules.init(lo, po, mod_user, template_object=obj_tmpl)
		obj_user = mod_user.object(None, lo, po)
		obj_user.open()
		obj_user.info.update(user_properties)
		dn_user = obj_user.create()

	udm._cleanup.setdefault(MOD_USER, []).append(dn_user)
	print('dn_user=%s' % (dn_user,))

	utils.verify_ldap_object(dn_user, {
		'univentionObjectType': [MOD_USER],
		'title': [properties['title']],
		# 'description': [properties['description']],  # BUG udm.python filters out, while umc.JS does not
		'o': [properties['organisation']],
		# 'displayName': [properties['displayName']],
		'postalCode': [properties['postcode']],  # BUG #43428
		'mail': [properties['e-mail']],
		'homeDirectory': ['/home/%s/%s' % (user_properties['username'][0], user_properties['username'])],
		'loginShell': [properties['shell']],
		'sambaHomePath': ['//%s/%s' % (host, user_properties['username'])],
		'sambaLogonScript': ['//%s/scripts/%s' % (host, user_properties['username'])],
		'sambaProfilePath': ['//%s/profile/%s' % (host, user_properties['username'])],
		'sambaHomeDrive': [properties['homedrive']],
		'st': [properties['country']],
		'telephoneNumber': [properties['phone']],
		'roomNumber': [properties['roomNumber']],
		'employeeNumber': [properties['employeeNumber']],
		'employeeType': [properties['employeeType']],
		'secretary': [properties['secretary']],
		'departmentNumber': [properties['departmentNumber']],
		'street': [properties['street']],
		'l': [properties['city']],
		# 'userDisabledPreset': [properties['disabled']],  # TODO
		# 'userPwdMustChangePreset': [properties['pwdChangeNextLogin']],  # TODO
		'automountInformation': ['-rw %s:%s/%s/%s' % (host, path, user_properties['username'][0], user_properties['username']), ],
		# 'gidNumber': [properties['primaryGroup']],  # TODO
		# 'userGroupsPreset': properties['groups'],  # TODO
		'mailPrimaryAddress': ['%s.%s@%s' % (user_properties['firstname'], user_properties['lastname'], MAIL_DOMAIN)],
		'mailAlternativeAddress': ['%s@%s' % (user_properties['username'], MAIL_DOMAIN), '%s@%s' % (user_properties['lastname'], MAIL_DOMAIN)],
		# 'krb5PrincipalName': [],
		# 'krb5PasswordEnd': [],
		# 'krb5Key': [],
		'krb5MaxRenew': ['604800'],
		'krb5KDCFlags': ['254'],
		'krb5KeyVersionNumber': ['1'],
	})


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


def test_usertemplate_filter(udm, ucr):
	properties = {
		'CLIName': 'mail',
		'copyable': '0',
		'deleteObjectClass': '0',
		'disableUDMWeb': '0',
		'doNotSearch': '0',
		'fullWidth': '0',
		'groupName': 'User account',
		'groupPosition': '11',
		'ldapMapping': 'mail',
		'longDescription': 'Mail Attribut',
		'mayChange': '1',
		'module': ['users/user', 'settings/usertemplate'],
		'name': 'mail',
		'objectClass': 'inetOrgPerson',
		'overwritePosition': 'None',
		'overwriteTab': '0',
		'shortDescription': 'Mail Attribut',
		'syntax': 'String',
		'tabAdvanced': '0',
		'tabName': 'General',
		'tabPosition': '11',
		'valueRequired': '0'
	}
	extended_attribute = udm.create_object('settings/extended_attribute', position='cn=custom attributes,cn=univention,%s' % (ucr.get('ldap/base')), **properties)
	utils.verify_ldap_object(extended_attribute, should_exist=True)

	template = udm.create_object('settings/usertemplate', name=uts.random_name(), mail='<username>@example.com')
	utils.verify_ldap_object(template, {'mail': ['<username>@example.com'], 'objectClass': ['top', 'univentionUserTemplate', 'univentionObject']}, strict=True, should_exist=True)
