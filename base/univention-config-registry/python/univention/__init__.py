# this file should be removed, once the python-univention package has been
# converted to dh_python2

# find univention.* (except univention.config_registry) below /usr/share/pyshared
# (as that's in sys.path)
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

