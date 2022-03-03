#!/usr/share/ucs-test/runner python3
## desc: Create a UMC portal entry
## tags: [udm-ldapextensions,apptest]
## roles: [domaincontroller_master]
## exposure: dangerous
## packages:
##   - univention-directory-manager-tools

import base64

import univention.testing.strings as uts
import univention.testing.ucr as ucr_test
import univention.testing.udm as udm_test
import univention.testing.utils as utils


class Bunch(object):
	"""
	>>> y = Bunch(foo=42, bar='TEST')
	>>> print repr(y.foo), repr(y.bar)
	42 'TEST'

	>>> x = Bunch()
	>>> x.a = 4
	>>> print x.a
	4
	"""

	def __init__(self, **kwds):
		self.__dict__.update(kwds)

	def __str__(self):
		result = []
		for key, value in self.__dict__.iteritems():
			result.append('%s=%r' % (key, value))
		return 'Bunch(' + ', '.join(result) + ')'

	def __repr__(self):
		return str(self)


if __name__ == '__main__':
	with ucr_test.UCSTestConfigRegistry() as ucr:
		with udm_test.UCSTestUDM() as udm:
			portal = Bunch(
				name=uts.random_name(),
				displayName='"de_DE" "%s"' % (uts.random_name(),),
				logo=base64.b64encode(uts.random_name().encode('utf-8')).decode('ASCII'),
				background=base64.b64encode(uts.random_name().encode('utf-8')).decode('ASCII'),
			)

			kwargs = portal.__dict__.copy()
			kwargs['portalComputers'] = [ucr.get('ldap/hostdn')]

			dn = udm.create_object('portals/portal', **kwargs)
			utils.verify_ldap_object(
				dn,
				{
					'cn': [portal.name],
					'univentionNewPortalLogo': [portal.logo],
					'univentionNewPortalDisplayName': [portal.displayName.replace('"', '')],
					'univentionNewPortalBackground': [portal.background],
				})
