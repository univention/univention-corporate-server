from typing import Dict, List

modrdn = "1"

_delay = None


def handler(dn: str, new: Dict[str, List[bytes]], old: Dict[str, List[bytes]], command: str) -> None:
	global _delay
	if _delay:
		old_dn, old = _delay
		_delay = None
		if "a" == command and old['entryUUID'] == new['entryUUID']:
			handler_move(old_dn, old, dn, new)
			return
		handler_remove(old_dn, old)

	if "n" == command and "cn=Subschema" == dn:
		handler_schema(old, new)
	elif new and not old:
		handler_add(dn, new)
	elif new and old:
		handler_modify(dn, old, new)
	elif not new and old:
		if "r" == command:
			_delay = (dn, old)
		else:
			handler_remove(dn, old)
	else:
		pass  # ignore, reserved for future use


def handler_add(dn: str, new: Dict[str, List[bytes]]):
	"""Handle creation of object."""
	pass  # replace this


def handler_modify(dn: str, old: Dict[str, List[bytes]], new: Dict[str, List[bytes]]):
	"""Handle modification of object."""
	pass  # replace this


def handler_remove(dn: str, old: Dict[str, List[bytes]]):
	"""Handle removal of object."""
	pass  # replace this


def handler_move(old_dn: str, old: Dict[str, List[bytes]], new_dn: str, new: Dict[str, List[bytes]]):
	"""Handle rename or move of object."""
	pass  # replace this


def handler_schema(old: Dict[str, List[bytes]], new: Dict[str, List[bytes]]):
	"""Handle change in LDAP schema."""
	pass  # replace this
