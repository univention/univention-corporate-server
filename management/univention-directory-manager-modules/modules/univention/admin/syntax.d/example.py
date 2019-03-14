# -*- coding: utf-8 -*-
from univention.admin.syntax import select


class ExampleSyntax(select):
	"""
	This is an example for a syntax having 3 values.
	"""
	choices = [
		('value1', 'This item selects value 1'),
		('value2', 'This item selects value 2'),
		('value3', 'This item selects value 3'),
	]
