# vim: set fileencoding=utf-8 ft=python sw=4 ts=4 :
"""UCS Test errors."""
__all__ = ['TestError', 'TestConditionError']


class TestError(Exception):

	"""
	General test error.
	"""


class TestConditionError(Exception):

	"""
	Error during prepaation for test.
	"""

	def __iter__(self):
		return self.tests.__iter__()

	@property
	def tests(self):
		"""Return failed tests."""
		return self.args[0]


if __name__ == '__main__':
	import doctest
	doctest.testmod()
