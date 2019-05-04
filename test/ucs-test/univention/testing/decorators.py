from __future__ import print_function
import time

DEFAULT_TIMEOUT = 90  # seconds


class WaitForNonzeroResultOrTimeout(object):

	def __init__(self, func, timeout=DEFAULT_TIMEOUT):
		self.func = func
		self.timeout = timeout

	def __call__(self, *args, **kwargs):
		for i in xrange(self.timeout):
			result = self.func(*args, **kwargs)
			if result:
				break
			else:
				time.sleep(1)
		return result


class SetTimeout(object):

	def __init__(self, func, timeout=DEFAULT_TIMEOUT):
		self.func = func
		self.timeout = timeout

	def __call__(self, *args, **kwargs):
		for i in xrange(self.timeout):
			try:
				print("** Entering", self.func.__name__)
				self.func(*args, **kwargs)
				print("** Exiting", self.func.__name__)
				break
			except Exception as ex:
				print("(%d)-- Exception cought: %s %s" % (i, type(ex), str(ex)))
				time.sleep(1)
		else:
			self.func(*args, **kwargs)


def setTimeout(func, timeout=DEFAULT_TIMEOUT):
	def wrapper(*args, **kwargs):
		for i in xrange(timeout):
			try:
				print("** Entering", func.__name__)
				func(*args, **kwargs)
				print("** Exiting", func.__name__)
				break
			except Exception as ex:
				print("(%d)-- Exception cought: %s %s" % (i, type(ex), str(ex)))
				time.sleep(1)
		else:
			func(*args, **kwargs)
	return wrapper

# vim: set ft=python ts=4 sw=4 et ai :
