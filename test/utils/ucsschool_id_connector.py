#!/usr/bin/python2.7

import json

from univention.config_registry import ConfigRegistry
from univention.udm import UDM
from univention.udm.exceptions import CreateError


def setup_kelvin_traeger():
	with open('/var/lib/ucs-school-import/configs/kelvin.json', 'r+w') as fp:
		config = json.load(fp)
		config['configuration_checks'] = ['defaults', 'class_overwrites', 'mapped_udm_properties']
		config['mapped_udm_properties'] = ['displayName', 'e-mail', 'organisation', 'phone']
		fp.seek(0)
		json.dump(config, fp, indent=4, sort_keys=True)


def create_extended_attr():
	ucr = ConfigRegistry()
	ucr.load()
	sea_mod = UDM.admin().version(1).get('settings/extended_attribute')
	ldap_base = ucr.get('ldap/base')
	ucsschool_id_connector_last_update = sea_mod.new(superordinate='cn=univention,{}'.format(ldap_base))
	ucsschool_id_connector_last_update.position = 'cn=custom attributes,cn=univention,{}'.format(ldap_base)
	props = {
		'name': 'ucsschool_id_connector_last_update',
		'CLIName': 'ucsschool_id_connector_last_update',
		'shortDescription': 'Date of last update by the UCS@school ID Connector app.',
		'module': 'users/user',
		'tabName': 'UCS@school',
		'tabPosition': '9',
		'groupName': 'ID Sync',
		'groupPosition': '2',
		'translationGroupName': [('de_DE', 'ID Sync', )],
		'syntax': 'string',
		'default': '',
		'multivalue': '0',
		'valueRequired': '0',
		'mayChange': '1',
		'doNotSearch': '1',
		'objectClass': 'univentionFreeAttributes',
		'ldapMapping': 'univentionFreeAttribute14',
		'deleteObjectClass': '0',
		'overwriteTab': '0',
		'fullWidth': '1',
		'disableUDMWeb': '0',
	}
	for key, value in props.items():
		setattr(ucsschool_id_connector_last_update.props, key, value)
	ucsschool_id_connector_last_update.options.extend(('ucsschoolStudent', 'ucsschoolTeacher', 'ucsschoolStaff', 'ucsschoolAdministrator'))
	try:
		ucsschool_id_connector_last_update.save()
	except CreateError:
		print('Extended attr: "ucsschool_id_connector_last_update" already exists. Ignoring.')

	ucsschool_id_connector_pw = sea_mod.new(superordinate='cn=univention,{}'.format(ldap_base))
	ucsschool_id_connector_pw.position = 'cn=custom attributes,cn=univention,{}'.format(ldap_base)
	props = {
		'name': 'ucsschool_id_connector_pw',
		'CLIName': 'ucsschool_id_connector_pw',
		'shortDescription': 'UCS@school ID Connector password sync.',
		'module': 'users/user',
		'syntax': 'string',
		'default': '',
		'multivalue': '0',
		'valueRequired': '0',
		'mayChange': '1',
		'doNotSearch': '1',
		'objectClass': 'univentionFreeAttributes',
		'ldapMapping': 'univentionFreeAttribute15',
		'deleteObjectClass': '0',
		'overwriteTab': '0',
		'fullWidth': '1',
		'disableUDMWeb': '1',
	}
	for key, value in props.items():
		setattr(ucsschool_id_connector_pw.props, key, value)
	ucsschool_id_connector_pw.options.extend(('ucsschoolStudent', 'ucsschoolTeacher', 'ucsschoolStaff', 'ucsschoolAdministrator'))
	try:
		ucsschool_id_connector_pw.save()
	except CreateError:
		print('Extended attr: "ucsschool_id_connector_pw" already exists. Ignoring.')
