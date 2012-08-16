#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Decorators for functions in UMC 2.0 modules
#
# Copyright 2012 Univention GmbH
#
# http://www.univention.de/
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
# <http://www.gnu.org/licenses/>.

"""
Convenience decorators for developers of UMC modules
====================================================

Functions exposed by UMC modules often share some logic. They check the
existance and formatting of variables or check permissions. If anything
fails, they react in a similar way. If everything is correct, the real
logic is often as simple as returning one single value.

This module provides functions that can be used to separate repeating
tasks from the actual business logic. This means:

 * less time to code
 * fewer bugs
 * consistent behaviour throughout the UMC in standard cases

Note that the functions defined herein do not cover every corner case during
UMC module development. You are not bound to use them if you need more
flexibility.
"""

import inspect
import univention.debug as ud
from univention.lib.i18n import Translation
_ = Translation( 'univention.management.console' ).translate

from ..protocol.definitions import BAD_REQUEST, BAD_REQUEST_INVALID_OPTS, BAD_REQUEST_INVALID_ARGS
from ..modules import UMC_Error, UMC_OptionTypeError
from ..log import MODULE

from .sanitizers import ValidationError

def sanitize(**kwargs):
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
	     var2 = request.options.get('var2')
	     try:
	         var1 = int(var1)
		 var2 = int(var2)
             except ValueError:
	         self.finished(request.id, None, 'Cannot convert to int', success=False, status=BAD_REQUEST)
		 return
	     if var2 < 10:
	         self.finished(request.id, None, 'var2 must be >= 10', success=False, status=BAD_REQUEST)
		 return
	     self.finished(request.id, var1 + var2)

	After::

	 @sanitize(var1=IntegerSanitizer(required=True),
	   var2=IntegerSanitizer(required=True, minimum=10))
	 def add(self, request):
	     var1 = request.options.get('var1')
	     var2 = request.options.get('var2')
	     self.finished(request.id, var1 + var2)

	The decorator can be combined with other decorators like
	:func:`simple_response` (be careful with ordering of decorators here)::

	 @sanitize(var1=IntegerSanitizer(required=True),
	   var2=IntegerSanitizer(required=True, minimum=10))
	 @simple_response
	 def add(self, var1, var2):
	     return var1 + var2
	"""
	return lambda function: _sanitize(function, kwargs)

def _sanitize(function, sanitized_arguments):
	def _response(self, request):
		copied_options = request.options.copy()
		for field, sanitizer in sanitized_arguments.iteritems():
			try:
				value, value_might_be_changed = sanitizer.sanitize(field, copied_options)
				if value_might_be_changed and sanitizer.may_change_value:
					request.options[field] = value
			except ValidationError as e:
				self.finished(request.id, {'name' : e.name, 'value' : e.value}, message=str(e), success=False, status=BAD_REQUEST)
				return
		return function(self, request)
	copy_function_meta_data(function, _response)
	return _response

def _error_handler(options, exception):
	raise exception

def _simple_response(function, with_flavor):
	# name of flavor argument. default: 'flavor' (if given, of course)
	if with_flavor is True:
		with_flavor = 'flavor'
	arguments, defaults = arginspect(function)
	# argument names of the function, including 'self'
	# remove self
	arguments = arguments[1:]
	# use defaults as dict
	if defaults:
		defaults = dict(zip(arguments[-len(defaults):], defaults))
	else:
		defaults = {}
	# remove flavor argument, if given
	# do it here to have a chance to add it in defaults
	if with_flavor:
		arguments.remove(with_flavor)
	def _response(self, request):
		if not isinstance(request.options, dict):
			raise UMC_OptionTypeError(_("argument type has to be '%s'") % 'dict')
		# check for required arguments (those without default)
		self.required_options(request, *[arg for arg in arguments if arg not in defaults])

		# extract arguments from request or take from default
		# pass arguments as **kwargs, not *args to be more flexible with defaults
		kwargs = {}
		# safely iterate over arguments, dont merge the whole request.options at once
		# who knows what else the user sent?
		for arg in arguments:
			# as we checked before, it is either in request.options or defaults
			kwargs[arg] = request.options.get(arg, defaults.get(arg))
		if with_flavor:
			kwargs[with_flavor] = request.flavor or defaults.get(with_flavor)
		return function(self, **kwargs)
	copy_function_meta_data(function, _response)
	return _response

def _multi_response(function, with_flavor, error_handler):
	def _response(self, request):
		if not isinstance(request.options, (list,tuple)):
			raise UMC_OptionTypeError(_("argument type has to be '%s'") % 'list')

		simple = _simple_response(function, with_flavor)

		response = []
		for option in request.options:
			try:
				req = type('request', (object,), {'options' : option, 'flavor': request.flavor})
				res = simple(self, req)
				#res = simple(self, type('request', (object,), {'options' : option, 'flavor': request.flavor}))
			except Exception, e:
				res = error_handler(option, e)
			finally:
				response.append(res)

		self.finished(request.id, response)
	copy_function_meta_data(function, _response)
	return _response

def simple_response(function=None, with_flavor=None):
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

	 def my_func(self, response):
	   variable1 = response.options.get('variable1')
	   variable2 = response.options.get('variable2')
	   flavor = response.flavor or 'default flavor'
	   if variable1 is None:
	     self.finished(request.id, None, message='variable1 is required', success=False)
	     return
	   if variable2 is None:
	     variable2 = ''
	   try:
	     value = '%s_%s_%s' % (self._saved_dict[variable1], variable2, flavor)
	   except KeyError:
	     self.finished(required.id, None, message='Something went wrong', success=False, status=500)
	     return
	   self.finished(request.id, value)

	After::

	 @simple_response(with_flavor=True)
	 def my_func(self, variable1, variable2='', flavor='default_flavor'):
	   try:
	     return '%s_%s_%s' % (self._saved_dict[variable1], variable2, flavor)
	   except KeyError:
	     raise UMC_CommandError('Something went wrong')

	'''
	def _response(self, request):
		self.finished(request.id, _simple_response(function, with_flavor)(self, request))
	if function is None:
		return lambda f: simple_response(f, with_flavor)
	copy_function_meta_data(function, _response)
	return _response

def multi_response(function=None, with_flavor=None, error_handler=_error_handler):
	if function is None:
		return lambda f: _multi_response(f, with_flavor, error_handler)
	return _multi_response(function, with_flavor, error_handler)

def _replace_sensitive_data(data, sensitives):
	""" recursive replace sensitive data with ****** from containing dicts """
	if isinstance(data, (list, tuple)):
		data = [_replace_sensitive_data(d, sensitives) for d in data]
	elif isinstance(data, dict):
		for sensitive in sensitives:
			if sensitive in data:
				data[sensitive] = '******'
	return data

def check_request_options(function=None, types=dict):
	""" check if request options type is valid """
	def check(function):
		def _response(self, request):
			if not isinstance(request.options, types):
				typename = ', '.join(map(lambda t: str(t.__name__), types)) if isinstance(types, tuple) else types.__name__
				raise UMC_OptionTypeError( _("argument type has to be '%s'") % typename )
			return function(self, request)
		return _response
	if function is not None:
		return check(function)
	return check

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

def log(function=None, sensitives=()):
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

	The variable names are ordered by name and hold the values that
	are actually going to be passed to the function (i.e. after they were
	:func:`sanitize` 'd or set to their default value).
	You may specify the names of sensitive arguments that should not
	show up in log files::

	 @simple_reponse
	 @log(sensitives=['password'])
	 def login(self, username, password):
	     return self._login_user(username, password)

	This results in::

	 <date>  MODULE      ( INFO    ) : login got: password='********', username='Administrator'
	 <date>  MODULE      ( INFO    ) : login returned: True

	The decorator also works with :func:`multi_response`::

	 @multi_response
	 @log
	 def multi_my_func(self, var1, var2):
	     return "%s__%s" % (var1, var2)

	This will give two lines in the logfile for each element in the
	list of *request.options*::

	 <date>  MODULE      ( INFO    ) : multi_my_func got: var1='value1', var2='value2'
	 <date>  MODULE      ( INFO    ) : multi_my_func returned: 'value1__value2'
	 <date>  MODULE      ( INFO    ) : multi_my_func got: var1='value3', var2='value4'
	 <date>  MODULE      ( INFO    ) : multi_my_func returned: 'value3__value4'

	'''
	if function is None:
		return lambda f: log(f, sensitives)
	sensitives = dict([(key, '********') for key in sensitives])
	def _response(self, **kwargs):
		name = function.__name__ # perhaps something like self.__class__.__module__?
		argument_representation = ['%s=%r' % (key, sensitives.get(key, kwargs[key])) for key in sorted(kwargs.keys())]
		if argument_representation:
			MODULE.info('%s got: %s' % (name, ', '.join(argument_representation)))
		ret = function(self, **kwargs)
		MODULE.info('%s returned: %r' % (name, ret))
		return ret
	copy_function_meta_data(function, _response, copy_arg_inspect=True)
	return _response

def log_request_options(function=None, sensitive=[]):
	""" log request options, strip sensitive data """
	def log(function):
		def _response(self, request):
			options = request.options
			if sensitive:
				from copy import deepcopy
				options = deepcopy(options)
				_replace_sensitive_data(options, sensitive)
			MODULE.info( '%s.%s: options: %s' % (self.__class__.__name__, function.func_name, options) )
			return function(self, request)
		return _response
	if function is not None:
		return log(function)
	return log

__all__ = ['simple_response', 'multi_response', 'log_request_options', 'check_request_options', 'sanitize', 'log']

