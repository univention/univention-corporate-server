from univention.admin.syntax import select


class ExampleSyntax(select):

	choices = [
		('value1', 'This item selects value 1'),
		('value2', 'This item selects value 2'),
		('value3', 'This item selects value 3'),
	]
