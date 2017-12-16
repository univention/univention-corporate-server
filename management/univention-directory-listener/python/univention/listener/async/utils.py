# -*- coding: utf-8 -*-
#
# Copyright 2017 Univention GmbH
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
# you and Univention.
#
# This program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

from __future__ import absolute_import
import os
import imp
import sys
import json
import base64
import inspect
import listener
from univention.listener.exceptions import ListenerModuleConfigurationError
from univention.listener.handler_configuration import ListenerModuleConfiguration
from univention.listener.handler import ListenerModuleHandler
from functools import wraps

from listener import configRegistry
try:
	from typing import Dict, List, Tuple, Type, Union
except ImportError:
	pass


__lm_stats_path = '/var/cache/univention-directory-listener/modules_stats_cache.json'
__lm_path = '/usr/lib/univention-directory-listener/system'
recode_attributes = (configRegistry.get('ldap/binaryattributes') or 'krb5Key,userCertificate;binary').split(',')


class DecodeDictError(Exception):
	pass


def encode_dict(dic):  # type: (Dict[str, List[str, str]]) -> Dict[str, List[str, str]]
	if dic:
		for attr in recode_attributes:
			try:
				val = dic[attr]
				if isinstance(val, list):
					dic[attr] = [base64.b64encode(a) for a in val]
				else:
					dic[attr] = base64.b64encode(val)
			except KeyError:
				pass
	return dic


def decode_dict(dic):  # type: (Dict[str, List[str]]) -> Dict[str, List[str]]
	if dic:
		for attr in recode_attributes:
			try:
				val = dic[attr]
				if isinstance(val, list):
					dic[attr] = [base64.b64decode(a) for a in val]
				else:
					dic[attr] = base64.b64decode(val)
			except KeyError:
				pass
	return dic


def decode_dicts(*dicts):
	def inner_wrapper(func):
		argspec = inspect.getargspec(func)
		argnames = argspec.args
		dict_names = ('new', 'old')

		def wrapper_func(*args, **kwargs):
			if not dicts or not (isinstance(dicts, list), isinstance(dicts, tuple)) or not all(s in dict_names for s in dicts):
				raise DecodeDictError('Arguments to decode_dicts must be "new" and/or "old". dicts={!r}'.format(dicts))
			for name in dict_names:
				if name in kwargs:
					kwargs[name] = decode_dict(kwargs[name])
			new_args = list(args)
			for num, name in enumerate(argnames):
				if name in dict_names and name not in kwargs:
					new_args[num] = decode_dict(args[num])
					args = new_args
			return func(*args, **kwargs)
		return wraps(func)(wrapper_func)
	return inner_wrapper


def entry_uuid_var_name(entry_uuid):
	return 'entryUUID_{}'.format(entry_uuid)


def get_configuration_object(path):  # type: (str) -> Union[ListenerModuleConfiguration, None]
	"""
	Load a ListenerModuleConfiguration object from  a file if a
	AsyncListenerModuleHandler is found.

	:param path: str: Path to a Python module.
	:return: ListenerModuleConfiguration object or None
	"""
	module_name = os.path.basename(path)[:-3]
	directory = os.path.dirname(path)

	old_dont_write_bytecode = sys.dont_write_bytecode
	sys.dont_write_bytecode = True
	info = imp.find_module(module_name, [directory])

	# prevent changing of UID in /usr/lib/univention-directory-listener/system/samba4-idmap.py
	old_setuid = listener.setuid
	old_unsetuid = listener.unsetuid
	try:
		listener.setuid = id
		listener.unsetuid = lambda: id(0)

		a_module = imp.load_module(module_name, *info)
	except Exception as exc:
		print('# Error loading module {!r}: {}'.format(path, exc))
		return None
	finally:
		listener.setuid = old_setuid
		listener.unsetuid = old_unsetuid
		sys.dont_write_bytecode = old_dont_write_bytecode

	for thing in dir(a_module):
		candidate = getattr(a_module, thing)
		if (
				inspect.isclass(candidate) and
				issubclass(candidate, ListenerModuleHandler) and
				getattr(candidate, '_support_async', False)
		):
			# found an async handler class
			try:
				return getattr(candidate, '_get_configuration', lambda: None)()
			except ListenerModuleConfigurationError:
				# found the AsyncListenerModuleHandler, and received exception
				# "Missing AsyncListenerModuleHandler.Configuration class."
				continue
	return None


def get_all_configuration_objects():  # type: () -> List[ListenerModuleConfiguration]
	"""
	Search and load ListenerModuleConfiguration objects of
	AsyncListenerModuleHandler classes found in
	/usr/lib/univention-directory-listener/system.

	:return: list: ListenerModuleConfiguration objects
	"""
	conf_objects = list()
	for filename in os.listdir(__lm_path):
		if filename.endswith('.py'):
			conf_obj = get_configuration_object(os.path.join(__lm_path, filename))
			if conf_obj:
				conf_objects.append(conf_obj)
	return conf_objects


def get_listener_module_file_stats():  # type: () -> Dict[str, str]
	res = dict()
	for filename in os.listdir(__lm_path):
		if filename.endswith('.py'):
			res[os.path.join(__lm_path, filename)] = os.stat(os.path.join(__lm_path, filename)).st_mtime
	return res


def load_listener_module_cache():  # type: () -> Dict[str, Dict[str, str]]
	try:
		with open(__lm_stats_path, 'rb') as fp:
			return json.load(fp)
	except (IOError, ValueError):
		return dict()


def store_listener_module_cache(obj):  # type: (Dict[str, Dict[str, str]]) -> None
	try:
		os.mkdir(os.path.dirname(__lm_stats_path))
	except OSError:
		pass
	with open(__lm_stats_path, 'wb') as fp:
		json.dump(obj, fp, indent=4)


def update_listener_module_cache():  # type: () -> Tuple(bool, Dict[str, Dict[str, str]])
	changed = False

	lm_file_stats_new = get_listener_module_file_stats()
	lm_cache = load_listener_module_cache()

	# update entries in loaded cache
	for path, mtime in lm_file_stats_new.items():
		if mtime != lm_cache.get(path, dict()).get('mtime'):
			changed = True
			lm_cache[path] = dict(mtime=mtime)
			conf_obj = get_configuration_object(path)
			if conf_obj:
				lm_cache[path].update({
					'name': conf_obj.get_name(),
					'run_asynchronously': conf_obj.get_run_asynchronously(),
					'parallelism': conf_obj.get_parallelism(),
				})
	# remove entries of nonexistent files
	for key in set(lm_cache.keys()) - set(lm_file_stats_new.keys()):
		changed = True
		del lm_cache[key]
	if changed:
		store_listener_module_cache(lm_cache)
	return changed, lm_cache
