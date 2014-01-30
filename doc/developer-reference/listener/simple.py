def handler(dn, new, old):
	if new and not old:
		handler_add(dn, new)
	elif new and old:
		handler_modify(dn, old, new)
	elif not new and old:
		handler_remove(dn, old)
	else:
		pass  # error


def handler_add(dn, new):
	"""Handle addition of object."""
	pass


def handler_modify(dn, old, new):
	"""Handle modification of object."""
	pass


def handler_remove(dn, old):
	"""Handle removal of object."""
	pass
