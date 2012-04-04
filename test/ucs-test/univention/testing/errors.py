__all__ = ['TestError', 'TestConditionError']

class TestError(Exception):
	"""
	General test error.
	"""
	pass

class TestConditionError(Exception):
	"""
	Error during prepaation for test.
	"""
	def __iter__(self):
		return self.tests.__iter__()

	@property
	def tests(self):
		return self.args[0]

if __name__ == '__main__':
	import doctest
	doctest.testmod()
