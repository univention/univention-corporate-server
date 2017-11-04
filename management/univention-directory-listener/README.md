# Univention Directory Listener

## Listener/notifier domain replication
See http://docs.software-univention.de/manual-4.2.html#domain:listenernotifier

## Listener module development
Classic API: see http://docs.software-univention.de/developer-reference-4.2.html#chap:listener

New API: To use this listener module interface copy `/usr/share/doc/univention-directory-listener/examples/listener_module_template.py` and modify the code to your needs, or:

* subclass ListenerModuleHandler
* subclass ListenerModuleConfiguration
* at the bottom add:

		globals().update(ListenerModuleAdapter(ListenerModuleConfiguration()).get_globals())

## Static type checking new API code
In a UCS 4.2 system:

	# univention-install virtualenv libpython2.7-dev libpython3.4-dev
	# virtualenv -p python3 --system-site-packages virtenv3_mypy
	# . virtenv3_mypy/bin/activate
	(virtenv3_mypy) pip install -U mypy
	(virtenv3_mypy) mypy --py2 --ignore-missing-imports --follow-imports skip /usr/share/pyshared/univention/listener/*
	(virtenv3_mypy) deactivate
