/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

export type Locale = 'en' | 'en_US' | 'de_DE' | 'fr_FR';

export type ShortLocale = 'en' | 'de' | 'fr';

export interface LocaleDefinition {
  id: string;
  label: string;
  default?: boolean;
}
