from pkgutil import extend_path
try:
	from typing import Iterable  # noqa
except ImportError:
	pass
__path__ = extend_path(__path__, __name__)  # type: Iterable[str]
del extend_path
