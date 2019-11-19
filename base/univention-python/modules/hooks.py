# -*- coding: utf-8 -*-
#
# Univention HookManager
#
# Copyright 2010-2019 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/>.

import os
import imp


class HookManager:

	"""
	This class tries to provide a simple interface to load and call hooks within existing code.
	Python modules are loaded from specified `module_dir` and automatically registered.
	These python modules have to contain at least a global method `register_hooks()` that returns
	a list of tuples (`hook_name`, `callable`).

	Simple hook file example::

		def my_test_hook(*args, **kwargs):
			print('TEST_HOOK:', args, kwargs)
			return ['Mein', 'Result', 123]

		def other_hook(*args, **kwargs):
			print('MY_SECOND_TEST_HOOK:', args, kwargs)
			return ['Mein', 'Result', 123]

		def register_hooks():
			return [
				('test_hook', my_test_hook),
				('pre_hook', other_hook),
			]

	The method `call_hook(hookname, *args, **kwargs)` calls all registered methods for specified
	hookname and passes `*args` and `**kwargs` to them. The return value of each method will be
	saved and returned by `call_hook()` as a list. If no method has been registered for
	specified hookname, an empty list will be returned.

	If `raise_exceptions` has been set to `False`, exceptions while loading Python modules will be
	discarded silently. If a hook raises an exception, it will be caught and returned in
	result list of `call_hooks()` instead of corresponding return value. E.g.::

		[['Mein', 'Result', 123], <exceptions.ValueError instance at 0x7f80496f6638>]

	How to use HookManager::

	>>> import univention.hooks
	>>> hm = univention.hooks.HookManager('./test')
	>>> hm.get_hook_list()
	['test_hook', 'pre_hook']
	>>> hm.call_hook('test_hook', 'abc', 123, x=1, y='B')
	TEST_HOOK: ('abc', 123) {'y': 'B', 'x': 1}                                <=== OUTPUT OF FIRST TESTHOOK
	MY_SECOND_TEST_HOOK: ('abc', 123) {'y': 'B', 'x': 1}                      <=== OUTPUT OF SECOND TESTHOOK
	[['First-Hook', 'Result', 123], ['Result', 'of', 'second', 'testhook']]   <=== RESULT OF call_hook()
	>>> hm.call_hook('unknown_hook')
	[]
	>>>
	"""

	def __init__(self, module_dir, raise_exceptions=True):
		"""
		:param module_dir:				path to directory that contains python modules with hook functions
		:param raise_exceptions:		if `False`, all exceptions while loading python modules will be dropped and all exceptions while calling hooks will be caught and returned in result list
		"""
		self.__loaded_modules = {}
		self.__registered_hooks = {}
		self.__module_dir = module_dir
		self.__raise_exceptions = raise_exceptions
		self.__load_hooks()
		self.__register_hooks()

	def __load_hooks(self):
		"""
		loads all python modules in specified module dir
		"""
		if os.path.exists(self.__module_dir) and os.path.isdir(self.__module_dir):
			for f in os.listdir(self.__module_dir):
				if f.endswith('.py') and len(f) > 3:
					modname = f[0:-3]
					fd = open(os.path.join(self.__module_dir, f))
					module = imp.new_module(modname)
					try:
						exec(fd, module.__dict__)
						self.__loaded_modules[modname] = module
					except Exception:
						if self.__raise_exceptions:
							raise

	def __register_hooks(self):
		for module in self.__loaded_modules.values():
			try:
				hooklist = module.register_hooks()
				for hookname, func in hooklist:
					# if returned function is not callable then continue
					if not callable(func):
						continue
					# append function to corresponding hook queue
					if hookname in self.__registered_hooks:
						self.__registered_hooks[hookname].append(func)
					else:
						self.__registered_hooks[hookname] = [func]
			except Exception:
				if self.__raise_exceptions:
					raise

	def set_raise_exceptions(self, val):
		"""
		Enable or disable raising exceptions.

		:param val: `True` to pass exceptions through, `False` to return them instead of the return value.
		"""
		if val in (True, False):
			self.__raise_exceptions = val
		else:
			raise ValueError('boolean value required')

	def get_hook_list(self):
		"""
		returns a list of hook names that have been defined by loaded python modules
		"""
		return self.__registered_hooks.keys()

	def call_hook(self, name, *args, **kwargs):
		"""
		All additional arguments are passed to hook methods.
		If `self.__raise_exceptions` is `False`, all exceptions while calling hooks will be caught and returned in result list.
		If return value is an empty list, no hook has been called.
		"""
		result = []
		for func in self.__registered_hooks.get(name, []):
			try:
				res = func(*args, **kwargs)
				result.append(res)
			except Exception as e:
				if self.__raise_exceptions:
					raise
				else:
					result.append(e)
		return result


# test code
if __name__ == '__main__':
	x = HookManager('./test')
	print('get_hook_list()={}'.format(x.get_hook_list()))
	print('call_hook(test_hook)={}'.format(x.call_hook('test_hook', 'abc', 123, x=1, y='B')))
