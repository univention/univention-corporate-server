modrdn = "1"

_delay = None


def handler(dn, new, old, command):
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


def handler_move(old_dn, old, new_dn, dn):
	"""Handle rename or move of object."""
	pass  # replace this


def handler_schema(old, new):
	"""Handle change in LDAP schema."""
	pass  # replace this
