modrdn = "1"

_old = None


def handler(dn, new, old, command):
	if "a" == command:
		if _old:
			global _old
			old_dn, old = _old
			_old = None
			handler_move(old_dn, old, dn, new)
		else:
			handler_add(dn, new)
	elif "m" == command:
		handler_modify(dn, old, new)
	elif "d" == command:
		handler_remove(dn, old)
	elif "r" == command:
		global _old
		_old = (dn, old)
	elif "n" == command:
		if "cn=Subschema" == dn:
			handler_schema()
		else:
			handler_add(dn, new)
	else:
		pass  # ignore, reserved for future use


def handler_move(old_dn, old, new_dn, dn):
	"""Handle rename or move of object."""
	pass  # replace this


def handlee_schema():
	"""Handle change in LDAP schema."""
	pass  # replace this
