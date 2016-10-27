import re


class UCS_Version(object):

	'''Version object consisting of major-, minor-number and patch-level'''
	FORMAT = '%(major)d.%(minor)d'
	FULLFORMAT = '%(major)d.%(minor)d-%(patchlevel)d'
	# regular expression matching a UCS version X.Y-Z
	_regexp = re.compile('(?P<major>[0-9]+)\.(?P<minor>[0-9]+)-(?P<patch>[0-9]+)')

	def __init__(self, version):
		'''version must a string matching the pattern X.Y-Z or a triple
		with major, minor and patchlevel.
		>>> v = UCS_Version((2,3,1))
		>>> v = UCS_Version([2,3,1])
		>>> v = UCS_Version("2.3-1")
		>>> v2 = UCS_Version(v)
		'''
		if isinstance(version, (tuple, list)) and len(version) == 3:
			self.major, self.minor, self.patchlevel = map(int, version)
		elif isinstance(version, str):
			self.set(version)
		elif isinstance(version, UCS_Version):
			self.major, self.minor, self.patchlevel = version.major, version.minor, version.patchlevel
		else:
			raise TypeError("not a tuple, list or string")

	def __cmp__(self, right):
		'''Compare to UCS versions. The method returns 0 if the versions
		are equal, -1 if the left is less than the right and 1 of the
		left is greater than the right'''
		# major version differ
		if self.major < right.major:
			return -1
		if self.major > right.major:
			return 1
		# major is equal, check minor
		if self.minor < right.minor:
			return -1
		if self.minor > right.minor:
			return 1
		# minor is equal, check patchlevel
		if self.patchlevel < right.patchlevel:
			return -1
		if self.patchlevel > right.patchlevel:
			return 1

		return 0

	def set(self, version):
		'''Parse string and set version.'''
		match = UCS_Version._regexp.match(version)
		if not match:
			raise ValueError('string does not match UCS version pattern')
		self.major, self.minor, self.patchlevel = map(int, match.groups())

	def __getitem__(self, k):
		'''Dual natured dictionary: retrieve value from attribute.'''
		return self.__dict__[k]

	def __str__(self):
		'''Return full version string.'''
		return UCS_Version.FULLFORMAT % self

	def __hash__(self):
		return hash((self.major, self.minor, self.patchlevel))

	def __eq__(self, other):
		return (self.major, self.minor, self.patchlevel) == (other.major, other.minor, other.patchlevel)

	def __repr__(self):
		'''Return canonical string representation.'''
		return 'UCS_Version((%d,%d,%r))' % (self.major, self.minor, self.patchlevel)
