#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
#
# Univention Management Console
#  Mixins for UMC 2.0 modules
#
# Copyright 2013-2019 Univention GmbH
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
Mixins for UMC module classes
=============================

This module provides some mixins that can be incorporated in existing UMC
modules. These mixins extend the functionality of the module in an easy-to-use
way. Just let your module derive from
:class:`~univention.management.console.module.Base` (as before) and the mixin
classes.
"""
import random

import six

from univention.lib.i18n import Translation
from univention.management.console.error import BadRequest
from univention.management.console.modules.decorators import simple_response

_ = Translation('univention-management-console').translate


class Progress(object):

	"""
	Class to keep track of the progress during execution of a function.
	Used internally.
	"""

	def __init__(self, progress_id, title, total):
		self.id = progress_id
		self.title = title
		self.message = ''
		self.current = 0.0
		self.total = total
		self.intermediate = []
		self.finished = False
		self.exc_info = None
		self.retry_after = 200
		self.location = None
		# there is another variable named
		#   "result". it is only set if explicitly
		#   calling finish_with_result

	def progress(self, detail=None, message=None):
		self.current += 1
		self.intermediate.append(detail)
		if message is not None:
			self.message = message

	def finish(self):
		if self.finished:
			return False
		self.finished = True
		return True

	def finish_with_result(self, result):
		if self.finish():
			self.result = result

	def initialised(self):
		return {'id': self.id, 'title': self.title}

	def exception(self, exc_info):
		self.exc_info = exc_info

	def poll(self):
		if self.exc_info:
			self.finish()
			six.reraise(self.exc_info[1], None, self.exc_info[2])
		ret = {
			'title': self.title,
			'finished': self.finished,
			'intermediate': self.intermediate[:],
			'message': self.message,
			'retry_after': self.retry_after,
		}
		try:
			ret['percentage'] = self.current / self.total * 100
		except ZeroDivisionError:
			# ret['percentage'] = float('Infinity') FIXME: JSON cannot handle Infinity
			ret['percentage'] = 'Infinity'
		if self.location is not None:
			ret['location'] = self.location
		if hasattr(self, 'result'):
			ret['result'] = self.result
		del self.intermediate[:]
		return ret


class ProgressMixin(object):

	"""
	Mixin to provide two new functions:

	* *new_progress* to create a new :class:`~univention.management.console.modules.mixins.Progress`.
	* *progress* to let the client fetch the progress made up to this moment.

	The *progress* function needs to be made public by the XML definition of the module. To use this mixin, just do::

		class Instance(Base, ProgressMixin):
			pass

	"""

	def new_progress(self, title=None, total=0):
		if not hasattr(self, '_progress_id'):
			self._progress_id = 0
		if not hasattr(self, '_progress_objs'):
			self._progress_objs = {}
		if title is None:
			title = _('Please wait for operation to finish')
		self._progress_id += random.randint(1, 100000)
		self._progress_objs[self._progress_id] = progress = Progress(self._progress_id, title, total)
		return progress

	@simple_response
	def progress(self, progress_id):
		if not hasattr(self, '_progress_objs'):
			self._progress_objs = {}
		try:
			progress_obj = self._progress_objs[progress_id]
		except KeyError:
			raise BadRequest(_('Invalid progress ID'))
		else:
			ret = progress_obj.poll()
			if ret['finished']:
				del self._progress_objs[progress_id]
			return ret
