#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Apply valid/invalid values for various UDM syntaxes
## tags: [udm,udm-syntax]
## roles: [domaincontroller_master]
## exposure: careful
## packages:
##   - univention-config
##   - univention-directory-manager-tools
## bugs: [40731]

import pytest

import univention.testing.strings as uts
import univention.testing.udm as udm_test


@pytest.mark.parametrize('syntax,valid_values,invalid_values', [
	('integer', ('5', '3000', '0', ''), ('one', 'somestring', '-5', '1.9')),
	('TrueFalse', ('true', 'false', ''), ('True', 'False', 'TRUE', 'FALSE', 'tRue', 'fAlse', 'yes', 'no', 'Yes', 'No', 'YES', 'NO', '1', '0')),
	('TrueFalseUpper', ('TRUE', 'FALSE', ''), ('True', 'False', 'TrUE', 'FaLSE', 'Yes', 'No', 'YES', 'NO', 'YeS', 'nO', '1', '0')),
	('boolean', ('1', '0', ''), ('True', 'False', 'TRUE', 'FALSE', 'true', 'false', 'yes', 'no', 'Yes', 'No', 'YES', 'NO')),
	('emailAddress', ('foo@example.com', 'foo+bar@example.com', 'foo-bar@example.com', 'foo@sub.sub.sub.domain.example.com', ''), ('foo', 'example.com', '@', 'foo', 'foo@', '@example.com')),
	('emailAddressTemplate', ('foo@example.com', 'foo+bar@example.com', 'foo-bar@example.com', 'foo@sub.sub.sub.domain.example.com', ''), ('foo', 'example.com', '@', 'foo', 'foo@', '@example.com')),
])
def test_udm_syntax(udm, syntax, valid_values, invalid_values, verify_ldap_object):
	"""Apply valid/invalid values for various UDM syntaxes"""
	cli_name = uts.random_string()
	udm.create_object(
		'settings/extended_attribute',
		position=udm.UNIVENTION_CONTAINER,
		name=uts.random_name(),
		shortDescription=uts.random_string(),
		CLIName=cli_name,
		module='users/user',
		objectClass='univentionFreeAttributes',
		ldapMapping='univentionFreeAttribute15',
		syntax=syntax
	)

	# check valid values
	for value in valid_values:
		user_dn, username = udm.create_user(**{cli_name: value})
		if syntax in ('emailAddress', 'emailAddressTemplate'):
			verify_ldap_object(user_dn, {
				'univentionFreeAttribute15': [value] if value else [],
			})

	# check invalid values
	for value in invalid_values:
		with pytest.raises(udm_test.UCSTestUDM_CreateUDMObjectFailed):
			udm.create_user(**{cli_name: value})
