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
from ..modules import UMC_Error, UMC_OptionMissing

def simple_response(function):
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

	Instead of stating at the end of your function
	
	.. code-block:: python

	 self.finished(request.id, some_value)

	you now just
	
	.. code-block:: python

	 return some_value

	You may raise one of the Exceptions derived from
	:class:`~univention.management.console.modules.UMC_Error`.
	It will be correctly propagated if initialised like this::

	 raise UMC_Error(406, 'This is the error message')
	
	Note that some status codes are translated to 500 for HTTP.

	Other exceptions are not supported and will be handled by the UMC
	server itself which results in a 500 Internal Server Error.

	Before::

	 def my_func(self, response):
	   variable1 = response.options.get('variable')
	   variable2 = response.options.get('variable2')
	   if variable1 is None:
	     self.finished(request.id, None, message='variable1 is required', success=False)
	     return
	   if variable2 is None:
	     variable2 = ''
	   try:
	     value = '%s_%s' % (self._saved_dict[variable1], variable2)
	   except KeyError:
	     self.finished(required.id, None, message='Something went wrong', success=False, status=407)
	     return
	   self.finished(request.id, value)

	After::

	 @simple_response
	 def my_func(self, variable1, variable2=''):
	   try:
	     return '%s_%s' % (self._saved_dict[variable1], variable2)
	   except KeyError:
	     raise UMC_CommandError(407, 'Something went wrong')

	'''
	# argument names of the function, including 'self'
	argspec = inspect.getargspec(function)
	# remove self, use all the others
	arguments = argspec.args[1:]
	defaults = argspec.defaults
	# use defaults as dict
	if defaults:
		defaults = dict(zip(arguments[-len(defaults):], defaults))
	else:
		defaults = {}
	def _response(self, request):
		# try: as long as error handling in umc.modules is mercyless
		# we need to catch them here and return a status code not
		# as hard as 500
		try:
			try:
				# check for required arguments (those without default)
				self.required_options(request, *[arg for arg in arguments if arg not in defaults])
			except UMC_OptionMissing as e:
				# insert a status_code here
				# better raise 40x
				# codes like CLIENT_ERR_NONFATAL 301 are mapped to 500 for HTTP requests.
				raise UMC_OptionMissing(BAD_REQUEST_INVALID_OPTS, str(e))

			# extract arguments from request or take from default
			# pass arguments as **kwargs, not *args to be more flexible with defaults
			kwargs = {}
			# safely iterate over arguments, dont merge the whole request.options at once
			# who knows what else the user sent?
			for arg in arguments:
				# as we checked before, it is either in request.options or defaults
				kwargs[arg] = request.options.get(arg, defaults.get(arg))
			ret = function(self, **kwargs)
		except UMC_Error as e:
			try:
				# we hope it was initialized this way:
				# UMC_Error(status_code, message)
				self.finished(request.id, None, message=e.args[1], success=False, status=e.args[0])
				return
			except:
				pass
			# otherwise we should let UMC handle it (with a meaningful traceback)
			raise
		else:
			self.finished(request.id, ret)
	# copy __doc__, otherwise it would not show up in api and such
	_response.__doc__ = function.__doc__
	return _response

