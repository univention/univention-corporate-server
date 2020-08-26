#!/usr/bin/python2.7

import sys
import json
import os
from itertools import groupby
from operator import itemgetter
from univention.updater.tools import UCS_Version


def gen_releases(path, releases):  # type: (str, List[Tuple[int, int, int]]) -> None
    """Generate a releases.json string from a list of given releases"""
    data = dict(
        releases=[
            dict(
                major=major,
                minors=[
                    dict(
                        minor=minor,
                        patchlevels=[
                            dict(
                                patchlevel=patchlevel,
                                status="maintained",
                            ) for major, minor, patchlevel in patchlevels
                        ]
                    ) for minor, patchlevels in groupby(minors, key=itemgetter(1))
                ]
            ) for major, minors in groupby(releases, key=itemgetter(0))
        ]
    )
    with open(os.path.join(path, 'releases.json'), 'w') as releases_json:
        json.dump(data, releases_json)


def main():
    releases = []
    for version in sys.argv[2:]:
        mmp = UCS_Version(version)
        releases.append((mmp.major, mmp.minor, mmp.patchlevel))
    gen_releases(sys.argv[1], releases)


if __name__ == '__main__':
    main()
