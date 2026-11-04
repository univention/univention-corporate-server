#!/usr/bin/python3
# SPDX-FileCopyrightText: 2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from collections.abc import Iterable

from univention.config_registry import ucr_live as ucr
from univention.lib.i18n import Translation
from univention.management.console.modules.diagnostic import MODULE, Instance, Warning  # noqa: A004


_ = Translation('univention-management-console-module-diagnostic').translate

Range = tuple[int, int]
DEFAULT_UDM_RANGES = '1000-55000,65536-1000000'
DEFAULT_DOMAIN_RANGE = '1000-54999'
DEFAULT_WILDCARD_RANGE = '55000-64000'
SAMBA_AUTOMATIC_IDMAP_RANGE = (3000000, 4000000)

title = _('Check UDM UID/GID ranges against Samba idmap ranges')
description = _('No inconsistencies found between the UDM UID/GID ranges and the Samba idmap ranges.')
run_descr = [_('Checking UDM UID/GID ranges against Samba idmap ranges.')]


def _parse_ranges(value: str, variable: str, fallback_to_default: bool = False) -> list[Range]:
    ranges = []
    fallback_message = _(' UDM falls back to the default UID/GID ranges.') if fallback_to_default else ''
    for item in (value or '').split(','):
        try:
            first, last = (int(number.strip()) for number in item.split('-', 1))
        except (TypeError, ValueError):
            raise ValueError(_('The UCR variable %(variable)s contains the invalid range %(range)r.%(fallback)s') % {'variable': variable, 'range': item, 'fallback': fallback_message}) from None
        if first < 0 or first > last:
            raise ValueError(_('The UCR variable %(variable)s contains the invalid range %(range)r.%(fallback)s') % {'variable': variable, 'range': item, 'fallback': fallback_message})
        ranges.append((first, last))
    if not ranges:
        raise ValueError(_('The UCR variable %(variable)s does not contain a range.') % {'variable': variable})
    return ranges


def _parse_single_range(value: str, variable: str) -> list[Range]:
    ranges = _parse_ranges(value, variable)
    if len(ranges) != 1:
        raise ValueError(_('The UCR variable %(variable)s must contain exactly one contiguous range.') % {'variable': variable})
    return ranges


def _is_covered(ranges: Iterable[Range], covering_ranges: Iterable[Range]) -> bool:
    covering_ranges = sorted(covering_ranges)
    for first, last in ranges:
        next_id = first
        for covering_first, covering_last in covering_ranges:
            if covering_last < next_id:
                continue
            if covering_first > next_id:
                break
            next_id = max(next_id, covering_last + 1)
            if next_id > last:
                break
        if next_id <= last:
            return False
    return True


def _overlap(first: Range, second: Range) -> bool:
    return first[0] <= second[1] and second[0] <= first[1]


def _get_domain_range(domain: str) -> str:
    for domain_name in (domain.upper(), domain.lower()):
        configured_range = ucr.get(f'samba/idmap/{domain_name}/range')
        if configured_range:
            return configured_range
    return DEFAULT_DOMAIN_RANGE


def run(_umc_instance: Instance) -> None:
    errors = []
    udm_ranges = []
    for variable in ('directory/manager/uidNumber/ranges', 'directory/manager/gidNumber/ranges'):
        value = ucr.get(variable, DEFAULT_UDM_RANGES)
        try:
            udm_ranges.extend(_parse_ranges(value, variable, fallback_to_default=True))
        except ValueError as error:
            errors.append(str(error))

    if errors:
        MODULE.error('\n'.join(errors))
        raise Warning('\n'.join(errors))

    if any(_overlap(udm_range, SAMBA_AUTOMATIC_IDMAP_RANGE) for udm_range in udm_ranges):
        errors.append(_('The UDM UID/GID ranges overlap with Samba\'s automatically allocated idmap range %(first)d-%(last)d.') % {'first': SAMBA_AUTOMATIC_IDMAP_RANGE[0], 'last': SAMBA_AUTOMATIC_IDMAP_RANGE[1]})

    domain = ucr.get('windows/domain')
    if not domain or ucr.get('samba4/role') in ('DC', 'RODC'):
        if errors:
            MODULE.error('\n'.join(errors))
            raise Warning('\n'.join(errors))
        return

    domain_variable = f'samba/idmap/{domain}/range'
    wildcard_variable = 'samba/idmap/range'
    try:
        domain_ranges = _parse_single_range(_get_domain_range(domain), domain_variable)
        wildcard_ranges = _parse_single_range(ucr.get(wildcard_variable, DEFAULT_WILDCARD_RANGE), wildcard_variable)
    except ValueError as error:
        MODULE.error(str(error))
        raise Warning(str(error))

    if any(_overlap(domain_range, wildcard_range) for domain_range in domain_ranges for wildcard_range in wildcard_ranges):
        errors.append(_('%(domain_variable)s and %(wildcard_variable)s contain overlapping ranges.') % {'domain_variable': domain_variable, 'wildcard_variable': wildcard_variable})

    if not _is_covered(udm_ranges, domain_ranges):
        errors.append(_('The UDM UID/GID ranges are not covered by %(variable)s. Adjust %(variable)s or the UDM range variables.') % {'variable': domain_variable})

    if errors:
        MODULE.error('\n'.join(errors))
        raise Warning('\n'.join(errors))


if __name__ == '__main__':
    from univention.management.console.modules.diagnostic import main

    main()
