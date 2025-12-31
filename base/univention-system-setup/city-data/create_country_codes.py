#!/usr/bin/python3
# SPDX-FileCopyrightText: 2014-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Generate `country_codes.json`"""


import json
from argparse import ArgumentParser, FileType

import _util


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("outfile", type=FileType("w"))
    opt = parser.parse_args()

    print('generating country code data...')
    pairs = _util.get_country_codes(3)
    json.dump(pairs, opt.outfile, ensure_ascii=False, indent=2, sort_keys=True)
    opt.outfile.write("\n")

    print('... done :)')


if __name__ == '__main__':
    main()
