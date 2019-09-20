#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Decorators for functions in UMC 2.0 modules
#
# Copyright 2012-2019 Univention GmbH
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

"""
Convenience decorators for developers of UMC modules
====================================================

Functions exposed by UMC modules often share some logic. They check the
existence and formatting of variables or check permissions. If anything
fails, they react in a similar way. If everything is correct, the real
logic is often as simple as returning one single value.

This module provides functions that can be used to separate repeating
tasks from the actual business logic. This means:

* less time to code
* fewer bugs
* consistent behavior throughout the UMC in standard cases

Note that the functions defined herein do not cover every corner case during
UMC module development. You are not bound to use them if you need more
flexibility.
"""

import sys
import inspect
import time
import types
import notifier
import notifier.threads
import functools
from threading import Thread

from univention.lib.i18n import Translation

from univention.management.console.error import UMC_Error, UnprocessableEntity
from univention.management.console.log import MODULE

from univention.management.console.modules.sanitizers import MultiValidationError, ValidationError, Sanitizer, DictSanitizer, ListSanitizer

_ = Translation('univention.management.console').translate


def sanitize(*args, **kwargs):
	"""
	Decorator that lets you sanitize the user input.

	The sanitize function can be used to validate the input
	as well as change it.

	Note that changing a value here will actually alter the request
	object. This should be no problem though.

	If the validation step fails an error will be passed to the user
	instead of executing the function. This step should not raise
	anything other than
	:class:`~univention.management.console.modules.sanitizers.ValidationError`
	or
	:class:`~univention.management.console.modules.sanitizers.UnformattedValidationError`
	(one should use the method
	:meth:`~univention.management.console.modules.sanitizers.Sanitizer.raise_validation_error`).

	You can find some predefined Sanitize classes in the
	corresponding module or you define one yourself, deriving it from
	:class:`~univention.management.console.modules.sanitizers.Sanitizer`::

		class SplitPathSanitizer(Sanitizer):
			def __init__(self):
				super(SplitPathSanitizer, self).__init__(
					validate_none=True,
					may_change_value=True)

			def _sanitize(self, value, name, further_fields):
				if value is None:
					return []
				try:
					return value.split('/')
				except:
					self.raise_validation_error('Split failed')

	Before::

		def my_func(self, request):
			var1 = request.options.get('var1')
			var2 = request.options.get('var2', 20)
			try:
				var1 = int(var1)
				var2 = int(var2)
			except (ValueError, TypeError):
				self.finished(request.id, None, 'Cannot convert to int', status=400)
				return
			if var2 < 10:
				self.finished(request.id, None, 'var2 must be >= 10', status=400)
				return
			self.finished(request.id, var1 + var2)

	After::

		@sanitize(
			var1=IntegerSanitizer(required=True),
			var2=IntegerSanitizer(required=True, minimum=10, default=20)
		)
		def add(self, request):
			var1 = request.options.get('var1')  # could now use ['var1']
			var2 = request.options.get('var2')
			self.finished(request.id, var1 + var2)

	The decorator can be combined with other decorators like
	:func:`simple_response` (be careful with ordering of decorators here)::

		@sanitize(
			var1=IntegerSanitizer(required=True),
			var2=IntegerSanitizer(required=True, minimum=10)
		)
		@simple_response
		def add(self, var1, var2):
			return var1 + var2

	Note that you lose the capability of specifying defaults in
	*@simple_response*. You need to do it in *@sanitize* now.
	"""
	if args:
		return sanitize_list(args[0], **kwargs)
	else:
		return sanitize_dict(kwargs)


def sanitize_list(sanitizer, **kwargs):
	return lambda function: _sanitize_list(function, sanitizer, kwargs)


def sanitize_dict(sanitized_attrs, **kwargs):
	return lambda function: _sanitize_dict(function, sanitized_attrs, kwargs)


def _sanitize_dict(function, sanitized_attrs, sanitizer_parameters):
	defaults = {'default': {}, 'required': True, 'may_change_value': True}
	defaults.update(sanitizer_parameters)
	return _sanitize(function, DictSanitizer(sanitized_attrs, **defaults))


def _sanitize_list(function, sanitizer, sanitizer_parameters):
	defaults = {'default': [], 'required': True, 'may_change_value': True}
	defaults.update(sanitizer_parameters)
	return _sanitize(function, ListSanitizer(sanitizer, **defaults))


def _sanitize(function, sanitizer):
	def _response(self, request):
		request.options = sanitize_args(sanitizer, 'request.options', {'request.options': request.options})
		return function(self, request)
	copy_function_meta_data(function, _response)
	return _response


def sanitize_args(sanitizer, name, args):
	try:
		try:
			return sanitizer.sanitize(name, args)
		except MultiValidationError:
			raise
		except ValidationError as exc:
			multi_error = MultiValidationError()
			multi_error.add_error(exc, name)
			raise multi_error
	except MultiValidationError as exc:
		raise UnprocessableEntity(str(exc), result=exc.result())


def simple_response(function=None, with_flavor=None, with_progress=False):
	'''If your function is as simple as: "Just return some variables"
	this decorator is for you.

	Instead of defining the function

	.. code-block :: python

		def my_func(self, response): pass

	you now define a function with the variables you would expect in
	*request.options*. Default values are supported:

	.. code-block :: python

		@simple_response
		def my_func(self, var1, var2='default'): pass

	The decorator extracts variables from *request.options*. If the
	variable is not found, it either returns a failure or sets it to a
	default value (if specified by you).

	If you need to get the flavor passed to the function you can do it
	like this::

		@simple_response(with_flavor=True)
		def my_func(self, flavor, var1, var2='default'): pass

	With *with_flavor* set, the flavor is extracted from the *request*.
	You can also set with_flavor='varname', in which case the variable
	name for the flavor is *varname*. *True* means 'flavor'.
	As with ordinary option arguments, you may specify a default value
	for flavor in the function definition::

		@simple_response(with_flavor='module_flavor')
		def my_func(self, flavor='this comes from request.options',
			module_flavor='this is the flavor (and its default value)'): pass

	Instead of stating at the end of your function

	.. code-block:: python

		self.finished(request.id, some_value)

	you now just

	.. code-block:: python

		return some_value

	Before::

		def my_func(self, request):
			variable1 = request.options.get('variable1')
			variable2 = request.options.get('variable2')
			flavor = request.flavor or 'default flavor'
			if variable1 is None:
				self.finished(request.id, None, message='variable1 is required', success=False)
				return
			if variable2 is None:
			variable2 = ''
			try:
				value = '%s_%s_%s' % (self._saved_dict[variable1], variable2, flavor)
			except KeyError:
				self.finished(request.id, None, message='Something went wrong', success=False, status=500)
				return
			self.finished(request.id, value)

	After::

		@simple_response(with_flavor=True)
		def my_func(self, variable1, variable2='', flavor='default_flavor'):
			try:
				return '%s_%s_%s' % (self._saved_dict[variable1], variable2, flavor)
			except KeyError:
				raise UMC_Error('Something went wrong')

	'''
	if function is None:
		return lambda f: simple_response(f, with_flavor, with_progress)

	if with_progress is True:
		with_progress = 'progress'

	# fake a generator function that yields whatever the original
	# function returned
	def _fake_func(self, iterator, *args):
		for args in iterator:
			break
		yield function(self, *args)
	copy_function_meta_data(function, _fake_func, copy_arg_inspect=True)
	# fake another variable name
	# the name is not important as it is removed from the list while
	# being processed. Even a variable named 'iterator' in the original
	# function does not break anything
	_fake_func._original_argument_names = ['self', 'iterator'] + _fake_func._original_argument_names[1:]

	_multi_response = _eval_simple_decorated_function(_fake_func, with_flavor)

	def _response(self, request, *args, **kwargs):
		# other arguments than request won't be propagated
		# needed for @LDAP_Connection

		# fake a multi_request
		request.options = [request.options]

		if with_progress:
			progress_obj = self.new_progress()
			request.options[0][with_progress] = progress_obj

			def _thread(self, progress_obj, _multi_response, request):
				try:
					result = _multi_response(self, request)
				except Exception:
					progress_obj.exception(sys.exc_info())
				else:
					progress_obj.finish_with_result(result[0])
			thread = Thread(target=_thread, args=[self, progress_obj, _multi_response, request])
			thread.start()
			self.finished(request.id, progress_obj.initialised())
		else:
			result = _multi_response(self, request)
			if not isinstance(result[0], types.FunctionType):
				self.finished(request.id, result[0])
			else:
				# return value is a function which is meant to be executed as thread
				# TODO: replace notfier by threading

				thread = notifier.threads.Simple('simple_response', notifier.Callback(result[0], self, request), notifier.Callback(self.thread_finished_callback, request))
				thread.run()
	if with_progress:
		_response = sanitize_dict({})(_response)

	copy_function_meta_data(function, _response)
	return _response


def multi_response(function=None, with_flavor=None, single_values=False, progress=False):
	''' This decorator acts similar to :func:`simple_response` but
	can handle a list of dicts instead of a single dict.

	Technically another object is passed to the function that you can
	name as you like. You can iterate over this object and get the values
	from each dictionary in *request.options*.

	Default values and flavors are supported.

	You do not return a value, you yield them (and you are supposed to
	yield!)::

		@multi_response
		def my_multi_func(self, iterator, variable1, variable2=''):
			# here, variable1 and variable2 are yet to be initialised
			# i.e. variable1 and variable2 will be None!
			do_some_initial_stuff()
			try:
				for variable1, variable2 in iterator:
					# now they are set
					yield '%s_%s' % (self._saved_dict[variable1], variable2)
			except KeyError:
				raise UMC_Error('Something went wrong')
			else:
				# only when everything went right...
				do_some_cleanup_stuff()

	The above code will send a list of answers to the client as soon as
	the function is finished (i.e. after *do_some_cleanup_stuff()*)
	filled with values yielded.

	If you have just one variable in your dictionary, do not forget to
	add a comma, otherwise Python will assign the first value a list
	of one element::

		for var, in iterator:
			# now var is set correctly
			pass
	'''
	if function is None:
		return lambda f: multi_response(f, with_flavor, single_values, progress)
	response_func = _eval_simple_decorated_function(function, with_flavor, single_values, progress)

	def _response(self, request):
		result = response_func(self, request)
		self.finished(request.id, result)
	copy_function_meta_data(function, _response)
	return _response


def _eval_simple_decorated_function(function, with_flavor, single_values=False, progress=False):
	# name of flavor argument. default: 'flavor' (if given, of course)
	if with_flavor is True:
		with_flavor = 'flavor'

	# argument names of the function, including 'self'
	arguments, defaults = arginspect(function)
	# remove self, remove iterator
	arguments = arguments[2:]
	# use defaults as dict
	if defaults:
		defaults = dict(zip(arguments[-len(defaults):], defaults))
	else:
		defaults = {}

	@sanitize(DictSanitizer(dict((arg, Sanitizer(required=arg not in defaults and arg != with_flavor, default=defaults.get(arg))) for arg in arguments), _copy_value=False) if not single_values else None)
	def _response(self, request):
		# single_values: request.options is, e.g., ["id1", "id2", "id3"], no need for complicated dicts
		if not single_values:
			# normalize the whole request.options
			for element in request.options:
				# add flavor before default checking
				if with_flavor:
					element[with_flavor] = request.flavor or defaults.get(with_flavor)

		# checked for required arguments, set default... now run!
		iterator = RequestOptionsIterator(request.options, arguments, single_values)
		nones = [None] * len(arguments)
		if progress:
			number = len(request.options)
			if progress is True:
				progress_title = None
			else:
				if isinstance(progress, (list, tuple)):
					progress_title, progress_msg = progress
				else:
					progress_title, progress_msg = progress, None
				if '%d' in progress_title:
					progress_title = progress_title % number
			progress_obj = self.new_progress(progress_title, number)

			def _thread(self, progress_obj, iterator, nones):
				try:
					for res in function(self, iterator, *nones):
						if progress_msg:
							res_msg = progress_msg % res
						progress_obj.progress(res, res_msg)
				except Exception:
					progress_obj.exception(sys.exc_info())
				else:
					progress_obj.finish()
			thread = Thread(target=_thread, args=[self, progress_obj, iterator, nones])
			thread.start()
			return progress_obj.initialised()
		else:
			return list(function(self, iterator, *nones))
	return _response


class RequestOptionsIterator(object):

	def __init__(self, everything, names, single_values):
		self.everything = everything
		self.names = names
		self.single_values = single_values
		self.max = len(self.everything)
		self.current = 0

	def __nonzero__(self):
		return self.current < self.max

	def __iter__(self):
		self.current = 0
		return self

	def next(self):
		if self:
			values = self.everything[self.current]
			self.current += 1
			if self.single_values:
				return values
			else:
				return [values[name] for name in self.names]
		else:
			raise StopIteration


def arginspect(function):
	argspec = inspect.getargspec(function)
	if hasattr(function, '_original_argument_names'):
		arguments = function._original_argument_names
	else:
		arguments = argspec.args
	if hasattr(function, '_original_argument_defaults'):
		defaults = function._original_argument_defaults
	else:
		defaults = argspec.defaults
	return arguments, defaults


def copy_function_meta_data(original_function, new_function, copy_arg_inspect=False):
	# set function attrs to allow another arginspect to get original info
	# (used in @simple_response / @log - combo)
	if copy_arg_inspect:
		arguments, defaults = arginspect(original_function)
		new_function._original_argument_names = arguments
		new_function._original_argument_defaults = defaults
	# copy __doc__, otherwise it would not show up in api and such
	new_function.__doc__ = original_function.__doc__
	# copy __name__, otherwise it would be something like "_response"
	new_function.__name__ = original_function.__name__
	# copy __module__, otherwise it would be "univention.management.console.modules.decorators"
	new_function.__module__ = original_function.__module__


def log(function=None, sensitives=None, customs=None, single_values=False):
	'''Log decorator to be used with
	:func:`simple_response`::

		@simple_response
		@log
		def my_func(self, var1, var2):
			return "%s__%s" % (var1, var2)

	The above example will write two lines into the logfile for the
	module (given that the the UCR variable *umc/module/debug/level*
	is set to at least 3)::

		<date>  MODULE      ( INFO    ) : my_func got: var1='value1', var2='value2'
		<date>  MODULE      ( INFO    ) : my_func returned: 'value1__value2'

	The variable names are ordered by appearance and hold the values that
	are actually going to be passed to the function (i.e. after they were
	:func:`sanitize` 'd or set to their default value).
	You may specify the names of sensitive arguments that should not
	show up in log files and custom functions that can alter the
	representation of a certain variable's values (useful for non-standard
	datatypes like regular expressions - you may have used a
	:class:`~univention.management.console.modules.sanitizers.PatternSanitizer`
	)::

		@sanitize(pattern=PatternSanitizer())
		@simple_reponse
		@log(sensitives=['password'], customs={'pattern':lambda x: x.pattern})
		def count_ucr(self, username, password, pattern):
			return self._ucr_count(username, password, pattern)

	This results in something like::

		<date>  MODULE      ( INFO    ) : count_ucr got: password='********', username='Administrator', pattern='.*'
		<date>  MODULE      ( INFO    ) : count_ucr returned: 650

	The decorator also works with :func:`multi_response`::

		@multi_response
		@log
		def multi_my_func(self, var1, var2):
			return "%s__%s" % (var1, var2)

	This results in something like::

		<date>  MODULE      ( INFO    ) : multi_my_func got: [var1='value1', var2='value2'], [var1='value3', var2='value4']
		<date>  MODULE      ( INFO    ) : multi_my_func returned: ['value1__value2', 'value3__value4']
	'''
	if function is None:
		return lambda f: log(f, sensitives, customs, single_values)
	if customs is None:
		customs = {}
	if sensitives is None:
		sensitives = []
	for sensitive in sensitives:
		customs[sensitive] = lambda x: '********'

	def _log(names, args):
		if single_values:
			args = [args]
		return ['%s=%r' % (name, customs.get(name, lambda x: x)(arg)) for name, arg in zip(names, args)]

	# including self
	names, _ = arginspect(function)
	name = function.__name__
	# multi_response yields i.e. is generator function
	if inspect.isgeneratorfunction(function):
		# remove self, iterator
		names = names[2:]

		def _response(self, iterator, *args):
			arg_reprs = []
			for element in iterator:
				arg_repr = _log(names, element)
				if arg_repr:
					arg_reprs.append(arg_repr)
			if arg_reprs:
				MODULE.info('%s got: [%s]' % (name, '], ['.join(', '.join(arg_repr) for arg_repr in arg_reprs)))
			result = []
			for res in function(self, iterator, *args):
				result.append(res)
				yield res
			MODULE.info('%s returned: %r' % (name, result))
	else:
		# remove self
		names = names[1:]

		def _response(self, *args):
			arg_repr = _log(names, args)
			if arg_repr:
				MODULE.info('%s got: %s' % (name, ', '.join(arg_repr)))
			result = function(self, *args)
			MODULE.info('%s returned: %r' % (name, result))
			return result
	copy_function_meta_data(function, _response, copy_arg_inspect=True)
	return _response


def file_upload(function):
	''' This decorator restricts requests to be
	UPLOAD-commands. Simple, yet effective '''

	def _response(self, request):
		if request.command != 'UPLOAD':
			raise UMC_Error(_('%s can only be used as UPLOAD') % (function.__name__))
		return function(self, request)
	copy_function_meta_data(function, _response)
	prevent_referer_check(_response)
	prevent_xsrf_check(_response)
	return _response


class reloading_ucr(object):

	_last_reload = dict()

	def __init__(self, ucr, timeout=0.2):
		self._ucr = ucr
		self._timeout = timeout

	def __call__(self, func):
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			last_reload = self._last_reload.get(id(self._ucr), 0)
			if last_reload == 0 or time.time() - last_reload > self._timeout:
				self._ucr.load()
				self._last_reload[id(self._ucr)] = time.time()
			return func(*args, **kwargs)
		return wrapper


def require_password(function):
	@functools.wraps(function)
	def _decorated(self, request, *args, **kwargs):
		self.require_password()
		return function(self, request, *args, **kwargs)
	return _decorated


def allow_get_request(function=None, xsrf_check=False, referer_check=False):
	"""Allows HTTP GET requests. Additionally prevents the XSRF check and the referer check."""
	def _decorator(function):
		if not xsrf_check:
			prevent_xsrf_check(function)
		if not referer_check:
			prevent_referer_check(function)
		function.allow_get = True
		return function
	if function is None:
		return _decorator
	return _decorator(function)


def prevent_xsrf_check(function):
	function.xsrf_protection = False
	return function


def prevent_referer_check(function):
	function.referer_protection = False
	return function


__all__ = ['simple_response', 'multi_response', 'sanitize', 'log', 'sanitize_list', 'sanitize_dict', 'file_upload', 'reloading_ucr', 'require_password']
