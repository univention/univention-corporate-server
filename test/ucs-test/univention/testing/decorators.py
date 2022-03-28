from __future__ import print_function

import time
from functools import wraps
from typing import Any, Callable, TypeVar, cast  # noqa: F401

DEFAULT_TIMEOUT = 90  # seconds

F = TypeVar('F', bound=Callable[..., None])


class WaitForNonzeroResultOrTimeout(object):

	def __init__(self, func, timeout=DEFAULT_TIMEOUT):
		# type: (Callable[..., Any], int) -> None
		self.func = func
		self.timeout = timeout

	def __call__(self, *args, **kwargs):
		# type: (*Any, **Any) -> Any
		for i in range(self.timeout):
			result = self.func(*args, **kwargs)
			if result:
				break
			else:
				time.sleep(1)
		return result


class SetTimeout(object):

	def __init__(self, func, timeout=DEFAULT_TIMEOUT):
		# type: (Callable[..., None], int) -> None
		self.func = func
		self.timeout = timeout

	def __call__(self, *args, **kwargs):
		# type: (*Any, **Any) -> Any
		for i in range(self.timeout):
			try:
				print("** Entering", self.func.__name__)
				self.func(*args, **kwargs)
				print("** Exiting", self.func.__name__)
				break
			except Exception as ex:
				print("(%d)-- Exception cought: %s %s" % (i, type(ex), ex))
				time.sleep(1)
		else:
			self.func(*args, **kwargs)


def setTimeout(timeout=DEFAULT_TIMEOUT):
	# type: (int) -> Callable[[F], F]
	def decorator(func):
		# type: (F) -> F
		@wraps(func)
		def wrapper(*args, **kwargs):
			# type: (*Any, **Any) -> None
			for i in range(timeout):
				try:
					print("** Entering", func.__name__)
					func(*args, **kwargs)
					print("** Exiting", func.__name__)
					break
				except Exception as ex:
					print("(%d)-- Exception cought: %s %s" % (i, type(ex), ex))
					time.sleep(1)
			else:
				func(*args, **kwargs)
		return cast(F, wrapper)
	return decorator

# vim: set ft=python ts=4 sw=4 et ai :
