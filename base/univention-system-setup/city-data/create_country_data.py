#!/usr/bin/python3
# SPDX-FileCopyrightText: 2014-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Generate `country_data.json`"""

from __future__ import annotations

import json
from argparse import ArgumentParser, FileType
from typing import Any

import _util


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("outfile", type=FileType("w"))
    parser.add_argument("locales", nargs="+")
    opt = parser.parse_args()

    print('generating country data...')
    country_data: dict[str, dict[str, Any]] = {}

    country_default_lang = _util.get_country_default_language()
    for icountry, ilang in country_default_lang.items():
        country_data.setdefault(icountry, {})['default_lang'] = ilang

    nameservers = _util.get_country_code_to_nameserver_map()
    for icountry, iservers in nameservers.items():
        country_data.setdefault(icountry, {}).update(iservers)

    country_code_to_geonameid_map = _util.get_country_code_to_geonameid_map()
    country_geonameids = list(country_code_to_geonameid_map.values())
    for ilocale in [*opt.locales, ""]:
        print('loading data for locale %s' % ilocale)
        country_names = _util.get_localized_names(country_geonameids, ilocale)
        for icode, iid in country_code_to_geonameid_map.items():
            data_set = country_data.get(icode)
            if not data_set:
                print('  empty country code: %s' % icode)
                continue
            ilabel = country_names.get(iid)
            if ilabel:
                data_set.setdefault('label', {})[ilocale] = ilabel

    json.dump(country_data, opt.outfile, ensure_ascii=False, indent=2, sort_keys=True)
    opt.outfile.write("\n")

    print('... done :)')


if __name__ == '__main__':
    main()
