#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Sort ucslint output for stable comparison."""
#
from __future__ import print_function
import sys
import re

RE_ID = re.compile('^[UWEIS]:\d\d\d\d-\d+: ')


def main():
	"""Sort ucslint output for stable comparison."""
	if len(sys.argv) == 1:
		content = sys.stdin
	elif len(sys.argv) == 2:
		content = open(sys.argv[1], 'r')
	else:
		print('ucslint-sort-output.py <filename>', file=sys.stderr)
		sys.exit(2)

	tmplines = []
	eventlist = []

	for line in content:
		if RE_ID.match(line):
			if tmplines:
				eventlist.append('\n'.join(tmplines))
			tmplines = []
		tmplines.append(line.rstrip())

	if tmplines:
		eventlist.append('\n'.join(tmplines))

	eventlist.sort()

	for event in eventlist:
		print(event)


if __name__ == '__main__':
	main()
