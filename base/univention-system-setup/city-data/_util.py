#!/usr/bin/python3
# SPDX-FileCopyrightText: 2012-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import json
import os
import sys
from collections.abc import Container
from typing import Any


def _get_path(filename: str) -> str:
    for ipath in (
            os.path.join(os.path.dirname(sys.argv[0]), filename),
            filename,
    ):
        if os.path.exists(ipath):
            return ipath
    raise RuntimeError('Cannot find data file %s' % filename)


def get_country_codes(countryCodeKeyType: int = 2) -> dict[str, str]:
    if countryCodeKeyType == 2:
        idx1 = 0
        idx2 = 1
    elif countryCodeKeyType == 3:
        idx1 = 1
        idx2 = 0
    else:
        raise ValueError('Unknown countryCodeKeyType (=%s), only 2 or 3 allowed' % countryCodeKeyType)

    with open(_get_path('countryInfo.txt')) as infile:
        pairs = {}
        for line in infile:
            if line.startswith('#'):
                continue
            parts = line.split('\t')
            pairs[parts[idx1]] = parts[idx2]
        return pairs


def get_country_code_to_geonameid_map(countryCodeType: int = 2) -> dict[str, str]:
    countries = {}
    if countryCodeType == 2:
        countryCodeIndex = 0
    elif countryCodeType == 3:
        countryCodeIndex = 1
    else:
        raise ValueError('Unknown countryCodeType (=%s), only 2 or 3 allowed' % countryCodeType)

    with open(_get_path('countryInfo.txt')) as infile:
        for line in infile:
            if line.startswith('#'):
                continue
            parts = line.split('\t')
            countries[parts[countryCodeIndex]] = parts[16].strip()
    return countries


def get_country_default_language(countryCodeType: int = 2) -> dict[str, str]:
    if countryCodeType == 2:
        countryCodeIndex = 0
    elif countryCodeType == 3:
        countryCodeIndex = 1
    else:
        raise ValueError('Unknown countryCodeType (=%s), only 2 or 3 allowed' % countryCodeType)

    with open(_get_path('countryInfo.txt')) as infile:
        locales = {}
        for line in infile:
            if line.startswith('#'):
                continue

            parts = line.split('\t')
            languages = parts[15]
            if not languages.strip():
                continue

            default_lang = languages.split(',')[0]
            default_lang = default_lang.split('-')[0]
            country_code = parts[countryCodeIndex]
            locales[country_code] = default_lang

    return locales


def get_city_geonameid_to_country_code_map() -> dict[str, str]:
    cities = {}
    with open(_get_path('cities15000.txt')) as infile:
        for line in infile:
            parts = line.split('\t')
            cities[parts[0]] = parts[8].strip()
    return cities


def get_city_data() -> dict[str, dict[str, Any]]:
    cities = {}
    with open(_get_path('cities15000.txt')) as infile:
        for line in infile:
            parts = line.split('\t')
            cities[parts[0]] = {
                "country": parts[8].strip(),
                "timezone": parts[17].strip(),
                "population": int(parts[14]),
            }
    return cities


def get_localized_names(geonameids: Container[str], lang: str) -> dict[str, str]:
    labels = {}
    label_score: dict[str, int] = {}
    with open(_get_path('alternateNames.txt')) as infile:
        for line in infile:
            parts = line.split('\t')
            iid = parts[1]
            ilang = parts[2]
            ilabel = parts[3]
            isprefered = bool(parts[4])
            isshort = bool(parts[5])

            if ilang == lang and iid in geonameids:
                iscore = isshort + 2 * isprefered
                if iscore >= label_score.get(iid, 0):
                    labels[iid] = ilabel
                    label_score[iid] = iscore

    return labels


def get_alternate_names(geonameids: Container[str], *locales: str) -> list[tuple[str, str]]:
    labels = []
    with open(_get_path('alternateNames.txt')) as infile:
        for line in infile:
            parts = line.split('\t')
            iid = parts[1]
            ilabel = parts[3]
            ilang = parts[2]

            if iid in geonameids and (not ilang or ilang in locales):
                labels.append((iid, ilabel))

    return labels


def get_timezones() -> dict[str, dict[str, str]]:
    with open(_get_path('timeZones.txt')) as infile:
        countries = {}
        for line in infile:
            parts = line.split('\t')
            countries[parts[0]] = {"id": parts[1], "offset": parts[4]}

    return countries


def get_country_code_to_nameserver_map() -> dict[str, dict[str, list[str]]]:
    mapping: dict[str, dict[str, list[str]]] = {}

    with open(_get_path('nameservers.json')) as infile:
        for ientry in json.load(infile):
            country = ientry['country_id']
            if not country:
                continue

            imapEntry = mapping.setdefault(country, {"ipv4": [], "ipv4_erroneous": [], "ipv6": [], "ipv6_erroneous": []})
            ip = ientry['ip']
            has_error = ientry['error']
            idx = ''
            if ':' in ip:
                idx = 'ipv6'
                if has_error:
                    idx = 'ipv6_erroneous'
            else:
                idx = 'ipv4'
                if has_error:
                    idx = 'ipv4_erroneous'

            imapEntry[idx].append(ientry['ip'])

    return mapping
