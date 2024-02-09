/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

module.exports = {
  plugins: ['cypress'],
  env: {
    'mocha': true,
    'cypress/globals': true,
  },
  rules: {
    strict: 'off',
  },
};
