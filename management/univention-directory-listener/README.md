# Univention Directory Listener

## Listener/notifier domain replication
See [UCS Manual - Listener/notifier domain replication](https://docs.software-univention.de/manual-4.4.html#domain:listenernotifier)

## Listener module development

### Classic API

See [Developer Reference - Univention Directory Listener](https://docs.software-univention.de/developer-reference-4.4.html#chap:listener)

### New API

To use this listener module interface copy [/usr/share/doc/univention-directory-listener/examples/listener_module_template.py](examples/listener_module_template.py) and modify the code to your needs, or:

* subclass `ListenerModuleHandler`
* add an inner class `Configuration` that has at least the class attributes `name`, `description` and `ldap_filter`


An example from `examples/listener_module_template.py`:

```python
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
```

## Static type checking new API code

UCS 4.2 systems provide type information for static type checking using [mypy](http://mypy-lang.org/):

```bash
univention-install virtualenv libpython2.7-dev libpython3.4-dev
virtualenv -p python3 --system-site-packages virtenv3_mypy
. virtenv3_mypy/bin/activate
(virtenv3_mypy) pip install -U mypy
(virtenv3_mypy) mypy --py2 --ignore-missing-imports --follow-imports skip /usr/share/pyshared/univention/listener/*
(virtenv3_mypy) deactivate
```

## Internals

See [src/README.md](src/README.md) for implementation details.
