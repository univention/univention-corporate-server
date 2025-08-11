#!/usr/bin/python3
# SPDX-FileCopyrightText: 2014-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Generate localized country labels."""


import json
from argparse import ArgumentParser, FileType

import _util


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("languageCode", nargs="+")
    parser.add_argument("outfile", type=FileType("w"))
    opt = parser.parse_args()

    print('generating country label data...')
    countries = _util.get_country_code_to_geonameid_map(3)
    country_ids = set(countries.values())
    labels = _util.get_localized_names(country_ids, opt.languageCode)
    final_lables = {icountry: labels.get(igeonameid, '') for icountry, igeonameid in countries.items()}
    json.dump(final_lables, opt.outfile, ensure_ascii=False, indent=2, sort_keys=True)
    opt.outfile.write("\n")

    print('... done :)')


if __name__ == '__main__':
    main()
