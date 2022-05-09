#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Sort ucslint output for stable comparison."""
#
import re
from argparse import ArgumentParser, FileType
from collections import defaultdict
from operator import itemgetter
from typing import IO, Dict, List  # noqa: F401

RE_ID = re.compile(r'^([UWEIS]:\d{4}-[BEFNW]?\d+)(?=: )')


def main() -> None:
	"""Sort ucslint output for stable comparison."""
	parser = ArgumentParser(description=__doc__)
	parser.add_argument('content', type=FileType("r"), default='-', nargs='?', help="input")
	parser.add_argument('--group', '-g', action='store_true', help='Group consecutive entries')
	parser.add_argument('--summary', '-s', action='store_true', help='Print summary')
	args = parser.parse_args()

	eventlist = parse_content(args.content)

	eventlist.sort()

	last = ''
	summary = defaultdict(int)  # type: Dict[str, int]
	for event in eventlist:
		match = RE_ID.match(event)
		assert match
		group = match.group()

		if args.group:
			if last and last != group:
				print()
			last = group

		if args.summary:
			summary[group] += 1

		print(event)

	if summary:
		print()
		for group, count in sorted(summary.items(), key=itemgetter(1), reverse=True):
			print('%-12s %d' % (group, count))


def parse_content(content: IO[str]) -> List[str]:
	eventlist = []  # type: List[str]

	tmplines = []  # type: List[str]
	for line in content:
		if not line:
			continue
		if RE_ID.match(line):
			if tmplines:
				eventlist.append('\n'.join(tmplines))
			tmplines = []
		tmplines.append(line.rstrip())

	if tmplines:
		eventlist.append('\n'.join(tmplines))

	return eventlist


if __name__ == '__main__':
	main()
