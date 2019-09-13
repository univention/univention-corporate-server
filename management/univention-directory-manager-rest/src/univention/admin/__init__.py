__path__ = __import__("pkgutil").extend_path(__path__, __name__)
try:
	locals().update(__import__('imp').load_source('univention.admin', '/usr/share/pyshared/univention/admin/__init__.py').__dict__)
except IOError:
	pass
