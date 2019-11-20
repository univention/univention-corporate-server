from __future__ import print_function
import sys
import os
from urlparse import urlparse


def get_idps(ucr, log_fd=sys.stderr):

	def __get_supplement(key):
		return key.replace(idp_supplement_keybase, '')

	def __is_enabled_supplement(key, value):
		return key.startswith(idp_supplement_keybase) and ucr.is_true(value=value)

	def __is_valid_supplement(supplement):
		return supplement not in supplement_blacklist and '/' not in supplement

	def __get_supplement_entityID(supplement):
		if urlparse(main_entityID).path.startswith('/{}/'.format(main_basepath)):
			return main_entityID.replace(
				'/{}/'.format(main_basepath),
				'/{}/{}/'.format(main_basepath, supplement)
			)
		else:
			print('Unknown default entity ID format, using fallback for supplement entity IDs', file=log_fd)
			return main_entityID + '/{}'.format(supplement)

	def __get_supplement_basepath(supplement):
		return os.path.join(main_basepath, supplement)

	def __get_supplement_baseurl(supplement):
		return os.path.join(sso_fqdn, __get_supplement_basepath(supplement))

	supplement_blacklist = (os.listdir('/usr/share/simplesamlphp/www/'))
	main_basepath = 'simplesamlphp'
	sso_fqdn = ucr.get('ucs/server/sso/fqdn', '{}.{}'.format(
		'ucs-sso',
		ucr.get('domainname')
	))
	main_entityID = ucr.get('saml/idp/entityID', 'https://{}/{}/saml2/idp/metadata.php'.format(
		sso_fqdn,
		main_basepath
	))
	idp_supplement_keybase = 'saml/idp/entityID/supplement/'
	idp_supplements = (__get_supplement(key) for key, value in ucr.items() if __is_enabled_supplement(key, value))
	entityIDs = [{
		'entityID': main_entityID,
		'basepath': main_basepath,
		'baseurl': '__DEFAULT__',
	}]
	for idp_supplement in idp_supplements:
		if __is_valid_supplement(idp_supplement):
			supplement_entityID = __get_supplement_entityID(idp_supplement)
			entityIDs.append({
				'entityID': supplement_entityID,
				'basepath': __get_supplement_basepath(idp_supplement),
				'baseurl': __get_supplement_baseurl(idp_supplement),
			})
		else:
			print('"{}" is not a valid entity id supplement. Ignoring.'.format(idp_supplement), file=log_fd)
	return entityIDs
