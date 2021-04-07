import re
from typing import Any, Iterable, Mapping, Set, Text, Union  # noqa F401

from six import binary_type, text_type


RE_SPLIT = re.compile(r"""(?<=")[^"]*(?=") | (?<=')[^']*(?=') | [^ "',]+""", re.VERBOSE)


def split_attributes(value):
	# type: (str) -> Set[str]
	"""
	>>> split_attributes("") == set()
	True
	>>> split_attributes("a b,c") == {"a", "b", "c"}
	True
	>>> split_attributes("'a b'") == {'a b'}
	True
	>>> split_attributes('"a b"') == {'a b'}
	True
	"""
	return set(RE_SPLIT.findall(value))


def php_bool(value):
	# type: (bool) -> str
	"""
	>>> php_bool(True)
	'TRUE'
	>>> php_bool(False)
	'FALSE'
	"""
	return 'TRUE' if value else 'FALSE'


def php_string(text):
	# type: (Text) -> str
	"""
	>>> php_string("")
	"''"
	"""
	text = text.replace("\x00", "")
	text = text.replace("\\", "\\\\")
	text = text.replace("'", "\\'")
	return "'%s'" % (text,)


def php_bytes(byte):
	# type: (bytes) -> str
	"""
	>>> php_bytes(n"")
	"''"
	"""
	return php_string(byte.decode("utf-8"))


def php_int(value):
	# type: (int) -> str
	"""
	>>> php_int(0)
	'0'
	"""
	return str(value)


def php_array(values):
	# type: (Iterable[Any]) -> str
	"""
	>>> php_array(None) == 'array()'
	True
	>>> php_array([]) == 'array()'
	True
	>>> php_array([b""]) == "array('')"
	True
	>>> php_array([u""]) == "array('')"
	True
	>>> php_array(["", ""]) == "array('', '')"
	True
	"""
	return "array(%s)" % (", ".join(php_dump(value) for value in (values or [])),)


def php_dict(mapping):
	# type: (Mapping[str, Any]) -> str
	"""
	>>> php_dict({"a": "b"}) == "array('a' => 'b',)"
	True
	"""
	return "array(%s)" % (
		"\n".join(
			"%s => %s," % (php_string(key), php_dump(value))
			for key, value in mapping.items()
		))


def php_dump(value):
	# type: (Any) -> str
	"""
	>>> php_dump(b"") == "''"
	True
	>>> php_dump(u"") == "''"
	True
	>>> php_dump(False)
	'FALSE'
	>>> php_dump(0)
	'0'
	>>> php_dump([])
	'array()'
	>>> php_dump(())
	'array()'
	>>> php_dump(set())
	'array()'
	>>> php_dump({})
	'array()'
	"""
	if isinstance(value, binary_type):
		return php_bytes(value)
	elif isinstance(value, text_type):
		return php_string(value)
	elif isinstance(value, bool):
		return php_bool(value)
	elif isinstance(value, int):
		return php_int(value)
	elif isinstance(value, (list, tuple, set)):
		return php_array(value)
	elif isinstance(value, dict):
		return php_dict(value)
	else:
		raise TypeError(value)
