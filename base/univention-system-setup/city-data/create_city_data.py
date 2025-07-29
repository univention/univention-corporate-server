#!/usr/bin/python3
#
# SPDX-FileCopyrightText: 2014-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Generate `city_data.json`"""


import json
from argparse import ArgumentParser, FileType

import _util


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("outfile", type=FileType("w"))
    parser.add_argument("locales", nargs="+")
    opt = parser.parse_args()

    print('generating city data...')
    city_data = _util.get_city_data()
    city_geonameids = set(city_data.keys())
    for iid, icity in city_data.items():
        icity['id'] = iid

    for ilocale in [*opt.locales, ""]:
        print('loading data for locale %s' % ilocale)
        city_names = _util.get_localized_names(city_geonameids, ilocale)
        for iid, ilabel in city_names.items():
            city_data[iid].setdefault('label', {})[ilocale] = ilabel

    json.dump(list(city_data.values()), opt.outfile, ensure_ascii=False, indent=2, sort_keys=True)
    opt.outfile.write("\n")

    print('... done :)')


if __name__ == '__main__':
    main()
