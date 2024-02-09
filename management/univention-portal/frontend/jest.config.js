/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

module.exports = {
  preset: '@vue/cli-plugin-unit-jest/presets/typescript-and-babel',
  transform: {
    '^.+\\.vue$': 'vue-jest',
  },
  transformIgnorePatterns: [
    '<rootDir>/node_modules/',
  ],
  moduleNameMapper: {
    // Re-implement aliases here:
    // Also look at
    //   vue.config.js
    //   tsconfig.json
    '^@/(.*)$': '<rootDir>/src/$1',
    '^(globals)($|/.*)$': '<rootDir>/src/components/$1$2',
    '^(components|assets|mixins|views)($|/.*)$': '<rootDir>/src/$1$2',
  },
};
