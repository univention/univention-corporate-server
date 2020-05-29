from fnmatch import fnmatch


class AndFilter(object):
	def __init__(self, children):
		self.children = children

	def __repr__(self):
		return 'AND({!r})'.format(self.children)

	def matches(self, obj):
		return all(child.matches(obj) for child in self.children)


class OrFilter(object):
	def __init__(self, children):
		self.children = children

	def __repr__(self):
		return 'OR({!r})'.format(self.children)

	def matches(self, obj):
		return any(child.matches(obj) for child in self.children)


class NotFilter(object):
	def __init__(self, children):
		assert len(children) == 1
		self.child = children[0]

	def __repr__(self):
		return 'NOT({!r})'.format(self.child)

	def matches(self, obj):
		return not self.child.matches(obj)


class AttrFilter(object):
	def __init__(self, key, value):
		self.key = key
		self.value = value

	def __repr__(self):
		return 'ATTR({}={})'.format(self.key, self.value)

	def matches(self, obj):
		obj_values = obj.attrs.get(self.key, [])
		if not self.value:
			return not obj_values
		for obj_value in obj_values:
			obj_value = obj_value.decode('utf-8')
			if fnmatch(obj_value, self.value):
				return True
		return False


def parse_filter(filter_string):
	if filter_string.startswith('(&'):
		if not filter_string.endswith(')'):
			raise ValueError(filter_string)
		return [AndFilter(parse_filter(filter_string[2:-1]))]
	if filter_string.startswith('(|'):
		if not filter_string.endswith(')'):
			raise ValueError(filter_string)
		return [OrFilter(parse_filter(filter_string[2:-1]))]
	if filter_string.startswith('(!'):
		if not filter_string.endswith(')'):
			raise ValueError(filter_string)
		return [NotFilter(parse_filter(filter_string[2:-1]))]
	idx = filter_string.find(')')
	attr = [AttrFilter(*filter_string[1:idx].split('='))]
	tail = filter_string[idx + 1:]
	if tail:
		return attr + parse_filter(tail)
	else:
		return attr


def make_filter(filter_string):
	if not filter_string:
		return AndFilter([])
	else:
		filter_objs = parse_filter(filter_string)
		return AndFilter(filter_objs)
