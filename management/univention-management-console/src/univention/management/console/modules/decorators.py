#!/usr/bin/python2.6
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Decorators for functions inUMC 2.0 modules
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

from ..protocol.definitions import BAD_REQUEST_INVALID_OPTS
from ..modules import UMC_Error, UMC_OptionTypeError
from ..log import MODULE

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
	if function is None:
		if with_flavor is not None:
			return lambda f: _simple_response(f, with_flavor)
		else:
			raise RuntimeError('Dont use @simple_response without a function')
	return _simple_response(function, bool(with_flavor))

def _simple_response(function, with_flavor):
	# name of flavor argument. default: 'flavor' (if given, of course)
	if with_flavor is True:
		with_flavor = 'flavor'
	# argument names of the function, including 'self'
	argspec = inspect.getargspec(function)
	# remove self, use all the others except with_flavor
	arguments = argspec.args[1:]
	if with_flavor:
		arguments.remove(with_flavor)
	defaults = argspec.defaults
	# use defaults as dict
	if defaults:
		defaults = dict(zip(arguments[-len(defaults):], defaults))
	else:
		defaults = {}
	def _response(self, request):
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
		ret = function(self, **kwargs)
		self.finished(request.id, ret)
	# copy __doc__, otherwise it would not show up in api and such
	_response.__doc__ = function.__doc__
	return _response


def _remove_sensitive_data(data, sensitives):
	""" recursive remove sensitive data from containing dicts """
	if isinstance(data, (list, tuple)):
		for i in len(data):
			data[i] = self._remove_sensitive_data(data[i], sensitives)
	elif isinstance(data, dict):
		for sensitive in sensitives:
			if sensitive in data:
				data.pop(sensitive)
	return data

def check_request_options(seq = dict):
	""" check if request options type is valid """
	def check(self, function):
		def _response(self, request):
			if not isinstance(request.options, seq):
				raise UMC_OptionTypeError( _("argument type has to be '%r'") % seq )
			return function(self, request)
		return _response
	return check

def log_request_options(sensitive = []):
	""" log request options, strip sensitive data """
	def log(self, function):
		def _response(self, request):
			options = request.options
			if sensitive:
				from copy import deepcopy
				options = deepcopy(options)
				_remove_sensitive_data(options, sensitive)
			MODULE.info( '%s.%s: options: %s' % (self.__class__.__name__, function.func_name, options) )
			return function(self, request)
		return _response
	return log

__all__ = ['simple_response', 'log_request_options', 'check_request_options']

