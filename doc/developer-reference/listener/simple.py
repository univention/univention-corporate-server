from typing import Dict, List


def handler(dn: str, new: Dict[str, List[bytes]], old: Dict[str, List[bytes]]) -> None:
	if new and not old:
		handler_add(dn, new)
	elif new and old:
		handler_modify(dn, old, new)
	elif not new and old:
		handler_remove(dn, old)
	else:
		pass  # ignore


def handler_add(dn: str, new: Dict[str, List[bytes]]) -> None:
	"""Handle addition of object."""
	pass  # replace this


def handler_modify(dn: str, old: Dict[str, List[bytes]], new: Dict[str, List[bytes]]) -> None:
	"""Handle modification of object."""
	pass  # replace this


def handler_remove(dn: str, old: Dict[str, List[bytes]]) -> None:
	"""Handle removal of object."""
	pass  # replace this
