# Univention Directory Listener

## Listener/notifier domain replication
See http://docs.software-univention.de/manual-4.2.html#domain:listenernotifier

## Listener module development

### Classic API

See http://docs.software-univention.de/developer-reference-4.2.html#chap:listener

### New API

To use this listener module interface copy `/usr/share/doc/univention-directory-listener/examples/listener_module_template.py` and modify the code to your needs, or:

* subclass ListenerModuleHandler
* add an inner class "Configuration" that has at least the class attributes `name`, `description` and `ldap_filter`


An example from `examples/listener_module_template.py`:

	from __future__ import absolute_import
	from univention.listener import ListenerModuleHandler


	class ListenerModuleTemplate(ListenerModuleHandler):
		class Configuration:
			name = 'unique_name'
			description = 'listener module description'
			ldap_filter = '(&(objectClass=inetOrgPerson)(uid=example))'
			attributes = ['sn', 'givenName']

		def create(self, dn, new):
			self.logger.debug('dn: %r', dn)

		def modify(self, dn, old, new, old_dn):
			self.logger.debug('dn: %r', dn)
			if old_dn:
				self.logger.debug('it is (also) a move! old_dn: %r', old_dn)
			self.logger.debug('changed attributes: %r', self.diff(old, new))

		def remove(self, dn, old):
			self.logger.debug('dn: %r', dn)


### Asynchronous listener module API

The new listener module API support creation of asynchronous listener modules. The code of those modules will not run in the listener process, but in a separate process. The main listener process will only send signals to the worker(s) that do the work and will return immediately.

Asynchronous listener modules can optionally run in multiple instances at once. When a listener module is configured with `parallelism > 1` the handler code will run in multiple processes in parallel. To share variables between the processes, methods are provided to easily save data to and retrieve it from a memcached server.

`set_shared_var()` and `get_shared_var()` can be used to store and retrieve data, `lock()` can be used to prevent race conditions.

All operations on the same LDAP object will be serialized: `create()`, `modify()` and `remove()` will never run in parallel for objects with the same `entryUUID` and the execution order of those functions will be preserved.	Operations on LDAP object with different `entryUUIDs` will run in parallel.

A word of *caution* about `pre_run()` and `post_run()` in asynchronous listener modules: If possible their use should be completely avoided. They will run in the expected order, but as they might be queued in between `create()`, `modify()`, `remove()`, it is possible for those calls to follow a `post_run()`. So even if a `pre_run()` will follow a `post_run()` before the next c/m/r call, it may not be efficient to tear down network/DB connections etc.

`pre_run()` is guaranteed to only run before the first `create/modify/remove()` and after a `post_run()`. `post_run()` is guaranteed to run as the last function.

An asynchronous listener module can be created using the same API as a synchronous listener module! The only difference is the use of `AsyncListenerModuleHandler` and `AsyncListenerModuleAdapter` from `univention.listener.async` instead of the respective classes without the "Async" prefix. In the configuration class `run_asynchronously = True` has to be specified and optionally `parallelism = <int:number of workers>`.

The example above as an asynchronous listener modules:

	from __future__ import absolute_import
	from univention.listener.async import AsyncListenerModuleHandler


	class ListenerModuleTemplate(AsyncListenerModuleHandler):
		class Configuration:
			name = 'listener module template'
			description = 'a listener module template'
			ldap_filter = ''
			attributes = []
			run_asynchronously = True

		def create(self, dn, new):
			self.logger.debug('dn: %r', dn)

		def modify(self, dn, old, new, old_dn):
			self.logger.debug('dn: %r old_dn: %r', dn, old_dn)
			if old_dn:
				self.logger.info('it is (also) a move')

		def remove(self, dn, old):
			self.logger.debug('dn: %r', dn)


## Static type checking new API code
In a UCS 4.2 system:

	# univention-install virtualenv libpython2.7-dev libpython3.4-dev
	# virtualenv -p python3 --system-site-packages virtenv3_mypy
	# . virtenv3_mypy/bin/activate
	(virtenv3_mypy) pip install -U mypy
	(virtenv3_mypy) mypy --py2 --ignore-missing-imports --follow-imports skip /usr/share/pyshared/univention/listener/*
	(virtenv3_mypy) deactivate
