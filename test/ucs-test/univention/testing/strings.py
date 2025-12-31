#
# UCS test
#
# SPDX-FileCopyrightText: 2013-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import string
from collections.abc import Iterator
from random import choice, randint


STR_NUMERIC = string.digits
STR_ALPHA = string.ascii_letters
STR_ALPHANUM = STR_ALPHA + STR_NUMERIC
STR_ALPHANUMDOTDASH = STR_ALPHANUM + '.-'

STR_SPECIAL_CHARACTER = '!"#$ %&\'()*+,-./:;<=>?@[\\]^_`{|}~ ´€Ω®½'
STR_UMLAUT = 'äöüßâêôûŵẑŝĝĵŷĉÄÖÜÂÊÔÛŴẐŜĜĴŶĈ'
STR_UMLAUTNUM = STR_UMLAUT + STR_NUMERIC
FORBIDDEN_USERNAME_CHARS = ''.join((  # noqa: FLY002
    '@',  # heimdal kerberos principal name breaks due to duplicated @
    '$',  # not identifyable as users/user
    r'"/\[]:;|=,+*?<>',  # ldap.CONSTRAINT_VIOLATION: "0000202F: samldb: sAMAccountName contains invalid '+' character\n", see https://learn.microsoft.com/en-us/windows/win32/adschema/a-samaccountname
))
STR_SPECIAL_USERNAME_CHARACTER = STR_SPECIAL_CHARACTER.translate(str.maketrans('', '', FORBIDDEN_USERNAME_CHARS))


def random_string(length: int = 10, alpha: bool = True, numeric: bool = True, mixed_case: bool = False, charset: str = "", encoding: str = 'utf-8') -> str:
    """
    Get specified number of random characters (ALPHA, NUMERIC or ALPHANUMERIC).
    Default is an alphanumeric string of 10 characters length. A custom character set
    may be defined via "charset" as string. The default encoding is UTF-8.
    If length is 0 or negative, an empty string is returned.
    """
    result = ''
    for _ in range(length):
        if charset:
            result += choice(charset)
        elif alpha and numeric:
            result += choice(STR_ALPHANUM)
        elif alpha:
            result += choice(STR_ALPHA)
        elif numeric:
            result += choice(STR_NUMERIC)
    if not mixed_case:
        return result.lower()
    return result


def random_name(length: int = 10, mixed_case: bool = False) -> str:
    """create random name (1 ALPHA, 8 ALPHANUM, 1 ALPHA)"""
    return ''.join((
        random_string(length=1, alpha=True, numeric=False, mixed_case=mixed_case),
        random_string(length=(length - 2), alpha=True, numeric=True, mixed_case=mixed_case),
        random_string(length=1, alpha=True, numeric=False, mixed_case=mixed_case),
    ))


def random_name_special_characters(length: int = 10) -> str:
    """create random name (1 UMLAUT, 2 ALPHA, 6 SPECIAL_CHARACTERS + UMLAUT, 1 UMLAUTNUM)"""
    return ''.join((
        random_string(length=1, alpha=False, numeric=False, charset=STR_UMLAUT),
        random_string(length=2, alpha=True, numeric=False),
        random_string(length=(length - 4), alpha=False, numeric=False, charset=STR_SPECIAL_CHARACTER + STR_UMLAUT),
        random_string(length=1, alpha=False, numeric=False, charset=STR_UMLAUTNUM),
    ))


def random_username_special_characters(length: int = 10) -> str:
    """create random username (1 UMLAUT, 2 ALPHA, 6 SPECIAL_CHARACTERS + UMLAUT, 1 UMLAUTNUM)"""
    return ''.join((
        random_string(length=1, alpha=False, numeric=False, charset=STR_UMLAUT),
        random_string(length=2, alpha=True, numeric=False),
        random_string(length=(length - 4), alpha=False, numeric=False, charset=STR_SPECIAL_USERNAME_CHARACTER + STR_UMLAUT),
        random_string(length=1, alpha=False, numeric=False, charset=STR_UMLAUTNUM),
    ))


random_username = random_name
random_groupname = random_name


def random_int(bottom_end: int = 0, top_end: int = 9) -> str:
    return str(randint(bottom_end, top_end))


def random_version(elements: int = 3) -> str:
    return '.'.join(random_int(0, 9) for _ in range(elements))


def random_ucs_version(min_major: int = 1, max_major: int = 9, min_minor: int = 0, max_minor: int = 99, min_patchlevel: int = 0, max_patchlevel: int = 99) -> str:
    return '%s.%s-%s' % (
        randint(min_major, max_major),
        randint(min_minor, max_minor),
        randint(min_patchlevel, max_patchlevel),
    )


def random_mac() -> str:
    return ':'.join(
        f"{randint(0, 0x7f if i < 4 else 0xff):02x}"
        for i in range(6)
    )


def random_ip(ip_iter: Iterator[int] = iter(range(11, 121))) -> str:
    """Returns 110 different ip addresses in the range 11.x.x.x-120.x.x.x"""
    return '%d.%d.%d.%d' % (
        next(ip_iter),
        randint(1, 254),
        randint(1, 254),
        randint(1, 254),
    )


def random_subnet(ip_iter: Iterator[int] = iter(range(11, 121))) -> str:
    """Returns 110 different ip addresses in the range 11.x.x.x-120.x.x.x"""
    return '%d.%d.%d' % (
        next(ip_iter),
        randint(1, 254),
        randint(1, 254),
    )


def random_ipv6_subnet() -> str:
    """Returns random six blocks of an ipv6 address"""
    m = 16**4
    return ":".join("%04x" % randint(0, m) for i in range(6))


def random_domain_name(length: int = 10) -> str:
    return '%s.%s' % (
        random_string(length=length // 2, alpha=True, numeric=False),
        random_string(length=length - length // 2, alpha=True, numeric=False),
    )


def random_dns_record() -> str:
    # Bug #49679: the S4-Connector always appends a dot to nSRecord and ptrRecords without dot
    return f'{random_string()}.'


def random_date() -> str:
    return '20%02d-%02d-%02d' % (randint(0, 99), randint(1, 12), randint(1, 27))


def random_time(range_hour: tuple[int, int] = (0, 23)) -> str:
    return '%02d:%02d:%02d' % (randint(*range_hour), randint(0, 60), randint(0, 60))


def random_email() -> str:
    return f'{random_name()}@{random_domain_name()}'
