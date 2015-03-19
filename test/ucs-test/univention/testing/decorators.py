import time

DEFAULT_TIMEOUT = 30 # seconds

class SetTimeout(object):

	def __init__(self, func, timeout=DEFAULT_TIMEOUT):
		self.func = func
		self.timeout = timeout

	def __call__(self, *args, **kwargs):
		for i in xrange(self.timeout):
			try:
				print "** Entering", self.func.__name__
				self.func(*args, **kwargs)
				print "** Exiting", self.func.__name__
			except Exception as ex:
				print "(%d)-- Exception cought: %s %s" % (i,  type(ex), str(ex))
				time.sleep(1)
			else:
				break
		else:
			self.func(*args, **kwargs)

def setTimeout(func, timeout=DEFAULT_TIMEOUT):
	def wrapper(*args, **kwargs):
		for i in xrange(timeout):
			try:
				print "** Entering", func.__name__
				func(*args, **kwargs)
				print "** Exiting", func.__name__
			except Exception as ex:
				print "(%d)-- Exception cought: %s %s" % (i,  type(ex), str(ex))
				time.sleep(1)
			else:
				break
		else:
			func(*args, **kwargs)
	return wrapper
