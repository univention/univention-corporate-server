/*
 * SPDX-FileCopyrightText: 2021-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

// copy pasted from https://git.knut.univention.de/univention/dev/ucs/-/blob/5.0-0/management/univention-web/js/tools.js

export function isFalse(input: any) {
  if (typeof input === 'string') {
    switch (input.toLowerCase()) {
      case 'no':
      case 'not':
      case 'false':
      case '0':
      case 'disable':
      case 'disabled':
      case 'off':
        return true;
      default:
        break;
    }
  }
  return input === false || input === 0 || input === null || input === undefined || input === '';
}

export function isTrue(input: any) {
  // ('yes', 'true', '1', 'enable', 'enabled', 'on')
  return !isFalse(input);
}
