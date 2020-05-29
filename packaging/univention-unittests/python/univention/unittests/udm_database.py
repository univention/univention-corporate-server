from collections import OrderedDict


class LDAPObject(object):
	def __init__(self, dn, attrs):
		self.dn = dn
		self.attrs = attrs
		self.changed = {}

	def __repr__(self):
		return 'Object({!r}, {!r})'.format(self.dn, self.attrs)


def make_obj(obj):
	dn = obj.pop('dn')[0].decode('utf-8')
	return LDAPObject(dn, obj)


def parse_ldif(ldif):
	ret = []
	obj = {}
	for line in ldif.splitlines():
		if not line.strip():
			if obj:
				ret.append(make_obj(obj))
			obj = {}
			continue
		k, v = line.split(': ', 1)
		obj.setdefault(k, [])
		obj[k].append(v.encode('utf-8'))
	if obj:
		ret.append(make_obj(obj))
	return ret


class Database(object):
	def __init__(self):
		self.objs = OrderedDict()

	def fill(self, fname):
		with open(fname) as fd:
			objs = parse_ldif(fd.read())
			for obj in objs:
				self.add(obj)

	def __iter__(self):
		for obj in self.objs.values():
			yield obj

	def __repr__(self):
		return 'Database({!r})'.format(self.objs)

	def add(self, obj):
		self.objs[obj.dn] = obj
		return obj.dn

	def delete(self, dn):
		del self.objs[dn]

	def modify(self, dn, ml):
		obj = self.objs[dn]
		for attr, old, new in ml:
			if new:
				obj.attrs[attr] = new
			else:
				obj.attrs.pop(attr, None)


def default_database():
	database = Database()
	database.fill('nagios.ldif')
	return database


# def make_univention_object(object_type, attrs, parent=None):
# 	if parent is None:
# 		parent = get_domain()
# 	id_attr = 'cn'
# 	id_value = attrs[id_attr][0]
# 	attrs['univentionObjectType'] = [object_type]
# 	attrs['objectClass'].append('univentionObject')
# 	dn = '{}={},{}'.format(id_attr, id_value, parent)
# 	return LDAPObject(dn, attrs)
