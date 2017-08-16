# coding: utf-8

import univention.testing.strings as tstrings

UTF8_CHARSET = tstrings.STR_UMLAUT + u"КирилицаКириллицаĆirilicaЋирилица" + u"普通話普通话"
# the S4C sync can't # handle them (see bug #44373)
SPECIAL_CHARSET = "".join(set(tstrings.STR_SPECIAL_CHARACTER) - set('\\#"?'))
# we exclude '$' as it has special meaning
FORBIDDEN_SAMACCOUNTNAME = "\\/[]:;|=,+*?<>@ " + '$' + '#"'
SPECIAL_CHARSET_USERNAME = "".join(set(SPECIAL_CHARSET) - set(FORBIDDEN_SAMACCOUNTNAME))


def random_string(length=10, alpha=False, numeric=False, charset=None, encoding='utf-8'):
	return tstrings.random_string(length, alpha, numeric, charset, encoding)


class TestUser(object):
	def __init__(self, user, rename={}, container=None):
		selection = ("username", "firstname", "lastname")
		self.basic = {k: v for (k, v) in user.iteritems() if k in selection}
		self.user = user
		self.rename = dict(self.basic)
		self.rename.update(rename)
		self.container = container

	def __repr__(self):
		args = (self.user, self.rename, self.container)
		return "{}({})".format(self.__class__.__name__, ", ".join(repr(a) for a in args))


class NormalUser(TestUser):
	def __init__(self):
		super(NormalUser, self).__init__(
			user={
				"username": tstrings.random_username(),
				"firstname": tstrings.random_name(),
				"lastname": tstrings.random_name(),
				"description": random_string(alpha=True, numeric=True),
				"street": random_string(alpha=True, numeric=True),
				"city": random_string(alpha=True, numeric=True),
				"postcode": random_string(numeric=True),
				"profilepath": random_string(alpha=True, numeric=True),
				"scriptpath": random_string(alpha=True, numeric=True),
				"homeTelephoneNumber": random_string(numeric=True),
				"mobileTelephoneNumber": random_string(numeric=True),
				"pagerTelephoneNumber": random_string(numeric=True),
				"sambaUserWorkstations": random_string(numeric=True)
			},
			rename={"username": tstrings.random_username()},
			container=tstrings.random_name(),
		)


class Utf8User(TestUser):
	def __init__(self):
		super(Utf8User, self).__init__(
			user={
				"username": random_string(charset=UTF8_CHARSET),
				"firstname": random_string(charset=UTF8_CHARSET),
				"lastname": random_string(charset=UTF8_CHARSET),
				"description": random_string(charset=UTF8_CHARSET),
				"street": random_string(charset=UTF8_CHARSET),
				"city": random_string(charset=UTF8_CHARSET),
				"postcode": random_string(numeric=True),
				"profilepath": random_string(charset=UTF8_CHARSET),
				"scriptpath": random_string(charset=UTF8_CHARSET),
				"homeTelephoneNumber": random_string(numeric=True),
				"mobileTelephoneNumber": random_string(numeric=True),
				"pagerTelephoneNumber": random_string(numeric=True),
				"sambaUserWorkstations": random_string(numeric=True)
			},
			rename={"username": random_string(charset=UTF8_CHARSET)},
			container=random_string(charset=UTF8_CHARSET),
		)


class SpecialUser(TestUser):
	def __init__(self):
		super(SpecialUser, self).__init__(
			user={
				"username": random_string(charset=SPECIAL_CHARSET_USERNAME),
				"firstname": tstrings.random_name_special_characters(),
				"lastname": tstrings.random_name_special_characters(),
				"description": random_string(charset=SPECIAL_CHARSET),
				"street": random_string(charset=SPECIAL_CHARSET),
				"city": random_string(charset=SPECIAL_CHARSET),
				"postcode": random_string(numeric=True),
				"profilepath": random_string(charset=SPECIAL_CHARSET),
				"scriptpath": random_string(charset=SPECIAL_CHARSET),
				"homeTelephoneNumber": random_string(numeric=True),
				"mobileTelephoneNumber": random_string(numeric=True),
				"pagerTelephoneNumber": random_string(numeric=True),
				"sambaUserWorkstations": random_string(numeric=True)
			},
			rename={"username": random_string(charset=SPECIAL_CHARSET_USERNAME)},
			container=random_string(charset=SPECIAL_CHARSET),
		)


class TestGroup(object):
	def __init__(self, group, rename={}, container=None):
		self.group = group
		self.rename = dict(self.group)
		self.rename.update(rename)
		self.container = container

	def __repr__(self):
		args = (self.group, self.rename, self.container)
		return "{}({})".format(self.__class__.__name__, ", ".join(repr(a) for a in args))


class NormalGroup(TestGroup):
	def __init__(self):
		super(NormalGroup, self).__init__(
			group={
				"name": tstrings.random_groupname(),
				"description": random_string(alpha=True, numeric=True)
			},
			rename={"name": tstrings.random_groupname()},
			container=tstrings.random_name(),
		)


class Utf8Group(TestGroup):
	def __init__(self):
		super(Utf8Group, self).__init__(
			group={
				"name": random_string(charset=UTF8_CHARSET),
				"description": random_string(charset=UTF8_CHARSET)
			},
			rename={"name": tstrings.random_string(charset=UTF8_CHARSET)},
			container=random_string(charset=UTF8_CHARSET),
		)


class SpecialGroup(TestGroup):
	def __init__(self):
		super(SpecialGroup, self).__init__(
			group={
				"name": random_string(charset=SPECIAL_CHARSET_USERNAME),
				"description": random_string(charset=SPECIAL_CHARSET)
			},
			rename={"name": tstrings.random_string(charset=SPECIAL_CHARSET_USERNAME)},
			container=random_string(charset=SPECIAL_CHARSET),
		)
