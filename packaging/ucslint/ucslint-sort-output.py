#!/usr/bin/env python3

"""Sort ucslint output for stable comparison."""

from __future__ import annotations

import re
from argparse import ArgumentParser, FileType
from collections import defaultdict
from operator import itemgetter
from typing import IO


RE_ID = re.compile(r'^([UWEIS]:\d{4}-[BEFNW]?\d+)(?=: )')


def main() -> None:
    """Sort ucslint output for stable comparison."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('content', nargs='?', default='-', type=FileType('r'), help='input')
    parser.add_argument('--group', '-g', action='store_true', help='Group consecutive entries')
    parser.add_argument('--summary', '-s', action='store_true', help='Print summary')
    args = parser.parse_args()

    eventlist = sorted(parse_content(args.content))

    last = ''
    summary: dict[str, int] = defaultdict(int)
    for event in eventlist:
        match = RE_ID.match(event)
        if not match:
            continue
        group = match[0]

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
            print(f'{group:<12s} {count:d}')


def parse_content(content: IO[str]) -> list[str]:
    eventlist: list[str] = []

    tmplines: list[str] = []
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
