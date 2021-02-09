#!/usr/bin/python

import argparse
import json
import os
from itertools import groupby
from operator import itemgetter
from univention.lib.ucs import UCS_Version
try:
    from typing import List, Tuple  # noqa F401
except ImportError:
    pass


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


def main():  # type: () -> None
    parser = argparse.ArgumentParser(
        description='Generates a valid releases.json.'
    )
    parser.add_argument('repodir', help='path to repository, where releases.json is created/updated.')
    parser.add_argument('versions', nargs='*', help='a UCS version to be added to the releases.json. If omitted, the  automatic UCS version detection is activated!')
    args = parser.parse_args()
    releases = []
    if args.versions:
        for version in args.versions:
            mmp = UCS_Version(version)
            releases.append((mmp.major, mmp.minor, mmp.patchlevel))
    else:
        distdir = os.path.join(args.repodir, 'dists')
        for dirname in os.listdir(distdir):
            if not os.path.isdir(os.path.join(distdir, dirname)):
                continue
            if not dirname.startswith('ucs'):
                continue
            if len(dirname) != 6:
                raise Exception('unexpected dirname length: {}'.format(dirname))
            major, minor, patchlevel = [int(x) for x in dirname[3:]]
            releases.append((major, minor, patchlevel))

    gen_releases(args.repodir, releases)


if __name__ == '__main__':
    main()
