from copy import deepcopy

from univention.unittests.udm_database import default_database
from univention.unittests.udm_filter import make_filter

from mock import MagicMock

from univention.admin.uldap import access


def get_domain():
	return 'dc=intranet,dc=example,dc=de'


class MockedAccess(MagicMock):
#	def __init__(self, database=None):
#		self.database = database or default_database()
#
	def search(self, filter=None, base=None, attr=None):
		if base is None:
			base = get_domain()
		res = []
		ldap_filter = make_filter(filter)
		for obj in self.database:
			if not obj.dn.endswith(base):
				continue
			if not ldap_filter.matches(obj):
				continue
			if attr:
				attrs = {}
				for att in attr:
					if att in obj.attrs:
						attrs[att] = deepcopy(obj.attrs[att])
			else:
				attrs = deepcopy(obj.attrs)
			result = obj.dn, attrs
			res.append(result)
		return res

	def searchDn(self, filter=None, base=None, attr=None):
		res = []
		for dn, attrs in self.search(filter, base, attr):
			res.append(dn)
		return res

	def modify(self, dn, ml):
		self.database.modify(dn, ml)

	def create(self, obj):
		self.database.add(obj)

	def get(self, dn, attr=[], required=False, exceptions=False):
		return self.database[dn]

	def getAttr(self, dn, attr):
		obj = self.database.objs.get(dn)
		if obj:
			return obj.attrs.get(attr)


def mock_conn(database):
	lo = mock_lo(database)
	pos = MockedPosition()
	return lo, pos


def mock_lo(database):
	lo = MockedAccess()
	lo.database = database
	lo.mock_add_spec(access)
	return lo


class MockedPosition(object):
	def getDomain(self):
		return get_domain()

	def getDomainConfigBase(self):
		return 'cn=univention,%s' % self.getDomain()
